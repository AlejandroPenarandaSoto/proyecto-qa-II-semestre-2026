"""Consulta de disponibilidad de una sala: RF-08."""

import tkinter as tk
from tkinter import ttk

from src.view.selector_fecha import abrir_selector_fecha
from src.view.tema import COLOR_FONDO

HORAS = tuple(f"{hora:02d}:00" for hora in range(8, 20))


class DialogoDisponibilidad(ttk.Frame):
    """Consulta si una sala está libre sin modificar datos."""

    def __init__(self, ventana, controlador):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.sala_var = tk.StringVar()
        self.fecha_var = tk.StringVar()
        self.hora_var = tk.StringVar(value=HORAS[0])
        self.duracion_var = tk.StringVar(value="1")
        self.resultado_var = tk.StringVar(
            value="Elija la sala, la fecha y el horario, y presione Consultar."
        )
        self.pack(fill="both", expand=True)
        self._crear_contenido()
        codigos = self.controlador.obtener_codigos_salas()
        self.sala_combo.configure(values=codigos)
        if codigos:
            self.sala_var.set(codigos[0])

    def _crear_contenido(self):
        ttk.Label(self, text="Disponibilidad", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Consulte si una sala está libre. Esta consulta no crea reservaciones.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        formulario = ttk.Frame(self, style="Panel.TFrame", padding=16)
        formulario.pack(fill="x")
        for columna, texto in enumerate(("SALA", "FECHA", "HORA DE INICIO", "DURACIÓN")):
            ttk.Label(formulario, text=texto, style="Campo.TLabel").grid(
                row=0, column=columna, sticky="w", padx=(0, 10), pady=(0, 4)
            )
            formulario.columnconfigure(columna, weight=1)
        self.sala_combo = ttk.Combobox(formulario, textvariable=self.sala_var, state="readonly")
        self.sala_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        fecha = ttk.Frame(formulario, style="Panel.TFrame")
        fecha.grid(row=1, column=1, sticky="ew", padx=(0, 10))
        ttk.Entry(fecha, textvariable=self.fecha_var, state="readonly").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            fecha,
            text="Elegir",
            style="Secundario.TButton",
            command=lambda: abrir_selector_fecha(self.ventana, self.fecha_var, "Seleccionar fecha"),
        ).pack(side="left", padx=(6, 0))
        ttk.Combobox(
            formulario, textvariable=self.hora_var, values=HORAS, state="readonly"
        ).grid(row=1, column=2, sticky="ew", padx=(0, 10))
        ttk.Combobox(
            formulario, textvariable=self.duracion_var, values=("1", "2"), state="readonly"
        ).grid(row=1, column=3, sticky="ew")
        ttk.Button(
            formulario, text="Consultar", style="Primario.TButton", command=self.consultar
        ).grid(row=2, column=3, sticky="e", pady=(12, 0))

        self.etiqueta_resultado = ttk.Label(
            self, textvariable=self.resultado_var, style="Subtitulo.TLabel", wraplength=640
        )
        self.etiqueta_resultado.pack(anchor="w", pady=(16, 0))

        ttk.Button(
            self, text="Cerrar", style="Secundario.TButton", command=self.ventana.destroy
        ).pack(side="bottom", anchor="e")

    def consultar(self):
        if not self.fecha_var.get().strip():
            self.resultado_var.set("Seleccione una fecha antes de consultar.")
            return
        resultado = self.controlador.consultar_disponibilidad(
            self.sala_var.get(),
            self.fecha_var.get(),
            self.hora_var.get(),
            int(self.duracion_var.get()),
        )
        if resultado["disponible"]:
            self.resultado_var.set(f"Disponible. {resultado['motivo']}")
        else:
            self.resultado_var.set(f"No disponible. {resultado['motivo']}")


def abrir_dialogo_disponibilidad(parent, controlador):
    """Abre la consulta modal de disponibilidad."""
    ventana = tk.Toplevel(parent)
    ventana.title("Disponibilidad")
    ventana.geometry("820x380")
    ventana.minsize(720, 340)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    DialogoDisponibilidad(ventana, controlador)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
