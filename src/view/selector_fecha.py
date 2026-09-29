"""Selector de fecha reutilizable construido únicamente con Tkinter."""

import calendar
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk

from src.view.tema import COLOR_FONDO

MESES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)
DIAS_SEMANA = ("L", "M", "X", "J", "V", "S", "D")


def construir_matriz_mes(anio, mes):
    """Devuelve seis semanas, iniciando en lunes, para una cuadrícula estable."""
    semanas = calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(
        anio,
        mes,
    )
    while len(semanas) < 6:
        semanas.append([0] * 7)
    return semanas


def sumar_meses(anio, mes, desplazamiento):
    """Calcula un mes anterior o posterior respetando cambios de año."""
    indice = (anio * 12) + (mes - 1) + desplazamiento
    nuevo_anio, indice_mes = divmod(indice, 12)
    return nuevo_anio, indice_mes + 1


def _fecha_inicial(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return date.today()


class SelectorFecha(ttk.Frame):
    """Calendario mensual que devuelve una fecha ISO mediante callback."""

    def __init__(self, ventana, valor_inicial, al_seleccionar):
        super().__init__(ventana, style="Fondo.TFrame", padding=18)
        self.ventana = ventana
        self.al_seleccionar = al_seleccionar
        self.seleccionada = _fecha_inicial(valor_inicial)
        self.anio_visible = self.seleccionada.year
        self.mes_visible = self.seleccionada.month
        self.titulo_var = tk.StringVar()
        self.pack(fill="both", expand=True)
        self._crear_contenido()
        self._dibujar_mes()

    def _crear_contenido(self):
        navegacion = ttk.Frame(self, style="Panel.TFrame", padding=10)
        navegacion.pack(fill="x", pady=(0, 10))
        ttk.Button(
            navegacion,
            text="‹",
            style="CalendarioNavegacion.TButton",
            command=lambda: self._cambiar_mes(-1),
        ).pack(side="left")
        ttk.Label(
            navegacion,
            textvariable=self.titulo_var,
            style="CalendarioTitulo.TLabel",
        ).pack(side="left", expand=True)
        ttk.Button(
            navegacion,
            text="›",
            style="CalendarioNavegacion.TButton",
            command=lambda: self._cambiar_mes(1),
        ).pack(side="right")

        self.cuadricula = ttk.Frame(self, style="Panel.TFrame", padding=10)
        self.cuadricula.pack(fill="both", expand=True)
        for columna, nombre in enumerate(DIAS_SEMANA):
            ttk.Label(
                self.cuadricula,
                text=nombre,
                style="CalendarioDiaSemana.TLabel",
                anchor="center",
            ).grid(row=0, column=columna, sticky="nsew", pady=(0, 5))
            self.cuadricula.columnconfigure(columna, weight=1)

        ttk.Button(
            self,
            text="Hoy",
            style="Secundario.TButton",
            command=lambda: self._elegir_fecha(date.today()),
        ).pack(pady=(10, 0))

    def _dibujar_mes(self):
        self.titulo_var.set(
            f"{MESES[self.mes_visible - 1]} {self.anio_visible}"
        )
        for widget in self.cuadricula.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        for fila, semana in enumerate(
            construir_matriz_mes(self.anio_visible, self.mes_visible),
            start=1,
        ):
            self.cuadricula.rowconfigure(fila, weight=1)
            for columna, dia in enumerate(semana):
                if dia == 0:
                    ttk.Label(
                        self.cuadricula,
                        text="",
                        style="Panel.TLabel",
                    ).grid(row=fila, column=columna, sticky="nsew", padx=2, pady=2)
                    continue

                fecha = date(self.anio_visible, self.mes_visible, dia)
                estilo = (
                    "CalendarioSeleccionado.TButton"
                    if fecha == self.seleccionada
                    else "Calendario.TButton"
                )
                ttk.Button(
                    self.cuadricula,
                    text=str(dia),
                    width=3,
                    style=estilo,
                    command=lambda valor=fecha: self._elegir_fecha(valor),
                ).grid(row=fila, column=columna, sticky="nsew", padx=2, pady=2)

    def _cambiar_mes(self, desplazamiento):
        self.anio_visible, self.mes_visible = sumar_meses(
            self.anio_visible,
            self.mes_visible,
            desplazamiento,
        )
        self._dibujar_mes()

    def _elegir_fecha(self, valor):
        self.al_seleccionar(valor.strftime("%Y-%m-%d"))
        self.ventana.destroy()


def abrir_selector_fecha(parent, variable, titulo):
    """Abre el calendario modal y escribe la selección en una StringVar."""
    ventana = tk.Toplevel(parent)
    ventana.title(titulo)
    ventana.geometry("410x430")
    ventana.resizable(False, False)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    SelectorFecha(ventana, variable.get(), variable.set)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
