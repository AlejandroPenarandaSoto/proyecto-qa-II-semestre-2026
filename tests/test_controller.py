from src.controller.controller import ControladorAplicacion


def test_controlador_solicita_panel_con_filtros(monkeypatch):
    recibido = {}

    def consulta_simulada(**filtros):
        recibido.update(filtros)
        return {"exito": True}

    monkeypatch.setattr(
        "src.controller.controller.consultar_panel",
        consulta_simulada,
    )
    controlador = ControladorAplicacion()

    resultado = controlador.obtener_panel(
        fecha="2026-10-10",
        codigo_sala="S01",
        estado="activa",
    )

    assert resultado["exito"] is True
    assert recibido == {
        "fecha": "2026-10-10",
        "codigo_sala": "S01",
        "estado": "activa",
    }


def test_controlador_devuelve_codigos_de_sala(monkeypatch):
    monkeypatch.setattr(
        "src.controller.controller.consultar_salas",
        lambda: [
            {"codigo": "S01"},
            {"codigo": "S02"},
        ],
    )
    controlador = ControladorAplicacion()

    assert controlador.obtener_codigos_salas() == ["S01", "S02"]


def test_controlador_cierra_la_conexion(monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        "src.controller.controller.cerrar_conexion",
        lambda: llamadas.append("cerrada"),
    )
    controlador = ControladorAplicacion()

    controlador.cerrar_aplicacion()

    assert llamadas == ["cerrada"]


def test_controlador_delega_operaciones_recurrentes(monkeypatch):
    llamadas = []

    monkeypatch.setattr(
        "src.controller.controller.previsualizar_reservaciones_recurrentes",
        lambda **datos: llamadas.append(("previsualizar", datos)) or {"exito": True},
    )
    monkeypatch.setattr(
        "src.controller.controller.crear_reservaciones_recurrentes",
        lambda **datos: llamadas.append(("crear", datos)) or {"exito": True},
    )
    monkeypatch.setattr(
        "src.controller.controller.cancelar_ocurrencias_futuras",
        lambda identificador: llamadas.append(("cancelar", identificador))
        or {"exito": True},
    )
    controlador = ControladorAplicacion()
    datos = {"carne": "C123456789", "semanas": 4}

    assert controlador.previsualizar_recurrencia(**datos)["exito"] is True
    assert controlador.crear_recurrencia(**datos)["exito"] is True
    assert controlador.cancelar_recurrencia_desde("R0002")["exito"] is True
    assert llamadas == [
        ("previsualizar", datos),
        ("crear", datos),
        ("cancelar", "R0002"),
    ]
