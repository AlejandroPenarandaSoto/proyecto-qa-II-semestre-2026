from unittest.mock import Mock

from src.view.tema import (
    RUTA_ISOTIPO_CABECERA,
    RUTA_LOGO_COMPLETO,
    configurar_tipografia_global,
    obtener_fuente_interfaz,
)


def test_recursos_de_identidad_visual_estan_disponibles():
    assert RUTA_ISOTIPO_CABECERA.is_file()
    assert RUTA_LOGO_COMPLETO.is_file()


def test_fuente_interfaz_elige_primera_geometrica_disponible(monkeypatch):
    monkeypatch.setattr(
        "src.view.tema.tkfont.families",
        lambda _master: ("Helvetica Neue", "Segoe UI", "Roboto"),
    )

    assert obtener_fuente_interfaz(object()) == "Segoe UI"


def test_tipografia_global_actualiza_fuentes_nativas(monkeypatch):
    fuente = Mock()
    obtener_fuente = Mock(return_value=fuente)
    monkeypatch.setattr("src.view.tema.tkfont.nametofont", obtener_fuente)

    configurar_tipografia_global(object(), "Segoe UI")

    assert obtener_fuente.call_count == 8
    assert fuente.configure.call_count == 8
    fuente.configure.assert_called_with(family="Segoe UI")
