"""
Pruebas de inicialización, base de datos y persistencia.

Requisitos cubiertos: RF-01 (cargar datos), RF-10 (guardado antes de salir),
RNF-03 (portabilidad), RNF-05 (robustez), RNF-06 (integridad) y RNF-08
(codificación). Cada prueba usa un archivo SQLite temporal propio (tmp_path),
de modo que se verifica la persistencia real en disco y no solo en memoria.

Las pruebas marcadas con xfail(strict=True) documentan defectos encontrados
(ver motivo en cada marca). Cuando el defecto se corrija, la prueba pasará
"inesperadamente" y strict=True hará fallar la suite: ese es el aviso para
quitar la marca xfail.

Cada prueba lleva en su docstring el ID del caso (CP-INI, CP-BD o CP-PER) del plan de pruebas.

Ubicación sugerida en el repositorio: tests/test_inicializacion_persistencia.py
"""
import re
import sqlite3
from pathlib import Path

import pytest

from src.controller.controller import ControladorAplicacion
from src.db import conexion as conexion_bd
from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.db.semilla import SALAS_INICIALES
from src.model.salas.servicio import consultar_salas, registrar_sala


@pytest.fixture
def ruta_bd(tmp_path):
    """Base de datos en archivo temporal, aislada para cada prueba."""
    cerrar_conexion()
    ruta = tmp_path / "reservas_prueba.db"
    configurar_ruta_base_datos(ruta)
    yield ruta
    cerrar_conexion()
    configurar_ruta_base_datos(":memory:")


def _reabrir():
    """Cierra la conexión y la vuelve a abrir (simula cerrar y abrir la app)."""
    cerrar_conexion()
    return obtener_conexion()


# --------------------------------------------------------------------------
# RF-01 · Primera ejecución (la base de datos no existe)
# --------------------------------------------------------------------------

def test_rf01_crea_archivo_y_reporta_primera_ejecucion(ruta_bd):
    """CP-INI-01"""
    assert not ruta_bd.exists()

    resultado = inicializar_base_datos()

    assert resultado.exito is True
    assert resultado.base_datos_creada is True
    assert resultado.salas_insertadas == len(SALAS_INICIALES)
    assert ruta_bd.exists()


def test_rf01_crea_todas_las_tablas_e_indices(ruta_bd):
    """CP-INI-01"""
    inicializar_base_datos()
    conexion = obtener_conexion()

    tablas = {f[0] for f in conexion.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    indices = {f[0] for f in conexion.execute(
        "SELECT name FROM sqlite_master WHERE type='index'")}

    assert {"estudiantes", "salas", "reservaciones", "auditoria"} <= tablas
    assert {
        "idx_reservaciones_sala_fecha",
        "idx_reservaciones_estudiante",
        "idx_reservaciones_serie",
    } <= indices


def test_rf01_reservaciones_tiene_columnas_requeridas(ruta_bd):
    """CP-INI-01"""
    inicializar_base_datos()
    columnas = {f["name"] for f in obtener_conexion().execute(
        "PRAGMA table_info(reservaciones)")}

    assert {"id", "estudiante_id", "sala_id", "fecha", "hora_inicio",
            "duracion_horas", "cantidad_personas", "estado",
            "serie_id"} <= columnas


def test_rf01_salas_iniciales_con_valores_y_estado_especificados(ruta_bd):
    """CP-INI-01"""
    inicializar_base_datos()
    filas = obtener_conexion().execute(
        "SELECT codigo, nombre, capacidad, estado FROM salas ORDER BY codigo"
    ).fetchall()

    assert [tuple(f) for f in filas] == sorted(SALAS_INICIALES)
    estados = {f["codigo"]: f["estado"] for f in filas}
    assert estados["S04"] == "fuera_de_servicio"
    assert all(e == "disponible" for c, e in estados.items() if c != "S04")


def test_rf01_salas_iniciales_disponibles_para_consulta(ruta_bd):
    """CP-INI-01"""
    inicializar_base_datos()

    codigos = [s["codigo"] for s in consultar_salas()]

    assert codigos == ["S01", "S02", "S03", "S04", "S05"]


@pytest.mark.xfail(
    strict=True,
    reason="Hallazgo: semilla.py solo inserta salas; RF-01 exige también "
           "datos iniciales de estudiantes.",
)
def test_rf01_crea_estudiantes_iniciales(ruta_bd):
    """CP-INI-02"""
    inicializar_base_datos()

    (total,) = obtener_conexion().execute(
        "SELECT COUNT(*) FROM estudiantes").fetchone()

    assert total > 0


# --------------------------------------------------------------------------
# RF-01 · Ejecuciones posteriores (la base de datos ya existe)
# --------------------------------------------------------------------------

def test_rf01_segunda_ejecucion_reutiliza_base_sin_duplicar(ruta_bd):
    """CP-INI-03"""
    inicializar_base_datos()

    resultado = inicializar_base_datos()

    assert resultado.exito is True
    assert resultado.base_datos_creada is False
    assert resultado.salas_insertadas == 0
    (total,) = obtener_conexion().execute(
        "SELECT COUNT(*) FROM salas").fetchone()
    assert total == len(SALAS_INICIALES)


def test_rf01_reinicializar_no_sobrescribe_datos_modificados(ruta_bd):
    """CP-INI-03"""
    inicializar_base_datos()
    conexion = obtener_conexion()
    conexion.execute("UPDATE salas SET capacidad = 99 WHERE codigo = 'S01'")
    conexion.commit()

    inicializar_base_datos()

    (capacidad,) = obtener_conexion().execute(
        "SELECT capacidad FROM salas WHERE codigo = 'S01'").fetchone()
    assert capacidad == 99


def test_rf01_reinicializar_conserva_reservaciones_existentes(ruta_bd):
    """CP-INI-03"""
    inicializar_base_datos()
    conexion = obtener_conexion()
    conexion.execute(
        "INSERT INTO estudiantes (carne, nombre_completo, correo) "
        "VALUES ('E001', 'Ana Prueba', 'ana@u.cr')")
    conexion.execute(
        "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, "
        "hora_inicio, duracion_horas, cantidad_personas) "
        "VALUES (1, 1, '2026-11-02', '09:00', 1, 2)")
    conexion.commit()

    cerrar_conexion()
    inicializar_base_datos()

    conexion = obtener_conexion()
    assert conexion.execute(
        "SELECT COUNT(*) FROM reservaciones").fetchone()[0] == 1
    assert conexion.execute(
        "SELECT COUNT(*) FROM estudiantes").fetchone()[0] == 1


# --------------------------------------------------------------------------
# RF-01 / RNF-05 · Errores de inicialización (sin cierre inesperado)
# --------------------------------------------------------------------------

def test_rf01_archivo_corrupto_se_informa_sin_excepcion(ruta_bd):
    """CP-INI-04"""
    ruta_bd.write_bytes(b"esto no es una base de datos sqlite" * 50)

    resultado = inicializar_base_datos()

    assert resultado.exito is False
    assert resultado.mensaje


def test_rf01_esquema_incompatible_se_informa_sin_excepcion(ruta_bd):
    """CP-INI-04"""
    previa = sqlite3.connect(ruta_bd)
    previa.execute(
        "CREATE TABLE salas (id INTEGER PRIMARY KEY, codigo TEXT, "
        "nombre TEXT, capacidad INTEGER)")
    previa.commit()
    previa.close()

    resultado = inicializar_base_datos()

    assert resultado.exito is False
    assert resultado.mensaje


def test_rf01_archivo_vacio_se_inicializa_correctamente(ruta_bd):
    """CP-INI-05"""
    ruta_bd.write_bytes(b"")

    resultado = inicializar_base_datos()

    assert resultado.exito is True
    assert len(consultar_salas()) == len(SALAS_INICIALES)


@pytest.mark.xfail(
    strict=True,
    raises=OSError,
    reason="Hallazgo: inicializar_base_datos solo captura sqlite3.Error; una "
           "ruta inválida lanza OSError sin controlar (RF-01, RNF-05).",
)
def test_rf01_ruta_imposible_se_informa_sin_excepcion(tmp_path):
    """CP-INI-06"""
    cerrar_conexion()
    archivo = tmp_path / "es_un_archivo"
    archivo.write_text("x")
    configurar_ruta_base_datos(archivo / "subcarpeta" / "reservas.db")
    try:
        resultado = inicializar_base_datos()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(":memory:")

    assert resultado.exito is False


# --------------------------------------------------------------------------
# Persistencia entre ejecuciones y cierre (RF-10)
# --------------------------------------------------------------------------

def test_persistencia_datos_sobreviven_al_cerrar_y_reabrir(ruta_bd):
    """CP-PER-01"""
    inicializar_base_datos()
    resultado = registrar_sala("S06", "Sala Nueva", 7)
    assert resultado["exito"] is True

    _reabrir()
    inicializar_base_datos()

    codigos = [s["codigo"] for s in consultar_salas()]
    assert "S06" in codigos
    assert len(codigos) == len(SALAS_INICIALES) + 1


def test_rf10_cerrar_aplicacion_deja_datos_guardados_y_libera_conexion(ruta_bd):
    """CP-PER-01"""
    inicializar_base_datos()
    registrar_sala("S07", "Sala Cierre", 3)

    ControladorAplicacion().cerrar_aplicacion()

    assert conexion_bd._conexion is None
    verificacion = sqlite3.connect(ruta_bd)
    try:
        fila = verificacion.execute(
            "SELECT nombre FROM salas WHERE codigo = 'S07'").fetchone()
    finally:
        verificacion.close()
    assert fila == ("Sala Cierre",)


def test_persistencia_operacion_rechazada_no_altera_datos(ruta_bd):
    """CP-PER-02"""
    inicializar_base_datos()

    resultado = registrar_sala("S01", "Duplicada", 5)

    assert resultado["exito"] is False
    assert len(consultar_salas()) == len(SALAS_INICIALES)
    (nombre,) = obtener_conexion().execute(
        "SELECT nombre FROM salas WHERE codigo = 'S01'").fetchone()
    assert nombre == "Sala Biblioteca 1"


def test_rnf06_rollback_descarta_cambios_parciales(ruta_bd):
    """CP-PER-02"""
    inicializar_base_datos()
    conexion = obtener_conexion()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO estudiantes (carne, nombre_completo, correo) "
            "VALUES ('E100', 'Parcial', 'p@u.cr')")
        # Falla por llave foránea: el estudiante anterior no debe quedar.
        conexion.execute(
            "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, "
            "hora_inicio, duracion_horas, cantidad_personas) "
            "VALUES (1, 999, '2026-11-02', '09:00', 1, 1)")
    conexion.rollback()

    (total,) = conexion.execute(
        "SELECT COUNT(*) FROM estudiantes WHERE carne = 'E100'").fetchone()
    assert total == 0


# --------------------------------------------------------------------------
# Conexión
# --------------------------------------------------------------------------

def test_conexion_es_unica_y_reutilizada(ruta_bd):
    """CP-BD-05"""
    assert obtener_conexion() is obtener_conexion()


def test_conexion_cerrar_es_idempotente(ruta_bd):
    """CP-BD-05"""
    obtener_conexion()
    cerrar_conexion()
    cerrar_conexion()  # no debe lanzar excepción

    assert conexion_bd._conexion is None


def test_conexion_configurar_ruta_cierra_conexion_previa(ruta_bd, tmp_path):
    """CP-BD-05"""
    anterior = obtener_conexion()

    configurar_ruta_base_datos(tmp_path / "otra.db")

    assert conexion_bd._conexion is None
    with pytest.raises(sqlite3.ProgrammingError):
        anterior.execute("SELECT 1")
    assert obtener_ruta_base_datos() == tmp_path / "otra.db"


def test_conexion_la_base_existe_se_consulta_antes_de_crearla(ruta_bd):
    """CP-BD-05"""
    assert conexion_bd.la_base_datos_existe() is False

    obtener_conexion()

    assert conexion_bd.la_base_datos_existe() is True


def test_conexion_crea_carpeta_destino_si_no_existe(tmp_path):
    """CP-INI-05"""
    cerrar_conexion()
    destino = tmp_path / "nueva" / "carpeta" / "reservas.db"
    configurar_ruta_base_datos(destino)
    try:
        resultado = inicializar_base_datos()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(":memory:")

    assert resultado.exito is True
    assert destino.exists()


def test_rnf03_ruta_por_defecto_no_usa_rutas_absolutas_fijas():
    """CP-BD-06"""
    codigo = Path(conexion_bd.__file__).read_text(encoding="utf-8")

    assert "Path(__file__)" in codigo
    assert not re.search(r"[A-Za-z]:\\\\|/home/|/Users/", codigo)


# --------------------------------------------------------------------------
# Integridad del esquema (RNF-06)
# --------------------------------------------------------------------------

def test_rnf06_llaves_foraneas_activas(ruta_bd):
    """CP-BD-01"""
    inicializar_base_datos()

    (activas,) = obtener_conexion().execute("PRAGMA foreign_keys").fetchone()

    assert activas == 1


@pytest.mark.parametrize("sentencia", [
    # llave foránea: estudiante inexistente
    "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, hora_inicio, "
    "duracion_horas, cantidad_personas) "
    "VALUES (999, 1, '2026-11-02', '09:00', 1, 1)",
    # duración fuera de 1 o 2 horas
    "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, hora_inicio, "
    "duracion_horas, cantidad_personas) "
    "VALUES (1, 1, '2026-11-02', '09:00', 3, 1)",
    # cantidad de personas no positiva
    "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, hora_inicio, "
    "duracion_horas, cantidad_personas) "
    "VALUES (1, 1, '2026-11-02', '09:00', 1, 0)",
    # estado de reservación inválido
    "INSERT INTO reservaciones (estudiante_id, sala_id, fecha, hora_inicio, "
    "duracion_horas, cantidad_personas, estado) "
    "VALUES (1, 1, '2026-11-02', '09:00', 1, 1, 'pendiente')",
    # capacidad de sala no positiva
    "INSERT INTO salas (codigo, nombre, capacidad, estado) "
    "VALUES ('X1', 'Sala X', 0, 'disponible')",
    # estado de sala inválido
    "INSERT INTO salas (codigo, nombre, capacidad, estado) "
    "VALUES ('X2', 'Sala X', 4, 'roto')",
    # código de sala duplicado
    "INSERT INTO salas (codigo, nombre, capacidad, estado) "
    "VALUES ('S01', 'Repetida', 4, 'disponible')",
    # estado de estudiante inválido
    "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) "
    "VALUES ('E9', 'Ana', 'a@u.cr', 'suspendido')",
    # campo obligatorio nulo
    "INSERT INTO estudiantes (carne, nombre_completo, correo) "
    "VALUES (NULL, 'Ana', 'a@u.cr')",
], ids=['CP-BD-01-fk_estudiante_inexistente', 'CP-BD-02-duracion_3_horas', 'CP-BD-02-cantidad_personas_0', 'CP-BD-03-estado_reservacion_invalido', 'CP-BD-02-capacidad_sala_0', 'CP-BD-03-estado_sala_invalido', 'CP-BD-04-codigo_sala_duplicado', 'CP-BD-03-estado_estudiante_invalido', 'CP-BD-03-carne_nulo'])
def test_rnf06_esquema_rechaza_datos_invalidos(ruta_bd, sentencia):
    """CP-BD-01 a CP-BD-04 (ver ids del parametrize)"""
    inicializar_base_datos()
    conexion = obtener_conexion()
    conexion.execute(
        "INSERT INTO estudiantes (carne, nombre_completo, correo) "
        "VALUES ('E001', 'Ana Prueba', 'ana@u.cr')")
    conexion.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sentencia)


def test_rnf06_carne_de_estudiante_es_unico(ruta_bd):
    """CP-BD-04"""
    inicializar_base_datos()
    conexion = obtener_conexion()
    insertar = ("INSERT INTO estudiantes (carne, nombre_completo, correo) "
                "VALUES ('E001', 'Ana', 'a@u.cr')")
    conexion.execute(insertar)

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(insertar)


# --------------------------------------------------------------------------
# RNF-08 · Codificación (tildes y ñ)
# --------------------------------------------------------------------------

def test_rnf08_tildes_y_enie_se_conservan_tras_reabrir(ruta_bd):
    """CP-PER-03"""
    inicializar_base_datos()
    nombre = "Sala Ñandú Café Árbol"
    resultado = registrar_sala("S08", nombre, 4)
    assert resultado["exito"] is True

    _reabrir()

    (guardado,) = obtener_conexion().execute(
        "SELECT nombre FROM salas WHERE codigo = 'S08'").fetchone()
    assert guardado == nombre
