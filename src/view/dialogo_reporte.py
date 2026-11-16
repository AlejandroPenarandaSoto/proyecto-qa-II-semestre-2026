"""Diálogo de presentación para generar el reporte CSV de RF-16."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.view.selector_fecha import abrir_selector_fecha
from src.view.tema import COLOR_FONDO


class DialogoReporte(ttk.Frame):
    """Solicita el rango y delega la validación y exportación al controlador."""

    def __init__(self, ventana, controlador):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.fecha_inicio_var = tk.StringVar()
        self.fecha_fin_var = tk.StringVar()
        self.pack(fill="both", expand=True)
        self._crear_contenido()

    def _crear_contenido(self):
        ttk.Label(
            self,
            text="Generar reporte CSV",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            self,
            text="Seleccione el rango inclusivo de reservaciones que desea exportar.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 18))

        formulario = ttk.Frame(self, style="Panel.TFrame", padding=18)
        formulario.pack(fill="x")
        ttk.Label(
            formulario,
            text="FECHA INICIAL (AAAA-MM-DD)",
            style="Campo.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Label(
            formulario,
            text="FECHA FINAL (AAAA-MM-DD)",
            style="Campo.TLabel",
        ).grid(row=0, column=1, sticky="w", pady=(0, 5))
        campo_inicio = ttk.Frame(formulario, style="Panel.TFrame")
        campo_inicio.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Entry(
            campo_inicio,
            textvariable=self.fecha_inicio_var,
            state="readonly",
            width=22,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            campo_inicio,
            text="Elegir fecha",
            style="Secundario.TButton",
            command=lambda: abrir_selector_fecha(
                self.ventana,
                self.fecha_inicio_var,
                "Seleccionar fecha inicial",
            ),
        ).pack(side="left", padx=(6, 0))

        campo_fin = ttk.Frame(formulario, style="Panel.TFrame")
        campo_fin.grid(row=1, column=1, sticky="ew")
        ttk.Entry(
            campo_fin,
            textvariable=self.fecha_fin_var,
            state="readonly",
            width=22,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            campo_fin,
            text="Elegir fecha",
            style="Secundario.TButton",
            command=lambda: abrir_selector_fecha(
                self.ventana,
                self.fecha_fin_var,
                "Seleccionar fecha final",
            ),
        ).pack(side="left", padx=(6, 0))
        formulario.columnconfigure(0, weight=1)
        formulario.columnconfigure(1, weight=1)

        acciones = ttk.Frame(self, style="Fondo.TFrame")
        acciones.pack(fill="x", pady=(18, 0))
        ttk.Button(
            acciones,
            text="Cancelar",
            style="Secundario.TButton",
            command=self.ventana.destroy,
        ).pack(side="right")
        ttk.Button(
            acciones,
            text="Seleccionar ubicación y generar",
            style="Primario.TButton",
            command=self.generar,
        ).pack(side="right", padx=(0, 8))

    def generar(self):
        fecha_inicio = self.fecha_inicio_var.get().strip()
        fecha_fin = self.fecha_fin_var.get().strip()
        validacion = self.controlador.validar_rango_reporte(
            fecha_inicio,
            fecha_fin,
        )
        if not validacion["exito"]:
            messagebox.showerror(
                "Rango de fechas inválido",
                validacion["mensaje"],
                parent=self.ventana,
            )
            return

        ruta_destino = filedialog.asksaveasfilename(
            parent=self.ventana,
            title="Guardar reporte de reservaciones",
            defaultextension=".csv",
            initialfile="reporte_reservaciones.csv",
            filetypes=(("Archivo CSV", "*.csv"),),
        )
        resultado = self.controlador.generar_reporte(
            fecha_inicio,
            fecha_fin,
            ruta_destino or None,
        )
        if resultado.get("cancelado"):
            return
        if not resultado["exito"]:
            messagebox.showerror(
                "No fue posible generar el reporte",
                resultado["mensaje"],
                parent=self.ventana,
            )
            return

        messagebox.showinfo(
            "Reporte generado",
            (
                f"El archivo se creó correctamente con "
                f"{resultado['cantidad']} reservaciones.\n\n"
                f"{resultado['ruta']}"
            ),
            parent=self.ventana,
        )
        self.ventana.destroy()


def abrir_dialogo_reporte(parent, controlador):
    """Crea una ventana modal para RF-16."""
    ventana = tk.Toplevel(parent)
    ventana.title("Generar reporte CSV")
    ventana.geometry("760x310")
    ventana.resizable(False, False)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    DialogoReporte(ventana, controlador)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
