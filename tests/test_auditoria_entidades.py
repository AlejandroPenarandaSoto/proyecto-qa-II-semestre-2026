import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.auditoria.servicio import consultar_auditoria
from src.model.estudiantes.servicio import (
    consultar_estudiantes,
    modificar_estudiante,
    registrar_estudiante,
)
from src.model.salas.servicio import (
    consultar_salas,
    modificar_sala,
    registrar_sala,
)


@pytest.fixture
def base_datos_entidades(tmp_path):
    """Prepara una base SQLite temporal para cada prueba."""
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "auditoria_entidades.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje

    try:
        yield
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def test_registrar_estudiante_genera_evento_de_auditoria(
    base_datos_entidades,
):
    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 1

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "creacion"
    assert evento["entidad"] == "estudiante"
    assert evento["entidad_id"] == "C123456789"
    assert evento["detalle"] == (
        "Estudiante C123456789 registrado correctamente."
    )


def test_modificar_estudiante_genera_evento_de_auditoria(
    base_datos_entidades,
):
    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    exito, mensaje = modificar_estudiante(
        "C123456789",
        "Ana Rodríguez Mora",
        "ana.mora@tec.ac.cr",
        "inactivo",
    )
    assert exito, mensaje

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 2

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "modificacion"
    assert evento["entidad"] == "estudiante"
    assert evento["entidad_id"] == "C123456789"
    assert evento["detalle"] == (
        "Estudiante C123456789 modificado correctamente."
    )


def test_registrar_sala_genera_evento_de_auditoria(
    base_datos_entidades,
):
    resultado = registrar_sala(
        codigo="S06",
        nombre="Sala de estudio 6",
        capacidad=6,
    )
    assert resultado["exito"] is True

    auditoria = consultar_auditoria()

    assert len(auditoria["eventos"]) == 1

    evento = auditoria["eventos"][0]
    assert evento["accion"] == "creacion"
    assert evento["entidad"] == "sala"
    assert evento["entidad_id"] == "S06"
    assert evento["detalle"] == "Sala S06 registrada correctamente."


def test_modificar_sala_genera_evento_de_auditoria(
    base_datos_entidades,
):
    resultado = modificar_sala(
        codigo="S01",
        nuevo_nombre="Sala Biblioteca Renovada",
        nueva_capacidad=5,
        nuevo_estado="disponible",
    )
    assert resultado["exito"] is True

    eventos = consultar_auditoria()["eventos"]

    assert len(eventos) == 1
    assert eventos[0]["accion"] == "modificacion"
    assert eventos[0]["entidad"] == "sala"
    assert eventos[0]["entidad_id"] == "S01"
    assert eventos[0]["detalle"] == "Sala S01 modificada correctamente."


def test_operaciones_fallidas_no_generan_eventos(
    base_datos_entidades,
):
    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    duplicado, _mensaje = registrar_estudiante(
        "C123456789",
        "Otra Persona",
        "otra@tec.ac.cr",
    )
    sala_duplicada = registrar_sala("S01", "Sala duplicada", 5)
    sala_invalida = modificar_sala("S01", "Sala", 0, "disponible")

    assert duplicado is False
    assert sala_duplicada["exito"] is False
    assert sala_invalida["exito"] is False
    assert len(consultar_auditoria()["eventos"]) == 1


def test_fallo_de_auditoria_revierte_registro_de_estudiante(
    base_datos_entidades,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.model.estudiantes.servicio.registrar_evento",
        _simular_fallo_de_auditoria,
    )

    exito, _mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )

    assert exito is False
    assert consultar_estudiantes()[2] == []
    assert consultar_auditoria()["eventos"] == []


def test_fallo_de_auditoria_revierte_modificacion_de_estudiante(
    base_datos_entidades,
    monkeypatch,
):
    assert registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )[0]

    monkeypatch.setattr(
        "src.model.estudiantes.servicio.registrar_evento",
        _simular_fallo_de_auditoria,
    )

    exito, _mensaje = modificar_estudiante(
        "C123456789",
        "Ana Rodríguez Mora",
        "ana.mora@tec.ac.cr",
        "inactivo",
    )

    assert exito is False
    estudiante = consultar_estudiantes()[2][0]
    assert estudiante["nombre_completo"] == "Ana Rodríguez"
    assert estudiante["correo"] == "ana@tec.ac.cr"
    assert estudiante["estado"] == "activo"
    assert [
        evento["accion"] for evento in consultar_auditoria()["eventos"]
    ] == ["creacion"]


def test_fallo_de_auditoria_revierte_registro_de_sala(
    base_datos_entidades,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.model.salas.servicio.registrar_evento",
        _simular_fallo_de_auditoria,
    )

    resultado = registrar_sala("S06", "Sala de estudio 6", 6)

    assert resultado["exito"] is False
    assert all(sala["codigo"] != "S06" for sala in consultar_salas())
    assert consultar_auditoria()["eventos"] == []


def test_fallo_de_auditoria_revierte_modificacion_de_sala(
    base_datos_entidades,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.model.salas.servicio.registrar_evento",
        _simular_fallo_de_auditoria,
    )

    resultado = modificar_sala(
        "S01",
        "Sala Biblioteca Renovada",
        5,
        "fuera_de_servicio",
    )

    assert resultado["exito"] is False
    sala = next(
        sala for sala in consultar_salas() if sala["codigo"] == "S01"
    )
    assert sala == {
        "codigo": "S01",
        "nombre": "Sala Biblioteca 1",
        "capacidad": 4,
        "estado": "disponible",
    }
    assert consultar_auditoria()["eventos"] == []


def _simular_fallo_de_auditoria(**_argumentos):
    return {
        "exito": False,
        "mensaje": "Fallo simulado de auditoría.",
    }
