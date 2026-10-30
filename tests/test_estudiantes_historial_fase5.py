"""CP-EST-13/18/19/20/21: estados, datos e historial de estudiantes.

Los INSERT de los helpers preparan datos controlados en una base temporal.
No evalúan creación/cancelación de reservaciones ni simulan una GUI ausente.
Las observaciones se imprimen antes de las aserciones de resultado para que
queden disponibles también cuando una de esas comprobaciones falle.
"""

import json
from datetime import date, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import (
    buscar_reservaciones_estudiante,
    consultar_estudiantes,
    modificar_estudiante,
    registrar_estudiante,
)


CARNE = "C123456789"
NOMBRE = "Ana Rodríguez"
CORREO = "ana@tec.ac.cr"


@pytest.fixture
def base_temporal(tmp_path):
    ruta_anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "estudiantes_historial_fase5.db")
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        yield obtener_conexion()
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(ruta_anterior)


def _observar(caso, requisito, datos, esperado, obtenido):
    print(
        "OBSERVACION_CP "
        + json.dumps(
            {
                "caso": caso,
                "requisito": requisito,
                "datos": datos,
                "esperado": esperado,
                "obtenido": obtenido,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _insertar_estudiante(conexion, carne=CARNE, nombre=NOMBRE, correo=CORREO, estado="activo"):
    cursor = conexion.execute(
        """INSERT INTO estudiantes (carne, nombre_completo, correo, estado)
           VALUES (?, ?, ?, ?)""",
        (carne, nombre, correo, estado),
    )
    conexion.commit()
    return cursor.lastrowid


def _insertar_reservacion(conexion, estudiante_id, dias, estado="activa", duracion=2, personas=3):
    fecha = (date.today() + timedelta(days=dias)).isoformat()
    sala_id = conexion.execute(
        "SELECT id FROM salas WHERE codigo = ?", ("S01",)
    ).fetchone()["id"]
    cursor = conexion.execute(
        """INSERT INTO reservaciones
               (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas,
                cantidad_personas, estado)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (estudiante_id, sala_id, fecha, "10:00", duracion, personas, estado),
    )
    conexion.commit()
    return {
        "id": cursor.lastrowid,
        "sala": "S01",
        "fecha": fecha,
        "hora_inicio": "10:00",
        "duracion_horas": duracion,
        "cantidad_personas": personas,
        "estado": estado,
    }


def _reservaciones_persistidas(conexion):
    return [
        dict(fila)
        for fila in conexion.execute("SELECT * FROM reservaciones ORDER BY id")
    ]


def test_cp_est_13_consulta_incluye_estudiantes_activos_e_inactivos(base_temporal):
    """RF-03: se incluyen Ana activa y Carlos inactivo con todos sus datos."""
    _insertar_estudiante(
        base_temporal, "A123456789", "Carlos López", "carlos@tec.ac.cr", "inactivo"
    )
    _insertar_estudiante(base_temporal)
    filas_esperadas = [
        {"carne": CARNE, "nombre_completo": NOMBRE, "correo": CORREO, "estado": "activo"},
        {
            "carne": "A123456789",
            "nombre_completo": "Carlos López",
            "correo": "carlos@tec.ac.cr",
            "estado": "inactivo",
        },
    ]

    exito, mensaje, estudiantes = consultar_estudiantes()

    _observar(
        "CP-EST-13",
        "RF-03",
        {"preparacion": "Dos estudiantes insertados en SQLite temporal", "estudiantes": filas_esperadas},
        {"exito": True, "estudiantes": filas_esperadas},
        {"exito": exito, "mensaje": mensaje, "estudiantes": estudiantes},
    )
    assert exito is True, mensaje
    assert estudiantes == filas_esperadas


def test_cp_est_18_buscar_carne_en_minusculas_devuelve_mismo_historial(base_temporal):
    """RF-07: mayúsculas y minúsculas devuelven la misma reservación e ID."""
    estudiante_id = _insertar_estudiante(base_temporal)
    reservacion = _insertar_reservacion(base_temporal, estudiante_id, dias=5)
    persistido_antes = _reservaciones_persistidas(base_temporal)

    exito_mayusculas, mensaje_mayusculas, mayusculas = buscar_reservaciones_estudiante(CARNE)
    exito_minusculas, mensaje_minusculas, minusculas = buscar_reservaciones_estudiante(CARNE.lower())
    persistido_despues = _reservaciones_persistidas(base_temporal)

    _observar(
        "CP-EST-18",
        "RF-07",
        {"carnes": [CARNE, CARNE.lower()], "reservacion_preparada_por_sql": reservacion},
        {"exito_ambas": True, "historial_ambas": [reservacion], "persistencia_sin_cambios": True},
        {
            "mayusculas": {"exito": exito_mayusculas, "mensaje": mensaje_mayusculas, "historial": mayusculas},
            "minusculas": {"exito": exito_minusculas, "mensaje": mensaje_minusculas, "historial": minusculas},
            "persistencia_antes": persistido_antes,
            "persistencia_despues": persistido_despues,
        },
    )
    assert exito_mayusculas is True, mensaje_mayusculas
    assert exito_minusculas is True, mensaje_minusculas
    assert mayusculas == minusculas == [reservacion]
    assert persistido_antes == persistido_despues


def test_cp_est_19_busqueda_incluye_reservacion_activa_y_cancelada(base_temporal):
    """RF-07: el historial incluye ambas reservaciones, con IDs y estados."""
    estudiante_id = _insertar_estudiante(base_temporal)
    activa = _insertar_reservacion(
        base_temporal, estudiante_id, dias=1, estado="activa", duracion=1, personas=2
    )
    cancelada = _insertar_reservacion(
        base_temporal, estudiante_id, dias=2, estado="cancelada", duracion=1, personas=2
    )
    persistido_antes = _reservaciones_persistidas(base_temporal)

    exito, mensaje, historial = buscar_reservaciones_estudiante(CARNE)
    persistido_despues = _reservaciones_persistidas(base_temporal)

    _observar(
        "CP-EST-19",
        "RF-07",
        {"carne": CARNE, "reservaciones_preparadas_por_sql": [activa, cancelada]},
        {"exito": True, "historial": [activa, cancelada], "persistencia_sin_cambios": True},
        {
            "exito": exito,
            "mensaje": mensaje,
            "historial": historial,
            "persistencia_antes": persistido_antes,
            "persistencia_despues": persistido_despues,
        },
    )
    assert exito is True, mensaje
    assert historial == [activa, cancelada]
    assert persistido_antes == persistido_despues


def test_cp_est_21_inactivar_estudiante_conserva_historial_e_identificadores(base_temporal):
    """RF-11: cambia a inactivo sin alterar la reservación previamente asociada."""
    estudiante_id = _insertar_estudiante(base_temporal)
    reservacion = _insertar_reservacion(base_temporal, estudiante_id, dias=5)
    exito_antes, mensaje_antes, historial_antes = buscar_reservaciones_estudiante(CARNE)
    persistido_antes = _reservaciones_persistidas(base_temporal)

    exito_modificacion, mensaje_modificacion = modificar_estudiante(CARNE, NOMBRE, CORREO, "inactivo")
    exito_consulta, mensaje_consulta, estudiantes = consultar_estudiantes()
    exito_despues, mensaje_despues, historial_despues = buscar_reservaciones_estudiante(CARNE)
    persistido_despues = _reservaciones_persistidas(base_temporal)
    fila_estudiante = base_temporal.execute(
        "SELECT id, carne, nombre_completo, correo, estado FROM estudiantes WHERE id = ?",
        (estudiante_id,),
    ).fetchone()
    estudiante_persistido = dict(fila_estudiante) if fila_estudiante is not None else None
    estudiante_esperado = {
        "carne": CARNE, "nombre_completo": NOMBRE, "correo": CORREO, "estado": "inactivo"
    }

    _observar(
        "CP-EST-21",
        "RF-11",
        {"carne": CARNE, "nuevo_estado": "inactivo", "reservacion_preparada_por_sql": reservacion},
        {"exito_modificacion": True, "estudiante": estudiante_esperado, "historial_antes_y_despues": [reservacion]},
        {
            "modificacion": {"exito": exito_modificacion, "mensaje": mensaje_modificacion},
            "consulta_estudiantes": {"exito": exito_consulta, "mensaje": mensaje_consulta, "estudiantes": estudiantes},
            "consulta_historial_antes": {"exito": exito_antes, "mensaje": mensaje_antes, "historial": historial_antes},
            "consulta_historial_despues": {"exito": exito_despues, "mensaje": mensaje_despues, "historial": historial_despues},
            "estudiante_persistido": estudiante_persistido,
            "persistencia_reservaciones_antes": persistido_antes,
            "persistencia_reservaciones_despues": persistido_despues,
        },
    )
    assert exito_antes is True, mensaje_antes
    assert exito_modificacion is True, mensaje_modificacion
    assert exito_consulta is True, mensaje_consulta
    assert exito_despues is True, mensaje_despues
    assert estudiantes == [estudiante_esperado]
    assert estudiante_persistido == {"id": estudiante_id, **estudiante_esperado}
    assert historial_antes == historial_despues == [reservacion]
    assert persistido_antes == persistido_despues


def test_cp_est_20_modificar_nombre_y_correo_mantiene_carne_y_estado_activo(base_temporal):
    """RF-11: variante de la matriz que modifica datos sin inactivar."""
    exito_registro, mensaje_registro = registrar_estudiante(CARNE, NOMBRE, CORREO)
    fila_antes = base_temporal.execute(
        "SELECT id, carne, nombre_completo, correo, estado FROM estudiantes WHERE carne = ?",
        (CARNE,),
    ).fetchone()
    antes = dict(fila_antes) if fila_antes is not None else None
    nuevo_nombre = "Ana Rodríguez López"
    nuevo_correo = "ana.lopez@tec.ac.cr"

    exito_modificacion, mensaje_modificacion = modificar_estudiante(
        CARNE, nuevo_nombre, nuevo_correo, "activo"
    )
    exito_consulta, mensaje_consulta, estudiantes = consultar_estudiantes()
    fila_despues = base_temporal.execute(
        "SELECT id, carne, nombre_completo, correo, estado FROM estudiantes WHERE carne = ?",
        (CARNE,),
    ).fetchone()
    despues = dict(fila_despues) if fila_despues is not None else None
    estudiante_esperado = {
        "carne": CARNE,
        "nombre_completo": nuevo_nombre,
        "correo": nuevo_correo,
        "estado": "activo",
    }

    _observar(
        "CP-EST-20",
        "RF-11",
        {
            "carne": CARNE,
            "nombre_original": NOMBRE,
            "correo_original": CORREO,
            "nombre_nuevo": nuevo_nombre,
            "correo_nuevo": nuevo_correo,
            "estado_solicitado": "activo",
        },
        {"exito_modificacion": True, "estudiante": estudiante_esperado, "mismo_id": True},
        {
            "registro": {"exito": exito_registro, "mensaje": mensaje_registro},
            "modificacion": {"exito": exito_modificacion, "mensaje": mensaje_modificacion},
            "consulta": {"exito": exito_consulta, "mensaje": mensaje_consulta, "estudiantes": estudiantes},
            "persistido_antes": antes,
            "persistido_despues": despues,
        },
    )
    assert exito_registro is True, mensaje_registro
    assert antes is not None
    assert antes["carne"] == CARNE
    assert antes["estado"] == "activo"
    assert exito_modificacion is True, mensaje_modificacion
    assert exito_consulta is True, mensaje_consulta
    assert estudiantes == [estudiante_esperado]
    assert despues == {"id": antes["id"], **estudiante_esperado}
