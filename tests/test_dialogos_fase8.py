"""Pruebas de las vistas agregadas en Fase 8 (estudiantes, salas, reservación y disponibilidad).

Siguen el estilo de test_dialogo_auditoria.py: se ejercita la lógica de cada vista
con objetos simulados, sin abrir ventanas.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.controller.controller import ControladorAplicacion
from src.view.dialogo_disponibilidad import DialogoDisponibilidad
from src.view.dialogo_estudiantes import DialogoEstudiantes
from src.view.dialogo_reservacion import DialogoReservacion
from src.view.dialogo_salas import DialogoSalas


def _var(valor=""):
    return SimpleNamespace(get=Mock(return_value=valor), set=Mock())


def _dialogo(clase, controlador, **variables):
    dialogo = clase.__new__(clase)
    dialogo.ventana = Mock()
    dialogo.controlador = controlador
    dialogo.al_completar = Mock()
    dialogo.al_cambiar_pendientes = Mock()
    dialogo._tiene_cambios = True
    dialogo._cargando = False
    dialogo.mensaje_var = _var()
    dialogo.refrescar = Mock()
    for nombre, valor in variables.items():
        setattr(dialogo, nombre, _var(valor))
    return dialogo


@pytest.fixture
def mensajes(monkeypatch):
    registro = SimpleNamespace(info=Mock(), error=Mock(), aviso=Mock())
    for modulo in ("dialogo_estudiantes", "dialogo_salas", "dialogo_reservacion"):
        monkeypatch.setattr(f"src.view.{modulo}.messagebox.showinfo", registro.info)
        monkeypatch.setattr(f"src.view.{modulo}.messagebox.showerror", registro.error)
        monkeypatch.setattr(f"src.view.{modulo}.messagebox.showwarning", registro.aviso)
    return registro


# --- Estudiantes ---------------------------------------------------------------

def test_registrar_estudiante_valido_actualiza_tabla_y_panel(mensajes):
    controlador = SimpleNamespace(
        registrar_estudiante=Mock(return_value=(True, "Estudiante registrado correctamente."))
    )
    dialogo = _dialogo(
        DialogoEstudiantes,
        controlador,
        carne_var="B123456789",
        nombre_var="María Pérez",
        correo_var="maria@estudiantec.cr",
    )

    dialogo.registrar()

    controlador.registrar_estudiante.assert_called_once_with(
        "B123456789", "María Pérez", "maria@estudiantec.cr"
    )
    dialogo.refrescar.assert_called_once()
    dialogo.al_completar.assert_called_once()
    dialogo.al_cambiar_pendientes.assert_called_with(False)
    mensajes.error.assert_not_called()


def test_registrar_estudiante_invalido_muestra_el_motivo_sin_refrescar(mensajes):
    controlador = SimpleNamespace(
        registrar_estudiante=Mock(return_value=(False, "El carné debe tener 10 caracteres."))
    )
    dialogo = _dialogo(
        DialogoEstudiantes, controlador, carne_var="X1", nombre_var="Ana", correo_var="a@b.cr"
    )

    dialogo.registrar()

    mensajes.error.assert_called_once()
    assert "10 caracteres" in mensajes.error.call_args.args[1]
    dialogo.refrescar.assert_not_called()
    dialogo.al_completar.assert_not_called()


def test_modificar_estudiante_sin_seleccion_no_llama_al_modelo(mensajes):
    controlador = SimpleNamespace(modificar_estudiante=Mock())
    dialogo = _dialogo(DialogoEstudiantes, controlador, carne_var="   ")

    dialogo.modificar()

    mensajes.aviso.assert_called_once()
    controlador.modificar_estudiante.assert_not_called()


# --- Salas ---------------------------------------------------------------------

def test_registrar_sala_con_capacidad_no_numerica_no_llama_al_modelo(mensajes):
    controlador = SimpleNamespace(registrar_sala=Mock())
    dialogo = _dialogo(
        DialogoSalas,
        controlador,
        codigo_var="S07",
        nombre_var="Sala",
        capacidad_var="cuatro",
        estado_var="disponible",
    )

    dialogo.registrar()

    mensajes.error.assert_called_once()
    controlador.registrar_sala.assert_not_called()


def test_modificar_sala_envia_los_datos_y_actualiza_el_panel(mensajes):
    controlador = SimpleNamespace(
        modificar_sala=Mock(return_value={"exito": True, "mensaje": "Sala modificada correctamente."})
    )
    dialogo = _dialogo(
        DialogoSalas,
        controlador,
        codigo_var="S02",
        nombre_var="Sala Biblioteca 2",
        capacidad_var="7",
        estado_var="fuera_de_servicio",
    )

    dialogo.modificar()

    controlador.modificar_sala.assert_called_once_with(
        "S02", "Sala Biblioteca 2", 7, "fuera_de_servicio"
    )
    dialogo.al_completar.assert_called_once()


# --- Reservación individual ----------------------------------------------------

def _dialogo_reservacion(controlador, reservacion=None):
    dialogo = _dialogo(
        DialogoReservacion,
        controlador,
        carne_var="A001234567",
        sala_var="S01",
        fecha_var="2030-01-15",
        hora_var="10:00",
        duracion_var="1",
        personas_var="2",
    )
    dialogo.reservacion = reservacion
    return dialogo


def test_crear_reservacion_envia_todos_los_campos(mensajes):
    controlador = SimpleNamespace(
        crear_reserva=Mock(return_value={"exito": True, "mensaje": "Reservación R0001 creada correctamente."})
    )
    dialogo = _dialogo_reservacion(controlador)

    dialogo.guardar()

    controlador.crear_reserva.assert_called_once_with(
        carne="A001234567",
        codigo_sala="S01",
        fecha="2030-01-15",
        hora_inicio="10:00",
        duracion=1,
        cantidad_personas=2,
    )
    dialogo.al_completar.assert_called_once()
    dialogo.ventana.destroy.assert_called_once()


def test_modificar_reservacion_usa_el_id_seleccionado(mensajes):
    controlador = SimpleNamespace(
        modificar_reserva=Mock(return_value={"exito": True, "mensaje": "Reservación R0003 modificada correctamente."})
    )
    dialogo = _dialogo_reservacion(controlador, reservacion={"id": "R0003"})

    dialogo.guardar()

    assert controlador.modificar_reserva.call_args.args == ("R0003",)
    assert controlador.modificar_reserva.call_args.kwargs["hora_inicio"] == "10:00"


def test_reservacion_rechazada_mantiene_el_formulario_abierto(mensajes):
    controlador = SimpleNamespace(
        crear_reserva=Mock(return_value={"exito": False, "mensaje": "La cantidad de personas excede la capacidad."})
    )
    dialogo = _dialogo_reservacion(controlador)

    dialogo.guardar()

    mensajes.error.assert_called_once()
    dialogo.ventana.destroy.assert_not_called()
    dialogo.al_completar.assert_not_called()


# --- Disponibilidad ------------------------------------------------------------

@pytest.mark.parametrize(
    ("respuesta", "inicio"),
    [
        ({"disponible": True, "motivo": "La sala está disponible."}, "Disponible."),
        ({"disponible": False, "motivo": "Conflicto: la sala tiene una reservación."}, "No disponible."),
    ],
)
def test_disponibilidad_muestra_el_resultado_del_modelo(respuesta, inicio):
    controlador = SimpleNamespace(consultar_disponibilidad=Mock(return_value=respuesta))
    dialogo = DialogoDisponibilidad.__new__(DialogoDisponibilidad)
    dialogo.controlador = controlador
    dialogo.sala_var = _var("S01")
    dialogo.fecha_var = _var("2030-01-15")
    dialogo.hora_var = _var("10:00")
    dialogo.duracion_var = _var("1")
    dialogo.resultado_var = _var()

    dialogo.consultar()

    controlador.consultar_disponibilidad.assert_called_once_with("S01", "2030-01-15", "10:00", 1)
    assert dialogo.resultado_var.set.call_args.args[0].startswith(inicio)


def test_disponibilidad_sin_fecha_no_consulta():
    controlador = SimpleNamespace(consultar_disponibilidad=Mock())
    dialogo = DialogoDisponibilidad.__new__(DialogoDisponibilidad)
    dialogo.controlador = controlador
    dialogo.fecha_var = _var("")
    dialogo.resultado_var = _var()

    dialogo.consultar()

    controlador.consultar_disponibilidad.assert_not_called()


# --- Controlador ---------------------------------------------------------------

def test_controlador_obtiene_una_reservacion_por_id(monkeypatch):
    monkeypatch.setattr(
        "src.controller.controller.consultar_reservaciones",
        lambda: {"exito": True, "reservaciones": [{"id": "R0001"}, {"id": "R0002"}]},
    )
    controlador = ControladorAplicacion()

    assert controlador.obtener_reserva("R0002") == {"id": "R0002"}
    assert controlador.obtener_reserva("R0009") is None
