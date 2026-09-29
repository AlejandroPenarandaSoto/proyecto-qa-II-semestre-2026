from types import SimpleNamespace
from unittest.mock import Mock

from src.view.app import Aplicacion


def crear_aplicacion_simulada(hay_cambios):
    return SimpleNamespace(
        _hay_cambios_pendientes=hay_cambios,
        controlador=SimpleNamespace(cerrar_aplicacion=Mock()),
        destroy=Mock(),
    )


def test_cierra_directamente_cuando_no_hay_cambios_pendientes(monkeypatch):
    aplicacion = crear_aplicacion_simulada(hay_cambios=False)
    confirmar = Mock()
    monkeypatch.setattr("src.view.app.messagebox.askyesno", confirmar)

    resultado = Aplicacion.solicitar_salida(aplicacion)

    assert resultado is True
    confirmar.assert_not_called()
    aplicacion.controlador.cerrar_aplicacion.assert_called_once_with()
    aplicacion.destroy.assert_called_once_with()


def test_cancela_el_cierre_si_hay_cambios_pendientes(monkeypatch):
    aplicacion = crear_aplicacion_simulada(hay_cambios=True)
    monkeypatch.setattr(
        "src.view.app.messagebox.askyesno",
        lambda *args, **kwargs: False,
    )

    resultado = Aplicacion.solicitar_salida(aplicacion)

    assert resultado is False
    aplicacion.controlador.cerrar_aplicacion.assert_not_called()
    aplicacion.destroy.assert_not_called()


def test_confirma_el_cierre_si_hay_cambios_pendientes(monkeypatch):
    aplicacion = crear_aplicacion_simulada(hay_cambios=True)
    monkeypatch.setattr(
        "src.view.app.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )

    resultado = Aplicacion.solicitar_salida(aplicacion)

    assert resultado is True
    aplicacion.controlador.cerrar_aplicacion.assert_called_once_with()
    aplicacion.destroy.assert_called_once_with()
