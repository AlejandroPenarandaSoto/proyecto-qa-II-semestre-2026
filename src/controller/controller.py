"""Controlador principal de la aplicación.

Conecta la interfaz con los servicios del modelo sin exponer detalles de
persistencia en la vista.
"""

from src.db.conexion import cerrar_conexion
from src.model.auditoria.servicio import consultar_auditoria
from src.model.panel.servicio import consultar_panel
from src.model.reportes.servicio import generar_reporte_csv, validar_rango_reporte
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
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

    def cancelar_reserva(self, id_reservacion):
        return cancelar_reservacion(id_reservacion)

    def validar_rango_reporte(self, fecha_inicio, fecha_fin):
        return validar_rango_reporte(fecha_inicio, fecha_fin)

    def generar_reporte(self, fecha_inicio, fecha_fin, ruta_destino):
        return generar_reporte_csv(fecha_inicio, fecha_fin, ruta_destino)

    def obtener_auditoria(self):
        return consultar_auditoria()

    def cerrar_aplicacion(self):
        """Libera los recursos de persistencia antes de cerrar la GUI."""
        cerrar_conexion()
