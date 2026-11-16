"""Verifica la corrección de DEF-F5-P4-03 (Grupo 4): auditoría de series recurrentes."""

from datetime import date, timedelta
import re

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.auditoria.servicio import consultar_auditoria
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    crear_reservaciones_recurrentes,
)


@pytest.fixture
def base_temporal(tmp_path):
    anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "verificacion_auditoria_fase8.db")
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)


def _eventos_de_serie(serie_id):
    return [
        evento
        for evento in consultar_auditoria()["eventos"]
        if evento["entidad"] == "reservacion" and evento["entidad_id"] == serie_id
    ]


def _ids_citados(detalle):
    # \b evita confundir R0001 con el código de serie SR0001.
    return set(re.findall(r"\bR\d{4}\b", detalle))


def _crear_serie():
    fecha = (date.today() + timedelta(days=2)).isoformat()
    serie = crear_reservaciones_recurrentes("A001234567", "S01", fecha, "10:00", 1, 2, 3)
    assert serie["exito"] is True, serie
    return serie


def test_f8_aud_01_creacion_de_serie_registra_ids_de_cada_ocurrencia(base_temporal):
    serie = _crear_serie()
    (evento,) = _eventos_de_serie(serie["serie_id"])
    assert evento["accion"] == "creacion"
    assert _ids_citados(evento["detalle"]) == set(serie["ids"])


def test_f8_aud_02_cancelacion_de_futuras_registra_solo_ids_cancelados(base_temporal):
    serie = _crear_serie()
    primera, segunda, tercera = serie["ids"]
    assert cancelar_ocurrencias_futuras(segunda)["exito"] is True

    cancelacion = next(e for e in _eventos_de_serie(serie["serie_id"]) if e["accion"] == "cancelacion")
    assert _ids_citados(cancelacion["detalle"]) == {segunda, tercera}
    assert primera not in _ids_citados(cancelacion["detalle"])
