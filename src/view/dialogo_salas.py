"""Gestión de salas: RF-04 y RF-12."""

import tkinter as tk
from tkinter import messagebox, ttk

from src.view.tema import COLOR_FILA_ALTERNA, COLOR_FONDO

ESTADOS_SALA = ("disponible", "fuera_de_servicio")


class DialogoSalas(ttk.Frame):
    """Registra, consulta y modifica salas sin contener reglas de negocio."""

    COLUMNAS = (
        ("codigo", "Código", 100),
        ("nombre", "Nombre", 320),
        ("capacidad", "Capacidad", 100),
        ("estado", "Estado", 150),
    )

    def __init__(self, ventana, controlador, al_completar, al_cambiar_pendientes):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.al_completar = al_completar
        self.al_cambiar_pendientes = al_cambiar_pendientes
        self._tiene_cambios = False
        self._cargando = False

        self.codigo_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.capacidad_var = tk.StringVar(value="1")
        self.estado_var = tk.StringVar(value=ESTADOS_SALA[0])
        self.mensaje_var = tk.StringVar()

        self.pack(fill="both", expand=True)
        self._crear_contenido()
        for variable in (self.codigo_var, self.nombre_var, self.capacidad_var, self.estado_var):
            variable.trace_add("write", self._marcar_cambios)
        self.refrescar()

    def _crear_contenido(self):
        ttk.Label(self, text="Salas", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Seleccione una sala para modificar su nombre, capacidad o estado.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        pie = ttk.Frame(self, style="Fondo.TFrame")
        pie.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Label(pie, textvariable=self.mensaje_var, style="Subtitulo.TLabel").pack(
            side="left"
        )
        ttk.Button(
            pie, text="Cerrar", style="Secundario.TButton", command=self.cerrar
        ).pack(side="right")

        formulario = ttk.Frame(self, style="Panel.TFrame", padding=16)
        formulario.pack(fill="x", pady=(0, 14))
        self._etiqueta(formulario, "CÓDIGO", 0)
        ttk.Entry(formulario, textvariable=self.codigo_var).grid(
            row=1, column=0, sticky="ew", padx=(0, 10)
        )
        self._etiqueta(formulario, "NOMBRE", 1)
        ttk.Entry(formulario, textvariable=self.nombre_var).grid(
            row=1, column=1, sticky="ew", padx=(0, 10)
        )
        self._etiqueta(formulario, "CAPACIDAD", 2)
        ttk.Spinbox(
            formulario, textvariable=self.capacidad_var, from_=1, to=100, increment=1
        ).grid(row=1, column=2, sticky="ew", padx=(0, 10))
        self._etiqueta(formulario, "ESTADO", 3)
        ttk.Combobox(
            formulario, textvariable=self.estado_var, values=ESTADOS_SALA, state="readonly"
        ).grid(row=1, column=3, sticky="ew")
        formulario.columnconfigure(1, weight=1)

        botones = ttk.Frame(formulario, style="Panel.TFrame")
        botones.grid(row=2, column=0, columnspan=4, sticky="e", pady=(12, 0))
        ttk.Button(
            botones, text="Limpiar", style="Secundario.TButton", command=self.limpiar
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botones, text="Guardar cambios", style="Secundario.TButton", command=self.modificar
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botones, text="Registrar", style="Primario.TButton", command=self.registrar
        ).pack(side="left")

        contenedor = ttk.Frame(self, style="Panel.TFrame", padding=12)
        contenedor.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(
            contenedor,
            columns=[columna[0] for columna in self.COLUMNAS],
            show="headings",
            selectmode="browse",
        )
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.tag_configure("alterna", background=COLOR_FILA_ALTERNA)
        for identificador, titulo, ancho in self.COLUMNAS:
            self.tabla.heading(identificador, text=titulo)
            self.tabla.column(identificador, width=ancho, anchor="w")
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)


    @staticmethod
    def _etiqueta(parent, texto, columna):
        ttk.Label(parent, text=texto, style="Campo.TLabel").grid(
            row=0, column=columna, sticky="w", padx=(0, 10), pady=(0, 4)
        )

    def _marcar_cambios(self, *_argumentos):
        if self._cargando:
            return
        self._tiene_cambios = True
        self.al_cambiar_pendientes(True)

    def _sin_cambios(self):
        self._tiene_cambios = False
        self.al_cambiar_pendientes(False)

    def refrescar(self):
        salas = self.controlador.obtener_salas()
        elementos = self.tabla.get_children()
        if elementos:
            self.tabla.delete(*elementos)
        for indice, sala in enumerate(salas):
            self.tabla.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(sala["codigo"], sala["nombre"], sala["capacidad"], sala["estado"]),
            )
        self.mensaje_var.set(f"{len(salas)} salas registradas.")

    def _al_seleccionar(self, _evento=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        codigo, nombre, capacidad, estado = self.tabla.item(seleccion[0], "values")
        self._cargando = True
        try:
            self.codigo_var.set(codigo)
            self.nombre_var.set(nombre)
            self.capacidad_var.set(capacidad)
            self.estado_var.set(estado)
        finally:
            self._cargando = False
        self._sin_cambios()

    def _capacidad(self):
        try:
            return int(str(self.capacidad_var.get()).strip())
        except ValueError:
            messagebox.showerror(
                "Datos inválidos",
                "La capacidad debe ser un número entero mayor que cero.",
                parent=self.ventana,
            )
            return None

    def registrar(self):
        capacidad = self._capacidad()
        if capacidad is None:
            return
        resultado = self.controlador.registrar_sala(
            self.codigo_var.get(), self.nombre_var.get(), capacidad, self.estado_var.get()
        )
        self._informar(resultado, "No fue posible registrar la sala")

    def modificar(self):
        if not self.codigo_var.get().strip():
            messagebox.showwarning(
                "Seleccione una sala",
                "Seleccione en la tabla la sala que desea modificar.",
                parent=self.ventana,
            )
            return
        capacidad = self._capacidad()
        if capacidad is None:
            return
        resultado = self.controlador.modificar_sala(
            self.codigo_var.get(), self.nombre_var.get(), capacidad, self.estado_var.get()
        )
        self._informar(resultado, "No fue posible modificar la sala")

    def _informar(self, resultado, titulo_error):
        if not resultado["exito"]:
            messagebox.showerror(titulo_error, resultado["mensaje"], parent=self.ventana)
            return
        self._sin_cambios()
        self.refrescar()
        self.al_completar()
        self.mensaje_var.set(resultado["mensaje"])
        messagebox.showinfo("Operación realizada", resultado["mensaje"], parent=self.ventana)

    def limpiar(self):
        self._cargando = True
        try:
            self.codigo_var.set("")
            self.nombre_var.set("")
            self.capacidad_var.set("1")
            self.estado_var.set(ESTADOS_SALA[0])
        finally:
            self._cargando = False
        self.tabla.selection_remove(self.tabla.selection())
        self._sin_cambios()

    def cerrar(self):
        if self._tiene_cambios and not messagebox.askyesno(
            "Descartar cambios",
            "¿Desea cerrar y descartar los datos ingresados?",
            parent=self.ventana,
        ):
            return
        self.al_cambiar_pendientes(False)
        self.ventana.destroy()


def abrir_dialogo_salas(parent, controlador, al_completar, al_cambiar_pendientes):
    """Abre la gestión modal de salas."""
    ventana = tk.Toplevel(parent)
    ventana.title("Salas")
    ventana.geometry("900x620")
    ventana.minsize(780, 520)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    dialogo = DialogoSalas(ventana, controlador, al_completar, al_cambiar_pendientes)
    ventana.protocol("WM_DELETE_WINDOW", dialogo.cerrar)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
