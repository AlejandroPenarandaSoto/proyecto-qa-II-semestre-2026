"""
Módulo de conexión a la base de datos SQLite.

Centraliza la apertura de la conexión para evitar condiciones de carrera
por escritura concurrente (riesgo R-08 del registro de riesgos): toda la
aplicación debe operar sobre una única conexión controlada, permitiendo
manejo explícito de transacciones (commit/rollback).

La ruta del archivo se calcula de forma relativa a este módulo (nunca
"hardcodeada") para cumplir RNF-03 - Portabilidad, y puede sobrescribirse
mediante `configurar_ruta_base_datos`, lo que permite aislar cada prueba
automatizada en un archivo temporal sin depender de una GUI (RNF-10).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Union

_ruta_base_datos: Path = Path(__file__).resolve().parent / "reservas.db"
_conexion: Optional[sqlite3.Connection] = None


def configurar_ruta_base_datos(ruta: Union[str, Path]) -> None:
    """Sobrescribe la ubicación del archivo de base de datos.

    Cierra cualquier conexión previamente abierta para evitar operar
    por error sobre el archivo anterior. Pensado principalmente para
    pruebas automatizadas.
    """
    global _ruta_base_datos, _conexion
    if _conexion is not None:
        _conexion.close()
        _conexion = None
    _ruta_base_datos = Path(ruta)


def obtener_ruta_base_datos() -> Path:
    """Devuelve la ruta actualmente configurada del archivo SQLite."""
    return _ruta_base_datos


def la_base_datos_existe() -> bool:
    """Indica si el archivo de base de datos ya existe en disco.

    Debe consultarse ANTES de abrir la conexión: `sqlite3.connect` crea
    el archivo automáticamente si no existe, por lo que preguntar
    después siempre respondería "sí".
    """
    return _ruta_base_datos.exists()


def obtener_conexion() -> sqlite3.Connection:
    """Devuelve la única conexión SQLite de la aplicación (patrón
    singleton), abriéndola la primera vez que se solicita.
    """
    global _conexion
    if _conexion is None:
        _ruta_base_datos.parent.mkdir(parents=True, exist_ok=True)
        _conexion = sqlite3.connect(_ruta_base_datos, check_same_thread=False)
        _conexion.row_factory = sqlite3.Row
        # Reglas de integridad referencial activas (RNF-06 - Integridad).
        _conexion.execute("PRAGMA foreign_keys = ON;")
    return _conexion


def cerrar_conexion() -> None:
    """Cierra la conexión activa, si existe.

    Se usa durante el cierre controlado de la aplicación (RF-10) y entre
    pruebas automatizadas para evitar archivos bloqueados.
    """
    global _conexion
    if _conexion is not None:
        _conexion.close()
        _conexion = None
