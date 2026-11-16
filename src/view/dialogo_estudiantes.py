"""Gestión de estudiantes: RF-02, RF-03, RF-07 y RF-11."""

import tkinter as tk
from tkinter import messagebox, ttk

from src.view.tema import COLOR_FILA_ALTERNA, COLOR_FONDO


class DialogoEstudiantes(ttk.Frame):
    """Registra, consulta y modifica estudiantes sin contener reglas de negocio."""

    COLUMNAS = (
        ("carne", "Carné", 120),
        ("nombre", "Nombre completo", 240),
        ("correo", "Correo", 240),
        ("estado", "Estado", 90),
    )
    COLUMNAS_HISTORIAL = (
        ("id", "ID", 80),
        ("sala", "Sala", 70),
        ("fecha", "Fecha", 100),
        ("hora", "Hora", 70),
        ("duracion", "Horas", 60),
        ("personas", "Personas", 80),
        ("estado", "Estado", 90),
    )

    def __init__(self, ventana, controlador, al_completar, al_cambiar_pendientes):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.al_completar = al_completar
        self.al_cambiar_pendientes = al_cambiar_pendientes
        self._tiene_cambios = False
        self._cargando = False

        self.carne_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.correo_var = tk.StringVar()
        self.estado_var = tk.StringVar(value="activo")
        self.mensaje_var = tk.StringVar()

        self.pack(fill="both", expand=True)
        self._crear_contenido()
        for variable in (self.carne_var, self.nombre_var, self.correo_var, self.estado_var):
            variable.trace_add("write", self._marcar_cambios)
        self.refrescar()

    def _crear_contenido(self):
        ttk.Label(self, text="Estudiantes", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Seleccione un estudiante para modificarlo o ver sus reservaciones. "
                "Los estudiantes nuevos se registran como activos."
            ),
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
        self.entrada_carne = self._campo(formulario, "CARNÉ", self.carne_var, 0)
        self._campo(formulario, "NOMBRE COMPLETO", self.nombre_var, 1)
        self._campo(formulario, "CORREO", self.correo_var, 2)
        ttk.Label(formulario, text="ESTADO", style="Campo.TLabel").grid(
            row=0, column=3, sticky="w", pady=(0, 4)
        )
        ttk.Combobox(
            formulario,
            textvariable=self.estado_var,
            values=("activo", "inactivo"),
            state="readonly",
            width=12,
        ).grid(row=1, column=3, sticky="ew")
        for columna in range(3):
            formulario.columnconfigure(columna, weight=1)

        botones = ttk.Frame(formulario, style="Panel.TFrame")
        botones.grid(row=2, column=0, columnspan=4, sticky="e", pady=(12, 0))
        ttk.Button(
            botones, text="Limpiar", style="Secundario.TButton", command=self.limpiar
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botones,
            text="Ver reservaciones",
            style="Secundario.TButton",
            command=self.ver_reservaciones,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botones,
            text="Guardar cambios",
            style="Secundario.TButton",
            command=self.modificar,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botones, text="Registrar", style="Primario.TButton", command=self.registrar
        ).pack(side="left")

        self.tabla = self._tabla(self, self.COLUMNAS, alto=8)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        ttk.Label(self, text="RESERVACIONES DEL ESTUDIANTE", style="Campo.TLabel").pack(
            anchor="w", pady=(12, 4)
        )
        self.tabla_historial = self._tabla(self, self.COLUMNAS_HISTORIAL, alto=5)


    def _campo(self, parent, etiqueta, variable, columna):
        ttk.Label(parent, text=etiqueta, style="Campo.TLabel").grid(
            row=0, column=columna, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        entrada = ttk.Entry(parent, textvariable=variable)
        entrada.grid(row=1, column=columna, sticky="ew", padx=(0, 10))
        return entrada

    def _tabla(self, parent, columnas, alto):
        contenedor = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        contenedor.pack(fill="both", expand=True)
        tabla = ttk.Treeview(
            contenedor,
            columns=[columna[0] for columna in columnas],
            show="headings",
            selectmode="browse",
            height=alto,
        )
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.tag_configure("alterna", background=COLOR_FILA_ALTERNA)
        for identificador, titulo, ancho in columnas:
            tabla.heading(identificador, text=titulo)
            tabla.column(identificador, width=ancho, anchor="w")
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    def _marcar_cambios(self, *_argumentos):
        if self._cargando:
            return
        self._tiene_cambios = True
        self.al_cambiar_pendientes(True)

    def _sin_cambios(self):
        self._tiene_cambios = False
        self.al_cambiar_pendientes(False)

    def refrescar(self):
        exito, mensaje, estudiantes = self.controlador.obtener_estudiantes()
        if not exito:
            messagebox.showerror(
                "No fue posible consultar los estudiantes", mensaje, parent=self.ventana
            )
            return
        _vaciar(self.tabla)
        for indice, estudiante in enumerate(estudiantes):
            self.tabla.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(
                    estudiante["carne"],
                    estudiante["nombre_completo"],
                    estudiante["correo"],
                    estudiante["estado"],
                ),
            )
        self.mensaje_var.set(
            f"{len(estudiantes)} estudiantes registrados." if estudiantes else mensaje
        )

    def _al_seleccionar(self, _evento=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        carne, nombre, correo, estado = self.tabla.item(seleccion[0], "values")
        self._cargando = True
        try:
            self.carne_var.set(carne)
            self.nombre_var.set(nombre)
            self.correo_var.set(correo)
            self.estado_var.set(estado)
        finally:
            self._cargando = False
        self._sin_cambios()
        self.ver_reservaciones(mostrar_errores=False)

    def registrar(self):
        exito, mensaje = self.controlador.registrar_estudiante(
            self.carne_var.get(), self.nombre_var.get(), self.correo_var.get()
        )
        self._informar(exito, mensaje, "No fue posible registrar al estudiante")

    def modificar(self):
        if not self.carne_var.get().strip():
            messagebox.showwarning(
                "Seleccione un estudiante",
                "Seleccione en la tabla el estudiante que desea modificar.",
                parent=self.ventana,
            )
            return
        exito, mensaje = self.controlador.modificar_estudiante(
            self.carne_var.get(),
            self.nombre_var.get(),
            self.correo_var.get(),
            self.estado_var.get(),
        )
        self._informar(exito, mensaje, "No fue posible modificar al estudiante")

    def _informar(self, exito, mensaje, titulo_error):
        if not exito:
            messagebox.showerror(titulo_error, mensaje, parent=self.ventana)
            return
        self._sin_cambios()
        self.refrescar()
        self.al_completar()
        self.mensaje_var.set(mensaje)
        messagebox.showinfo("Operación realizada", mensaje, parent=self.ventana)

    def ver_reservaciones(self, mostrar_errores=True):
        exito, mensaje, reservaciones = self.controlador.buscar_reservaciones_estudiante(
            self.carne_var.get()
        )
        _vaciar(self.tabla_historial)
        if not exito:
            if mostrar_errores:
                messagebox.showerror(
                    "No fue posible consultar las reservaciones",
                    mensaje,
                    parent=self.ventana,
                )
            return
        for indice, reservacion in enumerate(reservaciones):
            self.tabla_historial.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(
                    f"R{int(reservacion['id']):04d}",
                    reservacion["sala"],
                    reservacion["fecha"],
                    reservacion["hora_inicio"],
                    reservacion["duracion_horas"],
                    reservacion["cantidad_personas"],
                    reservacion["estado"],
                ),
            )
        self.mensaje_var.set(mensaje)

    def limpiar(self):
        self._cargando = True
        try:
            for variable in (self.carne_var, self.nombre_var, self.correo_var):
                variable.set("")
            self.estado_var.set("activo")
        finally:
            self._cargando = False
        self.tabla.selection_remove(self.tabla.selection())
        _vaciar(self.tabla_historial)
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


def _vaciar(tabla):
    elementos = tabla.get_children()
    if elementos:
        tabla.delete(*elementos)


def abrir_dialogo_estudiantes(parent, controlador, al_completar, al_cambiar_pendientes):
    """Abre la gestión modal de estudiantes."""
    ventana = tk.Toplevel(parent)
    ventana.title("Estudiantes")
    ventana.geometry("1000x780")
    ventana.minsize(860, 640)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    dialogo = DialogoEstudiantes(ventana, controlador, al_completar, al_cambiar_pendientes)
    ventana.protocol("WM_DELETE_WINDOW", dialogo.cerrar)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
