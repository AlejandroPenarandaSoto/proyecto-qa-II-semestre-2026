"""Controlador principal de la aplicación.

Conecta la interfaz con los servicios del modelo sin exponer detalles de
persistencia en la vista.
"""

from src.db.conexion import cerrar_conexion
from src.model.panel.servicio import consultar_panel
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    crear_reservaciones_recurrentes,
    previsualizar_reservaciones_recurrentes,
)
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

    def previsualizar_recurrencia(self, **datos):
        return previsualizar_reservaciones_recurrentes(**datos)

    def crear_recurrencia(self, **datos):
        return crear_reservaciones_recurrentes(**datos)

    def cancelar_recurrencia_desde(self, id_reservacion):
        return cancelar_ocurrencias_futuras(id_reservacion)

    def cerrar_aplicacion(self):
        """Libera los recursos de persistencia antes de cerrar la GUI."""
        cerrar_conexion()
