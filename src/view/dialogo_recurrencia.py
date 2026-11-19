"""Formulario y vista previa de reservaciones recurrentes RF-14."""

import tkinter as tk
from tkinter import messagebox, ttk

from src.view.selector_fecha import abrir_selector_fecha
from src.view.tema import COLOR_FONDO


class DialogoRecurrencia(ttk.Frame):
    """Coordina la captura y presentación sin contener reglas de negocio."""

    def __init__(
        self,
        ventana,
        controlador,
        al_completar,
        al_cambiar_pendientes,
    ):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.al_completar = al_completar
        self.al_cambiar_pendientes = al_cambiar_pendientes
        self._tiene_cambios = False

        self.carne_var = tk.StringVar()
        self.sala_var = tk.StringVar()
        self.fecha_var = tk.StringVar()
        self.hora_var = tk.StringVar(value="08:00")
        self.duracion_var = tk.StringVar(value="1")
        self.personas_var = tk.StringVar(value="1")
        self.semanas_var = tk.StringVar(value="2")
        self.mensaje_var = tk.StringVar(
            value="Complete los datos y genere una vista previa."
        )

        self.pack(fill="both", expand=True)
        self._crear_contenido()
        self._cargar_salas()
        self._observar_cambios()

    def _crear_contenido(self):
        ttk.Label(
            self,
            text="Nueva reservación recurrente",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Configure entre 2 y 8 semanas. La serie se guardará únicamente "
                "si todas las ocurrencias son válidas."
            ),
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        formulario = ttk.Frame(self, style="Panel.TFrame", padding=16)
        formulario.pack(fill="x", pady=(0, 14))
        self._crear_campo_texto(formulario, "CARNÉ", self.carne_var, 0, 0)
        self._crear_campo_sala(formulario, 0, 1)
        self._crear_campo_fecha(formulario, 0, 2)
        self._crear_campo_hora(formulario, 2, 0)
        self._crear_campo_duracion(formulario, 2, 1)
        self._crear_campo_personas(formulario, 2, 2)
        self._crear_campo_semanas(formulario, 4, 0)
        for columna in range(3):
            formulario.columnconfigure(columna, weight=1)

        ttk.Button(
            formulario,
            text="Previsualizar serie",
            style="Primario.TButton",
            command=self.previsualizar,
        ).grid(row=5, column=2, sticky="e", pady=(12, 0))

        vista = ttk.Frame(self, style="Panel.TFrame", padding=12)
        vista.pack(fill="both", expand=True)
        columnas = (
            ("numero", "Semana", 80),
            ("fecha", "Fecha", 120),
            ("estado", "Disponibilidad", 130),
            ("mensaje", "Detalle", 480),
        )
        self.tabla = ttk.Treeview(
            vista,
            columns=[columna[0] for columna in columnas],
            show="headings",
            selectmode="none",
        )
        barra = ttk.Scrollbar(vista, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        for identificador, titulo, ancho in columnas:
            self.tabla.heading(identificador, text=titulo)
            self.tabla.column(
                identificador,
                width=ancho,
                anchor="w" if identificador == "mensaje" else "center",
            )
        self.tabla.tag_configure("disponible", background="#E8F7F4")
        self.tabla.tag_configure("conflicto", background="#FCEBEC")
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        acciones = ttk.Frame(self, style="Fondo.TFrame")
        acciones.pack(fill="x", pady=(12, 0))
        ttk.Label(
            acciones,
            textvariable=self.mensaje_var,
            style="Subtitulo.TLabel",
        ).pack(side="left")
        ttk.Button(
            acciones,
            text="Cancelar",
            style="Secundario.TButton",
            command=self.cancelar,
        ).pack(side="right")
        self.boton_crear = ttk.Button(
            acciones,
            text="Crear serie",
            style="Primario.TButton",
            command=self.crear,
            state="disabled",
        )
        self.boton_crear.pack(side="right", padx=(0, 8))

    def _crear_campo_texto(self, parent, etiqueta, variable, fila, columna):
        ttk.Label(parent, text=etiqueta, style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(0, 4),
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=fila + 1,
            column=columna,
            sticky="ew",
            padx=(0, 10),
        )

    def _crear_campo_sala(self, parent, fila, columna):
        ttk.Label(parent, text="SALA", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(0, 4),
        )
        self.sala_combo = ttk.Combobox(
            parent,
            textvariable=self.sala_var,
            state="readonly",
        )
        self.sala_combo.grid(
            row=fila + 1,
            column=columna,
            sticky="ew",
            padx=(0, 10),
        )

    def _crear_campo_fecha(self, parent, fila, columna):
        ttk.Label(parent, text="FECHA INICIAL", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            pady=(0, 4),
        )
        contenedor = ttk.Frame(parent, style="Panel.TFrame")
        contenedor.grid(row=fila + 1, column=columna, sticky="ew")
        ttk.Entry(
            contenedor,
            textvariable=self.fecha_var,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            contenedor,
            text="Elegir",
            style="Secundario.TButton",
            command=lambda: abrir_selector_fecha(
                self.ventana,
                self.fecha_var,
                "Seleccionar fecha inicial",
            ),
        ).pack(side="left", padx=(6, 0))

    def _crear_campo_hora(self, parent, fila, columna):
        ttk.Label(parent, text="HORA DE INICIO", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(14, 4),
        )
        ttk.Combobox(
            parent,
            textvariable=self.hora_var,
            values=tuple(f"{hora:02d}:00" for hora in range(8, 20)),
            state="readonly",
        ).grid(row=fila + 1, column=columna, sticky="ew", padx=(0, 10))

    def _crear_campo_duracion(self, parent, fila, columna):
        ttk.Label(parent, text="DURACIÓN", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(14, 4),
        )
        ttk.Combobox(
            parent,
            textvariable=self.duracion_var,
            values=("1", "2"),
            state="readonly",
        ).grid(row=fila + 1, column=columna, sticky="ew", padx=(0, 10))

    def _crear_campo_personas(self, parent, fila, columna):
        ttk.Label(parent, text="PERSONAS", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            pady=(14, 4),
        )
        ttk.Spinbox(
            parent,
            textvariable=self.personas_var,
            from_=1,
            to=100,
            increment=1,
        ).grid(row=fila + 1, column=columna, sticky="ew")

    def _crear_campo_semanas(self, parent, fila, columna):
        ttk.Label(parent, text="SEMANAS", style="Campo.TLabel").grid(
            row=fila,
            column=columna,
            sticky="w",
            padx=(0, 10),
            pady=(14, 4),
        )
        ttk.Combobox(
            parent,
            textvariable=self.semanas_var,
            values=tuple(str(numero) for numero in range(2, 9)),
            state="readonly",
        ).grid(row=fila + 1, column=columna, sticky="ew", padx=(0, 10))

    def _cargar_salas(self):
        codigos = self.controlador.obtener_codigos_salas()
        self.sala_combo.configure(values=codigos)
        if codigos:
            self.sala_var.set(codigos[0])

    def _observar_cambios(self):
        variables = (
            self.carne_var,
            self.sala_var,
            self.fecha_var,
            self.hora_var,
            self.duracion_var,
            self.personas_var,
            self.semanas_var,
        )
        for variable in variables:
            variable.trace_add("write", self._invalidar_previsualizacion)

    def _invalidar_previsualizacion(self, *_argumentos):
        self._tiene_cambios = True
        self.al_cambiar_pendientes(True)
        self.boton_crear.configure(state="disabled")
        self.mensaje_var.set("Los datos cambiaron; genere una nueva vista previa.")

    def _datos_formulario(self):
        try:
            duracion = int(self.duracion_var.get())
            cantidad_personas = int(self.personas_var.get())
            semanas = int(self.semanas_var.get())
        except (TypeError, ValueError):
            return None, "Duración, personas y semanas deben ser números enteros."

        return {
            "carne": self.carne_var.get().strip(),
            "codigo_sala": self.sala_var.get().strip(),
            "fecha": self.fecha_var.get().strip(),
            "hora_inicio": self.hora_var.get().strip(),
            "duracion": duracion,
            "cantidad_personas": cantidad_personas,
            "semanas": semanas,
        }, None

    def previsualizar(self):
        datos, error = self._datos_formulario()
        if error:
            messagebox.showerror("Datos inválidos", error, parent=self.ventana)
            return

        resultado = self.controlador.previsualizar_recurrencia(**datos)
        self._llenar_previsualizacion(resultado.get("ocurrencias", []))
        self.mensaje_var.set(resultado["mensaje"])
        if not resultado["exito"]:
            self.boton_crear.configure(state="disabled")
            messagebox.showerror(
                "No fue posible validar la serie",
                resultado["mensaje"],
                parent=self.ventana,
            )
            return

        estado = "normal" if resultado["puede_crear"] else "disabled"
        self.boton_crear.configure(state=estado)

    def _llenar_previsualizacion(self, ocurrencias):
        elementos = self.tabla.get_children()
        if elementos:
            self.tabla.delete(*elementos)
        for ocurrencia in ocurrencias:
            disponible = ocurrencia["disponible"]
            self.tabla.insert(
                "",
                "end",
                tags=("disponible" if disponible else "conflicto",),
                values=(
                    ocurrencia["numero"],
                    ocurrencia["fecha"],
                    "Disponible" if disponible else "No disponible",
                    ocurrencia["mensaje"],
                ),
            )

    def crear(self):
        datos, error = self._datos_formulario()
        if error:
            messagebox.showerror("Datos inválidos", error, parent=self.ventana)
            return
        resultado = self.controlador.crear_recurrencia(**datos)
        if not resultado["exito"]:
            self.boton_crear.configure(state="disabled")
            messagebox.showerror(
                "No fue posible crear la serie",
                resultado["mensaje"],
                parent=self.ventana,
            )
            return

        self._tiene_cambios = False
        self.al_cambiar_pendientes(False)
        self.al_completar()
        messagebox.showinfo(
            "Serie creada",
            (
                f"La serie {resultado['serie_id']} se creó correctamente "
                f"con {len(resultado['ids'])} ocurrencias."
            ),
            parent=self.ventana,
        )
        self.ventana.destroy()

    def cancelar(self):
        if self._tiene_cambios:
            confirmar = messagebox.askyesno(
                "Descartar cambios",
                "¿Desea cerrar el formulario y descartar los datos ingresados?",
                parent=self.ventana,
            )
            if not confirmar:
                return
        self.al_cambiar_pendientes(False)
        self.ventana.destroy()


def abrir_dialogo_recurrencia(
    parent,
    controlador,
    al_completar,
    al_cambiar_pendientes,
):
    """Abre el formulario modal de RF-14."""
    ventana = tk.Toplevel(parent)
    ventana.title("Nueva reservación recurrente")
    ventana.geometry("980x760")
    ventana.minsize(850, 680)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    dialogo = DialogoRecurrencia(
        ventana,
        controlador,
        al_completar,
        al_cambiar_pendientes,
    )
    ventana.protocol("WM_DELETE_WINDOW", dialogo.cancelar)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
