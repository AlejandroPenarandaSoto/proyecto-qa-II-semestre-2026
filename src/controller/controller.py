"""Controlador principal de la aplicación.

Conecta la interfaz con los servicios del modelo sin exponer detalles de
persistencia en la vista.
"""

from src.db.conexion import cerrar_conexion
from src.model.auditoria.servicio import consultar_auditoria
from src.model.estudiantes.servicio import (
    buscar_reservaciones_estudiante,
    consultar_estudiantes,
    modificar_estudiante,
    registrar_estudiante,
)
from src.model.panel.servicio import consultar_panel
from src.model.reportes.servicio import generar_reporte_csv, validar_rango_reporte
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    crear_reservaciones_recurrentes,
    modificar_reservacion,
    previsualizar_reservaciones_recurrentes,
)
from src.model.salas.servicio import (
    consultar_disponibilidad,
    consultar_salas,
    modificar_sala,
    registrar_sala,
)


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

    def obtener_estudiantes(self):
        return consultar_estudiantes()

    def registrar_estudiante(self, carne, nombre, correo):
        return registrar_estudiante(carne, nombre, correo)

    def modificar_estudiante(self, carne, nombre, correo, estado):
        return modificar_estudiante(carne, nombre, correo, estado)

    def buscar_reservaciones_estudiante(self, carne):
        return buscar_reservaciones_estudiante(carne)

    def obtener_salas(self):
        return consultar_salas()

    def registrar_sala(self, codigo, nombre, capacidad, estado):
        return registrar_sala(codigo, nombre, capacidad, estado)

    def modificar_sala(self, codigo, nombre, capacidad, estado):
        return modificar_sala(codigo, nombre, capacidad, estado)

    def consultar_disponibilidad(self, codigo_sala, fecha, hora_inicio, duracion):
        return consultar_disponibilidad(codigo_sala, fecha, hora_inicio, duracion)

    def crear_reserva(self, **datos):
        return crear_reservacion(**datos)

    def modificar_reserva(self, id_reservacion, **cambios):
        return modificar_reservacion(id_reservacion, **cambios)

    def obtener_reserva(self, id_reservacion):
        """Devuelve los datos de una reservación o None si no existe."""
        resultado = consultar_reservaciones()
        for reservacion in resultado["reservaciones"]:
            if reservacion["id"] == id_reservacion:
                return reservacion
        return None

    def cerrar_aplicacion(self):
        """Libera los recursos de persistencia antes de cerrar la GUI."""
        cerrar_conexion()
