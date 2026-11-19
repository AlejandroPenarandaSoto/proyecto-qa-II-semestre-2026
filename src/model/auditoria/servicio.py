import sqlite3
from datetime import datetime

from src.db.conexion import obtener_conexion


def registrar_evento(accion, entidad, entidad_id, detalle=None, conexion=None):
    """Guarda un evento en la tabla de auditoría."""
    datos_invalidos = (
        not isinstance(accion, str)
        or not accion.strip()
        or not isinstance(entidad, str)
        or not entidad.strip()
        or entidad_id is None
        or not str(entidad_id).strip()
    )

    if datos_invalidos:
        return {
            "exito": False,
            "mensaje": (
                "Los datos obligatorios del evento de auditoría "
                "no son válidos."
            ),
        }

    accion = accion.strip()
    entidad = entidad.strip()
    entidad_id = str(entidad_id).strip()

    conexion_externa = conexion is not None
    conexion = conexion or obtener_conexion()

    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conexion.execute(
            """
            INSERT INTO auditoria (
                fecha_hora, accion, entidad, entidad_id, detalle
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                fecha_hora,
                accion,
                entidad,
                entidad_id,
                detalle,
            ),
        )

        if not conexion_externa:
            conexion.commit()

        return {
            "exito": True,
            "mensaje": "Evento de auditoría registrado correctamente.",
        }

    except sqlite3.Error:
        if not conexion_externa:
            conexion.rollback()

        return {
            "exito": False,
            "mensaje": "No fue posible registrar el evento de auditoría.",
        }


def consultar_auditoria():
    """Retorna los eventos de auditoría, comenzando por el más reciente."""
    conexion = obtener_conexion()

    try:
        filas = conexion.execute(
            """
            SELECT id, fecha_hora, accion, entidad, entidad_id, detalle
            FROM auditoria
            ORDER BY fecha_hora DESC, id DESC
            """
        ).fetchall()

        eventos = [dict(fila) for fila in filas]

        if not eventos:
            return {
                "exito": True,
                "mensaje": "No hay eventos de auditoría registrados.",
                "eventos": [],
            }

        return {
            "exito": True,
            "mensaje": "Consulta de auditoría realizada correctamente.",
            "eventos": eventos,
        }

    except sqlite3.Error:
        return {
            "exito": False,
            "mensaje": "No fue posible consultar la auditoría.",
            "eventos": [],
        }
