import pytest

# --- AMPLIACIÓN DE PRUEBAS FASE 5 ---

def test_cp_rec_14_modificar_ocurrencia_independiente(sistema_reservaciones):
    """
    Verifica que al modificar una ocurrencia recurrente individual (RF-13),
    esta no pierda su identificador de serie original (RF-14).
    """
    # 1. Crear serie de 3 semanas
    exito, ids_ocurrencias, id_serie = sistema_reservaciones.crear_serie_recurrente("A001234567", "S01", "2026-11-01", "10:00", 1, 2, semanas=3)
    assert exito is True
    id_modificar = ids_ocurrencias[1] # Segunda ocurrencia
    
    # 2. Modificar la hora de la segunda ocurrencia a las 14:00
    exito_mod = sistema_reservaciones.modificar_reservacion(id_modificar, hora_inicio="14:00")
    assert exito_mod is True
    
    # 3. Assert: Verificar en BD que id_serie siga siendo el original, no None.
    reserva_modificada = sistema_reservaciones.consultar_reserva_por_id(id_modificar)
    assert reserva_modificada.id_serie == id_serie, "La modificación corrompió el ID de serie (BUG-REC-01)."


def test_cp_pan_12_panel_actualiza_tras_cancelacion_recurrente(sistema_reservaciones, panel_controlador):
    """
    Verifica que el panel principal recargue los datos cuando se cancela una serie en cascada (RF-15).
    """
    # 1. Crear serie y validar que el panel dice "ocupado" para S03
    sistema_reservaciones.crear_serie_recurrente("B009876543", "S03", "2026-11-10", "15:00", 2, 5, semanas=2)
    ocupacion_antes = panel_controlador.obtener_proximos_compromisos()
    assert "S03" in [res["sala"] for res in ocupacion_antes]
    
    # 2. Cancelar toda la serie desde la ocurrencia inicial
    todas_las_reservas = panel_controlador.obtener_reservas_estudiante("B009876543")
    id_base = todas_las_reservas[0]["id"]
    sistema_reservaciones.cancelar_ocurrencias_futuras(id_base)
    
    # 3. Assert: Consultar panel nuevamente. NO debe estar S03 ocupada.
    ocupacion_despues = panel_controlador.obtener_proximos_compromisos()
    assert "S03" not in [res["sala"] for res in ocupacion_despues], "El caché del panel no se limpió (BUG-PAN-01)."