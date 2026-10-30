"""RF-08: fechas, límites, superposición e integridad, sin abrir la GUI."""

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
    configurar_ruta_base_datos(tmp_path / "disponibilidad.db")
    try:
        inicializacion = inicializar_base_datos()
        assert inicializacion.exito, inicializacion.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)


def _estado(conexion):
    return {
        tabla: [dict(fila) for fila in conexion.execute(f"SELECT * FROM {tabla} ORDER BY id")]
        for tabla in ("estudiantes", "salas", "reservaciones", "auditoria")
    }


def _reservar(conexion, fecha, hora="10:00", duracion=2):
    """Datos de preparación directos para aislar la consulta de disponibilidad."""
    conexion.execute(
        "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?, ?, ?, ?)",
        ("C123456789", "Ana Rodríguez", "ana@tec.ac.cr", "activo"),
    )
    estudiante_id = conexion.execute("SELECT id FROM estudiantes WHERE carne = ?", ("C123456789",)).fetchone()[0]
    sala_id = conexion.execute("SELECT id FROM salas WHERE codigo = ?", ("S01",)).fetchone()[0]
    conexion.execute(
        """INSERT INTO reservaciones
        (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, cantidad_personas, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (estudiante_id, sala_id, fecha, hora, duracion, 2, "activa"),
    )
    conexion.commit()


def _consultar(conexion, caso, fecha, hora, duracion, esperado, reloj=None):
    antes = _estado(conexion)
    resultado = servicio.consultar_disponibilidad("S01", fecha, hora, duracion)
    despues = _estado(conexion)
    observacion = {
        "caso": caso,
        "requisito": "RF-08; RN-09; RNF-06" if caso.startswith("F5-") else "RF-08",
        "datos": {"sala": "S01", "fecha": fecha, "hora": hora, "duracion": duracion,
                  "reloj_simulado_del_modulo": reloj},
        "esperado": esperado,
        "obtenido": {"respuesta": resultado, "estado_antes": antes, "estado_despues": despues,
                     "sin_cambios": antes == despues},
    }
    print("OBSERVACION_CP " + json.dumps(observacion, ensure_ascii=False, sort_keys=True))
    assert antes == despues, "Una consulta no debe escribir estudiantes, salas, reservas ni auditoría."
    return resultado


def _manana():
    return (date.today() + timedelta(days=1)).isoformat()


def test_cp_dis_01_consulta_horario_libre(base_temporal):
    resultado = _consultar(base_temporal, "CP-DIS-01", _manana(), "10:00", 1, "Disponible en horario libre.")
    assert resultado["disponible"] is True, resultado


def test_cp_dis_03_rechaza_fecha_pasada(base_temporal):
    resultado = _consultar(base_temporal, "CP-DIS-03", "2020-01-01", "10:00", 1, "Rechazar fecha pasada.")
    assert resultado["disponible"] is False
    assert "anterior" in resultado["motivo"].lower()


def test_cp_dis_04_rechaza_hora_pasada_de_hoy(base_temporal, monkeypatch):
    class RelojFijo(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 30, 14, 25, tzinfo=tz)

    monkeypatch.setattr(servicio, "datetime", RelojFijo)
    resultado = _consultar(
        base_temporal, "CP-DIS-04", "2026-10-30", "14:00", 1,
        "Rechazar las 14:00 cuando el reloj del módulo marca hoy a las 14:25.",
        reloj="2026-10-30 14:25:00",
    )
    assert resultado["disponible"] is False
    assert "transcurrió" in resultado["motivo"].lower()


@pytest.mark.parametrize("hora,duracion", [("07:00", 1), ("20:00", 1), ("19:00", 2)])
def test_cp_dis_06_rechaza_horarios_fuera_de_jornada(base_temporal, hora, duracion):
    resultado = _consultar(
        base_temporal, "CP-DIS-06", _manana(), hora, duracion,
        "Rechazar horarios que salen de la jornada 08:00–20:00.",
    )
    assert resultado["disponible"] is False
    assert "08:00 a 20:00" in resultado["motivo"]


def test_cp_dis_07_rechaza_tres_horas(base_temporal):
    resultado = _consultar(base_temporal, "CP-DIS-07", _manana(), "10:00", 3, "Rechazar duración de tres horas.")
    assert resultado["disponible"] is False
    assert "1 o 2 horas" in resultado["motivo"]


def _conflicto(conexion, caso, hora, duracion, duracion_existente=2):
    fecha = _manana()
    _reservar(conexion, fecha, duracion=duracion_existente)
    resultado = _consultar(
        conexion, caso, fecha, hora, duracion,
        "No disponible por superposición con la reservación activa preparada.",
    )
    assert resultado["disponible"] is False
    assert "conflicto" in resultado["motivo"].lower()


def test_cp_dis_08_rechaza_superposicion_total(base_temporal):
    _conflicto(base_temporal, "CP-DIS-08", "10:00", 2)


def test_cp_dis_09_rechaza_superposicion_inicial(base_temporal):
    _conflicto(base_temporal, "CP-DIS-09", "09:00", 2)


def test_cp_dis_10_rechaza_superposicion_final(base_temporal):
    _conflicto(base_temporal, "CP-DIS-10", "11:00", 2)


def test_cp_dis_11_rechaza_superposicion_envolvente(base_temporal):
    _conflicto(base_temporal, "CP-DIS-11", "10:00", 2, duracion_existente=1)


@pytest.mark.parametrize("hora,duracion", [("12:00", 1), ("08:00", 2)])
def test_cp_dis_12_permite_horarios_consecutivos(base_temporal, hora, duracion):
    fecha = _manana()
    _reservar(base_temporal, fecha)
    resultado = _consultar(
        base_temporal, "CP-DIS-12", fecha, hora, duracion,
        "Disponible al terminar exactamente donde empieza otra reserva o iniciar donde termina.",
    )
    assert resultado["disponible"] is True, resultado


def test_cp_dis_13_consulta_no_persiste_cambios(base_temporal):
    fecha = _manana()
    _reservar(base_temporal, fecha)
    resultado = _consultar(
        base_temporal, "CP-DIS-13", fecha, "14:00", 1,
        "Disponible sin crear, modificar ni eliminar ningún registro.",
    )
    assert resultado["disponible"] is True, resultado


def test_f5_dis_01_hora_sin_cero_no_ignora_conflicto(base_temporal):
    """Caso nuevo de robustez: rechazar 9:00 o detectar el conflicto de 09:00."""
    fecha = _manana()
    _reservar(base_temporal, fecha, hora="08:00", duracion=2)
    resultado = _consultar(
        base_temporal, "F5-DIS-01", fecha, "9:00", 1,
        "No disponible: rechazar el formato o reconocer el traslape 09:00–10:00 con 08:00–10:00.",
    )
    assert resultado["disponible"] is False, (
        "La consulta con 9:00 no puede declarar libre una sala ocupada entre 08:00 y 10:00."
    )
