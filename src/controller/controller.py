"""Controlador principal de la aplicación.

Conecta la interfaz con los servicios del modelo sin exponer detalles de
persistencia en la vista.
"""

from src.model.panel.servicio import consultar_panel
from src.model.salas.servicio import consultar_salas


class ControladorAplicacion:
    """Coordina las consultas requeridas por la interfaz gráfica."""

    def obtener_panel(self, fecha=None, codigo_sala=None, estado=None):
        return consultar_panel(
            fecha=fecha,
            codigo_sala=codigo_sala,
            estado=estado,
        )

    def obtener_codigos_salas(self):
        return [sala["codigo"] for sala in consultar_salas()]
