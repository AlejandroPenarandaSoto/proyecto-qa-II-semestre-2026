import csv
from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import registrar_estudiante
from src.model.reportes.servicio import ENCABEZADOS_REPORTE, generar_reporte_csv
from src.model.reservaciones.servicio import crear_reservacion


@pytest.fixture
def base_datos_reportes(tmp_path):
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "reportes.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje
    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
    )
    assert exito, mensaje

    try:
        yield tmp_path
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_original)


def _fecha_futura(dias):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _crear_reservacion(fecha, hora_inicio="10:00", duracion=1):
    resultado = crear_reservacion(
        carne="C123456789",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio=hora_inicio,
        duracion=duracion,
        cantidad_personas=2,
    )
    assert resultado["exito"] is True


def test_generar_reporte_csv_utf8_con_encabezados(base_datos_reportes):
    fecha = _fecha_futura(2)
    _crear_reservacion(fecha, duracion=2)
    destino = base_datos_reportes / "reporte.csv"

    resultado = generar_reporte_csv(fecha, fecha, destino)

    assert resultado["exito"] is True
    assert resultado["cantidad"] == 1
    with destino.open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        filas = list(lector)

    assert tuple(lector.fieldnames) == ENCABEZADOS_REPORTE
    assert filas == [
        {
            "estudiante": "Ana Rodríguez",
            "sala": "S01",
            "fecha": fecha,
            "horario": "10:00-12:00",
            "cantidad_personas": "2",
            "estado": "activa",
        }
    ]


def test_reporte_filtra_rango_inclusivo(base_datos_reportes):
    fecha_inicial = _fecha_futura(2)
    fecha_final = _fecha_futura(4)
    _crear_reservacion(fecha_inicial, "09:00")
    _crear_reservacion(fecha_final, "11:00")
    _crear_reservacion(_fecha_futura(6), "13:00")
    destino = base_datos_reportes / "rango.csv"

    resultado = generar_reporte_csv(fecha_inicial, fecha_final, destino)

    assert resultado["exito"] is True
    assert resultado["cantidad"] == 2
    with destino.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    assert [fila["fecha"] for fila in filas] == [fecha_inicial, fecha_final]


@pytest.mark.parametrize(
    "fecha_inicio, fecha_fin, texto_esperado",
    [
        ("", "2026-10-10", "inicial"),
        ("2026-10-10", "", "final"),
        ("10-10-2026", "2026-10-11", "formato"),
        ("2026-10-11", "2026-10-10", "anterior"),
    ],
)
def test_rechazar_rango_invalido(
    base_datos_reportes,
    fecha_inicio,
    fecha_fin,
    texto_esperado,
):
    destino = base_datos_reportes / "invalido.csv"

    resultado = generar_reporte_csv(fecha_inicio, fecha_fin, destino)

    assert resultado["exito"] is False
    assert texto_esperado in resultado["mensaje"].lower()
    assert not destino.exists()


def test_cancelar_destino_no_crea_archivos(base_datos_reportes):
    archivos_antes = set(base_datos_reportes.iterdir())

    resultado = generar_reporte_csv(
        _fecha_futura(1),
        _fecha_futura(2),
        None,
    )

    assert resultado["exito"] is False
    assert resultado["cancelado"] is True
    assert set(base_datos_reportes.iterdir()) == archivos_antes


def test_reporte_sin_datos_contiene_solo_encabezados(base_datos_reportes):
    destino = base_datos_reportes / "vacio.csv"

    resultado = generar_reporte_csv(
        _fecha_futura(20),
        _fecha_futura(21),
        destino,
    )

    assert resultado["exito"] is True
    assert resultado["cantidad"] == 0
    with destino.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.reader(archivo))
    assert filas == [list(ENCABEZADOS_REPORTE)]


def test_error_de_escritura_no_deja_archivo_temporal(base_datos_reportes):
    destino = base_datos_reportes / "inexistente" / "reporte.csv"

    resultado = generar_reporte_csv(
        _fecha_futura(1),
        _fecha_futura(2),
        destino,
    )

    assert resultado["exito"] is False
    assert not destino.exists()
    assert not list(base_datos_reportes.glob("*.tmp"))
