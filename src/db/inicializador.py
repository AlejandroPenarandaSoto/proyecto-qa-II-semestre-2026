"""
RF-01 · Cargar datos.

Punto de entrada de la capa de persistencia: se ejecuta al iniciar la
aplicación y garantiza que, exista o no la base de datos, el sistema
quede listo para operar sin duplicar información y sin cerrarse de
forma inesperada (RNF-05 - Robustez).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from . import conexion as conexion_bd
from .esquema import ESQUEMA_SQL
from .semilla import insertar_salas_iniciales


@dataclass
class ResultadoInicializacion:
    """Resultado informativo de `inicializar_base_datos`, pensado para
    que la capa de presentación decida qué mostrarle a la persona
    usuaria sin necesidad de inspeccionar excepciones."""

    exito: bool
    base_datos_creada: bool
    salas_insertadas: int
    mensaje: str


def inicializar_base_datos() -> ResultadoInicializacion:
    """Abre (o crea) la base de datos SQLite, aplica el esquema y carga
    los datos iniciales cuando corresponde.

    Criterios de aceptación cubiertos:
    - Si la base de datos existe y es válida, se utiliza sin duplicar
      registros.
    - Si la base de datos no existe, se crea con su estructura y datos
      iniciales.
    - Las salas iniciales quedan disponibles desde la primera ejecución.
    - Ningún error durante este proceso produce el cierre inesperado de
      la aplicación: toda excepción de SQLite se captura y se informa
      mediante el resultado devuelto.
    """
    base_datos_ya_existia = conexion_bd.la_base_datos_existe()

    try:
        conexion = conexion_bd.obtener_conexion()
        conexion.executescript(ESQUEMA_SQL)
        conexion.commit()

        salas_insertadas = insertar_salas_iniciales(conexion)

        if base_datos_ya_existia:
            mensaje = "Base de datos existente cargada correctamente."
        else:
            mensaje = "Base de datos creada e inicializada correctamente."

        return ResultadoInicializacion(
            exito=True,
            base_datos_creada=not base_datos_ya_existia,
            salas_insertadas=salas_insertadas,
            mensaje=mensaje,
        )
    except sqlite3.Error as error:
        return ResultadoInicializacion(
            exito=False,
            base_datos_creada=False,
            salas_insertadas=0,
            mensaje=f"No fue posible inicializar la base de datos: {error}",
        )
