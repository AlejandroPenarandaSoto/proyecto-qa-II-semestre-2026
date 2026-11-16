from src.view.selector_fecha import construir_matriz_mes, sumar_meses


def test_calendario_inicia_en_lunes_y_mantiene_seis_filas():
    semanas = construir_matriz_mes(2026, 9)

    assert len(semanas) == 6
    assert all(len(semana) == 7 for semana in semanas)
    assert semanas[0] == [0, 1, 2, 3, 4, 5, 6]
    assert [dia for semana in semanas for dia in semana if dia] == list(
        range(1, 31)
    )


def test_navegacion_de_meses_cambia_de_anio_correctamente():
    assert sumar_meses(2026, 12, 1) == (2027, 1)
    assert sumar_meses(2026, 1, -1) == (2025, 12)
