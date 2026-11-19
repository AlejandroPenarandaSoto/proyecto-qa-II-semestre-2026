from types import SimpleNamespace
from unittest.mock import Mock

from src.view.dialogo_reporte import DialogoReporte


def _dialogo_simulado(fecha_inicio="2026-10-01", fecha_fin="2026-10-31"):
    return SimpleNamespace(
        fecha_inicio_var=SimpleNamespace(get=lambda: fecha_inicio),
        fecha_fin_var=SimpleNamespace(get=lambda: fecha_fin),
        controlador=SimpleNamespace(
            validar_rango_reporte=Mock(),
            generar_reporte=Mock(),
        ),
        ventana=SimpleNamespace(destroy=Mock()),
    )


def test_no_abre_selector_si_el_rango_es_invalido(monkeypatch):
    dialogo = _dialogo_simulado()
    dialogo.controlador.validar_rango_reporte.return_value = {
        "exito": False,
        "mensaje": "Rango inválido.",
    }
    selector = Mock()
    error = Mock()
    monkeypatch.setattr(
        "src.view.dialogo_reporte.filedialog.asksaveasfilename",
        selector,
    )
    monkeypatch.setattr("src.view.dialogo_reporte.messagebox.showerror", error)

    DialogoReporte.generar(dialogo)

    selector.assert_not_called()
    dialogo.controlador.generar_reporte.assert_not_called()
    error.assert_called_once()


def test_cancelar_selector_no_crea_reporte(monkeypatch):
    dialogo = _dialogo_simulado()
    dialogo.controlador.validar_rango_reporte.return_value = {"exito": True}
    dialogo.controlador.generar_reporte.return_value = {
        "exito": False,
        "cancelado": True,
        "mensaje": "Cancelado.",
    }
    monkeypatch.setattr(
        "src.view.dialogo_reporte.filedialog.asksaveasfilename",
        lambda **_argumentos: "",
    )

    DialogoReporte.generar(dialogo)

    dialogo.controlador.generar_reporte.assert_called_once_with(
        "2026-10-01",
        "2026-10-31",
        None,
    )
    dialogo.ventana.destroy.assert_not_called()


def test_reporte_exitoso_informa_y_cierra_dialogo(monkeypatch):
    dialogo = _dialogo_simulado()
    dialogo.controlador.validar_rango_reporte.return_value = {"exito": True}
    dialogo.controlador.generar_reporte.return_value = {
        "exito": True,
        "cancelado": False,
        "cantidad": 5,
        "ruta": "/tmp/reporte.csv",
    }
    informacion = Mock()
    monkeypatch.setattr(
        "src.view.dialogo_reporte.filedialog.asksaveasfilename",
        lambda **_argumentos: "/tmp/reporte.csv",
    )
    monkeypatch.setattr(
        "src.view.dialogo_reporte.messagebox.showinfo",
        informacion,
    )

    DialogoReporte.generar(dialogo)

    dialogo.controlador.generar_reporte.assert_called_once_with(
        "2026-10-01",
        "2026-10-31",
        "/tmp/reporte.csv",
    )
    informacion.assert_called_once()
    dialogo.ventana.destroy.assert_called_once_with()
