"""Ampliación RF-02: cuatro límites previstos por CP-EST-04/05/07/08.

No se modifican pruebas originales. Cada caso utiliza una base temporal.
"""

import json

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import registrar_estudiante


@pytest.fixture
def base_temporal(tmp_path):
    ruta_anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "estudiantes_limites.db")
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_anterior)


def _estado(conexion):
    return {
        "estudiantes": [
            dict(fila) for fila in conexion.execute(
                "SELECT carne, nombre_completo, correo, estado FROM estudiantes ORDER BY carne"
            )
        ],
        "auditoria": [
            dict(fila) for fila in conexion.execute("SELECT * FROM auditoria ORDER BY id")
        ],
    }


def _registrar_observacion(caso, carne, nombre, exito, mensaje, antes, despues):
    observacion = {
        "caso": caso,
        "requisito": "RF-02",
        "carne": carne,
        "nombre": nombre,
        "correo": "ana@tec.ac.cr",
        "exito_obtenido": exito,
        "mensaje_obtenido": mensaje,
        "estado_antes": antes,
        "estado_despues": despues,
        "sin_cambios": antes == despues,
    }
    print("OBSERVACION_CP " + json.dumps(observacion, ensure_ascii=False, sort_keys=True))


def _comprobar_rechazo(conexion, caso, carne, nombre, campo):
    antes = _estado(conexion)
    exito, mensaje = registrar_estudiante(carne, nombre, "ana@tec.ac.cr")
    despues = _estado(conexion)
    _registrar_observacion(caso, carne, nombre, exito, mensaje, antes, despues)
    assert exito is False
    assert campo in mensaje.lower()
    assert despues == antes, "El rechazo debe conservar estudiantes y auditoría."


def test_cp_est_04_rechaza_carne_de_9_caracteres(base_temporal):
    """CP-EST-04: el carné de nueve caracteres se rechaza sin guardar datos."""
    carne = "C12345678"
    assert len(carne) == 9
    _comprobar_rechazo(base_temporal, "CP-EST-04", carne, "Ana Rodríguez", "carné")


def test_cp_est_05_rechaza_carne_de_11_caracteres(base_temporal):
    """CP-EST-05: el carné de once caracteres se rechaza sin guardar datos."""
    carne = "C1234567890"
    assert len(carne) == 11
    _comprobar_rechazo(base_temporal, "CP-EST-05", carne, "Ana Rodríguez", "carné")


def test_cp_est_07_rechaza_nombre_de_2_caracteres(base_temporal):
    """CP-EST-07: el nombre de dos caracteres se rechaza sin guardar datos."""
    nombre = "Al"
    assert len(nombre) == 2
    _comprobar_rechazo(base_temporal, "CP-EST-07", "C123456789", nombre, "nombre")


def test_cp_est_08_acepta_nombre_de_3_caracteres(base_temporal):
    """CP-EST-08: se registra Ana con carné válido y estado activo."""
    nombre = "Ana"
    assert len(nombre) == 3
    antes = _estado(base_temporal)
    exito, mensaje = registrar_estudiante("C123456789", nombre, "ana@tec.ac.cr")
    despues = _estado(base_temporal)
    _registrar_observacion(
        "CP-EST-08", "C123456789", nombre, exito, mensaje, antes, despues
    )
    assert exito is True, mensaje
    assert despues["estudiantes"] == [
        {
            "carne": "C123456789",
            "nombre_completo": "Ana",
            "correo": "ana@tec.ac.cr",
            "estado": "activo",
        }
    ]
