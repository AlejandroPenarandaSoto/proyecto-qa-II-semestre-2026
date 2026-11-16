"""Creación y modificación de una reservación individual: RF-05 y RF-13."""

import tkinter as tk
from tkinter import messagebox, ttk

from src.view.selector_fecha import abrir_selector_fecha
from src.view.tema import COLOR_FONDO

HORAS = tuple(f"{hora:02d}:00" for hora in range(8, 20))


class DialogoReservacion(ttk.Frame):
    """Captura los datos de una reservación; las reglas las valida el modelo."""

    def __init__(
        self,
        ventana,
        controlador,
        al_completar,
        al_cambiar_pendientes,
        reservacion=None,
    ):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.al_completar = al_completar
        self.al_cambiar_pendientes = al_cambiar_pendientes
        self.reservacion = reservacion
        self._tiene_cambios = False

        datos = reservacion or {}
        self.carne_var = tk.StringVar(value=datos.get("carne", ""))
        self.sala_var = tk.StringVar(value=datos.get("sala", ""))
        self.fecha_var = tk.StringVar(value=datos.get("fecha", ""))
        self.hora_var = tk.StringVar(value=datos.get("hora_inicio", HORAS[0]))
        self.duracion_var = tk.StringVar(value=str(datos.get("duracion_horas", 1)))
        self.personas_var = tk.StringVar(value=str(datos.get("cantidad_personas", 1)))

        self.pack(fill="both", expand=True)
        self._crear_contenido()
        codigos = self.controlador.obtener_codigos_salas()
        self.sala_combo.configure(values=codigos)
        if not self.sala_var.get() and codigos:
            self.sala_var.set(codigos[0])
        for variable in (
            self.carne_var,
            self.sala_var,
            self.fecha_var,
            self.hora_var,
            self.duracion_var,
            self.personas_var,
        ):
            variable.trace_add("write", self._marcar_cambios)

    @property
    def es_modificacion(self):
        return self.reservacion is not None

    def _crear_contenido(self):
        titulo = (
            f"Modificar reservación {self.reservacion['id']}"
            if self.es_modificacion
            else "Nueva reservación"
        )
        ttk.Label(self, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Se guardará solo si cumple las reglas de horario, capacidad, "
                "estado de la sala y límite de reservaciones."
            ),
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        formulario = ttk.Frame(self, style="Panel.TFrame", padding=16)
        formulario.pack(fill="x")
        for columna in range(3):
            formulario.columnconfigure(columna, weight=1)

        self._etiqueta(formulario, "CARNÉ", 0, 0)
        ttk.Entry(
            formulario,
            textvariable=self.carne_var,
            state="readonly" if self.es_modificacion else "normal",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 10))

        self._etiqueta(formulario, "SALA", 0, 1)
        self.sala_combo = ttk.Combobox(formulario, textvariable=self.sala_var, state="readonly")
        self.sala_combo.grid(row=1, column=1, sticky="ew", padx=(0, 10))

        self._etiqueta(formulario, "FECHA", 0, 2)
        fecha = ttk.Frame(formulario, style="Panel.TFrame")
        fecha.grid(row=1, column=2, sticky="ew")
        ttk.Entry(fecha, textvariable=self.fecha_var, state="readonly").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            fecha,
            text="Elegir",
            style="Secundario.TButton",
            command=lambda: abrir_selector_fecha(self.ventana, self.fecha_var, "Seleccionar fecha"),
        ).pack(side="left", padx=(6, 0))

        self._etiqueta(formulario, "HORA DE INICIO", 2, 0)
        ttk.Combobox(
            formulario, textvariable=self.hora_var, values=HORAS, state="readonly"
        ).grid(row=3, column=0, sticky="ew", padx=(0, 10))
        self._etiqueta(formulario, "DURACIÓN", 2, 1)
        ttk.Combobox(
            formulario, textvariable=self.duracion_var, values=("1", "2"), state="readonly"
        ).grid(row=3, column=1, sticky="ew", padx=(0, 10))
        self._etiqueta(formulario, "PERSONAS", 2, 2)
        ttk.Spinbox(
            formulario, textvariable=self.personas_var, from_=1, to=100, increment=1
        ).grid(row=3, column=2, sticky="ew")

        acciones = ttk.Frame(self, style="Fondo.TFrame")
        acciones.pack(fill="x", side="bottom", pady=(16, 0))
        ttk.Button(
            acciones, text="Cancelar", style="Secundario.TButton", command=self.cancelar
        ).pack(side="right")
        ttk.Button(
            acciones,
            text="Guardar cambios" if self.es_modificacion else "Crear reservación",
            style="Primario.TButton",
            command=self.guardar,
        ).pack(side="right", padx=(0, 8))

    @staticmethod
    def _etiqueta(parent, texto, fila, columna):
        ttk.Label(parent, text=texto, style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(0 if fila == 0 else 14, 4),
        )

    def _marcar_cambios(self, *_argumentos):
        self._tiene_cambios = True
        self.al_cambiar_pendientes(True)

    def _datos_formulario(self):
        try:
            duracion = int(self.duracion_var.get())
            personas = int(str(self.personas_var.get()).strip())
        except ValueError:
            return None, "La duración y la cantidad de personas deben ser números enteros."
        return {
            "codigo_sala": self.sala_var.get().strip(),
            "fecha": self.fecha_var.get().strip(),
            "hora_inicio": self.hora_var.get().strip(),
            "duracion": duracion,
            "cantidad_personas": personas,
        }, None

    def guardar(self):
        datos, error = self._datos_formulario()
        if error:
            messagebox.showerror("Datos inválidos", error, parent=self.ventana)
            return
        if self.es_modificacion:
            resultado = self.controlador.modificar_reserva(self.reservacion["id"], **datos)
        else:
            resultado = self.controlador.crear_reserva(carne=self.carne_var.get().strip(), **datos)
        if not resultado["exito"]:
            messagebox.showerror(
                "No fue posible guardar la reservación",
                resultado["mensaje"],
                parent=self.ventana,
            )
            return
        self._tiene_cambios = False
        self.al_cambiar_pendientes(False)
        self.al_completar()
        messagebox.showinfo("Reservación guardada", resultado["mensaje"], parent=self.ventana)
        self.ventana.destroy()

    def cancelar(self):
        if self._tiene_cambios and not messagebox.askyesno(
            "Descartar cambios",
            "¿Desea cerrar el formulario y descartar los datos ingresados?",
            parent=self.ventana,
        ):
            return
        self.al_cambiar_pendientes(False)
        self.ventana.destroy()


def abrir_dialogo_reservacion(
    parent,
    controlador,
    al_completar,
    al_cambiar_pendientes,
    reservacion=None,
):
    """Abre el formulario modal para crear o modificar una reservación."""
    ventana = tk.Toplevel(parent)
    ventana.title("Modificar reservación" if reservacion else "Nueva reservación")
    ventana.geometry("820x400")
    ventana.minsize(720, 360)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    dialogo = DialogoReservacion(
        ventana, controlador, al_completar, al_cambiar_pendientes, reservacion
    )
    ventana.protocol("WM_DELETE_WINDOW", dialogo.cancelar)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
