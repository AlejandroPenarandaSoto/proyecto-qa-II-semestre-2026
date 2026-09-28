import pytest
from datetime import datetime, timedelta
from src.model.salas.servicio import (
    consultar_salas, registrar_sala, modificar_sala, consultar_disponibilidad
)
from src.db.conexion import configurar_ruta_base_datos, obtener_conexion
from src.db.inicializador import inicializar_base_datos

@pytest.fixture(autouse=True)
def setup_bd():
    configurar_ruta_base_datos(":memory:")
    inicializar_base_datos()
    yield
    obtener_conexion().close()

def test_rf04_consultar_salas_iniciales():
    salas = consultar_salas()
    assert len(salas) == 5
    assert salas[0]['codigo'] == 'S01'

def test_rf12_registrar_sala_capacidad_invalida():
    resultado = registrar_sala("S06", "Sala Nueva", 0)
    assert resultado["exito"] is False
    assert "entero mayor que cero" in resultado["mensaje"]

def test_rf12_registrar_sala_codigo_duplicado():
    resultado = registrar_sala("S01", "Duplicada", 5)
    assert resultado["exito"] is False
    assert "ya se encuentra registrado" in resultado["mensaje"]

def test_rf08_disponibilidad_hora_incompleta():
    manana = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    resultado = consultar_disponibilidad("S01", manana, "09:30", 1)
    assert resultado["disponible"] is False
    assert "hora completa" in resultado["motivo"]

def test_rf08_disponibilidad_fuera_de_horario():
    manana = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    resultado = consultar_disponibilidad("S01", manana, "19:00", 2)
    assert resultado["disponible"] is False
    assert "08:00 a 20:00" in resultado["motivo"]

def test_rf08_disponibilidad_sala_fuera_servicio():
    manana = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    resultado = consultar_disponibilidad("S04", manana, "10:00", 1)
    assert resultado["disponible"] is False
    assert "fuera de servicio" in resultado["motivo"]