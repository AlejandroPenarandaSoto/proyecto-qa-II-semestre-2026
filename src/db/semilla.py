"""
Datos iniciales del sistema (sección 5.2 del enunciado): el catálogo
base de salas que debe estar disponible desde la primera ejecución
(criterio de aceptación de RF-01).
"""
import sqlite3
from typing import List, Tuple

SALAS_INICIALES: List[Tuple[str, str, int, str]] = [
    ("S01", "Sala Biblioteca 1", 4, "disponible"),
    ("S02", "Sala Biblioteca 2", 6, "disponible"),
    ("S03", "Laboratorio de estudio", 10, "disponible"),
    ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
    ("S05", "Cubículo individual", 1, "disponible"),
]


def insertar_salas_iniciales(conexion: sqlite3.Connection) -> int:
    """Inserta el catálogo de salas iniciales únicamente si la tabla
    está vacía, para no duplicar registros en ejecuciones posteriores.

    Devuelve la cantidad de filas insertadas (0 si ya había datos).
    """
    (cantidad_actual,) = conexion.execute("SELECT COUNT(*) FROM salas;").fetchone()
    if cantidad_actual > 0:
        return 0

    conexion.executemany(
        "INSERT INTO salas (codigo, nombre, capacidad, estado) "
        "VALUES (?, ?, ?, ?);",
        SALAS_INICIALES,
    )
    conexion.commit()
    return len(SALAS_INICIALES)
