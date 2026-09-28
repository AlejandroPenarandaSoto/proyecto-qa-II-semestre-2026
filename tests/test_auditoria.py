from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.auditoria.servicio import (
    consultar_auditoria,
    registrar_evento,
)
from src.model.estudiantes.servicio import registrar_estudiante
from src.model.reservaciones.servicio import (
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    modificar_reservacion,
)


@pytest.fixture
def base_datos_auditoria(tmp_path):
    """Prepara una base de datos temporal exclusiva para cada prueba."""
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "auditoria_pruebas.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje

    try:
        yield
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def test_registrar_evento_guarda_datos(base_datos_auditoria):
    resultado = registrar_evento(
        accion="creacion",
        entidad="reservacion",
        entidad_id="R0001",
        detalle="Reservación creada correctamente.",
    )

    assert resultado["exito"] is True

    evento = obtener_conexion().execute(
        """
        SELECT fecha_hora, accion, entidad, entidad_id, detalle
        FROM auditoria
        """
    ).fetchone()

    assert evento is not None
    assert evento["accion"] == "creacion"
    assert evento["entidad"] == "reservacion"
    assert evento["entidad_id"] == "R0001"
    assert evento["detalle"] == "Reservación creada correctamente."

    datetime.strptime(evento["fecha_hora"], "%Y-%m-%d %H:%M:%S")

def test_consultar_auditoria_muestra_eventos_mas_recientes_primero(
    base_datos_auditoria,
):
    registrar_evento(
        accion="creacion",
        entidad="reservacion",
        entidad_id="R0001",
        detalle="Primera operación.",
    )
    registrar_evento(
        accion="cancelacion",
        entidad="reservacion",
        entidad_id="R0001",
        detalle="Segunda operación.",
    )

    resultado = consultar_auditoria()

    assert resultado["exito"] is True
    assert resultado["mensaje"] == "Consulta de auditoría realizada correctamente."
    assert [
        evento["accion"] for evento in resultado["eventos"]
    ] == ["cancelacion", "creacion"]

def test_crear_reservacion_genera_evento_de_auditoria(
    base_datos_auditoria,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    auditoria = consultar_auditoria()

    assert auditoria["exito"] is True
    assert len(auditoria["eventos"]) == 1

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "creacion"
    assert evento["entidad"] == "reservacion"
    assert evento["entidad_id"] == reservacion["id"]
    assert evento["detalle"] == (
        f"Reservación {reservacion['id']} creada correctamente."
    )

def test_creacion_fallida_no_genera_evento_de_auditoria(
    base_datos_auditoria,
):
    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    resultado = crear_reservacion(
        carne="Z999999999",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )

    assert resultado["exito"] is False

    auditoria = consultar_auditoria()

    assert auditoria["exito"] is True
    assert auditoria["eventos"] == []
    assert auditoria["mensaje"] == "No hay eventos de auditoría registrados."

def test_modificar_reservacion_genera_evento_de_auditoria(
    base_datos_auditoria,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha_original = (
        datetime.now() + timedelta(days=1)
    ).strftime("%Y-%m-%d")
    fecha_nueva = (
        datetime.now() + timedelta(days=2)
    ).strftime("%Y-%m-%d")

    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha_original,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    modificacion = modificar_reservacion(
        reservacion["id"],
        fecha=fecha_nueva,
        hora_inicio="14:00",
    )
    assert modificacion["exito"] is True

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 2

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "modificacion"
    assert evento["entidad"] == "reservacion"
    assert evento["entidad_id"] == reservacion["id"]
    assert evento["detalle"] == (
        f"Reservación {reservacion['id']} modificada correctamente."
    )

def test_modificacion_fallida_no_genera_evento_de_auditoria(
    base_datos_auditoria,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    modificacion = modificar_reservacion(
        reservacion["id"],
        duracion=3,
    )
    assert modificacion["exito"] is False

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 1
    assert auditoria["eventos"][0]["accion"] == "creacion"

def test_cancelar_reservacion_genera_evento_de_auditoria(
    base_datos_auditoria,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    cancelacion = cancelar_reservacion(reservacion["id"])
    assert cancelacion["exito"] is True

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 2

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "cancelacion"
    assert evento["entidad"] == "reservacion"
    assert evento["entidad_id"] == reservacion["id"]
    assert evento["detalle"] == (
        f"Reservación {reservacion['id']} cancelada correctamente."
    )

def test_cancelacion_repetida_no_genera_otro_evento_de_auditoria(
    base_datos_auditoria,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True
    assert cancelar_reservacion(reservacion["id"])["exito"] is True

    segunda_cancelacion = cancelar_reservacion(reservacion["id"])
    assert segunda_cancelacion["exito"] is False

    auditoria = consultar_auditoria()

    assert [
        evento["accion"] for evento in auditoria["eventos"]
    ] == ["cancelacion", "creacion"]

def test_fallo_de_auditoria_revierte_creacion(
    base_datos_auditoria,
    monkeypatch,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    def simular_fallo_de_auditoria(**_argumentos):
        return {
            "exito": False,
            "mensaje": "Fallo simulado de auditoría.",
        }

    monkeypatch.setattr(
        "src.model.reservaciones.servicio.registrar_evento",
        simular_fallo_de_auditoria,
    )

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    resultado = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )

    assert resultado["exito"] is False
    assert consultar_reservaciones()["reservaciones"] == []
    assert consultar_auditoria()["eventos"] == []

def test_fallo_de_auditoria_revierte_modificacion(
    base_datos_auditoria,
    monkeypatch,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    def simular_fallo_de_auditoria(**_argumentos):
        return {
            "exito": False,
            "mensaje": "Fallo simulado de auditoría.",
        }

    monkeypatch.setattr(
        "src.model.reservaciones.servicio.registrar_evento",
        simular_fallo_de_auditoria,
    )

    resultado = modificar_reservacion(
        reservacion["id"],
        hora_inicio="14:00",
    )

    assert resultado["exito"] is False

    reservaciones = consultar_reservaciones()["reservaciones"]
    assert reservaciones[0]["hora_inicio"] == "10:00"

    eventos = consultar_auditoria()["eventos"]
    assert [evento["accion"] for evento in eventos] == ["creacion"]

def test_fallo_de_auditoria_revierte_cancelacion(
    base_datos_auditoria,
    monkeypatch,
):
    estudiante_creado, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert estudiante_creado, mensaje

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reservacion = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    assert reservacion["exito"] is True

    def simular_fallo_de_auditoria(**_argumentos):
        return {
            "exito": False,
            "mensaje": "Fallo simulado de auditoría.",
        }

    monkeypatch.setattr(
        "src.model.reservaciones.servicio.registrar_evento",
        simular_fallo_de_auditoria,
    )

    resultado = cancelar_reservacion(reservacion["id"])

    assert resultado["exito"] is False

    reservaciones = consultar_reservaciones()["reservaciones"]
    assert reservaciones[0]["estado"] == "activa"

    eventos = consultar_auditoria()["eventos"]
    assert [evento["accion"] for evento in eventos] == ["creacion"]

@pytest.mark.parametrize(
    "accion, entidad, entidad_id",
    [
        ("", "reservacion", "R0001"),
        ("   ", "reservacion", "R0001"),
        ("creacion", "", "R0001"),
        ("creacion", "reservacion", None),
    ],
)
def test_registrar_evento_rechaza_datos_obligatorios_vacios(
    base_datos_auditoria,
    accion,
    entidad,
    entidad_id,
):
    resultado = registrar_evento(
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
    )

    assert resultado["exito"] is False
    assert consultar_auditoria()["eventos"] == []