import pytest

# --- AMPLIACIÓN DE PRUEBAS FASE 5 ---

def test_cp_res_24_rechazar_fecha_inexistente(sistema_reservaciones):
    """
    Verifica que el sistema maneje correctamente fechas calendario irreales sin colapsar (RNF-05).
    Se envía un 30 de febrero.
    """
    datos = {
        "carne": "A001234567",
        "codigo_sala": "S01",
        "fecha": "2026-02-30", # Fecha irreal
        "hora_inicio": "10:00",
        "duracion": 1,
        "cantidad_personas": 2
    }
    
    # Act & Assert: El sistema debe rechazarlo con un mensaje, NO lanzar ValueError no controlado
    resultado, mensaje = sistema_reservaciones.crear_reservacion(**datos)
    assert resultado is False, "La reservación no debió crearse con una fecha inexistente."
    assert "fecha" in mensaje.lower() or "formato" in mensaje.lower(), "Debe devolver un mensaje de error validando la fecha."


def test_cp_res_27_modificar_sala_reevalua_capacidad(sistema_reservaciones):
    """
    Verifica que al modificar una reservación a una sala más pequeña, 
    se re-evalue la capacidad máxima (RF-13, RN-07).
    """
    # 1. Crear reserva original: Sala S02 (Cap. 6) para 4 personas.
    exito, msg_creacion = sistema_reservaciones.crear_reservacion("A001234567", "S02", "2026-11-20", "10:00", 1, 4)
    assert exito is True
    id_reserva = msg_creacion.split(" ")[-1] # Asumiendo que devuelve el ID al final
    
    # 2. Modificar reserva: Cambiar a Sala S05 (Cap. 1). Mantener 4 personas.
    exito_mod, msg_mod = sistema_reservaciones.modificar_reservacion(id_reserva, codigo_sala="S05")
    
    # 3. Assert: Debe rechazar porque 4 personas no caben en la S05.
    assert exito_mod is False, "Permitió cambiar a una sala donde no caben las personas registradas."
    assert "capacidad" in msg_mod.lower(), "El mensaje de error debe indicar el problema de capacidad."