from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.auditoria.servicio import consultar_auditoria
from src.model.estudiantes.servicio import registrar_estudiante
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    crear_reservaciones_recurrentes,
    previsualizar_reservaciones_recurrentes,
)

CARNE = "C123456789"
CARNE_B = "A123456789"


@pytest.fixture
def base_datos_recurrencias(tmp_path):
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "recurrencias.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje
    exito, mensaje = registrar_estudiante(
        CARNE,
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    try:
        yield
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def _fecha_futura(dias=10):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _parametros(fecha=None, semanas=3):
    return {
        "carne": CARNE,
        "codigo_sala": "S01",
        "fecha": fecha or _fecha_futura(),
        "hora_inicio": "10:00",
        "duracion": 1,
        "cantidad_personas": 2,
        "semanas": semanas,
    }


@pytest.mark.parametrize("semanas", [1, 9, True, 2.5, "2"])
def test_rechaza_cantidad_de_semanas_invalida(
    base_datos_recurrencias,
    semanas,
):
    resultado = previsualizar_reservaciones_recurrentes(
        **_parametros(semanas=semanas)
    )

    assert resultado["exito"] is False
    assert "2 y 8" in resultado["mensaje"]
    assert consultar_reservaciones()["reservaciones"] == []


def test_previsualiza_fechas_consecutivas_sin_guardar(base_datos_recurrencias):
    fecha_inicial = _fecha_futura()

    resultado = previsualizar_reservaciones_recurrentes(
        **_parametros(fecha=fecha_inicial, semanas=3)
    )

    assert resultado["exito"] is True
    assert resultado["puede_crear"] is True
    assert [item["fecha"] for item in resultado["ocurrencias"]] == [
        fecha_inicial,
        _fecha_futura(17),
        _fecha_futura(24),
    ]
    assert all(item["disponible"] for item in resultado["ocurrencias"])
    assert consultar_reservaciones()["reservaciones"] == []


def test_previsualizacion_identifica_conflicto_por_ocurrencia(
    base_datos_recurrencias,
):
    fecha_inicial = _fecha_futura()
    exito, mensaje = registrar_estudiante(
        CARNE_B,
        "Carlos López",
        "carlos@tec.ac.cr",
    )
    assert exito, mensaje
    conflicto = crear_reservacion(
        carne=CARNE_B,
        codigo_sala="S01",
        fecha=_fecha_futura(17),
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert conflicto["exito"] is True

    resultado = previsualizar_reservaciones_recurrentes(
        **_parametros(fecha=fecha_inicial, semanas=3)
    )

    assert resultado["exito"] is True
    assert resultado["puede_crear"] is False
    assert [item["disponible"] for item in resultado["ocurrencias"]] == [
        True,
        False,
        True,
    ]
    assert "conflicto" in resultado["ocurrencias"][1]["mensaje"].lower()


def test_crea_serie_atomica_con_identificador_compartido(
    base_datos_recurrencias,
):
    fecha_inicial = _fecha_futura()

    resultado = crear_reservaciones_recurrentes(
        **_parametros(fecha=fecha_inicial, semanas=4)
    )

    assert resultado["exito"] is True
    assert resultado["serie_id"] == "SR0001"
    assert resultado["ids"] == ["R0001", "R0002", "R0003", "R0004"]

    reservaciones = consultar_reservaciones()["reservaciones"]
    assert len(reservaciones) == 4
    assert {item["serie_id"] for item in reservaciones} == {"SR0001"}


def test_conflicto_impide_guardar_toda_la_serie(base_datos_recurrencias):
    fecha_inicial = _fecha_futura()
    exito, mensaje = registrar_estudiante(
        CARNE_B,
        "Carlos López",
        "carlos@tec.ac.cr",
    )
    assert exito, mensaje
    existente = crear_reservacion(
        carne=CARNE_B,
        codigo_sala="S01",
        fecha=_fecha_futura(17),
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert existente["exito"] is True

    resultado = crear_reservaciones_recurrentes(
        **_parametros(fecha=fecha_inicial, semanas=3)
    )

    assert resultado["exito"] is False
    reservaciones = consultar_reservaciones()["reservaciones"]
    assert [item["id"] for item in reservaciones] == ["R0001"]


def test_fallo_de_auditoria_revierte_toda_la_serie(
    base_datos_recurrencias,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.model.reservaciones.servicio.registrar_evento",
        lambda **_argumentos: {"exito": False, "mensaje": "Fallo simulado."},
    )

    resultado = crear_reservaciones_recurrentes(**_parametros(semanas=4))

    assert resultado["exito"] is False
    assert consultar_reservaciones()["reservaciones"] == []


def test_serie_cuenta_como_un_cupo_del_limite(base_datos_recurrencias):
    fecha = _fecha_futura()
    serie = crear_reservaciones_recurrentes(
        **_parametros(fecha=fecha, semanas=8)
    )
    assert serie["exito"] is True

    segunda_unidad = crear_reservacion(CARNE, "S02", fecha, "13:00", 1, 2)
    tercera_unidad = crear_reservacion(CARNE, "S03", fecha, "15:00", 1, 2)
    cuarta_unidad = crear_reservacion(CARNE, "S05", fecha, "17:00", 1, 1)

    assert segunda_unidad["exito"] is True
    assert tercera_unidad["exito"] is True
    assert cuarta_unidad["exito"] is False
    assert "3" in cuarta_unidad["mensaje"]


def test_cancelar_una_ocurrencia_conserva_las_demas(base_datos_recurrencias):
    serie = crear_reservaciones_recurrentes(**_parametros(semanas=3))
    assert serie["exito"] is True

    resultado = cancelar_reservacion(serie["ids"][1])

    assert resultado["exito"] is True
    estados = {
        item["id"]: item["estado"]
        for item in consultar_reservaciones()["reservaciones"]
    }
    assert estados == {
        "R0001": "activa",
        "R0002": "cancelada",
        "R0003": "activa",
    }


def test_cancelar_ocurrencia_y_futuras_de_la_serie(base_datos_recurrencias):
    serie = crear_reservaciones_recurrentes(**_parametros(semanas=4))
    assert serie["exito"] is True

    resultado = cancelar_ocurrencias_futuras(serie["ids"][1])

    assert resultado["exito"] is True
    assert resultado["serie_id"] == "SR0001"
    assert resultado["cantidad_cancelada"] == 3
    estados = {
        item["id"]: item["estado"]
        for item in consultar_reservaciones()["reservaciones"]
    }
    assert estados == {
        "R0001": "activa",
        "R0002": "cancelada",
        "R0003": "cancelada",
        "R0004": "cancelada",
    }


def test_fallo_de_auditoria_revierte_cancelacion_futura(
    base_datos_recurrencias,
    monkeypatch,
):
    serie = crear_reservaciones_recurrentes(**_parametros(semanas=3))
    assert serie["exito"] is True
    monkeypatch.setattr(
        "src.model.reservaciones.servicio.registrar_evento",
        lambda **_argumentos: {"exito": False, "mensaje": "Fallo simulado."},
    )

    resultado = cancelar_ocurrencias_futuras(serie["ids"][1])

    assert resultado["exito"] is False
    estados = {
        item["id"]: item["estado"]
        for item in consultar_reservaciones()["reservaciones"]
    }
    assert set(estados.values()) == {"activa"}


def test_no_cancela_futuras_de_una_reservacion_individual(
    base_datos_recurrencias,
):
    individual = crear_reservacion(
        CARNE,
        "S01",
        _fecha_futura(),
        "10:00",
        1,
        2,
    )
    assert individual["exito"] is True

    resultado = cancelar_ocurrencias_futuras(individual["id"])

    assert resultado["exito"] is False
    assert "serie" in resultado["mensaje"].lower()
    assert consultar_reservaciones()["reservaciones"][0]["estado"] == "activa"


def test_operaciones_de_serie_generan_auditoria(base_datos_recurrencias):
    serie = crear_reservaciones_recurrentes(**_parametros(semanas=3))
    assert serie["exito"] is True
    cancelacion = cancelar_ocurrencias_futuras(serie["ids"][1])
    assert cancelacion["exito"] is True

    eventos = consultar_auditoria()["eventos"]
    eventos_serie = [
        evento
        for evento in eventos
        if evento["entidad"] == "reservacion"
        and evento["entidad_id"] == "SR0001"
    ]
    assert [evento["accion"] for evento in eventos_serie] == [
        "cancelacion",
        "creacion",
    ]
