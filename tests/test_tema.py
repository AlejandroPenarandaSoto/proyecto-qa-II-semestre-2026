from src.view.tema import RUTA_ISOTIPO_CABECERA, RUTA_LOGO_COMPLETO


def test_recursos_de_identidad_visual_estan_disponibles():
    assert RUTA_ISOTIPO_CABECERA.is_file()
    assert RUTA_LOGO_COMPLETO.is_file()
