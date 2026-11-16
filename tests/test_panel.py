from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import registrar_estudiante
from src.model.panel.servicio import consultar_panel
from src.model.reservaciones.servicio import (
    cancelar_reservacion,
    crear_reservacion,
    modificar_reservacion,
)


@pytest.fixture
def base_datos_panel(tmp_path):
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "panel.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje
    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    try:
        yield
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def _fecha_futura(dias):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _crear(fecha, sala, hora, duracion=1, personas=2):
    resultado = crear_reservacion(
        carne="C123456789",
        codigo_sala=sala,
        fecha=fecha,
        hora_inicio=hora,
        duracion=duracion,
        cantidad_personas=personas,
    )
    assert resultado["exito"] is True
    return resultado["id"]


def test_panel_consolida_ocupacion_hoy_y_proximas(base_datos_panel):
    fecha_panel = _fecha_futura(10)
    fecha_proxima = _fecha_futura(11)
    _crear(fecha_panel, "S01", "10:00", duracion=2)
    cancelada = _crear(fecha_panel, "S02", "14:00")
    assert cancelar_reservacion(cancelada)["exito"] is True
    _crear(fecha_proxima, "S03", "12:00", personas=4)

    resultado = consultar_panel(
        ahora=datetime.strptime(
            f"{fecha_panel} 09:00",
            "%Y-%m-%d %H:%M",
        )
    )

    assert resultado["exito"] is True
    assert len(resultado["reservaciones_hoy"]) == 2
    assert [
        item["id"] for item in resultado["proximas_reservaciones"]
    ] == ["R0001", "R0003"]

    sala_1 = next(
        sala
        for sala in resultado["ocupacion_salas"]
        if sala["codigo"] == "S01"
    )
    assert sala_1["reservaciones_activas"] == 1
    assert sala_1["horas_reservadas"] == 2
    assert sala_1["personas_reservadas"] == 2

    sala_2 = next(
        sala
        for sala in resultado["ocupacion_salas"]
        if sala["codigo"] == "S02"
    )
    assert sala_2["reservaciones_activas"] == 0


def test_filtros_se_combinan_simultaneamente(base_datos_panel):
    fecha = _fecha_futura(10)
    _crear(fecha, "S01", "10:00")
    cancelada = _crear(fecha, "S02", "12:00")
    assert cancelar_reservacion(cancelada)["exito"] is True

    resultado = consultar_panel(
        fecha=fecha,
        codigo_sala="s02",
        estado="CANCELADA",
    )

    assert resultado["exito"] is True
    assert len(resultado["resultados"]) == 1
    assert resultado["resultados"][0]["id"] == "R0002"
    assert resultado["filtros"] == {
        "fecha": fecha,
        "codigo_sala": "S02",
        "estado": "cancelada",
    }


def test_panel_devuelve_estado_vacio_claro(base_datos_panel):
    resultado = consultar_panel(
        fecha=_fecha_futura(20),
        codigo_sala="S05",
        estado="activa",
    )

    assert resultado["exito"] is True
    assert resultado["resultados"] == []
    assert resultado["mensaje"] == (
        "No hay reservaciones para los filtros seleccionados."
    )


@pytest.mark.parametrize(
    "parametros, texto_esperado",
    [
        ({"fecha": "10-10-2026"}, "formato"),
        ({"estado": "pendiente"}, "activa o cancelada"),
        ({"ahora": "2026-10-10"}, "referencia"),
    ],
)
def test_panel_rechaza_filtros_invalidos(
    base_datos_panel,
    parametros,
    texto_esperado,
):
    resultado = consultar_panel(**parametros)

    assert resultado["exito"] is False
    assert texto_esperado in resultado["mensaje"].lower()
    assert resultado["resultados"] == []


def test_panel_refleja_operaciones_sin_cache(base_datos_panel):
    fecha = _fecha_futura(10)
    inicial = consultar_panel(fecha=fecha)
    assert inicial["resultados"] == []

    identificador = _crear(fecha, "S01", "10:00")
    despues_de_crear = consultar_panel(fecha=fecha)
    assert [
        item["id"] for item in despues_de_crear["resultados"]
    ] == [identificador]

    modificacion = modificar_reservacion(
        identificador,
        codigo_sala="S02",
        hora_inicio="12:00",
    )
    assert modificacion["exito"] is True
    despues_de_modificar = consultar_panel(
        fecha=fecha,
        codigo_sala="S02",
        estado="activa",
    )
    assert [
        item["id"] for item in despues_de_modificar["resultados"]
    ] == [identificador]
    assert despues_de_modificar["resultados"][0]["hora_inicio"] == "12:00"

    assert cancelar_reservacion(identificador)["exito"] is True
    despues_de_cancelar = consultar_panel(
        fecha=fecha,
        estado="cancelada",
    )
    assert [
        item["id"] for item in despues_de_cancelar["resultados"]
    ] == [identificador]
