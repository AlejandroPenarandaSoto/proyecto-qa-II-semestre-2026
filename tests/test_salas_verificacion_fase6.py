"""Verifica las correcciones de BUG-P1-SAL-01 y BUG-P1-DIS-01."""

from datetime import date, datetime, timedelta
import json

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.salas import servicio


@pytest.fixture
def base_temporal(tmp_path):
    anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "verificacion_fase6.db")
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)


def _estado(conexion):
    return {tabla: [dict(fila) for fila in conexion.execute(f"SELECT * FROM {tabla} ORDER BY id")]
            for tabla in ("estudiantes", "salas", "reservaciones", "auditoria")}


def _observar(caso, datos, esperado, obtenido):
    print("OBSERVACION_CP " + json.dumps({"caso": caso, "datos": datos, "esperado": esperado,
                                           "obtenido": obtenido}, ensure_ascii=False, sort_keys=True))


def test_f6_sal_01_rechaza_mayusculas_si_existe_codigo_en_minusculas(base_temporal):
    base_temporal.execute(
        "INSERT INTO salas (codigo, nombre, capacidad, estado) VALUES (?, ?, ?, ?)",
        ("s06", "Sala previa", 4, "disponible"),
    )
    base_temporal.commit()
    antes = _estado(base_temporal)
    resultado = servicio.registrar_sala("S06", "Duplicada", 4)
    despues = _estado(base_temporal)
    _observar("F6-SAL-01", {"existente": "s06", "solicitado": "S06"},
              {"exito": False, "sin_cambios": True},
              {"respuesta": resultado, "antes": antes, "despues": despues})
    assert resultado["exito"] is False
    assert "registrado" in resultado["mensaje"]
    assert despues == antes


def test_f6_sal_02_conserva_registro_de_codigo_nuevo_en_minusculas(base_temporal):
    resultado = servicio.registrar_sala("s06", "Sala nueva", 4)
    fila = base_temporal.execute("SELECT codigo, nombre, capacidad, estado FROM salas WHERE codigo = ?", ("s06",)).fetchone()
    esperado = {"codigo": "s06", "nombre": "Sala nueva", "capacidad": 4, "estado": "disponible"}
    _observar("F6-SAL-02", {"codigo": "s06", "nombre": "Sala nueva", "capacidad": 4},
              {"exito": True, "fila": esperado},
              {"respuesta": resultado, "fila": dict(fila) if fila else None})
    assert resultado["exito"] is True
    assert fila is not None and dict(fila) == esperado


def test_f6_dis_01_hora_con_y_sin_cero_coinciden_en_franja_libre(base_temporal):
    fecha = (date.today() + timedelta(days=1)).isoformat()
    antes = _estado(base_temporal)
    sin_cero = servicio.consultar_disponibilidad("S01", fecha, "9:00", 1)
    con_cero = servicio.consultar_disponibilidad("S01", fecha, "09:00", 1)
    despues = _estado(base_temporal)
    _observar("F6-DIS-01", {"fecha": fecha, "horas": ["9:00", "09:00"], "duracion": 1},
              {"disponible_ambas": True, "sin_cambios": True},
              {"sin_cero": sin_cero, "con_cero": con_cero, "sin_cambios": antes == despues})
    assert sin_cero["disponible"] is True
    assert sin_cero == con_cero
    assert despues == antes


def test_f6_dis_02_hora_sin_cero_pasada_de_hoy_se_rechaza(base_temporal, monkeypatch):
    class RelojFijo(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 2, 11, 15, tzinfo=tz)

    monkeypatch.setattr(servicio, "datetime", RelojFijo)
    antes = _estado(base_temporal)
    resultado = servicio.consultar_disponibilidad("S01", "2026-11-02", "9:00", 1)
    despues = _estado(base_temporal)
    _observar("F6-DIS-02", {"fecha": "2026-11-02", "hora": "9:00", "reloj_modulo": "11:15"},
              {"disponible": False, "motivo": "horario ya transcurrido", "sin_cambios": True},
              {"respuesta": resultado, "sin_cambios": antes == despues})
    assert resultado["disponible"] is False
    assert "transcurrió" in resultado["motivo"].lower()
    assert despues == antes
