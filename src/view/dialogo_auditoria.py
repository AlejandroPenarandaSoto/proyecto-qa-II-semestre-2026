"""Consulta visual de solo lectura para la auditoría RF-17."""

import tkinter as tk
from tkinter import messagebox, ttk

from src.view.tema import COLOR_FILA_ALTERNA, COLOR_FONDO


class DialogoAuditoria(ttk.Frame):
    """Presenta el historial de eventos sin acciones de modificación."""

    COLUMNAS = (
        ("fecha_hora", "Fecha y hora", 155),
        ("accion", "Acción", 105),
        ("entidad", "Entidad", 115),
        ("entidad_id", "Identificador", 115),
        ("detalle", "Detalle", 430),
    )

    def __init__(self, ventana, controlador):
        super().__init__(ventana, style="Fondo.TFrame", padding=22)
        self.ventana = ventana
        self.controlador = controlador
        self.mensaje_var = tk.StringVar()
        self.pack(fill="both", expand=True)
        self._crear_contenido()
        self.refrescar()

    def _crear_contenido(self):
        encabezado = ttk.Frame(self, style="Fondo.TFrame")
        encabezado.pack(fill="x", pady=(0, 16))
        ttk.Button(
            encabezado,
            text="Actualizar",
            style="Primario.TButton",
            command=self.refrescar,
        ).pack(side="right")
        ttk.Label(
            encabezado,
            text="Auditoría",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Historial de operaciones exitosas registrado por el sistema.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        contenedor = ttk.Frame(self, style="Panel.TFrame", padding=12)
        contenedor.pack(fill="both", expand=True)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)

        self.tabla = ttk.Treeview(
            contenedor,
            columns=[columna[0] for columna in self.COLUMNAS],
            show="headings",
            selectmode="browse",
        )
        barra_vertical = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=self.tabla.yview,
        )
        barra_horizontal = ttk.Scrollbar(
            contenedor,
            orient="horizontal",
            command=self.tabla.xview,
        )
        self.tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )
        self.tabla.tag_configure("alterna", background=COLOR_FILA_ALTERNA)
        for identificador, titulo, ancho in self.COLUMNAS:
            self.tabla.heading(identificador, text=titulo)
            self.tabla.column(
                identificador,
                width=ancho,
                minwidth=80,
                anchor="w" if identificador == "detalle" else "center",
            )

        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra_vertical.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")

        pie = ttk.Frame(self, style="Fondo.TFrame")
        pie.pack(fill="x", pady=(12, 0))
        ttk.Label(
            pie,
            textvariable=self.mensaje_var,
            style="Subtitulo.TLabel",
        ).pack(side="left")
        ttk.Button(
            pie,
            text="Cerrar",
            style="Secundario.TButton",
            command=self.ventana.destroy,
        ).pack(side="right")

    def refrescar(self):
        resultado = self.controlador.obtener_auditoria()
        if not resultado["exito"]:
            messagebox.showerror(
                "No fue posible consultar la auditoría",
                resultado["mensaje"],
                parent=self.ventana,
            )
            return

        elementos = self.tabla.get_children()
        if elementos:
            self.tabla.delete(*elementos)

        eventos = resultado["eventos"]
        for indice, evento in enumerate(eventos):
            self.tabla.insert(
                "",
                "end",
                tags=("alterna",) if indice % 2 else (),
                values=(
                    evento["fecha_hora"],
                    evento["accion"],
                    evento["entidad"],
                    evento["entidad_id"],
                    evento["detalle"] or "",
                ),
            )
        if len(eventos) == 1:
            mensaje = "1 evento registrado."
        elif eventos:
            mensaje = f"{len(eventos)} eventos registrados."
        else:
            mensaje = resultado["mensaje"]
        self.mensaje_var.set(mensaje)


def abrir_dialogo_auditoria(parent, controlador):
    """Abre la consulta modal de auditoría."""
    ventana = tk.Toplevel(parent)
    ventana.title("Auditoría")
    ventana.geometry("1080x620")
    ventana.minsize(850, 480)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(parent)
    DialogoAuditoria(ventana, controlador)
    ventana.grab_set()
    ventana.focus_force()
    return ventana
