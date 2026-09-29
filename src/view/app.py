"""Interfaz gráfica principal del sistema de reservaciones."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.controller.controller import ControladorAplicacion
from src.view.tema import (
    COLOR_ACENTO,
    COLOR_FILA_ALTERNA,
    COLOR_FONDO,
    cargar_logo,
    configurar_estilos,
)


class Aplicacion(tk.Tk):
    """Ventana principal y contenedor del panel RF-15."""

    def __init__(self, controlador=None):
        super().__init__()
        self.controlador = controlador or ControladorAplicacion()
        self._hay_cambios_pendientes = False

        self.title("TEC Room Manager")
        self.geometry("1280x840")
        self.minsize(1024, 700)
        self.configure(background=COLOR_FONDO)

        configurar_estilos(self)
        self.logo_marca = cargar_logo(self)
        self.iconphoto(True, self.logo_marca)
        self._crear_menu()
        self.protocol("WM_DELETE_WINDOW", self.solicitar_salida)
        self.panel = PanelControl(
            self,
            self.controlador,
            self.logo_marca,
            self.solicitar_salida,
        )
        self.panel.pack(fill="both", expand=True)

    def _crear_menu(self):
        barra_menu = tk.Menu(self)
        menu_archivo = tk.Menu(barra_menu, tearoff=False)
        es_macos = self.tk.call("tk", "windowingsystem") == "aqua"
        menu_archivo.add_command(
            label="Salir",
            accelerator="⌘Q" if es_macos else "Ctrl+Q",
            command=self.solicitar_salida,
        )
        barra_menu.add_cascade(label="Archivo", menu=menu_archivo)
        self.configure(menu=barra_menu)

        self.bind_all("<Command-q>", self.solicitar_salida)
        self.bind_all("<Control-q>", self.solicitar_salida)

    def marcar_cambios_pendientes(self, hay_cambios=True):
        """Permite a los formularios informar que tienen datos sin guardar."""
        self._hay_cambios_pendientes = bool(hay_cambios)

    def solicitar_salida(self, _evento=None):
        """Confirma cambios pendientes y libera recursos antes de salir."""
        if self._hay_cambios_pendientes:
            confirmar = messagebox.askyesno(
                "Cambios sin guardar",
                (
                    "Hay cambios pendientes que se perderán al salir.\n\n"
                    "¿Desea cerrar la aplicación?"
                ),
                parent=self,
            )
            if not confirmar:
                return False

        self.controlador.cerrar_aplicacion()
        self.destroy()
        return True


class PanelControl(ttk.Frame):
    """Presenta los datos consolidados y filtros combinables de RF-15."""

    COLUMNAS_RESERVACION = (
        ("id", "ID", 75),
        ("estudiante", "Estudiante", 170),
        ("sala", "Sala", 75),
        ("fecha", "Fecha", 100),
        ("horario", "Horario", 120),
        ("personas", "Personas", 80),
        ("estado", "Estado", 90),
    )

    def __init__(self, parent, controlador, logo, al_salir):
        super().__init__(parent, style="Fondo.TFrame", padding=20)
        self.controlador = controlador
        self.logo = logo
        self.al_salir = al_salir
        self.fecha_var = tk.StringVar()
        self.sala_var = tk.StringVar(value="Todas")
        self.estado_var = tk.StringVar(value="Todos")
        self.mensaje_var = tk.StringVar()
        self.total_hoy_var = tk.StringVar(value="0")
        self.total_proximas_var = tk.StringVar(value="0")
        self.total_salas_var = tk.StringVar(value="0")

        self._crear_encabezado()
        self._crear_filtros()
        self._crear_resumen()
        self._crear_contenido()
        self._cargar_salas()
        self.refrescar_panel()

    def _crear_encabezado(self):
        cabecera = ttk.Frame(
            self,
            style="Encabezado.TFrame",
            padding=(18, 12),
        )
        cabecera.pack(fill="x", pady=(0, 18))
        ttk.Button(
            cabecera,
            text="Salir",
            style="Cabecera.TButton",
            command=self.al_salir,
        ).pack(side="right", padx=(16, 0))
        ttk.Label(
            cabecera,
            image=self.logo,
            style="Encabezado.TLabel",
        ).pack(side="left", padx=(0, 16))

        identidad = ttk.Frame(cabecera, style="Encabezado.TFrame")
        identidad.pack(side="left", anchor="center")
        ttk.Label(
            identidad,
            text="TEC ROOM MANAGER",
            style="Marca.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            identidad,
            text="Reservación de espacios académicos",
            style="MarcaDetalle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        ttk.Label(
            self,
            text="Panel de control",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Ocupación por sala, reservaciones del día y próximos "
                "compromisos."
            ),
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 18))

    def _crear_filtros(self):
        contenedor = ttk.Frame(self, style="Panel.TFrame", padding=16)
        contenedor.pack(fill="x", pady=(0, 14))

        ttk.Label(
            contenedor,
            text="Filtros de reservaciones",
            style="Seccion.TLabel",
        ).grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 10))

        ttk.Label(
            contenedor,
            text="FECHA (AAAA-MM-DD)",
            style="Campo.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Entry(contenedor, textvariable=self.fecha_var, width=16).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(0, 12),
        )

        ttk.Label(
            contenedor,
            text="SALA",
            style="Campo.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=(0, 4))
        self.sala_combo = ttk.Combobox(
            contenedor,
            textvariable=self.sala_var,
            state="readonly",
            width=14,
        )
        self.sala_combo.grid(row=2, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(
            contenedor,
            text="ESTADO",
            style="Campo.TLabel",
        ).grid(row=1, column=2, sticky="w", pady=(0, 4))
        ttk.Combobox(
            contenedor,
            textvariable=self.estado_var,
            values=("Todos", "Activa", "Cancelada"),
            state="readonly",
            width=14,
        ).grid(row=2, column=2, sticky="ew", padx=(0, 16))

        ttk.Button(
            contenedor,
            text="Aplicar filtros",
            style="Primario.TButton",
            command=self.refrescar_panel,
        ).grid(row=2, column=3, padx=(0, 8))
        ttk.Button(
            contenedor,
            text="Limpiar",
            style="Secundario.TButton",
            command=self._limpiar_filtros,
        ).grid(row=2, column=4)

        contenedor.columnconfigure(0, weight=1)
        contenedor.columnconfigure(1, weight=1)
        contenedor.columnconfigure(2, weight=1)

    def _crear_resumen(self):
        contenedor = ttk.Frame(self, style="Fondo.TFrame")
        contenedor.pack(fill="x", pady=(0, 14))

        tarjetas = (
            ("Salas", self.total_salas_var),
            ("Reservaciones de hoy", self.total_hoy_var),
            ("Próximas activas", self.total_proximas_var),
        )
        for columna, (titulo, variable) in enumerate(tarjetas):
            tarjeta = ttk.Frame(contenedor, style="Panel.TFrame", padding=14)
            tarjeta.grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=(0 if columna == 0 else 6, 0 if columna == 2 else 6),
            )
            tk.Frame(tarjeta, background=COLOR_ACENTO, width=4).pack(
                side="left",
                fill="y",
                padx=(0, 12),
            )
            contenido = ttk.Frame(tarjeta, style="Panel.TFrame")
            contenido.pack(side="left", fill="both", expand=True)
            ttk.Label(contenido, text=titulo, style="Seccion.TLabel").pack(
                anchor="w"
            )
            ttk.Label(contenido, textvariable=variable, style="Resumen.TLabel").pack(
                anchor="w",
                pady=(4, 0),
            )
            contenedor.columnconfigure(columna, weight=1)

    def _crear_contenido(self):
        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True)

        resultados = ttk.Frame(cuaderno, style="Panel.TFrame", padding=12)
        ocupacion = ttk.Frame(cuaderno, style="Panel.TFrame", padding=12)
        hoy = ttk.Frame(cuaderno, style="Panel.TFrame", padding=12)
        proximas = ttk.Frame(cuaderno, style="Panel.TFrame", padding=12)
        cuaderno.add(resultados, text="Resultados")
        cuaderno.add(ocupacion, text="Ocupación por sala")
        cuaderno.add(hoy, text="Hoy")
        cuaderno.add(proximas, text="Próximas")

        self.tabla_resultados = self._crear_tabla_reservaciones(resultados)
        self.tabla_hoy = self._crear_tabla_reservaciones(hoy)
        self.tabla_proximas = self._crear_tabla_reservaciones(proximas)
        self.tabla_ocupacion = self._crear_tabla_ocupacion(ocupacion)

        self.estado_vacio = ttk.Label(
            resultados,
            textvariable=self.mensaje_var,
            style="Vacio.TLabel",
        )
        self.estado_vacio.pack(pady=10)

    def _crear_tabla_reservaciones(self, parent):
        contenedor = ttk.Frame(parent, style="Panel.TFrame")
        contenedor.pack(fill="both", expand=True)
        tabla = ttk.Treeview(
            contenedor,
            columns=[columna[0] for columna in self.COLUMNAS_RESERVACION],
            show="headings",
        )
        desplazamiento = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=tabla.yview,
        )
        tabla.configure(yscrollcommand=desplazamiento.set)
        tabla.tag_configure("alterna", background=COLOR_FILA_ALTERNA)
        for identificador, titulo, ancho in self.COLUMNAS_RESERVACION:
            tabla.heading(identificador, text=titulo)
            tabla.column(identificador, width=ancho, anchor="center")
        tabla.column("estudiante", anchor="w")
        tabla.pack(side="left", fill="both", expand=True)
        desplazamiento.pack(side="right", fill="y")
        return tabla

    def _crear_tabla_ocupacion(self, parent):
        columnas = (
            ("codigo", "Sala", 80),
            ("nombre", "Nombre", 230),
            ("estado", "Estado", 130),
            ("reservaciones", "Reservas activas", 120),
            ("horas", "Horas reservadas", 120),
            ("personas", "Personas", 90),
        )
        contenedor = ttk.Frame(parent, style="Panel.TFrame")
        contenedor.pack(fill="both", expand=True)
        tabla = ttk.Treeview(
            contenedor,
            columns=[columna[0] for columna in columnas],
            show="headings",
        )
        desplazamiento = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=tabla.yview,
        )
        tabla.configure(yscrollcommand=desplazamiento.set)
        tabla.tag_configure("alterna", background=COLOR_FILA_ALTERNA)
        for identificador, titulo, ancho in columnas:
            tabla.heading(identificador, text=titulo)
            tabla.column(identificador, width=ancho, anchor="center")
        tabla.column("nombre", anchor="w")
        tabla.pack(side="left", fill="both", expand=True)
        desplazamiento.pack(side="right", fill="y")
        return tabla

    def _cargar_salas(self):
        codigos = self.controlador.obtener_codigos_salas()
        self.sala_combo.configure(values=("Todas", *codigos))

    def _limpiar_filtros(self):
        self.fecha_var.set("")
        self.sala_var.set("Todas")
        self.estado_var.set("Todos")
        self.refrescar_panel()

    def refrescar_panel(self):
        """Recarga todos los datos; se invoca tras cada operación."""
        resultado = self.controlador.obtener_panel(
            fecha=self.fecha_var.get().strip() or None,
            codigo_sala=self._valor_filtro(self.sala_var.get(), "Todas"),
            estado=self._valor_filtro(self.estado_var.get(), "Todos"),
        )
        if not resultado["exito"]:
            messagebox.showerror("No fue posible cargar el panel", resultado["mensaje"])
            return

        self._llenar_reservaciones(
            self.tabla_resultados,
            resultado["resultados"],
        )
        self._llenar_reservaciones(
            self.tabla_hoy,
            resultado["reservaciones_hoy"],
        )
        self._llenar_reservaciones(
            self.tabla_proximas,
            resultado["proximas_reservaciones"],
        )
        self._llenar_ocupacion(resultado["ocupacion_salas"])

        self.total_salas_var.set(str(len(resultado["ocupacion_salas"])))
        self.total_hoy_var.set(str(len(resultado["reservaciones_hoy"])))
        self.total_proximas_var.set(str(len(resultado["proximas_reservaciones"])))
        self.mensaje_var.set(
            "" if resultado["resultados"] else resultado["mensaje"]
        )

    def _llenar_reservaciones(self, tabla, reservaciones):
        self._vaciar_tabla(tabla)
        for indice, reserva in enumerate(reservaciones):
            tabla.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(
                    reserva["id"],
                    reserva["estudiante"],
                    reserva["sala"],
                    reserva["fecha"],
                    f"{reserva['hora_inicio']} - {reserva['hora_fin']}",
                    reserva["cantidad_personas"],
                    reserva["estado"],
                ),
            )

    def _llenar_ocupacion(self, salas):
        self._vaciar_tabla(self.tabla_ocupacion)
        for indice, sala in enumerate(salas):
            self.tabla_ocupacion.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(
                    sala["codigo"],
                    sala["nombre"],
                    sala["estado"],
                    sala["reservaciones_activas"],
                    sala["horas_reservadas"],
                    sala["personas_reservadas"],
                ),
            )

    @staticmethod
    def _vaciar_tabla(tabla):
        elementos = tabla.get_children()
        if elementos:
            tabla.delete(*elementos)

    @staticmethod
    def _valor_filtro(valor, opcion_todas):
        return None if valor == opcion_todas else valor


def iniciar_aplicacion():
    """Crea la ventana y comienza el ciclo de eventos de Tkinter."""
    aplicacion = Aplicacion()
    aplicacion.mainloop()
