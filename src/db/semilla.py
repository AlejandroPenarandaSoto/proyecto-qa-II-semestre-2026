"""Catálogo y estudiantes iniciales previstos por el plan de Fase 4.

Las identidades y estados de estudiantes proceden del documento final de
Fase 4, página 11; sus correos, de CP-INI-02 en la matriz final v3.
Los helpers no confirman transacciones: esa responsabilidad es del llamador.
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


ESTUDIANTES_INICIALES: List[Tuple[str, str, str, str]] = [
    ("A001234567", "Andrea Solano", "andrea@universidad.ac.cr", "activo"),
    ("B009876543", "Carlos Méndez", "carlos@universidad.ac.cr", "activo"),
    ("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", "inactivo"),
]


def insertar_salas_iniciales(conexion: sqlite3.Connection) -> int:
    """Inserta el catálogo de salas iniciales únicamente si la tabla
    está vacía, para no duplicar registros en ejecuciones posteriores.

    Devuelve la cantidad de filas insertadas (0 si ya había datos).
    No confirma la transacción; el llamador decide commit o rollback.
    """
    (cantidad_actual,) = conexion.execute("SELECT COUNT(*) FROM salas;").fetchone()
    if cantidad_actual > 0:
        return 0

    conexion.executemany(
        "INSERT INTO salas (codigo, nombre, capacidad, estado) "
        "VALUES (?, ?, ?, ?);",
        SALAS_INICIALES,
    )
    return len(SALAS_INICIALES)


def insertar_estudiantes_iniciales(conexion: sqlite3.Connection) -> int:
    """Carga los tres estudiantes de Fase 4 solo si la tabla está vacía.

    Si hay datos previos, los conserva sin insertar ni sobrescribir filas.
    Devuelve el número de filas insertadas y no confirma la transacción.
    """
    (cantidad_actual,) = conexion.execute("SELECT COUNT(*) FROM estudiantes;").fetchone()
    if cantidad_actual > 0:
        return 0

    conexion.executemany(
        "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) "
        "VALUES (?, ?, ?, ?);",
        ESTUDIANTES_INICIALES,
    )
    return len(ESTUDIANTES_INICIALES)
