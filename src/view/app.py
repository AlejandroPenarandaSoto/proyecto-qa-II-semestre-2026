"""Interfaz gráfica principal del sistema de reservaciones."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.controller.controller import ControladorAplicacion

COLOR_FONDO = "#F4F7FB"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARIO = "#1F5AA6"
COLOR_TEXTO = "#172033"
COLOR_SECUNDARIO = "#5E6B7C"


class Aplicacion(tk.Tk):
    """Ventana principal y contenedor del panel RF-15."""

    def __init__(self, controlador=None):
        super().__init__()
        self.controlador = controlador or ControladorAplicacion()

        self.title("Sistema de reservación de salas")
        self.geometry("1240x820")
        self.minsize(1024, 700)
        self.configure(background=COLOR_FONDO)

        self._configurar_estilos()
        self.panel = PanelControl(self, self.controlador)
        self.panel.pack(fill="both", expand=True)

    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Fondo.TFrame", background=COLOR_FONDO)
        estilo.configure("Panel.TFrame", background=COLOR_PANEL)
        estilo.configure(
            "Titulo.TLabel",
            background=COLOR_FONDO,
            foreground=COLOR_TEXTO,
            font=("TkDefaultFont", 22, "bold"),
        )
        estilo.configure(
            "Subtitulo.TLabel",
            background=COLOR_FONDO,
            foreground=COLOR_SECUNDARIO,
            font=("TkDefaultFont", 11),
        )
        estilo.configure(
            "Seccion.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            font=("TkDefaultFont", 12, "bold"),
        )
        estilo.configure(
            "Resumen.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_PRIMARIO,
            font=("TkDefaultFont", 18, "bold"),
        )
        estilo.configure(
            "Primario.TButton",
            background=COLOR_PRIMARIO,
            foreground="#FFFFFF",
            padding=(14, 8),
        )
        estilo.map(
            "Primario.TButton",
            background=[("active", "#17457F")],
        )
        estilo.configure("Treeview", rowheight=27)
        estilo.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))


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

    def __init__(self, parent, controlador):
        super().__init__(parent, style="Fondo.TFrame", padding=24)
        self.controlador = controlador
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

        ttk.Label(contenedor, text="Fecha (AAAA-MM-DD):").grid(
            row=1,
            column=0,
            sticky="w",
        )
        ttk.Entry(contenedor, textvariable=self.fecha_var, width=16).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(0, 12),
        )

        ttk.Label(contenedor, text="Sala:").grid(row=1, column=1, sticky="w")
        self.sala_combo = ttk.Combobox(
            contenedor,
            textvariable=self.sala_var,
            state="readonly",
            width=14,
        )
        self.sala_combo.grid(row=2, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(contenedor, text="Estado:").grid(row=1, column=2, sticky="w")
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
            tarjeta = ttk.Frame(contenedor, style="Panel.TFrame", padding=16)
            tarjeta.grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=(0 if columna == 0 else 6, 0 if columna == 2 else 6),
            )
            ttk.Label(tarjeta, text=titulo, style="Seccion.TLabel").pack(anchor="w")
            ttk.Label(tarjeta, textvariable=variable, style="Resumen.TLabel").pack(
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
            style="Seccion.TLabel",
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
        for reserva in reservaciones:
            tabla.insert(
                "",
                "end",
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
        for sala in salas:
            self.tabla_ocupacion.insert(
                "",
                "end",
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
