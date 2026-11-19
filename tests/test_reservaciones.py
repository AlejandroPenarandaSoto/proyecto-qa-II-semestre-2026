from datetime import datetime, timedelta

import pytest

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos
from src.model.estudiantes.servicio import modificar_estudiante, registrar_estudiante
from src.model.reservaciones import reglas
from src.model.reservaciones.servicio import (
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    crear_reservaciones_recurrentes,
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


def _registrar_segundo_estudiante():
    exito, mensaje = registrar_estudiante(CARNE_B, "Carlos López", "carlos@tec.ac.cr")
    assert exito, mensaje


def _fecha_futura(dias=1):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _crear(**kwargs):
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
    resultado = _crear(fecha=fecha, duracion=2)

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
    resultado = _crear(hora_inicio="19:00", duracion=1)
    assert resultado["exito"] is True


# RN-01
def test_rechazar_estudiante_inexistente(base_datos_prueba):
    resultado = _crear(carne="Z999999999")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_rechazar_estudiante_inactivo(base_datos_prueba):
    modificar_estudiante(CARNE, "Ana Rodríguez", "ana@tec.ac.cr", "inactivo")
    resultado = _crear()
    assert resultado["exito"] is False
    assert "activo" in resultado["mensaje"].lower()


# RN-08 y sala inexistente
def test_rechazar_sala_inexistente(base_datos_prueba):
    resultado = _crear(codigo_sala="S99")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_rechazar_sala_fuera_de_servicio(base_datos_prueba):
    resultado = _crear(codigo_sala="S04")
    assert resultado["exito"] is False
    assert "fuera de servicio" in resultado["mensaje"].lower()


# RN-02
def test_rechazar_fecha_pasada(base_datos_prueba):
    resultado = _crear(fecha="2020-01-01")
    assert resultado["exito"] is False
    assert "anterior" in resultado["mensaje"].lower()


def test_rechazar_fecha_formato_invalido(base_datos_prueba):
    resultado = _crear(fecha="28-09-2026")
    assert resultado["exito"] is False
    assert "formato" in resultado["mensaje"].lower()


# RN-03
def test_rechazar_hora_ya_transcurrida_si_es_hoy(base_datos_prueba):
    ahora = datetime.now()
    if ahora.hour < 8:
        pytest.skip("Antes de las 08:00 no hay una hora válida del día que ya haya transcurrido.")
    hora_pasada = f"{ahora.hour:02d}:00"
    resultado = _crear(fecha=ahora.strftime("%Y-%m-%d"), hora_inicio=hora_pasada)
    assert resultado["exito"] is False
    assert "transcurrió" in resultado["mensaje"].lower()


# RN-04 y RN-05
def test_rechazar_hora_no_completa(base_datos_prueba):
    resultado = _crear(hora_inicio="09:30")
    assert resultado["exito"] is False
    assert "hora completa" in resultado["mensaje"].lower()


def test_rechazar_hora_antes_de_apertura(base_datos_prueba):
    resultado = _crear(hora_inicio="07:00")
    assert resultado["exito"] is False
    assert "08:00 a 20:00" in resultado["mensaje"]


def test_rechazar_reserva_que_termina_despues_de_cierre(base_datos_prueba):
    resultado = _crear(hora_inicio="19:00", duracion=2)
    assert resultado["exito"] is False
    assert "08:00 a 20:00" in resultado["mensaje"]


# RN-06
@pytest.mark.parametrize("duracion", [0, 3, -1, 1.5, "1"])
def test_rechazar_duracion_invalida(base_datos_prueba, duracion):
    resultado = _crear(duracion=duracion)
    assert resultado["exito"] is False
    assert "1 o 2" in resultado["mensaje"]


# RN-07
def test_rechazar_cantidad_cero(base_datos_prueba):
    resultado = _crear(cantidad_personas=0)
    assert resultado["exito"] is False
    assert "mayor que cero" in resultado["mensaje"].lower()


def test_rechazar_capacidad_excedida(base_datos_prueba):
    resultado = _crear(codigo_sala="S01", cantidad_personas=5)
    assert resultado["exito"] is False
    assert "capacidad" in resultado["mensaje"].lower()


def test_rechazar_capacidad_cubiculo(base_datos_prueba):
    resultado = _crear(codigo_sala="S05", cantidad_personas=2)
    assert resultado["exito"] is False
    assert "capacidad" in resultado["mensaje"].lower()


# RN-09 y RN-10 · tabla de superposición
# Reservación existente: 10:00-12:00 (duración 2).
# El caso envolvente necesita una existente de 1 h: ver la prueba dedicada.
@pytest.mark.parametrize(
    "hora_inicio, duracion, debe_permitir, caso",
    [
        ("10:00", 2, False, "total"),
        ("09:00", 2, False, "parcial_inicio"),
        ("11:00", 2, False, "parcial_fin"),
        ("10:00", 1, False, "contenida"),
        ("12:00", 1, True, "consecutiva_despues"),
        ("08:00", 2, True, "consecutiva_antes"),
        ("14:00", 1, True, "sin_traslape"),
    ],
)
def test_tabla_superposicion(base_datos_prueba, hora_inicio, duracion, debe_permitir, caso):
    fecha = _fecha_futura()
    existente = _crear(
        fecha=fecha,
        hora_inicio="10:00",
        duracion=2,
        cantidad_personas=1,
    )
    assert existente["exito"] is True

    _registrar_segundo_estudiante()
    resultado = _crear(
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
    existente = _crear(fecha=fecha, hora_inicio="10:00", duracion=1)
    assert existente["exito"] is True

    _registrar_segundo_estudiante()
    resultado = _crear(
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
    assert _crear(codigo_sala="S01", fecha=fecha, hora_inicio="08:00")["exito"]
    assert _crear(codigo_sala="S02", fecha=fecha, hora_inicio="10:00")["exito"]
    assert _crear(codigo_sala="S03", fecha=fecha, hora_inicio="12:00")["exito"]

    cuarta = _crear(codigo_sala="S05", fecha=fecha, hora_inicio="14:00", cantidad_personas=1)
    assert cuarta["exito"] is False
    assert "3" in cuarta["mensaje"]


# RF-06 · consulta incluye canceladas y ordena por fecha y hora
def test_consultar_reservaciones_orden_y_historial(base_datos_prueba):
    fecha_lejana = _fecha_futura(10)
    fecha_cercana = _fecha_futura(2)

    _crear(codigo_sala="S01", fecha=fecha_lejana, hora_inicio="10:00")
    _crear(codigo_sala="S02", fecha=fecha_cercana, hora_inicio="14:00")
    _crear(codigo_sala="S03", fecha=fecha_cercana, hora_inicio="09:00")

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
    creada = _crear(fecha=fecha, hora_inicio="10:00", duracion=2)
    assert creada["id"] == "R0001"

    cancelada = cancelar_reservacion("R0001")
    assert cancelada["exito"] is True

    _registrar_segundo_estudiante()
    nueva = _crear(
        carne=CARNE_B,
        fecha=fecha,
        hora_inicio="10:00",
        duracion=2,
    )
    assert nueva["exito"] is True
    assert nueva["id"] == "R0002"


def test_cancelar_con_entero(base_datos_prueba):
    _crear()
    resultado = cancelar_reservacion(1)
    assert resultado["exito"] is True


def test_cancelar_inexistente(base_datos_prueba):
    resultado = cancelar_reservacion("R0099")
    assert resultado["exito"] is False
    assert "no existe" in resultado["mensaje"].lower()


def test_cancelar_dos_veces(base_datos_prueba):
    _crear()
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
    _crear(codigo_sala="S01", fecha=fecha, hora_inicio="08:00")
    _crear(codigo_sala="S02", fecha=fecha, hora_inicio="10:00")
    _crear(codigo_sala="S03", fecha=fecha, hora_inicio="12:00")
    assert cancelar_reservacion("R0002")["exito"] is True

    cuarta = _crear(codigo_sala="S05", fecha=fecha, hora_inicio="14:00", cantidad_personas=1)
    assert cuarta["exito"] is True
    assert cuarta["id"] == "R0004"


# RN-13 · IDs no se reutilizan
def test_id_cancelado_no_se_reutiliza(base_datos_prueba):
    _crear(hora_inicio="08:00")
    cancelar_reservacion("R0001")
    nueva = _crear(hora_inicio="10:00")
    assert nueva["id"] == "R0002"


# RF-13 · modificar
def test_modificar_conserva_id(base_datos_prueba):
    fecha_original = _fecha_futura(1)
    fecha_nueva = _fecha_futura(3)
    creada = _crear(fecha=fecha_original, hora_inicio="10:00")
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
    primera = _crear(fecha=fecha, hora_inicio="10:00", duracion=2)
    _registrar_segundo_estudiante()
    segunda = _crear(
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
    _crear(fecha=fecha, hora_inicio="10:00", duracion=2)
    resultado = modificar_reservacion("R0001", duracion=1)
    assert resultado["exito"] is True
    consulta = consultar_reservaciones()
    assert consulta["reservaciones"][0]["hora_fin"] == "11:00"


def test_no_modificar_reservacion_cancelada(base_datos_prueba):
    _crear()
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


# Caracterización: identificadores aceptados por las operaciones sobre una reservación
@pytest.mark.parametrize("identificador", ["R0001", "r0001", " R0001 ", "1", " 1 ", 1])
def test_identificadores_validos_se_reconocen(base_datos_prueba, identificador):
    _crear()
    resultado = cancelar_reservacion(identificador)
    assert resultado["exito"] is True
    assert "R0001" in resultado["mensaje"]


@pytest.mark.parametrize("identificador", [None, True, 0, -1, "R0000", "X0001", "R", "", 1.0])
def test_identificadores_invalidos_se_rechazan(base_datos_prueba, identificador):
    _crear()
    for operacion in (cancelar_reservacion, modificar_reservacion):
        resultado = operacion(identificador)
        assert resultado["exito"] is False
        assert "no es válido" in resultado["mensaje"]


# Caracterización: orden de las validaciones (se informa el primer error)
def test_estudiante_se_valida_antes_que_la_sala(base_datos_prueba):
    resultado = _crear(carne="Z999999999", codigo_sala="S99")
    assert "estudiante" in resultado["mensaje"].lower()


def test_duracion_se_valida_antes_que_el_formato(base_datos_prueba):
    resultado = _crear(duracion=3, fecha="fecha-invalida")
    assert "1 o 2" in resultado["mensaje"]


def test_horario_se_valida_antes_que_la_sala(base_datos_prueba):
    resultado = _crear(hora_inicio="07:00", codigo_sala="S99")
    assert "08:00 a 20:00" in resultado["mensaje"]


@pytest.mark.parametrize("hora_inicio", [None, 9, "", "nueve", "25:00"])
def test_rechazar_hora_con_formato_invalido(base_datos_prueba, hora_inicio):
    resultado = _crear(hora_inicio=hora_inicio)
    assert resultado["exito"] is False
    assert "formato" in resultado["mensaje"].lower()


@pytest.mark.parametrize("cantidad", [-1, True, 1.5, "2"])
def test_rechazar_cantidad_no_entera_o_negativa(base_datos_prueba, cantidad):
    resultado = _crear(cantidad_personas=cantidad)
    assert resultado["exito"] is False
    assert "mayor que cero" in resultado["mensaje"].lower()


def test_sala_y_carne_ignoran_mayusculas_y_espacios(base_datos_prueba):
    resultado = _crear(carne=f" {CARNE.lower()} ", codigo_sala=" s01 ")
    assert resultado["exito"] is True
    assert consultar_reservaciones()["reservaciones"][0]["sala"] == "S01"


# Caracterización: RF-13 conserva los campos no indicados y revalida el resultado
def test_modificar_un_campo_conserva_los_demas(base_datos_prueba):
    fecha = _fecha_futura()
    _crear(fecha=fecha, hora_inicio="10:00", duracion=2, cantidad_personas=2)

    resultado = modificar_reservacion("R0001", cantidad_personas=3)

    assert resultado["exito"] is True
    reserva = consultar_reservaciones()["reservaciones"][0]
    assert (reserva["sala"], reserva["fecha"], reserva["hora_inicio"], reserva["duracion_horas"]) == (
        "S01", fecha, "10:00", 2
    )
    assert reserva["cantidad_personas"] == 3


def test_modificar_revalida_capacidad_de_la_nueva_sala(base_datos_prueba):
    _crear(cantidad_personas=2)
    resultado = modificar_reservacion("R0001", codigo_sala="S05")
    assert resultado["exito"] is False
    assert "capacidad" in resultado["mensaje"].lower()


def test_modificar_no_cuenta_contra_el_limite(base_datos_prueba):
    fecha = _fecha_futura()
    _crear(codigo_sala="S01", fecha=fecha, hora_inicio="08:00")
    _crear(codigo_sala="S02", fecha=fecha, hora_inicio="10:00")
    _crear(codigo_sala="S03", fecha=fecha, hora_inicio="12:00")

    resultado = modificar_reservacion("R0003", hora_inicio="15:00")
    assert resultado["exito"] is True


def test_consulta_vacia_informa_que_no_hay_reservaciones(base_datos_prueba):
    consulta = consultar_reservaciones()
    assert consulta["mensaje"] == "No hay reservaciones registradas."


# DEF-F7-P2-01 · CP-F7P2-04: la hora sin cero inicial se trata igual que HH:MM
def test_hora_sin_cero_inicial_detecta_traslape(base_datos_prueba):
    fecha = _fecha_futura()
    assert _crear(fecha=fecha, hora_inicio="09:00", duracion=1)["exito"] is True
    _registrar_segundo_estudiante()

    resultado = _crear(carne=CARNE_B, fecha=fecha, hora_inicio="9:00", duracion=1)

    assert resultado["exito"] is False
    assert "conflicto" in resultado["mensaje"].lower()


def test_hora_sin_cero_inicial_se_guarda_como_hh_mm(base_datos_prueba):
    assert _crear(hora_inicio="9:00", duracion=2)["exito"] is True

    reserva = consultar_reservaciones()["reservaciones"][0]
    assert (reserva["hora_inicio"], reserva["hora_fin"]) == ("09:00", "11:00")


def test_modificar_con_hora_sin_cero_inicial_se_guarda_como_hh_mm(base_datos_prueba):
    _crear(hora_inicio="10:00")
    assert modificar_reservacion("R0001", hora_inicio="9:00")["exito"] is True
    assert consultar_reservaciones()["reservaciones"][0]["hora_inicio"] == "09:00"


# DEF-F7-P2-01 · misma causa en la fecha: '2027-1-5' es la misma fecha que '2027-01-05'
def test_fecha_sin_ceros_detecta_traslape_y_se_guarda_como_aaaa_mm_dd(base_datos_prueba):
    anio = datetime.now().year + 1
    assert _crear(fecha=f"{anio}-01-05", hora_inicio="10:00")["exito"] is True
    _registrar_segundo_estudiante()

    resultado = _crear(carne=CARNE_B, fecha=f"{anio}-1-5", hora_inicio="10:00")

    assert resultado["exito"] is False
    assert "conflicto" in resultado["mensaje"].lower()
    assert consultar_reservaciones()["reservaciones"][0]["fecha"] == f"{anio}-01-05"


# Reglas puras: se prueban con una hora actual fija
AHORA = datetime(2026, 11, 16, 12, 30)


def test_regla_rechaza_fecha_pasada_escrita_sin_ceros():
    with pytest.raises(reglas.ReservacionInvalida, match="anterior"):
        reglas.validar_horario("2026-9-1", "10:00", 1, AHORA)


def test_regla_rechaza_hora_de_hoy_ya_transcurrida_escrita_sin_cero():
    with pytest.raises(reglas.ReservacionInvalida, match="transcurrió"):
        reglas.validar_horario("2026-11-16", "9:00", 1, AHORA)


@pytest.mark.parametrize(
    "fecha, hora, esperado",
    [
        ("2026-11-20", "09:00", ("2026-11-20", "09:00")),
        (" 2026-11-20 ", " 9:00 ", ("2026-11-20", "09:00")),
        ("2027-1-5", "8:00", ("2027-01-05", "08:00")),
    ],
)
def test_regla_devuelve_fecha_y_hora_en_formato_canonico(fecha, hora, esperado):
    assert reglas.validar_horario(fecha, hora, 1, AHORA) == esperado


# DEF-F5-P2-01 · RN-11: cada ocurrencia de una serie ocupa un cupo del límite
def _crear_serie(semanas, fecha=None, codigo_sala="S01", hora_inicio="10:00"):
    return crear_reservaciones_recurrentes(
        carne=CARNE,
        codigo_sala=codigo_sala,
        fecha=fecha or _fecha_futura(),
        hora_inicio=hora_inicio,
        duracion=1,
        cantidad_personas=1,
        semanas=semanas,
    )


def test_cp_rn11_02_serie_de_tres_mas_una_individual_se_rechaza(base_datos_prueba):
    fecha = _fecha_futura()
    serie = _crear_serie(semanas=3, fecha=fecha)
    assert serie["ids"] == ["R0001", "R0002", "R0003"]

    cuarta = _crear(codigo_sala="S02", fecha=fecha, hora_inicio="13:00", cantidad_personas=1)

    assert cuarta["exito"] is False
    assert "3" in cuarta["mensaje"]
    assert len(consultar_reservaciones()["reservaciones"]) == 3


def test_serie_que_supera_el_limite_no_se_crea(base_datos_prueba):
    fecha = _fecha_futura()
    assert _crear(codigo_sala="S02", fecha=fecha, hora_inicio="13:00")["exito"] is True
    assert _crear(codigo_sala="S03", fecha=fecha, hora_inicio="15:00")["exito"] is True

    serie = _crear_serie(semanas=2, fecha=fecha)

    assert serie["exito"] is False
    assert serie["puede_crear"] is False
    assert "3" in serie["mensaje"]
    assert len(consultar_reservaciones()["reservaciones"]) == 2


def test_cancelar_una_ocurrencia_libera_su_cupo(base_datos_prueba):
    fecha = _fecha_futura()
    serie = _crear_serie(semanas=3, fecha=fecha)
    assert cancelar_reservacion(serie["ids"][2])["exito"] is True

    nueva = _crear(codigo_sala="S02", fecha=fecha, hora_inicio="13:00")
    assert nueva["exito"] is True


def test_regla_cuenta_cada_reservacion_vigente_y_omite_las_terminadas():
    activas = [
        {"id": 1, "fecha": "2026-11-20", "hora_inicio": "10:00", "duracion_horas": 1, "serie_id": "SR0001"},
        {"id": 2, "fecha": "2026-11-27", "hora_inicio": "10:00", "duracion_horas": 1, "serie_id": "SR0001"},
        {"id": 3, "fecha": "2026-11-16", "hora_inicio": "12:00", "duracion_horas": 1, "serie_id": None},
        {"id": 4, "fecha": "2026-11-16", "hora_inicio": "08:00", "duracion_horas": 2, "serie_id": None},
    ]
    # La 3 está en curso (12:00-13:00 a las 12:30) y cuenta; la 4 ya terminó.
    assert reglas.contar_cupos_ocupados(activas, AHORA) == 3
