"""Identidad visual compartida por las vistas de TEC Room Manager."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk

COLOR_FONDO = "#F3F7FA"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARIO = "#063D73"
COLOR_PRIMARIO_ACTIVO = "#0A548F"
COLOR_ACENTO = "#00B9AE"
COLOR_ACENTO_ACTIVO = "#009F97"
COLOR_TEXTO = "#15263A"
COLOR_SECUNDARIO = "#607286"
COLOR_BORDE = "#D8E2EA"
COLOR_FILA_ALTERNA = "#F6FAFC"

DIRECTORIO_RECURSOS = Path(__file__).resolve().parent / "assets"
RUTA_LOGO_COMPLETO = DIRECTORIO_RECURSOS / "tec_room_manager.png"
RUTA_ISOTIPO_CABECERA = DIRECTORIO_RECURSOS / "isotipo_cabecera.png"


def cargar_logo(master):
    """Carga el isotipo preparado para la cabecera sin redimensionarlo."""
    return tk.PhotoImage(master=master, file=str(RUTA_ISOTIPO_CABECERA))


def configurar_estilos(master):
    """Configura los estilos visuales sin mezclar diseño con negocio."""
    estilo = ttk.Style(master)
    estilo.theme_use("clam")

    estilo.configure("Fondo.TFrame", background=COLOR_FONDO)
    estilo.configure("Panel.TFrame", background=COLOR_PANEL)
    estilo.configure("Encabezado.TFrame", background=COLOR_PRIMARIO)
    estilo.configure("Encabezado.TLabel", background=COLOR_PRIMARIO)
    estilo.configure(
        "Marca.TLabel",
        background=COLOR_PRIMARIO,
        foreground="#FFFFFF",
        font=("TkDefaultFont", 19, "bold"),
    )
    estilo.configure(
        "MarcaDetalle.TLabel",
        background=COLOR_PRIMARIO,
        foreground="#CDE5F2",
        font=("TkDefaultFont", 10),
    )
    estilo.configure(
        "Titulo.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO,
        font=("TkDefaultFont", 21, "bold"),
    )
    estilo.configure(
        "Subtitulo.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_SECUNDARIO,
        font=("TkDefaultFont", 10),
    )
    estilo.configure(
        "Seccion.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        font=("TkDefaultFont", 11, "bold"),
    )
    estilo.configure(
        "Campo.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_SECUNDARIO,
        font=("TkDefaultFont", 9, "bold"),
    )
    estilo.configure(
        "Resumen.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_PRIMARIO,
        font=("TkDefaultFont", 20, "bold"),
    )
    estilo.configure(
        "Vacio.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_SECUNDARIO,
        font=("TkDefaultFont", 10, "italic"),
    )
    estilo.configure(
        "Primario.TButton",
        background=COLOR_ACENTO,
        foreground="#FFFFFF",
        borderwidth=0,
        padding=(16, 9),
        font=("TkDefaultFont", 10, "bold"),
    )
    estilo.map(
        "Primario.TButton",
        background=[("pressed", COLOR_ACENTO_ACTIVO), ("active", COLOR_ACENTO_ACTIVO)],
    )
    estilo.configure(
        "Secundario.TButton",
        background="#E8F0F5",
        foreground=COLOR_PRIMARIO,
        borderwidth=0,
        padding=(16, 9),
        font=("TkDefaultFont", 10, "bold"),
    )
    estilo.map(
        "Secundario.TButton",
        background=[("pressed", "#D5E3EC"), ("active", "#D5E3EC")],
    )
    estilo.configure(
        "TEntry",
        fieldbackground=COLOR_PANEL,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        padding=7,
    )
    estilo.configure(
        "TCombobox",
        fieldbackground=COLOR_PANEL,
        background=COLOR_PANEL,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        padding=6,
    )
    estilo.map("TCombobox", fieldbackground=[("readonly", COLOR_PANEL)])
    estilo.configure(
        "TNotebook",
        background=COLOR_FONDO,
        borderwidth=0,
        tabmargins=0,
    )
    estilo.configure(
        "TNotebook.Tab",
        background="#E5EDF3",
        foreground=COLOR_SECUNDARIO,
        borderwidth=0,
        padding=(14, 8),
        font=("TkDefaultFont", 9, "bold"),
    )
    estilo.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_PRIMARIO), ("active", "#D2E2EC")],
        foreground=[("selected", "#FFFFFF"), ("active", COLOR_PRIMARIO)],
    )
    estilo.configure(
        "Treeview",
        background=COLOR_PANEL,
        fieldbackground=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        borderwidth=1,
        rowheight=30,
    )
    estilo.map(
        "Treeview",
        background=[("selected", COLOR_ACENTO)],
        foreground=[("selected", "#FFFFFF")],
    )
    estilo.configure(
        "Treeview.Heading",
        background=COLOR_PRIMARIO,
        foreground="#FFFFFF",
        relief="flat",
        padding=(6, 8),
        font=("TkDefaultFont", 9, "bold"),
    )
    estilo.map("Treeview.Heading", background=[("active", COLOR_PRIMARIO_ACTIVO)])
