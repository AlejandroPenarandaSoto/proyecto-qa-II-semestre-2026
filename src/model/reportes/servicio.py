"""RF-16: generación de reportes CSV de reservaciones."""

from __future__ import annotations

import csv
import logging
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union

from src.db.conexion import obtener_conexion

_LOGGER = logging.getLogger(__name__)

ENCABEZADOS_REPORTE = (
    "estudiante",
    "sala",
    "fecha",
    "horario",
    "cantidad_personas",
    "estado",
)


def generar_reporte_csv(
    fecha_inicio: str,
    fecha_fin: str,
    ruta_destino: Optional[Union[str, Path]],
) -> dict:
    """Exporta las reservaciones del rango inclusivo a un CSV UTF-8.

    La ruta es recibida desde la capa de interfaz. Si la persona cancela
    el diálogo de guardado, la interfaz debe llamar con ``None`` o una
    cadena vacía; en ese caso no se crea ningún archivo.
    """
    if ruta_destino is None or not str(ruta_destino).strip():
        return {
            "exito": False,
            "cancelado": True,
            "mensaje": "La generación del reporte fue cancelada.",
        }

    rango, error = _validar_rango_fechas(fecha_inicio, fecha_fin)
    if error:
        return {
            "exito": False,
            "cancelado": False,
            "mensaje": error,
        }

    destino = Path(ruta_destino)
    archivo_temporal = None

    try:
        filas = _consultar_reservaciones(*rango)
        archivo_temporal = _escribir_archivo_temporal(destino, filas)
        os.replace(archivo_temporal, destino)
        archivo_temporal = None

        return {
            "exito": True,
            "cancelado": False,
            "mensaje": "Reporte CSV generado correctamente.",
            "ruta": str(destino),
            "cantidad": len(filas),
        }
    except (OSError, sqlite3.Error):
        return {
            "exito": False,
            "cancelado": False,
            "mensaje": "No fue posible generar el reporte CSV.",
        }
    finally:
        if archivo_temporal is not None:
            try:
                Path(archivo_temporal).unlink(missing_ok=True)
            except OSError as error_limpieza:
                _LOGGER.warning(
                    "No fue posible eliminar el archivo temporal %s: %s",
                    archivo_temporal,
                    error_limpieza,
                )


def _validar_rango_fechas(fecha_inicio, fecha_fin):
    if not isinstance(fecha_inicio, str) or not fecha_inicio.strip():
        return None, "La fecha inicial es obligatoria."
    if not isinstance(fecha_fin, str) or not fecha_fin.strip():
        return None, "La fecha final es obligatoria."

    inicio = fecha_inicio.strip()
    fin = fecha_fin.strip()
    try:
        datetime.strptime(inicio, "%Y-%m-%d")
        datetime.strptime(fin, "%Y-%m-%d")
    except ValueError:
        return None, "Las fechas deben utilizar el formato AAAA-MM-DD."

    if fin < inicio:
        return None, "La fecha final no puede ser anterior a la fecha inicial."

    return (inicio, fin), None


def _consultar_reservaciones(fecha_inicio, fecha_fin):
    conexion = obtener_conexion()
    filas = conexion.execute(
        """
        SELECT
            e.nombre_completo AS estudiante,
            s.codigo AS sala,
            r.fecha,
            r.hora_inicio,
            r.duracion_horas,
            r.cantidad_personas,
            r.estado
        FROM reservaciones AS r
        JOIN estudiantes AS e ON e.id = r.estudiante_id
        JOIN salas AS s ON s.id = r.sala_id
        WHERE r.fecha BETWEEN ? AND ?
        ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC
        """,
        (fecha_inicio, fecha_fin),
    ).fetchall()

    return [
        {
            "estudiante": fila["estudiante"],
            "sala": fila["sala"],
            "fecha": fila["fecha"],
            "horario": (
                f"{fila['hora_inicio']}-"
                f"{_calcular_hora_fin(fila['hora_inicio'], fila['duracion_horas'])}"
            ),
            "cantidad_personas": fila["cantidad_personas"],
            "estado": fila["estado"],
        }
        for fila in filas
    ]


def _escribir_archivo_temporal(destino, filas):
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix=f".{destino.name}.",
        suffix=".tmp",
        dir=destino.parent,
        delete=False,
    ) as temporal:
        escritor = csv.DictWriter(
            temporal,
            fieldnames=ENCABEZADOS_REPORTE,
        )
        escritor.writeheader()
        escritor.writerows(filas)
        return temporal.name


def _calcular_hora_fin(hora_inicio, duracion_horas):
    inicio = datetime.strptime(hora_inicio, "%H:%M")
    return (inicio + timedelta(hours=duracion_horas)).strftime("%H:%M")
