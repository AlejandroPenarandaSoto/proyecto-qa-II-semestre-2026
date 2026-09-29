from types import SimpleNamespace
from unittest.mock import Mock

from src.view.app import PanelControl


def _panel_simulado():
    return SimpleNamespace(
        _id_reserva_seleccionada=lambda: "R0002",
        controlador=SimpleNamespace(
            cancelar_reserva=Mock(
                return_value={"exito": True, "mensaje": "Cancelada."}
            ),
            cancelar_recurrencia_desde=Mock(
                return_value={"exito": True, "mensaje": "Serie cancelada."}
            ),
        ),
        _mostrar_resultado_cancelacion=Mock(),
        winfo_toplevel=lambda: object(),
    )


def test_cancelacion_individual_delega_reservacion_seleccionada(monkeypatch):
    panel = _panel_simulado()
    monkeypatch.setattr(
        "src.view.app.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )

    PanelControl._cancelar_individual(panel)

    panel.controlador.cancelar_reserva.assert_called_once_with("R0002")
    panel._mostrar_resultado_cancelacion.assert_called_once_with(
        {"exito": True, "mensaje": "Cancelada."}
    )


def test_cancelacion_futura_delega_serie_seleccionada(monkeypatch):
    panel = _panel_simulado()
    monkeypatch.setattr(
        "src.view.app.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )

    PanelControl._cancelar_futuras(panel)

    panel.controlador.cancelar_recurrencia_desde.assert_called_once_with("R0002")
    panel._mostrar_resultado_cancelacion.assert_called_once_with(
        {"exito": True, "mensaje": "Serie cancelada."}
    )


def test_resultado_exitoso_actualiza_el_panel(monkeypatch):
    panel = SimpleNamespace(
        winfo_toplevel=lambda: object(),
        refrescar_panel=Mock(),
    )
    informacion = Mock()
    monkeypatch.setattr("src.view.app.messagebox.showinfo", informacion)

    PanelControl._mostrar_resultado_cancelacion(
        panel,
        {"exito": True, "mensaje": "Cancelación realizada."},
    )

    informacion.assert_called_once()
    panel.refrescar_panel.assert_called_once_with()
