
import pytest

from src.db.conexion import (
    configurar_ruta_base_datos,
    cerrar_conexion,
    obtener_ruta_base_datos,
    obtener_conexion,
)
from db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import (
    registrar_estudiante, 
    consultar_estudiantes,
    buscar_reservaciones_estudiante,
    modificar_estudiante,
)


@pytest.fixture
def base_datos_prueba(tmp_path):
    """Prepara una base de datos temporal para cada prueba."""

    ruta_original = obtener_ruta_base_datos()

    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "pruebas.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje

    yield

    cerrar_conexion()
    configurar_ruta_base_datos(ruta_original)


def test_registrar_estudiante_correctamente(base_datos_prueba):
    """Comprueba que se puede registrar un estudiante válido."""

    exito, mensaje = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    assert exito is True
    assert mensaje == "Estudiante registrado correctamente."


def test_rechazar_carne_duplicado(base_datos_prueba):
    """Comprueba que no se puede registrar dos veces el mismo carné."""

    # Registrar el primer estudiante
    exito1, mensaje1 = registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    # Intentar registrar el mismo carné en minúsculas
    exito2, mensaje2 = registrar_estudiante(
        "c123456789",
        "Carlos López",
        "carlos@tec.ac.cr"
    )

    assert exito1 is True
    assert exito2 is False
    assert mensaje2 == "Ya existe un estudiante con ese carné."


# PRUEBAS DE DATOS INVÁLIDOS - RF-02
@pytest.mark.parametrize(
    "carne, nombre, correo",
    [
        ("123", "Ana Rodríguez", "ana@tec.ac.cr"),
        ("123456789!", "Ana Rodríguez", "ana@tec.ac.cr"),
        ("C123456789", "A", "ana@tec.ac.cr"),
        ("C123456789", "   ", "ana@tec.ac.cr"),
        ("C123456789", "Ana Rodríguez", "anatec.ac.cr"),
        ("C123456789", "Ana Rodríguez", "ana@"),
        ("C123456789", "Ana Rodríguez", "ana@@tec.ac.cr"),
    ]
)
def test_rechazar_datos_invalidos(
    base_datos_prueba, carne, nombre, correo
):
    """Comprueba que se rechazan los datos inválidos."""

    exito, mensaje = registrar_estudiante(
        carne,
        nombre,
        correo
    )

    assert exito is False
    assert mensaje != ""


# PRUEBAS RF-03: CONSULTAR ESTUDIANTES
def test_consultar_estudiantes_registrados(base_datos_prueba):
    """Comprueba que la consulta devuelve los estudiantes registrados."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    exito, mensaje, estudiantes = consultar_estudiantes()

    assert exito is True
    assert len(estudiantes) == 1
    assert estudiantes[0]["carne"] == "C123456789"
    assert estudiantes[0]["nombre_completo"] == "Ana Rodríguez"
    assert estudiantes[0]["correo"] == "ana@tec.ac.cr"
    assert estudiantes[0]["estado"] == "activo"


def test_consultar_estudiantes_ordenados(base_datos_prueba):
    """Comprueba que los estudiantes aparecen ordenados por nombre."""

    registrar_estudiante(
        "C123456789",
        "Carlos López",
        "carlos@tec.ac.cr"
    )

    registrar_estudiante(
        "A123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    exito, mensaje, estudiantes = consultar_estudiantes()

    assert exito is True
    assert len(estudiantes) == 2
    assert estudiantes[0]["nombre_completo"] == "Ana Rodríguez"
    assert estudiantes[1]["nombre_completo"] == "Carlos López"


def test_consultar_sin_estudiantes(base_datos_prueba):
    """Comprueba la consulta cuando no hay estudiantes registrados."""

    exito, mensaje, estudiantes = consultar_estudiantes()

    assert exito is True
    assert estudiantes == []
    assert mensaje == "No hay estudiantes registrados."


# PRUEBAS RF-07: BUSCAR RESERVACIONES
def test_estudiante_sin_reservaciones(base_datos_prueba):
    """Comprueba la búsqueda de un estudiante sin reservaciones."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    exito, mensaje, reservaciones = buscar_reservaciones_estudiante(
        "C123456789"
    )

    assert exito is True
    assert reservaciones == []
    assert mensaje == "El estudiante no tiene reservaciones registradas."


def test_buscar_reservaciones_estudiante_inexistente(base_datos_prueba):
    """Comprueba que se informa cuando el estudiante no existe."""

    exito, mensaje, reservaciones = buscar_reservaciones_estudiante(
        "Z123456789"
    )

    assert exito is False
    assert reservaciones == []
    assert mensaje == "No existe un estudiante con ese carné."


def test_buscar_reservaciones_existentes(base_datos_prueba):
    """Comprueba que se encuentran las reservaciones del estudiante."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    conexion = obtener_conexion()

    # Obtener el ID del estudiante.
    estudiante = conexion.execute(
        "SELECT id FROM estudiantes WHERE carne = ?",
        ("C123456789",)
    ).fetchone()

    # Obtener una sala de las cinco salas iniciales.
    sala = conexion.execute(
        "SELECT id FROM salas LIMIT 1"
    ).fetchone()

    # Crear una reservación de prueba.
    conexion.execute(
        """
        INSERT INTO reservaciones
        (
            estudiante_id,
            sala_id,
            fecha,
            hora_inicio,
            duracion_horas,
            cantidad_personas,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            estudiante["id"],
            sala["id"],
            "2026-10-15",
            "10:00",
            2,
            3,
            "activa"
        )
    )

    conexion.commit()

    # Buscar las reservaciones.
    exito, mensaje, reservaciones = buscar_reservaciones_estudiante(
        "C123456789"
    )

    assert exito is True
    assert mensaje == "Reservaciones encontradas."
    assert len(reservaciones) == 1

    assert reservaciones[0]["fecha"] == "2026-10-15"
    assert reservaciones[0]["hora_inicio"] == "10:00"
    assert reservaciones[0]["duracion_horas"] == 2
    assert reservaciones[0]["cantidad_personas"] == 3

# PRUEBAS RF-11: MODIFICAR ESTUDIANTES
def test_modificar_estudiante_correctamente(base_datos_prueba):
    """Comprueba que se actualizan los datos del estudiante."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    exito, mensaje = modificar_estudiante(
        "C123456789",
        "Ana Rodríguez López",
        "ana.lopez@tec.ac.cr",
        "inactivo"
    )

    assert exito is True
    assert mensaje == "Estudiante modificado correctamente."

    # Consultar nuevamente para verificar los cambios.
    exito, mensaje, estudiantes = consultar_estudiantes()

    assert exito is True
    assert len(estudiantes) == 1
    assert estudiantes[0]["carne"] == "C123456789"
    assert estudiantes[0]["nombre_completo"] == "Ana Rodríguez López"
    assert estudiantes[0]["correo"] == "ana.lopez@tec.ac.cr"
    assert estudiantes[0]["estado"] == "inactivo"


def test_modificar_estudiante_inexistente(base_datos_prueba):
    """Comprueba que no se modifica un estudiante inexistente."""

    exito, mensaje = modificar_estudiante(
        "Z123456789",
        "Carlos López",
        "carlos@tec.ac.cr",
        "activo"
    )

    assert exito is False
    assert mensaje == "No existe un estudiante con ese carné."


@pytest.mark.parametrize(
    "nombre, correo, estado",
    [
        ("A", "ana@tec.ac.cr", "activo"),
        ("   ", "ana@tec.ac.cr", "activo"),
        ("Ana Rodríguez", "correo_invalido", "activo"),
        ("Ana Rodríguez", "ana@tec.ac.cr", "pendiente"),
    ]
)
def test_modificar_estudiante_datos_invalidos(
    base_datos_prueba, nombre, correo, estado
):
    """Comprueba que se rechazan las modificaciones inválidas."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    exito, mensaje = modificar_estudiante(
        "C123456789",
        nombre,
        correo,
        estado
    )

    assert exito is False

    # Comprobar que los datos originales no cambiaron.
    exito, mensaje, estudiantes = consultar_estudiantes()

    assert estudiantes[0]["nombre_completo"] == "Ana Rodríguez"
    assert estudiantes[0]["correo"] == "ana@tec.ac.cr"
    assert estudiantes[0]["estado"] == "activo"


# PRUEBAS ADICIONALES DE CASOS LÍMITE
def test_registrar_con_espacios(base_datos_prueba):
    """Comprueba que se eliminan los espacios innecesarios."""

    exito, mensaje = registrar_estudiante(
        "  C123456789  ",
        "  Ana Rodríguez  ",
        "  ana@tec.ac.cr  "
    )

    assert exito is True

    exito, mensaje, estudiantes = consultar_estudiantes()

    assert estudiantes[0]["carne"] == "C123456789"
    assert estudiantes[0]["nombre_completo"] == "Ana Rodríguez"
    assert estudiantes[0]["correo"] == "ana@tec.ac.cr"


def test_buscar_reservaciones_carne_vacio(base_datos_prueba):
    """Comprueba que se rechaza una búsqueda sin carné."""

    exito, mensaje, reservaciones = buscar_reservaciones_estudiante(
        "   "
    )

    assert exito is False
    assert reservaciones == []


def test_modificar_estado_a_activo(base_datos_prueba):
    """Comprueba que se puede reactivar un estudiante."""

    registrar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr"
    )

    modificar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
        "inactivo"
    )

    exito, mensaje = modificar_estudiante(
        "C123456789",
        "Ana Rodríguez",
        "ana@tec.ac.cr",
        "ACTIVO"
    )

    assert exito is True

    exito, mensaje, estudiantes = consultar_estudiantes()

    assert estudiantes[0]["estado"] == "activo"
