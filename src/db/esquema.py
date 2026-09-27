"""
Definición del esquema (DDL) de la base de datos.

Cada sentencia usa `CREATE TABLE IF NOT EXISTS`, por lo que aplicar el
esquema sobre una base de datos ya existente y válida es una operación
segura e idempotente: no duplica estructuras ni destruye información,
tal como lo exige RF-01.

Nota para el equipo: las tablas `estudiantes`, `salas` y `reservaciones`
reflejan el modelo de información de la sección 5 del enunciado. Cada
responsable de módulo (gestión de estudiantes, salas, reservaciones,
auditoría) debe construir su lógica de negocio sobre estas tablas; si se
requiere una columna adicional, se coordina con el resto del equipo y se
actualiza este archivo para mantener el esquema como fuente única de
verdad.
"""

ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS estudiantes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    carne           TEXT NOT NULL UNIQUE,
    nombre_completo TEXT NOT NULL,
    correo          TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'inactivo'))
);

CREATE TABLE IF NOT EXISTS salas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo    TEXT NOT NULL UNIQUE,
    nombre    TEXT NOT NULL,
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    estado    TEXT NOT NULL DEFAULT 'disponible'
        CHECK (estado IN ('disponible', 'fuera_de_servicio'))
);

CREATE TABLE IF NOT EXISTS reservaciones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id     INTEGER NOT NULL,
    sala_id           INTEGER NOT NULL,
    fecha             TEXT NOT NULL,
    hora_inicio       TEXT NOT NULL,
    duracion_horas    INTEGER NOT NULL CHECK (duracion_horas IN (1, 2)),
    cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas > 0),
    estado            TEXT NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'cancelada')),
    serie_id          TEXT,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
    FOREIGN KEY (sala_id) REFERENCES salas (id)
);

CREATE INDEX IF NOT EXISTS idx_reservaciones_sala_fecha
    ON reservaciones (sala_id, fecha);

CREATE INDEX IF NOT EXISTS idx_reservaciones_estudiante
    ON reservaciones (estudiante_id);

CREATE TABLE IF NOT EXISTS auditoria (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL,
    accion     TEXT NOT NULL,
    entidad    TEXT NOT NULL,
    entidad_id TEXT NOT NULL,
    detalle    TEXT
);
"""
