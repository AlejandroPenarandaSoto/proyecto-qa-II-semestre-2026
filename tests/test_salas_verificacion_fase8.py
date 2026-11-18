"""Verifica las correcciones de DEF-F5-P4-01 y DEF-F5-P4-02 (Grupo 4)."""

from datetime import date, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.panel.servicio import consultar_panel
from src.model.reservaciones.servicio import crear_reservacion
from src.model.salas import servicio


@pytest.fixture
def base_temporal(tmp_path):
    anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "verificacion_fase8.db")
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)


def _salas(conexion):
    return [dict(fila) for fila in conexion.execute("SELECT * FROM salas ORDER BY id")]


@pytest.mark.parametrize("codigo", [" S01 ", "S01 ", " s01"])
def test_f8_sal_01_rechaza_codigo_con_espacios_equivalente_a_existente(base_temporal, codigo):
    antes = _salas(base_temporal)
    resultado = servicio.registrar_sala(codigo, "Sala equivalente", 3)
    assert resultado["exito"] is False
    assert "registrado" in resultado["mensaje"]
    assert _salas(base_temporal) == antes


@pytest.mark.parametrize("nombre", ["", "   "])
def test_f8_sal_02_rechaza_nombre_vacio_al_registrar_y_modificar(base_temporal, nombre):
    antes = _salas(base_temporal)
    registro = servicio.registrar_sala("S07", nombre, 3)
    modificacion = servicio.modificar_sala("S01", nombre, 4, "disponible")
    assert registro["exito"] is False
    assert modificacion["exito"] is False
    assert "nombre" in registro["mensaje"].lower()
    assert "nombre" in modificacion["mensaje"].lower()
    assert _salas(base_temporal) == antes


def test_f8_sal_03_codigo_en_minuscula_es_la_misma_sala_en_todos_los_modulos(base_temporal):
    fecha = (date.today() + timedelta(days=2)).isoformat()
    assert servicio.registrar_sala("s06", "Sala nueva", 4)["exito"] is True

    reserva = crear_reservacion("A001234567", "S06", fecha, "10:00", 1, 2)
    disponibilidad = servicio.consultar_disponibilidad("S06", fecha, "10:00", 1)
    panel = consultar_panel(codigo_sala="s06")

    assert reserva["exito"] is True, reserva
    assert disponibilidad["disponible"] is False
    assert disponibilidad["motivo"] != "La sala especificada no existe."
    assert reserva["id"] in [fila["id"] for fila in panel["resultados"]]


def test_f8_sal_04_modificar_con_codigo_en_minuscula_actualiza_la_sala(base_temporal):
    resultado = servicio.modificar_sala("s02", "Sala Biblioteca 2", 6, "disponible")
    fila = base_temporal.execute("SELECT codigo, nombre FROM salas WHERE codigo = 'S02'").fetchone()
    assert resultado["exito"] is True, resultado
    assert dict(fila) == {"codigo": "S02", "nombre": "Sala Biblioteca 2"}
