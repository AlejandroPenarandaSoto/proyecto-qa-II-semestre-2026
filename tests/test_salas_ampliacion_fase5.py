"""Trece casos de salas de Fase 4, ejecutables como ampliación de Fase 5.

Los oráculos y datos proceden de la matriz final v3, no del resultado
observado del servicio. No se prueban clics ni se modifica la base real.
"""

import json
from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.salas.servicio import (
    consultar_salas,
    modificar_sala,
    registrar_sala,
)


# Copia explícita del oráculo documental; no se importa la semilla productiva.
SALAS_ESPERADAS = [
    {"codigo": "S01", "nombre": "Sala Biblioteca 1", "capacidad": 4,
     "estado": "disponible"},
    {"codigo": "S02", "nombre": "Sala Biblioteca 2", "capacidad": 6,
     "estado": "disponible"},
    {"codigo": "S03", "nombre": "Laboratorio de estudio", "capacidad": 10,
     "estado": "disponible"},
    {"codigo": "S04", "nombre": "Sala multimedia", "capacidad": 8,
     "estado": "fuera_de_servicio"},
    {"codigo": "S05", "nombre": "Cubículo individual", "capacidad": 1,
     "estado": "disponible"},
]


@pytest.fixture
def base_datos_salas(tmp_path):
    """Aísla cada caso y restaura la ruta aun si falla su preparación."""
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    try:
        configurar_ruta_base_datos(tmp_path / "salas_fase5.db")
        inicializacion = inicializar_base_datos()
        assert inicializacion.exito, inicializacion.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def _observar(caso, requisito, datos, esperado, obtenido):
    """Registra el observado antes de verificarlo, incluso si la prueba falla."""
    print("OBSERVACION_CP " + json.dumps(
        {"caso": caso, "requisito": requisito, "datos": datos,
         "esperado": esperado, "obtenido": obtenido},
        ensure_ascii=False, sort_keys=True,
    ))


def _fotografia_bd():
    conexion = obtener_conexion()
    return {
        tabla: [dict(fila) for fila in conexion.execute(
            f"SELECT * FROM {tabla} ORDER BY id"
        ).fetchall()]
        for tabla in ("salas", "estudiantes", "reservaciones", "auditoria")
    }


def _sala_del_catalogo(codigo):
    return next((sala for sala in consultar_salas()
                 if sala["codigo"] == codigo), None)


def _verificar_registro_rechazado(caso, capacidad, codigo="S06"):
    antes = _fotografia_bd()
    nombre = "Duplicada" if codigo in ("S01", "s01") else "Sala Nueva"
    resultado = registrar_sala(codigo, nombre, capacidad)
    despues = _fotografia_bd()
    _observar(
        caso, "RF-12",
        {"codigo": codigo, "nombre": nombre, "capacidad": capacidad},
        {"exito": False, "mensaje_informativo": True,
         "datos_y_auditoria_sin_cambios": True},
        {"respuesta": resultado, "antes": antes, "despues": despues},
    )
    assert resultado["exito"] is False
    assert isinstance(resultado["mensaje"], str) and resultado["mensaje"].strip()
    assert despues == antes


def _preparar_reserva_futura(conexion):
    """SQL de preparación válido: aísla modificar_sala de crear_reservacion."""
    estudiante = conexion.execute(
        "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) "
        "VALUES (?, ?, ?, ?)",
        ("C123456789", "Ana Rodríguez", "ana@tec.ac.cr", "activo"),
    )
    sala_id = conexion.execute(
        "SELECT id FROM salas WHERE codigo = ?", ("S02",)
    ).fetchone()["id"]
    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    conexion.execute(
        "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, "
        "hora_inicio, duracion_horas, cantidad_personas, estado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (estudiante.lastrowid, sala_id, fecha, "10:00", 1, 5, "activa"),
    )
    conexion.commit()
    return {"carne": "C123456789", "sala": "S02", "fecha": fecha,
            "hora_inicio": "10:00", "duracion_horas": 1,
            "cantidad_personas": 5, "estado": "activa"}


def test_cp_sal_01_catalogo_inicial_completo(base_datos_salas):
    salas = consultar_salas()
    _observar("CP-SAL-01", "RF-04", {"consulta": "salas iniciales"},
              SALAS_ESPERADAS, salas)
    assert salas == SALAS_ESPERADAS


def test_cp_sal_02_orden_ascendente_de_todos_los_codigos(base_datos_salas):
    codigos = [sala["codigo"] for sala in consultar_salas()]
    esperado = ["S01", "S02", "S03", "S04", "S05"]
    _observar("CP-SAL-02", "RF-04", {"consulta": "catálogo inicial"},
              esperado, codigos)
    assert codigos == esperado


def test_cp_sal_03_incluye_sala_fuera_de_servicio(base_datos_salas):
    coincidencias = [sala for sala in consultar_salas()
                    if sala["codigo"] == "S04"]
    esperado = [{"codigo": "S04", "nombre": "Sala multimedia",
                 "capacidad": 8, "estado": "fuera_de_servicio"}]
    _observar("CP-SAL-03", "RF-04; RN-08", {"codigo": "S04"},
              esperado, coincidencias)
    assert coincidencias == esperado


def test_cp_sal_05_registro_valido_aparece_en_catalogo(base_datos_salas):
    antes = consultar_salas()
    sala_esperada = {"codigo": "S06", "nombre": "Sala de estudio 6",
                     "capacidad": 6, "estado": "disponible"}
    resultado = registrar_sala(**sala_esperada)
    despues = consultar_salas()
    _observar(
        "CP-SAL-05", "RF-12", sala_esperada,
        {"exito": True, "nueva_sala": sala_esperada, "cantidad_salas": 6,
         "salas_previas_sin_cambios": True},
        {"respuesta": resultado, "salas": despues},
    )
    assert resultado["exito"] is True
    assert despues == antes + [sala_esperada]


def test_cp_sal_06_rechaza_duplicado_exacto(base_datos_salas):
    _verificar_registro_rechazado("CP-SAL-06", capacidad=5, codigo="S01")


def test_cp_sal_07_rechaza_duplicado_en_minusculas(base_datos_salas):
    _verificar_registro_rechazado("CP-SAL-07", capacidad=5, codigo="s01")


def test_cp_sal_08_rechaza_capacidad_cero(base_datos_salas):
    _verificar_registro_rechazado("CP-SAL-08", capacidad=0)


def test_cp_sal_09_rechaza_capacidad_negativa(base_datos_salas):
    _verificar_registro_rechazado("CP-SAL-09", capacidad=-1)


def test_cp_sal_10_rechaza_capacidad_decimal(base_datos_salas):
    _verificar_registro_rechazado("CP-SAL-10", capacidad=2.5)


def test_cp_sal_11_modifica_nombre_y_estado(base_datos_salas):
    antes = _fotografia_bd()
    resultado = modificar_sala("S02", "Sala Biblioteca 2B", 6,
                               "fuera_de_servicio")
    despues = _fotografia_bd()
    sala = _sala_del_catalogo("S02")
    esperado = {"codigo": "S02", "nombre": "Sala Biblioteca 2B",
                "capacidad": 6, "estado": "fuera_de_servicio"}
    _observar(
        "CP-SAL-11", "RF-12", esperado,
        {"exito": True, "sala": esperado, "otras_salas_sin_cambios": True},
        {"respuesta": resultado, "sala": sala,
         "antes": antes, "despues": despues},
    )
    assert resultado["exito"] is True
    assert sala == esperado
    assert [fila for fila in despues["salas"] if fila["codigo"] != "S02"] == [
        fila for fila in antes["salas"] if fila["codigo"] != "S02"
    ]
    assert despues["reservaciones"] == antes["reservaciones"]


def test_cp_sal_13_reduce_capacidad_sin_reservas_futuras(base_datos_salas):
    antes = _fotografia_bd()
    resultado = modificar_sala("S03", "Laboratorio de estudio", 5,
                               "disponible")
    despues = _fotografia_bd()
    sala = _sala_del_catalogo("S03")
    esperado = {"codigo": "S03", "nombre": "Laboratorio de estudio",
                "capacidad": 5, "estado": "disponible"}
    _observar(
        "CP-SAL-13", "RF-12",
        {"codigo": "S03", "capacidad_anterior": 10, "nueva_capacidad": 5,
         "reservaciones_antes": antes["reservaciones"]},
        {"exito": True, "sala": esperado,
         "reservaciones_sin_cambios": True},
        {"respuesta": resultado, "sala": sala,
         "antes": antes, "despues": despues},
    )
    assert antes["reservaciones"] == []
    assert resultado["exito"] is True
    assert sala == esperado
    assert despues["reservaciones"] == antes["reservaciones"]
    assert [fila for fila in despues["salas"] if fila["codigo"] != "S03"] == [
        fila for fila in antes["salas"] if fila["codigo"] != "S03"
    ]


def test_cp_sal_14_rechaza_capacidad_menor_a_reserva_futura(base_datos_salas):
    reserva = _preparar_reserva_futura(base_datos_salas)
    antes = _fotografia_bd()
    resultado = modificar_sala("S02", "Sala Biblioteca 2", 4, "disponible")
    despues = _fotografia_bd()
    _observar(
        "CP-SAL-14", "RF-12; RN-07",
        {"reserva": reserva, "nueva_capacidad": 4},
        {"exito": False, "datos_y_auditoria_sin_cambios": True},
        {"respuesta": resultado, "antes": antes, "despues": despues},
    )
    assert resultado["exito"] is False
    assert isinstance(resultado["mensaje"], str) and resultado["mensaje"].strip()
    assert despues == antes


def test_cp_sal_15_acepta_capacidad_igual_a_reserva_futura(base_datos_salas):
    reserva = _preparar_reserva_futura(base_datos_salas)
    antes = _fotografia_bd()
    resultado = modificar_sala("S02", "Sala Biblioteca 2", 5, "disponible")
    despues = _fotografia_bd()
    sala = _sala_del_catalogo("S02")
    esperado = {"codigo": "S02", "nombre": "Sala Biblioteca 2",
                "capacidad": 5, "estado": "disponible"}
    _observar(
        "CP-SAL-15", "RF-12; RN-07",
        {"reserva": reserva, "nueva_capacidad": 5},
        {"exito": True, "sala": esperado,
         "reservaciones_sin_cambios": True},
        {"respuesta": resultado, "sala": sala,
         "antes": antes, "despues": despues},
    )
    assert resultado["exito"] is True
    assert sala == esperado
    assert despues["reservaciones"] == antes["reservaciones"]
    assert despues["estudiantes"] == antes["estudiantes"]
    assert [fila for fila in despues["salas"] if fila["codigo"] != "S02"] == [
        fila for fila in antes["salas"] if fila["codigo"] != "S02"
    ]
