"""Acceso a datos de las reservaciones: solo consultas SQL, sin reglas de negocio.

Todas las funciones reciben la conexión para que el servicio controle la
transacción (commit o rollback).
"""


def buscar_estudiante(conexion, carne):
    return conexion.execute(
        "SELECT id, estado FROM estudiantes WHERE UPPER(carne) = ?",
        (carne.upper(),),
    ).fetchone()


def buscar_sala(conexion, codigo_sala):
    return conexion.execute(
        "SELECT id, capacidad, estado FROM salas WHERE codigo = ? COLLATE NOCASE",
        (codigo_sala,),
    ).fetchone()


def obtener_reservacion(conexion, identificador):
    return conexion.execute(
        """
        SELECT
            r.id,
            e.carne,
            s.codigo AS codigo_sala,
            r.fecha,
            r.hora_inicio,
            r.duracion_horas,
            r.cantidad_personas,
            r.estado,
            r.serie_id
        FROM reservaciones AS r
        JOIN estudiantes AS e ON r.estudiante_id = e.id
        JOIN salas AS s ON r.sala_id = s.id
        WHERE r.id = ?
        """,
        (identificador,),
    ).fetchone()


def listar_reservaciones(conexion):
    return conexion.execute(
        """
        SELECT
            r.id,
            e.carne,
            e.nombre_completo AS estudiante,
            s.codigo AS sala,
            s.nombre AS nombre_sala,
            r.fecha,
            r.hora_inicio,
            r.duracion_horas,
            r.cantidad_personas,
            r.estado,
            r.serie_id
        FROM reservaciones AS r
        JOIN estudiantes AS e ON r.estudiante_id = e.id
        JOIN salas AS s ON r.sala_id = s.id
        ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC
        """
    ).fetchall()


def horarios_activos_de_sala(conexion, sala_id, fecha, excluir_id=None):
    """Franjas activas de la sala en la fecha; ``excluir_id`` omite una reservación."""
    return conexion.execute(
        """
        SELECT hora_inicio, duracion_horas
        FROM reservaciones
        WHERE sala_id = ? AND fecha = ? AND estado = 'activa' AND id IS NOT ?
        """,
        (sala_id, fecha, excluir_id),
    ).fetchall()


def reservaciones_activas_de_estudiante(conexion, estudiante_id):
    return conexion.execute(
        """
        SELECT id, fecha, hora_inicio, duracion_horas, serie_id
        FROM reservaciones
        WHERE estudiante_id = ? AND estado = 'activa'
        """,
        (estudiante_id,),
    ).fetchall()


def ids_activos_de_serie_desde(conexion, serie_id, fecha):
    filas = conexion.execute(
        """
        SELECT id
        FROM reservaciones
        WHERE serie_id = ? AND fecha >= ? AND estado = 'activa'
        ORDER BY fecha ASC, id ASC
        """,
        (serie_id, fecha),
    ).fetchall()
    return [fila["id"] for fila in filas]


def series_registradas(conexion):
    filas = conexion.execute(
        "SELECT DISTINCT serie_id FROM reservaciones WHERE serie_id IS NOT NULL"
    ).fetchall()
    return [fila["serie_id"] for fila in filas]


def insertar_reservacion(conexion, datos, serie_id=None):
    """Guarda una reservación activa y devuelve su identificador interno."""
    cursor = conexion.execute(
        """
        INSERT INTO reservaciones (
            estudiante_id, sala_id, fecha, hora_inicio,
            duracion_horas, cantidad_personas, estado, serie_id
        )
        VALUES (?, ?, ?, ?, ?, ?, 'activa', ?)
        """,
        (
            datos["estudiante_id"],
            datos["sala_id"],
            datos["fecha"],
            datos["hora_inicio"],
            datos["duracion"],
            datos["cantidad_personas"],
            serie_id,
        ),
    )
    return cursor.lastrowid


def actualizar_reservacion(conexion, identificador, datos):
    conexion.execute(
        """
        UPDATE reservaciones
        SET sala_id = ?, fecha = ?, hora_inicio = ?,
            duracion_horas = ?, cantidad_personas = ?
        WHERE id = ?
        """,
        (
            datos["sala_id"],
            datos["fecha"],
            datos["hora_inicio"],
            datos["duracion"],
            datos["cantidad_personas"],
            identificador,
        ),
    )


def cancelar_reservaciones(conexion, identificadores):
    marcadores = ", ".join("?" for _ in identificadores)
    conexion.execute(
        f"UPDATE reservaciones SET estado = 'cancelada' WHERE id IN ({marcadores})",
        list(identificadores),
    )
