from types import SimpleNamespace
from unittest.mock import Mock

from src.view.dialogo_recurrencia import DialogoRecurrencia


DATOS = {
    "carne": "C123456789",
    "codigo_sala": "S01",
    "fecha": "2026-10-10",
    "hora_inicio": "10:00",
    "duracion": 1,
    "cantidad_personas": 2,
    "semanas": 3,
}


def _dialogo_simulado():
    return SimpleNamespace(
        controlador=SimpleNamespace(
            previsualizar_recurrencia=Mock(),
            crear_recurrencia=Mock(),
        ),
        _datos_formulario=lambda: (DATOS, None),
        _llenar_previsualizacion=Mock(),
        boton_crear=SimpleNamespace(configure=Mock()),
        mensaje_var=SimpleNamespace(set=Mock()),
        al_cambiar_pendientes=Mock(),
        al_completar=Mock(),
        ventana=SimpleNamespace(destroy=Mock()),
        _tiene_cambios=True,
    )


def test_previsualizacion_valida_habilita_creacion():
    dialogo = _dialogo_simulado()
    ocurrencias = [
        {
            "numero": 1,
            "fecha": "2026-10-10",
            "disponible": True,
            "mensaje": "Horario disponible.",
        }
    ]
    dialogo.controlador.previsualizar_recurrencia.return_value = {
        "exito": True,
        "puede_crear": True,
        "mensaje": "Todo disponible.",
        "ocurrencias": ocurrencias,
    }

    DialogoRecurrencia.previsualizar(dialogo)

    dialogo.controlador.previsualizar_recurrencia.assert_called_once_with(**DATOS)
    dialogo._llenar_previsualizacion.assert_called_once_with(ocurrencias)
    dialogo.boton_crear.configure.assert_called_once_with(state="normal")


def test_conflicto_mantiene_creacion_deshabilitada():
    dialogo = _dialogo_simulado()
    dialogo.controlador.previsualizar_recurrencia.return_value = {
        "exito": True,
        "puede_crear": False,
        "mensaje": "Existe un conflicto.",
        "ocurrencias": [],
    }

    DialogoRecurrencia.previsualizar(dialogo)

    dialogo.boton_crear.configure.assert_called_once_with(state="disabled")


def test_creacion_exitosa_refresca_panel_y_cierra(monkeypatch):
    dialogo = _dialogo_simulado()
    dialogo.controlador.crear_recurrencia.return_value = {
        "exito": True,
        "serie_id": "SR0001",
        "ids": ["R0001", "R0002", "R0003"],
    }
    informacion = Mock()
    monkeypatch.setattr(
        "src.view.dialogo_recurrencia.messagebox.showinfo",
        informacion,
    )

    DialogoRecurrencia.crear(dialogo)

    dialogo.controlador.crear_recurrencia.assert_called_once_with(**DATOS)
    dialogo.al_cambiar_pendientes.assert_called_once_with(False)
    dialogo.al_completar.assert_called_once_with()
    informacion.assert_called_once()
    dialogo.ventana.destroy.assert_called_once_with()


def test_cancelar_permite_conservar_formulario(monkeypatch):
    dialogo = _dialogo_simulado()
    monkeypatch.setattr(
        "src.view.dialogo_recurrencia.messagebox.askyesno",
        lambda *args, **kwargs: False,
    )

    DialogoRecurrencia.cancelar(dialogo)

    dialogo.al_cambiar_pendientes.assert_not_called()
    dialogo.ventana.destroy.assert_not_called()
