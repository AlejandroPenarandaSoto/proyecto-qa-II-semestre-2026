import sqlite3

from src.db.conexion import obtener_conexion
from src.model.estudiantes.validaciones import(
    validar_carne,
    validar_correo,
    validar_estado,
    validar_nombre,
)

def registrar_estudiante(carne, nombre, correo):
    """Valida y registra un estudiante."""

    valido, carne = validar_carne(carne)
    if not valido:
        return False, carne

    valido, nombre = validar_nombre(nombre)
    if not valido:
        return False, nombre

    valido, correo = validar_correo(correo)
    if not valido:
        return False, correo

    conexion = obtener_conexion()

    try:
        existente = conexion.execute(
            """
            SELECT id
            FROM estudiantes
            WHERE UPPER(carne) = ?
            """,
            (carne,)
        ).fetchone() #toma una sola fila del resultado de una consulta a la base de datos, si no hay ninguna fila disponible, devuelve None

        if existente:
            return False, "Ya existe un estudiante con ese carné."

        conexion.execute(
            """
            INSERT INTO estudiantes
                (carne, nombre_completo, correo, estado)
            VALUES (?, ?, ?, ?)
            """,
            (carne, nombre, correo, "activo")
        )

        conexion.commit()
        return True, "Estudiante registrado correctamente."

    except sqlite3.Error:
        conexion.rollback()
        return False, "No fue posible registrar al estudiante."


def consultar_estudiantes():
    """Consulta todos los estudiantes registrados."""

    conexion = obtener_conexion()

    try:
        estudiantes = conexion.execute(
            """
            SELECT carne, nombre_completo, correo, estado
            FROM estudiantes
            ORDER BY nombre_completo ASC
            """
        ).fetchall() #Obtiene todas las filas que quedan del resultado de una consulta y las devuelve en una lista.

        if not estudiantes:
            return True, "No hay estudiantes registrados.", []

        return True, "Consulta realizada correctamente.", [
            dict(estudiante) for estudiante in estudiantes
        ]

    except sqlite3.Error:
        return False, "No fue posible consultar los estudiantes.", []

def buscar_reservaciones_estudiante(carne):
    """Busca las reservaciones asociadas al carne de un estudiante."""

    carne = carne.strip().upper()

    if not carne:
        return False, "Debes ingresar un carne", []

    conexion = obtener_conexion()

    try:
        estudiante = conexion.execute(
            """
            SELECT id, nombre_completo
            FROM estudiantes
            WHERE UPPER(carne) = ?
            """,
            (carne,)
        ).fetchone()

        if estudiante is None:
            return False, "No existe un estudiante con ese carné.", []
        
        reservaciones = conexion.execute(
            """
            SELECT
                r.id,
                s.codigo AS sala,
                r. fecha,
                r.hora_inicio,
                r.duracion_horas,
                r.cantidad_personas,
                r.estado
            FROM reservaciones AS r
            JOIN salas AS s ON r.sala_id = s.id
            WHERE r.estudiante_id = ?
            ORDER BY r.fecha, r.hora_inicio
            """,
            (estudiante["id"],)
        ).fetchall()

        if not reservaciones:
            return True, "El estudiante no tiene reservaciones registradas.", []

        return True, "Reservaciones encontradas.", [
            dict(reservacion) for reservacion in reservaciones
        ]

    except sqlite3.Error:
        return False, "No fue posible consultar las reservaciones.", []



def modificar_estudiante(carne, nombre, correo, estado):
    """Modifica los datos y el estado de un estudiante."""

    valido, carne = validar_carne(carne)
    if not valido:
        return False, carne

    valido, nombre = validar_nombre(nombre)
    if not valido:
        return False, nombre

    valido, correo = validar_correo(correo)
    if not valido:
        return False, correo

    valido, estado = validar_estado(estado)
    if not valido:
        return False, estado

    conexion = obtener_conexion()

    try:
        estudiante = conexion.execute(
            """
            SELECT id
            FROM estudiantes
            WHERE UPPER(carne) = ?
            """,
            (carne,)
        ).fetchone()

        if estudiante is None:
            return False, "No existe un estudiante con ese carné."

        conexion.execute(
            """
            UPDATE estudiantes
            SET nombre_completo = ?,
                correo = ?,
                estado = ?
            WHERE id = ?
            """,
            (nombre, correo, estado, estudiante["id"])
        )

        conexion.commit()
        return True, "Estudiante modificado correctamente."

    except sqlite3.Error:
        conexion.rollback()
        return False, "No fue posible modificar al estudiante."
