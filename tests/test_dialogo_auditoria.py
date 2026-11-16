from types import SimpleNamespace
from unittest.mock import Mock

from src.view.dialogo_auditoria import DialogoAuditoria


def _dialogo_simulado(resultado, elementos=()):
    tabla = Mock()
    tabla.get_children.return_value = elementos
    return SimpleNamespace(
        controlador=SimpleNamespace(obtener_auditoria=Mock(return_value=resultado)),
        ventana=object(),
        tabla=tabla,
        mensaje_var=SimpleNamespace(set=Mock()),
    )


def test_auditoria_muestra_eventos_en_solo_lectura():
    evento = {
        "fecha_hora": "2026-09-28 18:30:00",
        "accion": "creacion",
        "entidad": "reservacion",
        "entidad_id": "R0001",
        "detalle": "Reservación creada.",
    }
    dialogo = _dialogo_simulado(
        {"exito": True, "mensaje": "Consulta correcta.", "eventos": [evento]},
        elementos=("anterior",),
    )

    DialogoAuditoria.refrescar(dialogo)

    dialogo.tabla.delete.assert_called_once_with("anterior")
    dialogo.tabla.insert.assert_called_once_with(
        "",
        "end",
        tags=(),
        values=(
            "2026-09-28 18:30:00",
            "creacion",
            "reservacion",
            "R0001",
            "Reservación creada.",
        ),
    )
    dialogo.mensaje_var.set.assert_called_once_with("1 evento registrado.")


def test_auditoria_muestra_estado_vacio():
    dialogo = _dialogo_simulado(
        {
            "exito": True,
            "mensaje": "No hay eventos de auditoría registrados.",
            "eventos": [],
        }
    )

    DialogoAuditoria.refrescar(dialogo)

    dialogo.tabla.insert.assert_not_called()
    dialogo.mensaje_var.set.assert_called_once_with(
        "No hay eventos de auditoría registrados."
    )


def test_error_de_auditoria_no_reemplaza_los_datos_visibles(monkeypatch):
    dialogo = _dialogo_simulado(
        {"exito": False, "mensaje": "Error de consulta.", "eventos": []},
        elementos=("visible",),
    )
    mostrar_error = Mock()
    monkeypatch.setattr(
        "src.view.dialogo_auditoria.messagebox.showerror",
        mostrar_error,
    )

    DialogoAuditoria.refrescar(dialogo)

    mostrar_error.assert_called_once()
    dialogo.tabla.delete.assert_not_called()
    dialogo.tabla.insert.assert_not_called()
