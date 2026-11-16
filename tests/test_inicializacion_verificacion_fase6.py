"""Robustez y recuperación de inicialización tras BUG-INI-02, sin GUI."""

from dataclasses import asdict
import errno
import json
from unittest.mock import Mock

import pytest

from src.db import conexion as conexion_bd
from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos


@pytest.fixture
def ruta_temporal(tmp_path):
    """Configura únicamente rutas temporales y restaura la ruta anterior."""
    anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    try:
        ruta = tmp_path / "reservas_verificacion.db"
        configurar_ruta_base_datos(ruta)
        yield ruta
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)


def _observar(variante, datos, esperado, obtenido):
    observacion = {
        "caso": "BUG-INI-02",
        "requisito": "RF-01; RNF-05",
        "datos": {"variante": variante, **datos},
        "esperado": esperado,
        "obtenido": obtenido,
    }
    print("OBSERVACION_CP " + json.dumps(
        observacion, ensure_ascii=False, sort_keys=True,
    ))


def test_f6_ini02_permission_error_al_consultar_existencia_se_informa(
    ruta_temporal, monkeypatch,
):
    """Un PermissionError en la comprobación previa no escapa al llamador."""
    comprobar_existencia = Mock(side_effect=PermissionError(
        errno.EACCES,
        "Permiso denegado simulado al comprobar la existencia de la base",
        str(ruta_temporal),
    ))
    with monkeypatch.context() as parche:
        parche.setattr(conexion_bd, "la_base_datos_existe", comprobar_existencia)
        resultado = inicializar_base_datos()

    archivo_creado = ruta_temporal.exists()
    _observar(
        "permiso_denegado_en_comprobacion_previa",
        {"ruta_temporal": str(ruta_temporal),
         "excepcion_simulada": "PermissionError",
         "punto_de_inyeccion": "conexion_bd.la_base_datos_existe"},
        {"exito": False, "base_datos_creada": False,
         "salas_insertadas": 0, "mensaje_informativo": True,
         "archivo_creado": False},
        {"resultado": asdict(resultado), "archivo_creado": archivo_creado,
         "llamadas_comprobacion": comprobar_existencia.call_count},
    )
    comprobar_existencia.assert_called_once_with()
    assert resultado.exito is False
    assert resultado.base_datos_creada is False
    assert resultado.salas_insertadas == 0
    assert resultado.mensaje.startswith("No fue posible inicializar la base de datos:")
    assert archivo_creado is False


def test_f6_ini02_recupera_ruta_valida_despues_de_not_a_directory_error(
    ruta_temporal,
):
    """Un obstáculo real de archivos no impide un siguiente inicio válido."""
    obstaculo = ruta_temporal.parent / "es_un_archivo"
    contenido_original = "Archivo de prueba que no debe modificarse."
    obstaculo.write_text(contenido_original, encoding="utf-8")
    ruta_imposible = obstaculo / "subcarpeta" / "reservas.db"
    configurar_ruta_base_datos(ruta_imposible)

    resultado_error = inicializar_base_datos()
    contenido_despues = obstaculo.read_text(encoding="utf-8")

    cerrar_conexion()
    ruta_valida = ruta_temporal.parent / "recuperada" / "reservas.db"
    configurar_ruta_base_datos(ruta_valida)
    resultado_recuperacion = inicializar_base_datos()
    codigos = [fila["codigo"] for fila in obtener_conexion().execute(
        "SELECT codigo FROM salas ORDER BY codigo"
    ).fetchall()]
    archivo_valido_creado = ruta_valida.is_file()

    _observar(
        "recuperacion_despues_de_ruta_bajo_un_archivo",
        {"ruta_imposible": str(ruta_imposible), "ruta_valida": str(ruta_valida),
         "obstaculo_real": "archivo regular usado como directorio"},
        {"primer_inicio_exito": False, "obstaculo_sin_cambios": True,
         "segundo_inicio_exito": True, "base_datos_creada": True,
         "codigos_salas": ["S01", "S02", "S03", "S04", "S05"]},
        {"primer_resultado": asdict(resultado_error),
         "segundo_resultado": asdict(resultado_recuperacion),
         "obstaculo_sin_cambios": contenido_despues == contenido_original,
         "archivo_valido_creado": archivo_valido_creado,
         "codigos_salas": codigos},
    )
    assert resultado_error.exito is False
    assert resultado_error.base_datos_creada is False
    assert resultado_error.salas_insertadas == 0
    assert resultado_error.mensaje.startswith("No fue posible inicializar la base de datos:")
    assert contenido_despues == contenido_original
    assert resultado_recuperacion.exito is True
    assert resultado_recuperacion.base_datos_creada is True
    assert resultado_recuperacion.salas_insertadas == 5
    assert archivo_valido_creado is True
    assert codigos == ["S01", "S02", "S03", "S04", "S05"]
