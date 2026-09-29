import sqlite3
from datetime import datetime, timedelta

from src.db.conexion import obtener_conexion
from src.model.auditoria.servicio import registrar_evento

_HORA_APERTURA = datetime.strptime("08:00", "%H:%M")
_HORA_CIERRE = datetime.strptime("20:00", "%H:%M")


def crear_reservacion(carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas):
    """RF-05: Crea una reservación activa si cumple las reglas de negocio."""
    conexion = obtener_conexion()
    try:
        datos, error = _preparar_datos_reservacion(
            conexion,
            carne=carne,
            codigo_sala=codigo_sala,
            fecha=fecha,
            hora_inicio=hora_inicio,
            duracion=duracion,
            cantidad_personas=cantidad_personas,
        )
        if error:
            return {"exito": False, "mensaje": error}

        if _contar_reservaciones_vigentes(conexion, datos["estudiante_id"]) >= 3:
            return {
                "exito": False,
                "mensaje": "El estudiante ya tiene el máximo de 3 reservaciones activas.",
            }

        conflicto = _buscar_conflicto(
            conexion,
            sala_id=datos["sala_id"],
            fecha=datos["fecha"],
            hora_inicio=datos["hora_inicio"],
            hora_fin=datos["hora_fin"],
        )
        if conflicto:
            return {"exito": False, "mensaje": conflicto}

        cursor = conexion.execute(
            """
            INSERT INTO reservaciones (
                estudiante_id, sala_id, fecha, hora_inicio,
                duracion_horas, cantidad_personas, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, 'activa')
            """,
            (
                datos["estudiante_id"],
                datos["sala_id"],
                datos["fecha"],
                datos["hora_inicio"],
                datos["duracion"],
                datos["cantidad_personas"],
            ),
        )
        identificador = _formatear_id(cursor.lastrowid)

        resultado_auditoria = registrar_evento(
            accion="creacion",
            entidad="reservacion",
            entidad_id=identificador,
            detalle=f"Reservación {identificador} creada correctamente.",
            conexion=conexion,
        )

        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {
                "exito": False,
                "mensaje": "No fue posible crear la reservación.",
            }

        conexion.commit()
        return {
            "exito": True,
            "mensaje": f"Reservación {identificador} creada correctamente.",
            "id": identificador,
        }
    except sqlite3.Error:
        conexion.rollback()
        return {"exito": False, "mensaje": "No fue posible crear la reservación."}


def previsualizar_reservaciones_recurrentes(
    carne,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
    semanas,
):
    """RF-14: valida de 2 a 8 ocurrencias semanales sin persistirlas."""
    conexion = obtener_conexion()
    try:
        evaluacion = _evaluar_recurrencia(
            conexion,
            carne=carne,
            codigo_sala=codigo_sala,
            fecha=fecha,
            hora_inicio=hora_inicio,
            duracion=duracion,
            cantidad_personas=cantidad_personas,
            semanas=semanas,
        )
        evaluacion.pop("_datos", None)
        return evaluacion
    except sqlite3.Error:
        return _respuesta_recurrencia_error(
            "No fue posible previsualizar las reservaciones recurrentes."
        )


def crear_reservaciones_recurrentes(
    carne,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
    semanas,
):
    """RF-14: crea una serie semanal completa en una sola transacción."""
    conexion = obtener_conexion()
    try:
        evaluacion = _evaluar_recurrencia(
            conexion,
            carne=carne,
            codigo_sala=codigo_sala,
            fecha=fecha,
            hora_inicio=hora_inicio,
            duracion=duracion,
            cantidad_personas=cantidad_personas,
            semanas=semanas,
        )
        datos_ocurrencias = evaluacion.pop("_datos", [])
        if not evaluacion["exito"]:
            return evaluacion
        if not evaluacion["puede_crear"]:
            return {
                **evaluacion,
                "exito": False,
                "mensaje": (
                    "La serie no fue creada porque una o más ocurrencias "
                    "presentan conflictos."
                ),
            }

        serie_id = _generar_id_serie(conexion)
        ids = []
        for datos in datos_ocurrencias:
            cursor = conexion.execute(
                """
                INSERT INTO reservaciones (
                    estudiante_id, sala_id, fecha, hora_inicio,
                    duracion_horas, cantidad_personas, estado, serie_id
                )
                VALUES (?, ?, ?, ?, ?, ?, 'activa', ?)
                """,
                (
                    datos["estudiante_id"],
                    datos["sala_id"],
                    datos["fecha"],
                    datos["hora_inicio"],
                    datos["duracion"],
                    datos["cantidad_personas"],
                    serie_id,
                ),
            )
            ids.append(_formatear_id(cursor.lastrowid))

        resultado_auditoria = registrar_evento(
            accion="creacion",
            entidad="reservacion",
            entidad_id=serie_id,
            detalle=(
                f"Serie {serie_id} creada correctamente con "
                f"{len(ids)} ocurrencias."
            ),
            conexion=conexion,
        )
        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return _respuesta_recurrencia_error(
                "No fue posible crear la serie recurrente."
            )

        conexion.commit()
        return {
            "exito": True,
            "puede_crear": True,
            "mensaje": f"Serie {serie_id} creada correctamente.",
            "serie_id": serie_id,
            "ids": ids,
            "ocurrencias": evaluacion["ocurrencias"],
        }
    except sqlite3.Error:
        conexion.rollback()
        return _respuesta_recurrencia_error(
            "No fue posible crear la serie recurrente."
        )


def consultar_reservaciones():
    """RF-06: Retorna todas las reservaciones, activas y canceladas."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            """
            SELECT
                r.id,
                e.carne,
                e.nombre_completo AS estudiante,
                s.codigo AS sala,
                s.nombre AS nombre_sala,
                r.fecha,
                r.hora_inicio,
                r.duracion_horas,
                r.cantidad_personas,
                r.estado,
                r.serie_id
            FROM reservaciones AS r
            JOIN estudiantes AS e ON r.estudiante_id = e.id
            JOIN salas AS s ON r.sala_id = s.id
            ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC
            """
        ).fetchall()

        reservaciones = []
        for fila in filas:
            hora_fin = _calcular_hora_fin(fila["hora_inicio"], fila["duracion_horas"])
            reservaciones.append(
                {
                    "id": _formatear_id(fila["id"]),
                    "carne": fila["carne"],
                    "estudiante": fila["estudiante"],
                    "sala": fila["sala"],
                    "nombre_sala": fila["nombre_sala"],
                    "fecha": fila["fecha"],
                    "hora_inicio": fila["hora_inicio"],
                    "hora_fin": hora_fin,
                    "duracion_horas": fila["duracion_horas"],
                    "cantidad_personas": fila["cantidad_personas"],
                    "estado": fila["estado"],
                    "serie_id": fila["serie_id"],
                }
            )

        if not reservaciones:
            return {
                "exito": True,
                "mensaje": "No hay reservaciones registradas.",
                "reservaciones": [],
            }

        return {
            "exito": True,
            "mensaje": "Consulta realizada correctamente.",
            "reservaciones": reservaciones,
        }
    except sqlite3.Error:
        return {
            "exito": False,
            "mensaje": "No fue posible consultar las reservaciones.",
            "reservaciones": [],
        }


def cancelar_reservacion(id_reservacion):
    """RF-09: Cambia a cancelada una reservación activa; no reutiliza el ID."""
    identificador_interno = _parsear_id(id_reservacion)
    if identificador_interno is None:
        return {"exito": False, "mensaje": "El identificador de la reservación no es válido."}

    conexion = obtener_conexion()
    try:
        reservacion = conexion.execute(
            "SELECT id, estado FROM reservaciones WHERE id = ?",
            (identificador_interno,),
        ).fetchone()

        if reservacion is None:
            return {"exito": False, "mensaje": "La reservación especificada no existe."}

        if reservacion["estado"] == "cancelada":
            return {
                "exito": False,
                "mensaje": "La reservación ya se encuentra cancelada.",
            }

        conexion.execute(
            "UPDATE reservaciones SET estado = 'cancelada' WHERE id = ?",
            (identificador_interno,),
        )
        visible = _formatear_id(identificador_interno)

        resultado_auditoria = registrar_evento(
            accion="cancelacion",
            entidad="reservacion",
            entidad_id=visible,
            detalle=f"Reservación {visible} cancelada correctamente.",
            conexion=conexion,
        )

        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {
                "exito": False,
                "mensaje": "No fue posible cancelar la reservación.",
            }

        conexion.commit()
        return {
            "exito": True,
            "mensaje": f"Reservación {visible} cancelada correctamente.",
        }
    except sqlite3.Error:
        conexion.rollback()
        return {"exito": False, "mensaje": "No fue posible cancelar la reservación."}


def cancelar_ocurrencias_futuras(id_reservacion):
    """RF-14: cancela la ocurrencia seleccionada y las posteriores de su serie."""
    identificador_interno = _parsear_id(id_reservacion)
    if identificador_interno is None:
        return {
            "exito": False,
            "mensaje": "El identificador de la reservación no es válido.",
        }

    conexion = obtener_conexion()
    try:
        seleccionada = conexion.execute(
            """
            SELECT id, fecha, serie_id
            FROM reservaciones
            WHERE id = ?
            """,
            (identificador_interno,),
        ).fetchone()
        if seleccionada is None:
            return {
                "exito": False,
                "mensaje": "La reservación especificada no existe.",
            }
        if not seleccionada["serie_id"]:
            return {
                "exito": False,
                "mensaje": "La reservación seleccionada no pertenece a una serie.",
            }

        ocurrencias = conexion.execute(
            """
            SELECT id
            FROM reservaciones
            WHERE serie_id = ?
              AND fecha >= ?
              AND estado = 'activa'
            ORDER BY fecha ASC, id ASC
            """,
            (seleccionada["serie_id"], seleccionada["fecha"]),
        ).fetchall()
        if not ocurrencias:
            return {
                "exito": False,
                "mensaje": "No hay ocurrencias activas por cancelar en la serie.",
            }

        ids_internos = [fila["id"] for fila in ocurrencias]
        marcadores = ", ".join("?" for _ in ids_internos)
        conexion.execute(
            f"UPDATE reservaciones SET estado = 'cancelada' WHERE id IN ({marcadores})",
            ids_internos,
        )

        serie_id = seleccionada["serie_id"]
        resultado_auditoria = registrar_evento(
            accion="cancelacion",
            entidad="reservacion",
            entidad_id=serie_id,
            detalle=(
                f"Se cancelaron {len(ids_internos)} ocurrencias futuras "
                f"de la serie {serie_id}."
            ),
            conexion=conexion,
        )
        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {
                "exito": False,
                "mensaje": "No fue posible cancelar las ocurrencias de la serie.",
            }

        conexion.commit()
        return {
            "exito": True,
            "mensaje": (
                f"Se cancelaron {len(ids_internos)} ocurrencias de la "
                f"serie {serie_id}."
            ),
            "serie_id": serie_id,
            "cantidad_cancelada": len(ids_internos),
            "ids": [_formatear_id(item) for item in ids_internos],
        }
    except sqlite3.Error:
        conexion.rollback()
        return {
            "exito": False,
            "mensaje": "No fue posible cancelar las ocurrencias de la serie.",
        }


def modificar_reservacion(
    id_reservacion,
    codigo_sala=None,
    fecha=None,
    hora_inicio=None,
    duracion=None,
    cantidad_personas=None,
):
    """RF-13: Actualiza solo los campos indicados y revalida el resultado final."""
    identificador_interno = _parsear_id(id_reservacion)
    if identificador_interno is None:
        return {"exito": False, "mensaje": "El identificador de la reservación no es válido."}

    conexion = obtener_conexion()
    try:
        actual = conexion.execute(
            """
            SELECT
                r.id,
                r.estudiante_id,
                e.carne,
                r.sala_id,
                s.codigo AS codigo_sala,
                r.fecha,
                r.hora_inicio,
                r.duracion_horas,
                r.cantidad_personas,
                r.estado
            FROM reservaciones AS r
            JOIN estudiantes AS e ON r.estudiante_id = e.id
            JOIN salas AS s ON r.sala_id = s.id
            WHERE r.id = ?
            """,
            (identificador_interno,),
        ).fetchone()

        if actual is None:
            return {"exito": False, "mensaje": "La reservación especificada no existe."}

        if actual["estado"] == "cancelada":
            return {
                "exito": False,
                "mensaje": "No se puede modificar una reservación cancelada.",
            }

        datos, error = _preparar_datos_reservacion(
            conexion,
            carne=actual["carne"],
            codigo_sala=actual["codigo_sala"] if codigo_sala is None else codigo_sala,
            fecha=actual["fecha"] if fecha is None else fecha,
            hora_inicio=actual["hora_inicio"] if hora_inicio is None else hora_inicio,
            duracion=actual["duracion_horas"] if duracion is None else duracion,
            cantidad_personas=(
                actual["cantidad_personas"]
                if cantidad_personas is None
                else cantidad_personas
            ),
        )
        if error:
            return {"exito": False, "mensaje": error}

        conflicto = _buscar_conflicto(
            conexion,
            sala_id=datos["sala_id"],
            fecha=datos["fecha"],
            hora_inicio=datos["hora_inicio"],
            hora_fin=datos["hora_fin"],
            excluir_id=identificador_interno,
        )
        if conflicto:
            return {"exito": False, "mensaje": conflicto}

        conexion.execute(
            """
            UPDATE reservaciones
            SET sala_id = ?,
                fecha = ?,
                hora_inicio = ?,
                duracion_horas = ?,
                cantidad_personas = ?
            WHERE id = ?
            """,
            (
                datos["sala_id"],
                datos["fecha"],
                datos["hora_inicio"],
                datos["duracion"],
                datos["cantidad_personas"],
                identificador_interno,
            ),
        )
        visible = _formatear_id(identificador_interno)

        resultado_auditoria = registrar_evento(
            accion="modificacion",
            entidad="reservacion",
            entidad_id=visible,
            detalle=f"Reservación {visible} modificada correctamente.",
            conexion=conexion,
        )

        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {
                "exito": False,
                "mensaje": "No fue posible modificar la reservación.",
            }

        conexion.commit()
        return {
            "exito": True,
            "mensaje": f"Reservación {visible} modificada correctamente.",
            "id": visible,
        }
    except sqlite3.Error:
        conexion.rollback()
        return {"exito": False, "mensaje": "No fue posible modificar la reservación."}


def _evaluar_recurrencia(
    conexion,
    carne,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
    semanas,
):
    if (
        not isinstance(semanas, int)
        or isinstance(semanas, bool)
        or semanas < 2
        or semanas > 8
    ):
        return _respuesta_recurrencia_error(
            "La recurrencia debe abarcar entre 2 y 8 semanas."
        )
    if not isinstance(fecha, str):
        return _respuesta_recurrencia_error(
            "La fecha debe utilizar el formato AAAA-MM-DD."
        )

    try:
        fecha_inicial = datetime.strptime(fecha.strip(), "%Y-%m-%d")
    except ValueError:
        return _respuesta_recurrencia_error(
            "La fecha debe utilizar el formato AAAA-MM-DD."
        )

    ocurrencias = []
    datos_ocurrencias = []
    hay_error_validacion = False
    for indice in range(semanas):
        fecha_ocurrencia = (
            fecha_inicial + timedelta(weeks=indice)
        ).strftime("%Y-%m-%d")
        datos, error = _preparar_datos_reservacion(
            conexion,
            carne=carne,
            codigo_sala=codigo_sala,
            fecha=fecha_ocurrencia,
            hora_inicio=hora_inicio,
            duracion=duracion,
            cantidad_personas=cantidad_personas,
        )
        if error:
            hay_error_validacion = True
            ocurrencias.append(
                {
                    "numero": indice + 1,
                    "fecha": fecha_ocurrencia,
                    "disponible": False,
                    "mensaje": error,
                }
            )
            continue

        conflicto = _buscar_conflicto(
            conexion,
            sala_id=datos["sala_id"],
            fecha=datos["fecha"],
            hora_inicio=datos["hora_inicio"],
            hora_fin=datos["hora_fin"],
        )
        datos_ocurrencias.append(datos)
        ocurrencias.append(
            {
                "numero": indice + 1,
                "fecha": fecha_ocurrencia,
                "disponible": conflicto is None,
                "mensaje": conflicto or "Horario disponible.",
            }
        )

    if hay_error_validacion:
        return {
            "exito": False,
            "puede_crear": False,
            "mensaje": "Una o más ocurrencias no cumplen las reglas de negocio.",
            "ocurrencias": ocurrencias,
            "_datos": datos_ocurrencias,
        }

    estudiante_id = datos_ocurrencias[0]["estudiante_id"]
    if _contar_reservaciones_vigentes(conexion, estudiante_id) >= 3:
        return {
            "exito": False,
            "puede_crear": False,
            "mensaje": "El estudiante ya tiene el máximo de 3 reservaciones activas.",
            "ocurrencias": ocurrencias,
            "_datos": datos_ocurrencias,
        }

    puede_crear = all(item["disponible"] for item in ocurrencias)
    return {
        "exito": True,
        "puede_crear": puede_crear,
        "mensaje": (
            "Todas las ocurrencias están disponibles."
            if puede_crear
            else "La serie presenta uno o más conflictos de horario."
        ),
        "ocurrencias": ocurrencias,
        "_datos": datos_ocurrencias,
    }


def _respuesta_recurrencia_error(mensaje):
    return {
        "exito": False,
        "puede_crear": False,
        "mensaje": mensaje,
        "ocurrencias": [],
    }


def _generar_id_serie(conexion):
    filas = conexion.execute(
        """
        SELECT DISTINCT serie_id
        FROM reservaciones
        WHERE serie_id IS NOT NULL
        """
    ).fetchall()
    numeros = []
    for fila in filas:
        serie_id = fila["serie_id"]
        if serie_id.startswith("SR") and serie_id[2:].isdigit():
            numeros.append(int(serie_id[2:]))
    siguiente = max(numeros, default=0) + 1
    return f"SR{siguiente:04d}"


def _preparar_datos_reservacion(
    conexion,
    carne,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
):
    estudiante = _buscar_estudiante(conexion, carne)
    if estudiante is None:
        return None, "No existe un estudiante con ese carné."
    if estudiante["estado"] != "activo":
        return None, "Solo un estudiante activo puede crear reservaciones."

    if not isinstance(cantidad_personas, int) or isinstance(cantidad_personas, bool) or cantidad_personas <= 0:
        return None, "La cantidad de personas debe ser un entero mayor que cero."

    valido, mensaje_horario = _validar_fecha_hora_duracion(fecha, hora_inicio, duracion)
    if not valido:
        return None, mensaje_horario

    sala = _buscar_sala(conexion, codigo_sala)
    if sala is None:
        return None, "La sala especificada no existe."
    if sala["estado"] == "fuera_de_servicio":
        return None, "La sala se encuentra fuera de servicio."
    if cantidad_personas > sala["capacidad"]:
        return None, "La cantidad de personas no puede ser mayor que la capacidad de la sala."

    fecha_norm = fecha.strip()
    hora_norm = hora_inicio.strip()
    return {
        "estudiante_id": estudiante["id"],
        "sala_id": sala["id"],
        "fecha": fecha_norm,
        "hora_inicio": hora_norm,
        "hora_fin": _calcular_hora_fin(hora_norm, duracion),
        "duracion": duracion,
        "cantidad_personas": cantidad_personas,
    }, None


def _validar_fecha_hora_duracion(fecha, hora_inicio, duracion):
    if not isinstance(duracion, int) or isinstance(duracion, bool) or duracion not in (1, 2):
        return False, "La duración permitida es únicamente de 1 o 2 horas."

    if not isinstance(fecha, str) or not isinstance(hora_inicio, str):
        return False, "Formato de fecha (AAAA-MM-DD) u hora (HH:MM) inválido."

    fecha = fecha.strip()
    hora_inicio = hora_inicio.strip()
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        hora_dt = datetime.strptime(hora_inicio, "%H:%M")
    except ValueError:
        return False, "Formato de fecha (AAAA-MM-DD) u hora (HH:MM) inválido."

    if hora_dt.minute != 0:
        return False, "La hora debe comenzar exactamente en una hora completa (ej. 08:00)."

    hora_fin_dt = hora_dt + timedelta(hours=duracion)
    if hora_dt < _HORA_APERTURA or hora_fin_dt > _HORA_CIERRE:
        return False, "El horario permitido de uso es de 08:00 a 20:00."

    ahora = datetime.now()
    fecha_actual = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    if fecha < fecha_actual:
        return False, "La fecha no puede ser anterior a la fecha actual."
    if fecha == fecha_actual and hora_inicio <= hora_actual:
        return False, "El horario solicitado para hoy ya transcurrió."

    return True, ""


def _buscar_estudiante(conexion, carne):
    if not isinstance(carne, str) or not carne.strip():
        return None
    return conexion.execute(
        """
        SELECT id, carne, nombre_completo, estado
        FROM estudiantes
        WHERE UPPER(carne) = ?
        """,
        (carne.strip().upper(),),
    ).fetchone()


def _buscar_sala(conexion, codigo_sala):
    if not isinstance(codigo_sala, str) or not codigo_sala.strip():
        return None
    return conexion.execute(
        "SELECT id, codigo, capacidad, estado FROM salas WHERE codigo = ?",
        (codigo_sala.strip(),),
    ).fetchone()


def _contar_reservaciones_vigentes(conexion, estudiante_id):
    filas = conexion.execute(
        """
        SELECT id, fecha, hora_inicio, duracion_horas, serie_id
        FROM reservaciones
        WHERE estudiante_id = ? AND estado = 'activa'
        """,
        (estudiante_id,),
    ).fetchall()
    ahora = datetime.now()
    unidades_vigentes = set()
    for fila in filas:
        inicio = datetime.strptime(f"{fila['fecha']} {fila['hora_inicio']}", "%Y-%m-%d %H:%M")
        fin = inicio + timedelta(hours=fila["duracion_horas"])
        if fin > ahora:
            if fila["serie_id"]:
                unidades_vigentes.add(("serie", fila["serie_id"]))
            else:
                unidades_vigentes.add(("reservacion", fila["id"]))
    return len(unidades_vigentes)


def _buscar_conflicto(conexion, sala_id, fecha, hora_inicio, hora_fin, excluir_id=None):
    consulta = """
        SELECT hora_inicio, duracion_horas
        FROM reservaciones
        WHERE sala_id = ? AND fecha = ? AND estado = 'activa'
    """
    parametros = [sala_id, fecha]
    if excluir_id is not None:
        consulta += " AND id != ?"
        parametros.append(excluir_id)

    for existente in conexion.execute(consulta, parametros).fetchall():
        existente_inicio = existente["hora_inicio"]
        existente_fin = _calcular_hora_fin(existente_inicio, existente["duracion_horas"])
        if hora_inicio < existente_fin and hora_fin > existente_inicio:
            return (
                f"Conflicto: la sala tiene una reservación activa de "
                f"{existente_inicio} a {existente_fin}."
            )
    return None


def _calcular_hora_fin(hora_inicio, duracion_horas):
    inicio = datetime.strptime(hora_inicio, "%H:%M")
    return (inicio + timedelta(hours=duracion_horas)).strftime("%H:%M")


def _formatear_id(identificador):
    return f"R{int(identificador):04d}"


def _parsear_id(id_reservacion):
    if isinstance(id_reservacion, bool) or id_reservacion is None:
        return None
    if isinstance(id_reservacion, int):
        return id_reservacion if id_reservacion > 0 else None
    if isinstance(id_reservacion, str):
        texto = id_reservacion.strip().upper()
        if texto.startswith("R") and texto[1:].isdigit():
            valor = int(texto[1:])
            return valor if valor > 0 else None
        if texto.isdigit():
            valor = int(texto)
            return valor if valor > 0 else None
    return None
