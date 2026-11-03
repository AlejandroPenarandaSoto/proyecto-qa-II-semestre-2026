"""Verificación de INI01 con el oráculo del plan final de Fase 4.

Se comprueban datos exactos, idempotencia, conservación de datos propios y
atomicidad de salas/estudiantes. Toda escritura ocurre en SQLite temporal.
"""

import json
import sqlite3

import pytest

from src.db import inicializador
from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.esquema import ESQUEMA_SQL


# Oráculo independiente del valor de las constantes de código productivo.
# Identidades/estados: Fase 4 final, p. 11. Correos: matriz v3, CP-INI-02.
ESTUDIANTES_ESPERADOS = [
    {"carne": "A001234567", "nombre_completo": "Andrea Solano",
     "correo": "andrea@universidad.ac.cr", "estado": "activo"},
    {"carne": "B009876543", "nombre_completo": "Carlos Méndez",
     "correo": "carlos@universidad.ac.cr", "estado": "activo"},
    {"carne": "C004567890", "nombre_completo": "Daniela Rojas",
     "correo": "daniela@universidad.ac.cr", "estado": "inactivo"},
]


@pytest.fixture
def base_temporal(tmp_path):
    ruta_anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "semilla_verificacion_fase6.db")
    try:
        yield
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_anterior)


def _estudiantes(conexion):
    return [
        dict(fila)
        for fila in conexion.execute(
            "SELECT carne, nombre_completo, correo, estado "
            "FROM estudiantes ORDER BY carne"
        )
    ]


def _conteos(conexion):
    return {
        tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        for tabla in ("salas", "estudiantes", "reservaciones", "auditoria")
    }


def _observar(variante, esperado, obtenido):
    print("OBSERVACION_CP " + json.dumps(
        {"caso": "CP-INI-02", "variante_fase6": variante, "requisito": "RF-01",
         "esperado": esperado, "obtenido": obtenido},
        ensure_ascii=False, sort_keys=True,
    ))


def test_f6_ini01_carga_estudiantes_exactos_sin_reservas_ni_auditoria(base_temporal):
    resultado = inicializador.inicializar_base_datos()
    conexion = obtener_conexion()
    estudiantes = _estudiantes(conexion)
    conteos = _conteos(conexion)
    _observar(
        "primera_carga_exacta",
        {"exito": True, "estudiantes": ESTUDIANTES_ESPERADOS,
         "reservaciones": 0, "auditoria": 0},
        {"exito": resultado.exito, "mensaje": resultado.mensaje,
         "estudiantes": estudiantes, "conteos": conteos},
    )
    assert resultado.exito is True, resultado.mensaje
    assert estudiantes == ESTUDIANTES_ESPERADOS
    assert conteos == {"salas": 5, "estudiantes": 3, "reservaciones": 0, "auditoria": 0}


def test_f6_ini01_reinicializar_preserva_modificaciones_sin_duplicar(base_temporal):
    primera = inicializador.inicializar_base_datos()
    assert primera.exito, primera.mensaje
    conexion = obtener_conexion()
    conexion.execute(
        "UPDATE estudiantes SET nombre_completo = ?, correo = ?, estado = ? WHERE carne = ?",
        ("Andrea Solano Actualizada", "andrea.nuevo@universidad.ac.cr", "inactivo", "A001234567"),
    )
    conexion.commit()
    antes = _estudiantes(conexion)

    segunda = inicializador.inicializar_base_datos()
    despues = _estudiantes(conexion)
    conteos = _conteos(conexion)
    _observar(
        "segunda_carga_conserva_datos",
        {"exito": True, "estudiantes": antes, "cantidad": 3},
        {"exito": segunda.exito, "mensaje": segunda.mensaje,
         "estudiantes": despues, "conteos": conteos},
    )
    assert segunda.exito is True, segunda.mensaje
    assert despues == antes
    assert despues[0] == {
        "carne": "A001234567", "nombre_completo": "Andrea Solano Actualizada",
        "correo": "andrea.nuevo@universidad.ac.cr", "estado": "inactivo",
    }
    assert conteos == {"salas": 5, "estudiantes": 3, "reservaciones": 0, "auditoria": 0}


def test_f6_ini01_no_inyecta_semilla_si_existe_estudiante_del_usuario(base_temporal):
    conexion = obtener_conexion()
    conexion.executescript(ESQUEMA_SQL)
    propio = {"carne": "U123456789", "nombre_completo": "Usuario Propio",
              "correo": "propio@universidad.ac.cr", "estado": "inactivo"}
    conexion.execute(
        "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?, ?, ?, ?)",
        (propio["carne"], propio["nombre_completo"], propio["correo"], propio["estado"]),
    )
    conexion.commit()

    resultado = inicializador.inicializar_base_datos()
    estudiantes = _estudiantes(conexion)
    conteos = _conteos(conexion)
    _observar(
        "base_con_datos_del_usuario",
        {"exito": True, "estudiantes": [propio]},
        {"exito": resultado.exito, "mensaje": resultado.mensaje,
         "estudiantes": estudiantes, "conteos": conteos},
    )
    assert resultado.exito is True, resultado.mensaje
    assert estudiantes == [propio]
    assert conteos == {"salas": 5, "estudiantes": 1, "reservaciones": 0, "auditoria": 0}


def test_f6_ini01_fallo_semilla_estudiantes_revierte_datos_parciales(base_temporal, monkeypatch):
    def fallar_despues_de_insertar_un_estudiante(conexion):
        primero = ESTUDIANTES_ESPERADOS[0]
        conexion.execute(
            "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?, ?, ?, ?)",
            (primero["carne"], primero["nombre_completo"], primero["correo"], primero["estado"]),
        )
        raise sqlite3.IntegrityError("Fallo simulado al completar la semilla de estudiantes")

    monkeypatch.setattr(
        inicializador, "insertar_estudiantes_iniciales", fallar_despues_de_insertar_un_estudiante
    )
    resultado = inicializador.inicializar_base_datos()
    conteos = _conteos(obtener_conexion())
    _observar(
        "fallo_de_semilla_atomica",
        {"exito": False, "conteos": {"salas": 0, "estudiantes": 0,
                                     "reservaciones": 0, "auditoria": 0}},
        {"exito": resultado.exito, "mensaje": resultado.mensaje,
         "salas_insertadas": resultado.salas_insertadas, "conteos": conteos},
    )
    assert resultado.exito is False
    assert "Fallo simulado" in resultado.mensaje
    assert resultado.salas_insertadas == 0
    assert conteos == {"salas": 0, "estudiantes": 0, "reservaciones": 0, "auditoria": 0}
