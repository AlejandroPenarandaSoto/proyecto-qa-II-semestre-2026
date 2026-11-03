"""Verificaciones propias derivadas de BUG-P5-REP-01, Fase 5, páginas 16–17.

No son las pruebas originales de su autora. Se reproduce el fallo de filas
y se añade la variante de encabezados; el reemplazo es un control que debe
conservarse correcto antes y después de cualquier corrección productiva.
Los errores se inyectan solo durante la llamada y no se utiliza una GUI.
"""

import json
from datetime import date, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import registrar_estudiante
from src.model.reportes import servicio
from src.model.reservaciones.servicio import crear_reservacion


@pytest.fixture
def escenario_reporte(tmp_path):
    """Prepara los datos del reporte en SQLite y una carpeta exportación propia."""
    ruta_anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    try:
        configurar_ruta_base_datos(tmp_path / "reportes_verificacion.db")
        inicializacion = inicializar_base_datos()
        assert inicializacion.exito, inicializacion.mensaje
        exito, mensaje = registrar_estudiante(
            "C123456789", "Ana Rodríguez", "ana@tec.ac.cr"
        )
        assert exito, mensaje
        fecha = (date.today() + timedelta(days=2)).isoformat()
        reservacion = crear_reservacion(
            "C123456789", "S01", fecha, "10:00", 2, 2
        )
        assert reservacion["exito"] is True, reservacion
        carpeta = tmp_path / "exportacion"
        carpeta.mkdir()
        destino = carpeta / "reporte.csv"
        contenido_anterior = b"reporte_anterior\ncontenido_previo_intacto\n"
        destino.write_bytes(contenido_anterior)
        yield obtener_conexion(), fecha, destino, contenido_anterior
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_anterior)


def _estado_bd(conexion):
    tablas = ("estudiantes", "salas", "reservaciones", "auditoria")
    return {
        tabla: [dict(fila) for fila in conexion.execute(
            f"SELECT * FROM {tabla} ORDER BY id"
        )]
        for tabla in tablas
    }


def _archivos(carpeta):
    """iterdir incluye los temporales ocultos, a diferencia de una lista visual."""
    return sorted(ruta.name for ruta in carpeta.iterdir())


def _registrar_y_comprobar(
    escenario, variante, resultado, antes, archivos_antes, inyecciones
):
    conexion, fecha, destino, contenido_anterior = escenario
    despues = _estado_bd(conexion)
    archivos_despues = _archivos(destino.parent)
    contenido_despues = destino.read_bytes() if destino.is_file() else None
    temporales_despues = sorted(
        ruta.name for ruta in destino.parent.glob(f".{destino.name}.*.tmp")
    )
    observacion = {
        "caso": "BUG-P5-REP-01",
        "caso_plan": "CP-REP-12",
        "variante": variante,
        "origen": "Verificación independiente derivada del reporte PDF, no test original.",
        "datos": {
            "carne": "C123456789", "estudiante": "Ana Rodríguez",
            "sala": "S01", "fecha_inicio": fecha, "fecha_fin": fecha,
            "horario": "10:00-12:00", "personas": 2,
            "ruta_destino": str(destino),
        },
        "esperado": {
            "exito": False, "cancelado": False, "mensaje_de_error": True,
            "destino_anterior_intacto": True, "datos_y_auditoria_sin_cambios": True,
            "archivos_exportacion": archivos_antes, "temporales_residuales": [],
        },
        "obtenido": {
            "respuesta": resultado, "inyecciones": inyecciones,
            "archivos_antes": archivos_antes, "archivos_despues": archivos_despues,
            "temporales_residuales": temporales_despues,
            "contenido_destino_antes_hex": contenido_anterior.hex(),
            "contenido_destino_despues_hex": (
                None if contenido_despues is None else contenido_despues.hex()
            ),
            "destino_anterior_intacto": contenido_despues == contenido_anterior,
            "estado_bd_antes": antes, "estado_bd_despues": despues,
            "datos_y_auditoria_sin_cambios": antes == despues,
        },
    }
    print("OBSERVACION_CP " + json.dumps(
        observacion, ensure_ascii=False, sort_keys=True
    ))

    # La evidencia anterior se conserva aunque una aserción falle.
    assert len(inyecciones) == 1, "El error previsto debe haberse inyectado."
    assert inyecciones[0]["operacion"] == variante
    assert resultado["exito"] is False
    assert resultado["cancelado"] is False
    assert "no fue posible" in resultado["mensaje"].lower(), resultado
    assert despues == antes, "Exportar no debe modificar datos ni auditoría."
    assert contenido_despues == contenido_anterior, "Debe conservarse el CSV anterior."
    assert temporales_despues == [], "No deben quedar temporales ocultos incompletos."
    assert archivos_despues == archivos_antes


@pytest.mark.parametrize("operacion", ("writeheader", "writerows"))
def test_verificacion_bug_p5_rep_01_error_escritura_limpia_temporal(
    escenario_reporte, monkeypatch, operacion
):
    conexion, fecha, destino, _contenido = escenario_reporte
    antes = _estado_bd(conexion)
    archivos_antes = _archivos(destino.parent)
    inyecciones = []

    def fallar_escritura(_escritor, *_argumentos, **_opciones):
        inyecciones.append({
            "operacion": operacion,
            "archivos_al_inyectar": _archivos(destino.parent),
            "error": "OSError simulado durante escritura del CSV temporal.",
        })
        raise OSError(f"Fallo de prueba en {operacion}")

    with monkeypatch.context() as parche:
        parche.setattr(servicio.csv.DictWriter, operacion, fallar_escritura)
        resultado = servicio.generar_reporte_csv(fecha, fecha, destino)

    _registrar_y_comprobar(
        escenario_reporte, operacion, resultado, antes, archivos_antes, inyecciones
    )


def test_control_bug_p5_rep_01_error_reemplazo_limpia_temporal(
    escenario_reporte, monkeypatch
):
    conexion, fecha, destino, _contenido = escenario_reporte
    antes = _estado_bd(conexion)
    archivos_antes = _archivos(destino.parent)
    inyecciones = []

    def fallar_reemplazo(origen, destino_reemplazo):
        inyecciones.append({
            "operacion": "os.replace", "origen": str(origen),
            "destino": str(destino_reemplazo),
            "archivos_al_inyectar": _archivos(destino.parent),
            "error": "OSError simulado al reemplazar el CSV anterior.",
        })
        raise OSError("Fallo de prueba en os.replace")

    with monkeypatch.context() as parche:
        parche.setattr(servicio.os, "replace", fallar_reemplazo)
        resultado = servicio.generar_reporte_csv(fecha, fecha, destino)

    _registrar_y_comprobar(
        escenario_reporte, "os.replace", resultado, antes, archivos_antes, inyecciones
    )
