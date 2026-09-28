from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import modificar_estudiante, registrar_estudiante
from src.model.reservaciones.servicio import (
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    modificar_reservacion,
)

CARNE = "C123456789"
CARNE_B = "A123456789"


@pytest.fixture
def base_datos_prueba(tmp_path):
    """Prepara una base de datos temporal con salas iniciales y un estudiante."""
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "pruebas.db")

    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje

    exito, mensaje = registrar_estudiante(CARNE, "Ana Rodríguez", "ana@tec.ac.cr")
    assert exito, mensaje

    yield

    cerrar_conexion()
    configurar_ruta_base_datos(ruta_original)


def _fecha_futura(dias=1):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _crear(base_datos_prueba, **kwargs):
    parametros = {
        "carne": CARNE,
        "codigo_sala": "S01",
        "fecha": _fecha_futura(),
        "hora_inicio": "10:00",
        "duracion": 1,
        "cantidad_personas": 2,
    }
    parametros.update(kwargs)
    return crear_reservacion(**parametros)


# RF-05 · creación exitosa
def test_crear_reservacion_exitosa(base_datos_prueba):
    fecha = _fecha_futura()
    resultado = _crear(base_datos_prueba, fecha=fecha, duracion=2)

    assert resultado["exito"] is True
    assert resultado["id"] == "R0001"
    assert "R0001" in resultado["mensaje"]

    consulta = consultar_reservaciones()
    assert consulta["exito"] is True
    assert len(consulta["reservaciones"]) == 1
    reserva = consulta["reservaciones"][0]
    assert reserva["id"] == "R0001"
    assert reserva["estudiante"] == "Ana Rodríguez"
    assert reserva["sala"] == "S01"
    assert reserva["fecha"] == fecha
    assert reserva["hora_inicio"] == "10:00"
    assert reserva["hora_fin"] == "12:00"
    assert reserva["cantidad_personas"] == 2
    assert reserva["estado"] == "activa"


def test_terminar_a_las_20_00_es_valido(base_datos_prueba):
    resultado = _crear(base_datos_prueba, hora_inicio="19:00", duracion=1)
    assert resultado["exito"] is True


# RN-01
def test_rechazar_estudiante_inexistente(base_datos_prueba):
    resultado = _crear(base_datos_prueba, carne="Z999999999")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_rechazar_estudiante_inactivo(base_datos_prueba):
    modificar_estudiante(CARNE, "Ana Rodríguez", "ana@tec.ac.cr", "inactivo")
    resultado = _crear(base_datos_prueba)
    assert resultado["exito"] is False
    assert "activo" in resultado["mensaje"].lower()


# RN-08 y sala inexistente
def test_rechazar_sala_inexistente(base_datos_prueba):
    resultado = _crear(base_datos_prueba, codigo_sala="S99")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_rechazar_sala_fuera_de_servicio(base_datos_prueba):
    resultado = _crear(base_datos_prueba, codigo_sala="S04")
    assert resultado["exito"] is False
    assert "fuera de servicio" in resultado["mensaje"].lower()


# RN-02
def test_rechazar_fecha_pasada(base_datos_prueba):
    resultado = _crear(base_datos_prueba, fecha="2020-01-01")
    assert resultado["exito"] is False
    assert "anterior" in resultado["mensaje"].lower()


def test_rechazar_fecha_formato_invalido(base_datos_prueba):
    resultado = _crear(base_datos_prueba, fecha="28-09-2026")
    assert resultado["exito"] is False
    assert "formato" in resultado["mensaje"].lower()


# RN-03
def test_rechazar_hora_ya_transcurrida_si_es_hoy(base_datos_prueba):
    ahora = datetime.now()
    if ahora.hour < 8:
        pytest.skip("Antes de las 08:00 no hay una hora válida del día que ya haya transcurrido.")
    hora_pasada = f"{ahora.hour:02d}:00"
    resultado = _crear(base_datos_prueba, fecha=ahora.strftime("%Y-%m-%d"), hora_inicio=hora_pasada)
    assert resultado["exito"] is False
    assert "transcurrió" in resultado["mensaje"].lower()


# RN-04 y RN-05
def test_rechazar_hora_no_completa(base_datos_prueba):
    resultado = _crear(base_datos_prueba, hora_inicio="09:30")
    assert resultado["exito"] is False
    assert "hora completa" in resultado["mensaje"].lower()


def test_rechazar_hora_antes_de_apertura(base_datos_prueba):
    resultado = _crear(base_datos_prueba, hora_inicio="07:00")
    assert resultado["exito"] is False
    assert "08:00 a 20:00" in resultado["mensaje"]


def test_rechazar_reserva_que_termina_despues_de_cierre(base_datos_prueba):
    resultado = _crear(base_datos_prueba, hora_inicio="19:00", duracion=2)
    assert resultado["exito"] is False
    assert "08:00 a 20:00" in resultado["mensaje"]


# RN-06
@pytest.mark.parametrize("duracion", [0, 3, -1, 1.5, "1"])
def test_rechazar_duracion_invalida(base_datos_prueba, duracion):
    resultado = _crear(base_datos_prueba, duracion=duracion)
    assert resultado["exito"] is False
    assert "1 o 2" in resultado["mensaje"]


# RN-07
def test_rechazar_cantidad_cero(base_datos_prueba):
    resultado = _crear(base_datos_prueba, cantidad_personas=0)
    assert resultado["exito"] is False
    assert "mayor que cero" in resultado["mensaje"].lower()


def test_rechazar_capacidad_excedida(base_datos_prueba):
    resultado = _crear(base_datos_prueba, codigo_sala="S01", cantidad_personas=5)
    assert resultado["exito"] is False
    assert "capacidad" in resultado["mensaje"].lower()


def test_rechazar_capacidad_cubiculo(base_datos_prueba):
    resultado = _crear(base_datos_prueba, codigo_sala="S05", cantidad_personas=2)
    assert resultado["exito"] is False
    assert "capacidad" in resultado["mensaje"].lower()


# RN-09 y RN-10 · tabla de superposición
# Reservación existente: 10:00-12:00 (duración 2)
@pytest.mark.parametrize(
    "hora_inicio, duracion, debe_permitir, caso",
    [
        ("10:00", 2, False, "total"),
        ("09:00", 2, False, "parcial_inicio"),
        ("11:00", 2, False, "parcial_fin"),
        ("10:00", 1, False, "contenida"),
        ("09:00", 2, False, "envolvente"),  # existente de 1h se cubre abajo en test dedicado
        ("12:00", 1, True, "consecutiva_despues"),
        ("08:00", 2, True, "consecutiva_antes"),
        ("14:00", 1, True, "sin_traslape"),
    ],
)
def test_tabla_superposicion(base_datos_prueba, hora_inicio, duracion, debe_permitir, caso):
    fecha = _fecha_futura()
    existente = _crear(
        base_datos_prueba,
        fecha=fecha,
        hora_inicio="10:00",
        duracion=2,
        cantidad_personas=1,
    )
    assert existente["exito"] is True

    registrar_estudiante(CARNE_B, "Carlos López", "carlos@tec.ac.cr")
    resultado = _crear(
        base_datos_prueba,
        carne=CARNE_B,
        fecha=fecha,
        hora_inicio=hora_inicio,
        duracion=duracion,
        cantidad_personas=1,
    )
    assert resultado["exito"] is debe_permitir, caso
    if not debe_permitir:
        assert "conflicto" in resultado["mensaje"].lower()


def test_superposicion_envolvente_sobre_reserva_de_una_hora(base_datos_prueba):
    fecha = _fecha_futura()
    existente = _crear(base_datos_prueba, fecha=fecha, hora_inicio="10:00", duracion=1)
    assert existente["exito"] is True

    registrar_estudiante(CARNE_B, "Carlos López", "carlos@tec.ac.cr")
    resultado = _crear(
        base_datos_prueba,
        carne=CARNE_B,
        fecha=fecha,
        hora_inicio="10:00",
        duracion=2,
    )
    assert resultado["exito"] is False
    assert "conflicto" in resultado["mensaje"].lower()


# RN-11
def test_limite_de_tres_reservaciones_activas(base_datos_prueba):
    fecha = _fecha_futura()
    assert _crear(base_datos_prueba, codigo_sala="S01", fecha=fecha, hora_inicio="08:00")["exito"]
    assert _crear(base_datos_prueba, codigo_sala="S02", fecha=fecha, hora_inicio="10:00")["exito"]
    assert _crear(base_datos_prueba, codigo_sala="S03", fecha=fecha, hora_inicio="12:00")["exito"]

    cuarta = _crear(base_datos_prueba, codigo_sala="S05", fecha=fecha, hora_inicio="14:00", cantidad_personas=1)
    assert cuarta["exito"] is False
    assert "3" in cuarta["mensaje"]


# RF-06 · consulta incluye canceladas y ordena por fecha y hora
def test_consultar_reservaciones_orden_y_historial(base_datos_prueba):
    fecha_lejana = _fecha_futura(10)
    fecha_cercana = _fecha_futura(2)

    _crear(base_datos_prueba, codigo_sala="S01", fecha=fecha_lejana, hora_inicio="10:00")
    _crear(base_datos_prueba, codigo_sala="S02", fecha=fecha_cercana, hora_inicio="14:00")
    _crear(base_datos_prueba, codigo_sala="S03", fecha=fecha_cercana, hora_inicio="09:00")

    cancelar_reservacion("R0001")
    consulta = consultar_reservaciones()
    ids_fechas_horas = [
        (item["id"], item["fecha"], item["hora_inicio"], item["estado"])
        for item in consulta["reservaciones"]
    ]

    assert ids_fechas_horas == [
        ("R0003", fecha_cercana, "09:00", "activa"),
        ("R0002", fecha_cercana, "14:00", "activa"),
        ("R0001", fecha_lejana, "10:00", "cancelada"),
    ]


def test_consultar_sin_reservaciones(base_datos_prueba):
    consulta = consultar_reservaciones()
    assert consulta["exito"] is True
    assert consulta["reservaciones"] == []


# RF-09 · cancelar libera horario; cancelar dos veces no altera
def test_cancelar_libera_horario(base_datos_prueba):
    fecha = _fecha_futura()
    creada = _crear(base_datos_prueba, fecha=fecha, hora_inicio="10:00", duracion=2)
    assert creada["id"] == "R0001"

    cancelada = cancelar_reservacion("R0001")
    assert cancelada["exito"] is True

    registrar_estudiante(CARNE_B, "Carlos López", "carlos@tec.ac.cr")
    nueva = _crear(
        base_datos_prueba,
        carne=CARNE_B,
        fecha=fecha,
        hora_inicio="10:00",
        duracion=2,
    )
    assert nueva["exito"] is True
    assert nueva["id"] == "R0002"


def test_cancelar_con_entero(base_datos_prueba):
    _crear(base_datos_prueba)
    resultado = cancelar_reservacion(1)
    assert resultado["exito"] is True


def test_cancelar_inexistente(base_datos_prueba):
    resultado = cancelar_reservacion("R0099")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_cancelar_dos_veces(base_datos_prueba):
    _crear(base_datos_prueba)
    primera = cancelar_reservacion("R0001")
    segunda = cancelar_reservacion("R0001")

    assert primera["exito"] is True
    assert segunda["exito"] is False
    assert "ya se encuentra cancelada" in segunda["mensaje"].lower()

    consulta = consultar_reservaciones()
    assert len(consulta["reservaciones"]) == 1
    assert consulta["reservaciones"][0]["estado"] == "cancelada"


def test_cancelar_permite_nueva_reserva_al_mismo_estudiante(base_datos_prueba):
    fecha = _fecha_futura()
    _crear(base_datos_prueba, codigo_sala="S01", fecha=fecha, hora_inicio="08:00")
    _crear(base_datos_prueba, codigo_sala="S02", fecha=fecha, hora_inicio="10:00")
    _crear(base_datos_prueba, codigo_sala="S03", fecha=fecha, hora_inicio="12:00")
    assert cancelar_reservacion("R0002")["exito"] is True

    cuarta = _crear(base_datos_prueba, codigo_sala="S05", fecha=fecha, hora_inicio="14:00", cantidad_personas=1)
    assert cuarta["exito"] is True
    assert cuarta["id"] == "R0004"


# RN-13 · IDs no se reutilizan
def test_id_cancelado_no_se_reutiliza(base_datos_prueba):
    _crear(base_datos_prueba, hora_inicio="08:00")
    cancelar_reservacion("R0001")
    nueva = _crear(base_datos_prueba, hora_inicio="10:00")
    assert nueva["id"] == "R0002"


# RF-13 · modificar
def test_modificar_conserva_id(base_datos_prueba):
    fecha_original = _fecha_futura(1)
    fecha_nueva = _fecha_futura(3)
    creada = _crear(base_datos_prueba, fecha=fecha_original, hora_inicio="10:00")
    assert creada["id"] == "R0001"

    modificada = modificar_reservacion("R0001", fecha=fecha_nueva, hora_inicio="15:00", duracion=2)
    assert modificada["exito"] is True
    assert modificada["id"] == "R0001"

    consulta = consultar_reservaciones()
    reserva = consulta["reservaciones"][0]
    assert reserva["id"] == "R0001"
    assert reserva["fecha"] == fecha_nueva
    assert reserva["hora_inicio"] == "15:00"
    assert reserva["hora_fin"] == "17:00"
    assert reserva["duracion_horas"] == 2


def test_modificar_con_conflicto_no_cambia_nada(base_datos_prueba):
    fecha = _fecha_futura()
    primera = _crear(base_datos_prueba, fecha=fecha, hora_inicio="10:00", duracion=2)
    registrar_estudiante(CARNE_B, "Carlos López", "carlos@tec.ac.cr")
    segunda = _crear(
        base_datos_prueba,
        carne=CARNE_B,
        fecha=fecha,
        hora_inicio="12:00",
        duracion=1,
    )
    assert primera["id"] == "R0001"
    assert segunda["id"] == "R0002"

    intento = modificar_reservacion("R0002", hora_inicio="11:00")
    assert intento["exito"] is False
    assert "conflicto" in intento["mensaje"].lower()

    consulta = consultar_reservaciones()
    reserva_2 = next(item for item in consulta["reservaciones"] if item["id"] == "R0002")
    assert reserva_2["hora_inicio"] == "12:00"
    assert reserva_2["hora_fin"] == "13:00"


def test_modificar_excluye_la_propia_reservacion_del_conflicto(base_datos_prueba):
    fecha = _fecha_futura()
    _crear(base_datos_prueba, fecha=fecha, hora_inicio="10:00", duracion=2)
    resultado = modificar_reservacion("R0001", duracion=1)
    assert resultado["exito"] is True
    consulta = consultar_reservaciones()
    assert consulta["reservaciones"][0]["hora_fin"] == "11:00"


def test_no_modificar_reservacion_cancelada(base_datos_prueba):
    _crear(base_datos_prueba)
    cancelar_reservacion("R0001")

    intento = modificar_reservacion("R0001", hora_inicio="16:00")
    assert intento["exito"] is False
    assert "cancelada" in intento["mensaje"].lower()

    consulta = consultar_reservaciones()
    assert consulta["reservaciones"][0]["hora_inicio"] == "10:00"
    assert consulta["reservaciones"][0]["estado"] == "cancelada"


def test_modificar_reservacion_inexistente(base_datos_prueba):
    resultado = modificar_reservacion("R0008", fecha=_fecha_futura())
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()
