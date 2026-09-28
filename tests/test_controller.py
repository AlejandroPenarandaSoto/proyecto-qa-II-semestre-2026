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
