"""RF-15: consultas para el panel de control y sus filtros."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from src.db.conexion import obtener_conexion


def consultar_panel(
    fecha: Optional[str] = None,
    codigo_sala: Optional[str] = None,
    estado: Optional[str] = None,
    ahora: Optional[datetime] = None,
) -> dict:
    """Construye los datos del panel sin depender de una interfaz gráfica.

    Los filtros son opcionales y se combinan con AND. ``ahora`` permite
    ejecutar pruebas deterministas; la aplicación normalmente lo omite.
    """
    filtros, error = _normalizar_filtros(fecha, codigo_sala, estado)
    if error:
        return _respuesta_error(error)

    if ahora is None:
        ahora = datetime.now()
    elif not isinstance(ahora, datetime):
        return _respuesta_error("La fecha y hora de referencia no son válidas.")

    fecha_referencia = ahora.strftime("%Y-%m-%d")
    hora_referencia = ahora.strftime("%H:%M")
    conexion = obtener_conexion()

    try:
        resultados = _consultar_reservaciones(
            conexion,
            fecha=filtros["fecha"],
            codigo_sala=filtros["codigo_sala"],
            estado=filtros["estado"],
        )
        reservaciones_hoy = _consultar_reservaciones(
            conexion,
            fecha=fecha_referencia,
        )
        proximas = _consultar_proximas(
            conexion,
            fecha_referencia,
            hora_referencia,
        )
        ocupacion = _consultar_ocupacion(conexion, fecha_referencia)

        if resultados:
            mensaje = "Consulta del panel realizada correctamente."
        else:
            mensaje = "No hay reservaciones para los filtros seleccionados."

        return {
            "exito": True,
            "mensaje": mensaje,
            "filtros": filtros,
            "ocupacion_salas": ocupacion,
            "reservaciones_hoy": reservaciones_hoy,
            "proximas_reservaciones": proximas,
            "resultados": resultados,
        }
    except sqlite3.Error:
        return _respuesta_error("No fue posible consultar el panel.")


def _normalizar_filtros(fecha, codigo_sala, estado):
    fecha_normalizada = None
    if fecha is not None and str(fecha).strip():
        if not isinstance(fecha, str):
            return None, "La fecha debe utilizar el formato AAAA-MM-DD."
        fecha_normalizada = fecha.strip()
        try:
            datetime.strptime(fecha_normalizada, "%Y-%m-%d")
        except ValueError:
            return None, "La fecha debe utilizar el formato AAAA-MM-DD."

    codigo_normalizado = None
    if codigo_sala is not None and str(codigo_sala).strip():
        if not isinstance(codigo_sala, str):
            return None, "El código de sala no es válido."
        codigo_normalizado = codigo_sala.strip().upper()

    estado_normalizado = None
    if estado is not None and str(estado).strip():
        if not isinstance(estado, str):
            return None, "El estado de reservación no es válido."
        estado_normalizado = estado.strip().lower()
        if estado_normalizado not in ("activa", "cancelada"):
            return None, "El estado debe ser activa o cancelada."

    return {
        "fecha": fecha_normalizada,
        "codigo_sala": codigo_normalizado,
        "estado": estado_normalizado,
    }, None


def _consultar_reservaciones(
    conexion,
    fecha=None,
    codigo_sala=None,
    estado=None,
):
    consulta = """
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
        JOIN estudiantes AS e ON e.id = r.estudiante_id
        JOIN salas AS s ON s.id = r.sala_id
        WHERE 1 = 1
    """
    parametros = []

    if fecha is not None:
        consulta += " AND r.fecha = ?"
        parametros.append(fecha)
    if codigo_sala is not None:
        consulta += " AND s.codigo = ?"
        parametros.append(codigo_sala)
    if estado is not None:
        consulta += " AND r.estado = ?"
        parametros.append(estado)

    consulta += " ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC"
    filas = conexion.execute(consulta, parametros).fetchall()
    return [_formatear_reservacion(fila) for fila in filas]


def _consultar_proximas(conexion, fecha_referencia, hora_referencia):
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
        JOIN estudiantes AS e ON e.id = r.estudiante_id
        JOIN salas AS s ON s.id = r.sala_id
        WHERE r.estado = 'activa'
          AND (
              r.fecha > ?
              OR (r.fecha = ? AND r.hora_inicio >= ?)
          )
        ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC
        """,
        (fecha_referencia, fecha_referencia, hora_referencia),
    ).fetchall()
    return [_formatear_reservacion(fila) for fila in filas]


def _consultar_ocupacion(conexion, fecha_referencia):
    filas = conexion.execute(
        """
        SELECT
            s.codigo,
            s.nombre,
            s.capacidad,
            s.estado,
            COUNT(r.id) AS reservaciones_activas,
            COALESCE(SUM(r.duracion_horas), 0) AS horas_reservadas,
            COALESCE(SUM(r.cantidad_personas), 0) AS personas_reservadas
        FROM salas AS s
        LEFT JOIN reservaciones AS r
          ON r.sala_id = s.id
         AND r.fecha = ?
         AND r.estado = 'activa'
        GROUP BY s.id, s.codigo, s.nombre, s.capacidad, s.estado
        ORDER BY s.codigo ASC
        """,
        (fecha_referencia,),
    ).fetchall()
    return [dict(fila) for fila in filas]


def _formatear_reservacion(fila):
    return {
        "id": f"R{int(fila['id']):04d}",
        "carne": fila["carne"],
        "estudiante": fila["estudiante"],
        "sala": fila["sala"],
        "nombre_sala": fila["nombre_sala"],
        "fecha": fila["fecha"],
        "hora_inicio": fila["hora_inicio"],
        "hora_fin": _calcular_hora_fin(
            fila["hora_inicio"],
            fila["duracion_horas"],
        ),
        "duracion_horas": fila["duracion_horas"],
        "cantidad_personas": fila["cantidad_personas"],
        "estado": fila["estado"],
        "serie_id": fila["serie_id"],
    }


def _calcular_hora_fin(hora_inicio, duracion_horas):
    inicio = datetime.strptime(hora_inicio, "%H:%M")
    return (inicio + timedelta(hours=duracion_horas)).strftime("%H:%M")


def _respuesta_error(mensaje):
    return {
        "exito": False,
        "mensaje": mensaje,
        "filtros": {},
        "ocupacion_salas": [],
        "reservaciones_hoy": [],
        "proximas_reservaciones": [],
        "resultados": [],
    }
