import sqlite3
from datetime import datetime, timedelta

from src.db.conexion import obtener_conexion
from src.model.auditoria.servicio import registrar_evento


def consultar_salas() -> list:
    """RF-04: Retorna todas las salas ordenadas por código."""
    conexion = obtener_conexion()
    cursor = conexion.execute("SELECT codigo, nombre, capacidad, estado FROM salas ORDER BY codigo ASC")
    return [dict(row) for row in cursor.fetchall()]

def registrar_sala(codigo: str, nombre: str, capacidad: int, estado: str = 'disponible') -> dict:
    """RF-12: Registra una nueva sala validando capacidad y unicidad."""
    if not isinstance(capacidad, int) or capacidad <= 0:
        return {"exito": False, "mensaje": "La capacidad debe ser un entero mayor que cero."}
    
    if estado not in ('disponible', 'fuera_de_servicio'):
        return {"exito": False, "mensaje": "Estado de sala inválido."}

    conexion = obtener_conexion()
    try:
        conexion.execute(
            "INSERT INTO salas (codigo, nombre, capacidad, estado) VALUES (?, ?, ?, ?)",
            (codigo, nombre, capacidad, estado)
        )

        resultado_auditoria = registrar_evento(
            accion="creacion",
            entidad="sala",
            entidad_id=codigo,
            detalle=f"Sala {codigo} registrada correctamente.",
            conexion=conexion,
        )

        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {"exito": False, "mensaje": "No fue posible registrar la sala."}

        conexion.commit()
        return {"exito": True, "mensaje": f"Sala {codigo} registrada exitosamente."}
    except sqlite3.IntegrityError:
        conexion.rollback()
        return {"exito": False, "mensaje": "El código de sala ya se encuentra registrado."}
    except sqlite3.Error:
        conexion.rollback()
        return {"exito": False, "mensaje": "No fue posible registrar la sala."}


def modificar_sala(codigo: str, nuevo_nombre: str, nueva_capacidad: int, nuevo_estado: str) -> dict:
    """RF-12: Modifica una sala validando que la capacidad soporte reservas futuras."""
    if not isinstance(nueva_capacidad, int) or nueva_capacidad <= 0:
        return {"exito": False, "mensaje": "La capacidad debe ser un entero mayor que cero."}

    if nuevo_estado not in ('disponible', 'fuera_de_servicio'):
        return {"exito": False, "mensaje": "Estado de sala inválido."}

    conexion = obtener_conexion()
    try:
        sala = conexion.execute(
            "SELECT id FROM salas WHERE codigo = ?",
            (codigo,),
        ).fetchone()
        if not sala:
            return {"exito": False, "mensaje": "La sala especificada no existe."}

        sala_id = sala['id']
        ahora = datetime.now()
        fecha_actual = ahora.strftime('%Y-%m-%d')
        hora_actual = ahora.strftime('%H:%M')

        cursor = conexion.execute(
            '''
            SELECT MAX(cantidad_personas) as max_personas
            FROM reservaciones
            WHERE sala_id = ? AND estado = 'activa'
              AND (fecha > ? OR (fecha = ? AND hora_inicio > ?))
            ''',
            (sala_id, fecha_actual, fecha_actual, hora_actual),
        )
        resultado = cursor.fetchone()

        max_personas_futuras = (
            resultado['max_personas']
            if resultado['max_personas'] is not None
            else 0
        )

        if nueva_capacidad < max_personas_futuras:
            return {
                "exito": False,
                "mensaje": (
                    f"No se puede reducir la capacidad a {nueva_capacidad}. "
                    "Hay reservas futuras activas para "
                    f"{max_personas_futuras} personas."
                ),
            }

        conexion.execute(
            "UPDATE salas SET nombre = ?, capacidad = ?, estado = ? WHERE codigo = ?",
            (nuevo_nombre, nueva_capacidad, nuevo_estado, codigo),
        )

        resultado_auditoria = registrar_evento(
            accion="modificacion",
            entidad="sala",
            entidad_id=codigo,
            detalle=f"Sala {codigo} modificada correctamente.",
            conexion=conexion,
        )

        if not resultado_auditoria["exito"]:
            conexion.rollback()
            return {"exito": False, "mensaje": "No fue posible modificar la sala."}

        conexion.commit()
        return {"exito": True, "mensaje": "Sala modificada correctamente."}
    except sqlite3.Error:
        conexion.rollback()
        return {"exito": False, "mensaje": "No fue posible modificar la sala."}


def consultar_disponibilidad(codigo_sala: str, fecha: str, hora_inicio: str, duracion: int) -> dict:
    """RF-08: Evalúa la disponibilidad aplicando reglas de horario y superposición."""
    conexion = obtener_conexion()
    sala = conexion.execute("SELECT id, estado FROM salas WHERE codigo = ?", (codigo_sala,)).fetchone()
    
    if not sala:
        return {"disponible": False, "motivo": "La sala especificada no existe."}
        
    if sala['estado'] == 'fuera_de_servicio':
        return {"disponible": False, "motivo": "La sala se encuentra fuera de servicio."}
        
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        hora_dt = datetime.strptime(hora_inicio, '%H:%M')
    except ValueError:
        return {"disponible": False, "motivo": "Formato de fecha (AAAA-MM-DD) u hora (HH:MM) inválido."}
        
    if duracion not in (1, 2):
        return {"disponible": False, "motivo": "La duración permitida es únicamente de 1 o 2 horas."}
        
    if hora_dt.minute != 0:
        return {"disponible": False, "motivo": "La hora debe comenzar exactamente en una hora completa (ej. 08:00)."}
        
    hora_fin_dt = hora_dt + timedelta(hours=duracion)
    
    hora_apertura = datetime.strptime('08:00', '%H:%M')
    hora_cierre = datetime.strptime('20:00', '%H:%M')
    if hora_dt < hora_apertura or hora_fin_dt > hora_cierre:
        return {"disponible": False, "motivo": "El horario permitido de uso es de 08:00 a 20:00."}
        
    ahora = datetime.now()
    fecha_actual_str = ahora.strftime('%Y-%m-%d')
    hora_actual_str = ahora.strftime('%H:%M')
    
    if fecha < fecha_actual_str:
        return {"disponible": False, "motivo": "La fecha no puede ser anterior a la fecha actual."}
        
    if fecha == fecha_actual_str and hora_inicio <= hora_actual_str:
        return {"disponible": False, "motivo": "El horario solicitado para hoy ya transcurrió."}
        
    hora_fin = hora_fin_dt.strftime('%H:%M')
    reservas_activas = conexion.execute('''
        SELECT hora_inicio, duracion_horas 
        FROM reservaciones 
        WHERE sala_id = ? AND fecha = ? AND estado = 'activa'
    ''', (sala['id'], fecha)).fetchall()
    
    for res in reservas_activas:
        res_inicio_dt = datetime.strptime(res['hora_inicio'], '%H:%M')
        res_fin_dt = res_inicio_dt + timedelta(hours=res['duracion_horas'])
        
        res_inicio = res_inicio_dt.strftime('%H:%M')
        res_fin = res_fin_dt.strftime('%H:%M')
        
        if hora_inicio < res_fin and hora_fin > res_inicio:
            return {"disponible": False, "motivo": f"Conflicto: la sala tiene una reservación activa de {res_inicio} a {res_fin}."}
            
    return {"disponible": True, "motivo": "La sala está disponible."}
