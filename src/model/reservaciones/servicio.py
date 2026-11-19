"""Casos de uso de reservaciones (RF-05, RF-06, RF-09, RF-13 y RF-14).

Cada función pública valida con ``reglas``, guarda con ``repositorio``,
registra la auditoría y confirma la transacción. Siempre devuelve un
diccionario con ``exito`` y ``mensaje``; nunca lanza excepciones.
"""

import sqlite3
from datetime import datetime
from typing import Any, NamedTuple

from src.db.conexion import obtener_conexion
from src.model.auditoria.servicio import registrar_evento
from src.model.reservaciones import reglas, repositorio
from src.model.reservaciones.reglas import ReservacionInvalida


class _Solicitud(NamedTuple):
    """Datos de una reservación tal como los envía el usuario."""

    carne: Any
    codigo_sala: Any
    fecha: Any
    hora_inicio: Any
    duracion: Any
    cantidad_personas: Any


class _FalloAuditoria(Exception):
    """La auditoría no pudo registrarse; la operación completa se revierte."""


# --- Casos de uso ----------------------------------------------------------


def crear_reservacion(carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas):
    """RF-05: Crea una reservación activa si cumple las reglas de negocio."""
    solicitud = _Solicitud(carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas)

    def operacion(conexion):
        datos = _validar_reservacion(conexion, solicitud, datetime.now())
        _verificar_limite(conexion, datos["estudiante_id"])
        _verificar_disponibilidad(conexion, datos)
        identificador = reglas.formatear_id(repositorio.insertar_reservacion(conexion, datos))
        mensaje = f"Reservación {identificador} creada correctamente."
        _auditar(conexion, "creacion", identificador, mensaje)
        return {"exito": True, "mensaje": mensaje, "id": identificador}

    return _en_transaccion(operacion, "No fue posible crear la reservación.")


def previsualizar_reservaciones_recurrentes(
    carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas, semanas
):
    """RF-14: valida de 2 a 8 ocurrencias semanales sin persistirlas."""
    solicitud = _Solicitud(carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas)

    def operacion(conexion):
        resumen, _ = _evaluar_serie(conexion, solicitud, semanas)
        return resumen

    return _en_transaccion(
        operacion,
        "No fue posible previsualizar las reservaciones recurrentes.",
        _respuesta_serie,
    )


def crear_reservaciones_recurrentes(
    carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas, semanas
):
    """RF-14: crea una serie semanal completa en una sola transacción."""
    solicitud = _Solicitud(carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas)

    def operacion(conexion):
        resumen, ocurrencias_validas = _evaluar_serie(conexion, solicitud, semanas)
        if not resumen["exito"]:
            return resumen
        if not resumen["puede_crear"]:
            return {
                **resumen,
                "exito": False,
                "mensaje": "La serie no fue creada porque una o más ocurrencias presentan conflictos.",
            }

        serie_id = reglas.siguiente_id_serie(repositorio.series_registradas(conexion))
        ids = [
            reglas.formatear_id(repositorio.insertar_reservacion(conexion, datos, serie_id))
            for datos in ocurrencias_validas
        ]
        _auditar(
            conexion,
            "creacion",
            serie_id,
            f"Serie {serie_id} creada correctamente con {len(ids)} ocurrencias: {', '.join(ids)}.",
        )
        return {
            "exito": True,
            "puede_crear": True,
            "mensaje": f"Serie {serie_id} creada correctamente.",
            "serie_id": serie_id,
            "ids": ids,
            "ocurrencias": resumen["ocurrencias"],
        }

    return _en_transaccion(
        operacion, "No fue posible crear la serie recurrente.", _respuesta_serie
    )


def consultar_reservaciones():
    """RF-06: Retorna todas las reservaciones, activas y canceladas."""

    def operacion(conexion):
        reservaciones = [
            _reservacion_visible(fila) for fila in repositorio.listar_reservaciones(conexion)
        ]
        mensaje = (
            "Consulta realizada correctamente."
            if reservaciones
            else "No hay reservaciones registradas."
        )
        return {"exito": True, "mensaje": mensaje, "reservaciones": reservaciones}

    return _en_transaccion(
        operacion,
        "No fue posible consultar las reservaciones.",
        lambda mensaje: {"exito": False, "mensaje": mensaje, "reservaciones": []},
    )


def cancelar_reservacion(id_reservacion):
    """RF-09: Cambia a cancelada una reservación activa; no reutiliza el ID."""

    def operacion(conexion, actual):
        if actual["estado"] == "cancelada":
            raise ReservacionInvalida("La reservación ya se encuentra cancelada.")
        repositorio.cancelar_reservaciones(conexion, [actual["id"]])
        visible = reglas.formatear_id(actual["id"])
        mensaje = f"Reservación {visible} cancelada correctamente."
        _auditar(conexion, "cancelacion", visible, mensaje)
        return {"exito": True, "mensaje": mensaje}

    return _sobre_reservacion(
        id_reservacion, operacion, "No fue posible cancelar la reservación."
    )


def cancelar_ocurrencias_futuras(id_reservacion):
    """RF-14: cancela la ocurrencia seleccionada y las posteriores de su serie."""

    def operacion(conexion, actual):
        serie_id = actual["serie_id"]
        if not serie_id:
            raise ReservacionInvalida("La reservación seleccionada no pertenece a una serie.")
        ids_internos = repositorio.ids_activos_de_serie_desde(conexion, serie_id, actual["fecha"])
        if not ids_internos:
            raise ReservacionInvalida("No hay ocurrencias activas por cancelar en la serie.")

        repositorio.cancelar_reservaciones(conexion, ids_internos)
        ids = [reglas.formatear_id(identificador) for identificador in ids_internos]
        _auditar(
            conexion,
            "cancelacion",
            serie_id,
            f"Se cancelaron {len(ids)} ocurrencias futuras de la serie {serie_id}: {', '.join(ids)}.",
        )
        return {
            "exito": True,
            "mensaje": f"Se cancelaron {len(ids)} ocurrencias de la serie {serie_id}.",
            "serie_id": serie_id,
            "cantidad_cancelada": len(ids),
            "ids": ids,
        }

    return _sobre_reservacion(
        id_reservacion, operacion, "No fue posible cancelar las ocurrencias de la serie."
    )


def modificar_reservacion(
    id_reservacion,
    codigo_sala=None,
    fecha=None,
    hora_inicio=None,
    duracion=None,
    cantidad_personas=None,
):
    """RF-13: Actualiza solo los campos indicados y revalida el resultado final."""
    cambios = {
        "codigo_sala": codigo_sala,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "duracion": duracion,
        "cantidad_personas": cantidad_personas,
    }
    cambios = {campo: valor for campo, valor in cambios.items() if valor is not None}

    def operacion(conexion, actual):
        if actual["estado"] == "cancelada":
            raise ReservacionInvalida("No se puede modificar una reservación cancelada.")
        solicitud = _Solicitud(
            carne=actual["carne"],
            codigo_sala=actual["codigo_sala"],
            fecha=actual["fecha"],
            hora_inicio=actual["hora_inicio"],
            duracion=actual["duracion_horas"],
            cantidad_personas=actual["cantidad_personas"],
        )._replace(**cambios)

        datos = _validar_reservacion(conexion, solicitud, datetime.now())
        _verificar_disponibilidad(conexion, datos, excluir_id=actual["id"])
        repositorio.actualizar_reservacion(conexion, actual["id"], datos)
        visible = reglas.formatear_id(actual["id"])
        mensaje = f"Reservación {visible} modificada correctamente."
        _auditar(conexion, "modificacion", visible, mensaje)
        return {"exito": True, "mensaje": mensaje, "id": visible}

    return _sobre_reservacion(
        id_reservacion, operacion, "No fue posible modificar la reservación."
    )


# --- Validación ------------------------------------------------------------


def _validar_reservacion(conexion, solicitud, ahora):
    """Aplica las reglas en orden y devuelve los datos listos para guardar."""
    estudiante = _buscar_estudiante(conexion, solicitud.carne)
    reglas.validar_cantidad_personas(solicitud.cantidad_personas)
    fecha, hora_inicio = reglas.validar_horario(
        solicitud.fecha, solicitud.hora_inicio, solicitud.duracion, ahora
    )
    sala = _buscar_sala(conexion, solicitud.codigo_sala)
    if solicitud.cantidad_personas > sala["capacidad"]:
        raise ReservacionInvalida(
            "La cantidad de personas no puede ser mayor que la capacidad de la sala."
        )
    return {
        "estudiante_id": estudiante["id"],
        "sala_id": sala["id"],
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": reglas.calcular_hora_fin(hora_inicio, solicitud.duracion),
        "duracion": solicitud.duracion,
        "cantidad_personas": solicitud.cantidad_personas,
    }


def _buscar_estudiante(conexion, carne):
    """RN-01: el estudiante existe y está activo."""
    estudiante = None
    if _es_texto_con_contenido(carne):
        estudiante = repositorio.buscar_estudiante(conexion, carne.strip())
    if estudiante is None:
        raise ReservacionInvalida("No existe un estudiante con ese carné.")
    if estudiante["estado"] != "activo":
        raise ReservacionInvalida("Solo un estudiante activo puede crear reservaciones.")
    return estudiante


def _buscar_sala(conexion, codigo_sala):
    """RN-08: la sala existe y está en servicio."""
    sala = None
    if _es_texto_con_contenido(codigo_sala):
        sala = repositorio.buscar_sala(conexion, codigo_sala.strip())
    if sala is None:
        raise ReservacionInvalida("La sala especificada no existe.")
    if sala["estado"] == "fuera_de_servicio":
        raise ReservacionInvalida("La sala se encuentra fuera de servicio.")
    return sala


def _es_texto_con_contenido(valor):
    return isinstance(valor, str) and bool(valor.strip())


def _verificar_limite(conexion, estudiante_id, cupos_nuevos=1):
    """RN-11: límite de reservaciones activas presentes o futuras."""
    activas = repositorio.reservaciones_activas_de_estudiante(conexion, estudiante_id)
    reglas.validar_limite(reglas.contar_cupos_ocupados(activas, datetime.now()), cupos_nuevos)


def _verificar_disponibilidad(conexion, datos, excluir_id=None):
    conflicto = _buscar_conflicto(conexion, datos, excluir_id)
    if conflicto:
        raise ReservacionInvalida(conflicto)


def _buscar_conflicto(conexion, datos, excluir_id=None):
    """RN-09 y RN-10: devuelve el mensaje del primer choque o None."""
    horarios = repositorio.horarios_activos_de_sala(
        conexion, datos["sala_id"], datos["fecha"], excluir_id
    )
    for existente in horarios:
        inicio = existente["hora_inicio"]
        fin = reglas.calcular_hora_fin(inicio, existente["duracion_horas"])
        if reglas.se_traslapan(datos["hora_inicio"], datos["hora_fin"], inicio, fin):
            return f"Conflicto: la sala tiene una reservación activa de {inicio} a {fin}."
    return None


# --- Series recurrentes ----------------------------------------------------


def _evaluar_serie(conexion, solicitud, semanas):
    """Evalúa cada ocurrencia sin guardar nada.

    Devuelve el resumen para el usuario y los datos de las ocurrencias válidas.
    """
    ahora = datetime.now()
    ocurrencias, ocurrencias_validas = [], []
    for numero, fecha in enumerate(reglas.fechas_semanales(solicitud.fecha, semanas), start=1):
        try:
            datos = _validar_reservacion(conexion, solicitud._replace(fecha=fecha), ahora)
        except ReservacionInvalida as error:
            ocurrencias.append(_ocurrencia(numero, fecha, str(error)))
            continue
        ocurrencias.append(_ocurrencia(numero, fecha, _buscar_conflicto(conexion, datos)))
        ocurrencias_validas.append(datos)

    return _resumir_serie(conexion, ocurrencias, ocurrencias_validas), ocurrencias_validas


def _resumir_serie(conexion, ocurrencias, ocurrencias_validas):
    if len(ocurrencias_validas) < len(ocurrencias):
        return _respuesta_serie(
            "Una o más ocurrencias no cumplen las reglas de negocio.", ocurrencias
        )
    try:
        _verificar_limite(
            conexion,
            ocurrencias_validas[0]["estudiante_id"],
            cupos_nuevos=len(ocurrencias_validas),
        )
    except ReservacionInvalida as error:
        return _respuesta_serie(str(error), ocurrencias)

    puede_crear = all(ocurrencia["disponible"] for ocurrencia in ocurrencias)
    return {
        "exito": True,
        "puede_crear": puede_crear,
        "mensaje": (
            "Todas las ocurrencias están disponibles."
            if puede_crear
            else "La serie presenta uno o más conflictos de horario."
        ),
        "ocurrencias": ocurrencias,
    }


def _ocurrencia(numero, fecha, problema=None):
    return {
        "numero": numero,
        "fecha": fecha,
        "disponible": problema is None,
        "mensaje": problema or "Horario disponible.",
    }


def _respuesta_serie(mensaje, ocurrencias=()):
    return {
        "exito": False,
        "puede_crear": False,
        "mensaje": mensaje,
        "ocurrencias": list(ocurrencias),
    }


# --- Transacciones y respuestas --------------------------------------------


def _en_transaccion(operacion, mensaje_fallo, respuesta_error=None):
    """Ejecuta la operación en una transacción y traduce los errores a respuestas.

    - Regla de negocio incumplida: se informa el mensaje de la regla.
    - Error de base de datos o de auditoría: se informa ``mensaje_fallo``.
    En ambos casos se revierte todo lo escrito.
    """
    respuesta_error = respuesta_error or _respuesta_error
    conexion = obtener_conexion()
    try:
        resultado = operacion(conexion)
        conexion.commit()
        return resultado
    except ReservacionInvalida as error:
        conexion.rollback()
        return respuesta_error(str(error))
    except (sqlite3.Error, _FalloAuditoria):
        conexion.rollback()
        return respuesta_error(mensaje_fallo)


def _sobre_reservacion(id_reservacion, operacion, mensaje_fallo):
    """Ubica la reservación indicada y ejecuta la operación sobre ella."""
    identificador = reglas.parsear_id(id_reservacion)
    if identificador is None:
        return _respuesta_error("El identificador de la reservación no es válido.")

    def con_reservacion(conexion):
        actual = repositorio.obtener_reservacion(conexion, identificador)
        if actual is None:
            raise ReservacionInvalida("La reservación especificada no existe.")
        return operacion(conexion, actual)

    return _en_transaccion(con_reservacion, mensaje_fallo)


def _auditar(conexion, accion, entidad_id, detalle):
    resultado = registrar_evento(
        accion=accion,
        entidad="reservacion",
        entidad_id=entidad_id,
        detalle=detalle,
        conexion=conexion,
    )
    if not resultado["exito"]:
        raise _FalloAuditoria(resultado.get("mensaje"))


def _respuesta_error(mensaje):
    return {"exito": False, "mensaje": mensaje}


def _reservacion_visible(fila):
    return {
        **dict(fila),
        "id": reglas.formatear_id(fila["id"]),
        "hora_fin": reglas.calcular_hora_fin(fila["hora_inicio"], fila["duracion_horas"]),
    }
