"""Identidad visual compartida por las vistas de TEC Room Manager."""

from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

COLOR_FONDO = "#F4F7FA"
COLOR_PANEL = "#FFFFFF"
COLOR_TARJETA = "#F8FAFC"
COLOR_PRIMARIO = "#063D73"
COLOR_PRIMARIO_ACTIVO = "#0A548F"
COLOR_ACENTO = "#00B9AE"
COLOR_ACENTO_ACTIVO = "#009F97"
COLOR_TEXTO = "#15263A"
COLOR_SECUNDARIO = "#607286"
COLOR_BORDE = "#D5E0E8"
COLOR_FILA_ALTERNA = "#F6FAFC"
COLOR_SECUNDARIO_ACTIVO = "#EAF1F6"

FUENTES_PREFERIDAS = (
    "Segoe UI",
    "Helvetica Neue",
    "Helvetica",
    "Inter",
    "Roboto",
    "TkDefaultFont",
)

DIRECTORIO_RECURSOS = Path(__file__).resolve().parent / "assets"
RUTA_LOGO_COMPLETO = DIRECTORIO_RECURSOS / "tec_room_manager.png"
RUTA_ISOTIPO_CABECERA = DIRECTORIO_RECURSOS / "isotipo_cabecera.png"


def cargar_logo(master):
    """Carga el isotipo preparado para la cabecera sin redimensionarlo."""
    return tk.PhotoImage(master=master, file=str(RUTA_ISOTIPO_CABECERA))


def obtener_fuente_interfaz(master):
    """Elige una fuente moderna disponible sin imponer dependencias externas."""
    fuentes_disponibles = set(tkfont.families(master))
    return next(
        (fuente for fuente in FUENTES_PREFERIDAS if fuente in fuentes_disponibles),
        "TkDefaultFont",
    )


def configurar_tipografia_global(master, familia):
    """Aplica la familia elegida a los textos nativos que no usan ttk."""
    for nombre in (
        "TkDefaultFont",
        "TkTextFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    ):
        tkfont.nametofont(nombre, root=master).configure(family=familia)


def configurar_estilos(master):
    """Configura los estilos visuales sin mezclar diseño con negocio."""
    estilo = ttk.Style(master)
    estilo.theme_use("clam")
    fuente = obtener_fuente_interfaz(master)
    configurar_tipografia_global(master, fuente)
    estilo.configure(".", font=(fuente, 10))

    estilo.configure("Fondo.TFrame", background=COLOR_FONDO)
    estilo.configure("Panel.TFrame", background=COLOR_PANEL)
    estilo.configure("Panel.TLabel", background=COLOR_PANEL)
    estilo.configure("Tarjeta.TFrame", background=COLOR_TARJETA)
    estilo.configure("Encabezado.TFrame", background=COLOR_PRIMARIO)
    estilo.configure("Encabezado.TLabel", background=COLOR_PRIMARIO)
    estilo.configure(
        "Marca.TLabel",
        background=COLOR_PRIMARIO,
        foreground="#FFFFFF",
        font=(fuente, 19, "bold"),
    )
    estilo.configure(
        "MarcaDetalle.TLabel",
        background=COLOR_PRIMARIO,
        foreground="#CDE5F2",
        font=(fuente, 10),
    )
    estilo.configure(
        "Titulo.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO,
        font=(fuente, 22, "bold"),
    )
    estilo.configure(
        "Subtitulo.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_SECUNDARIO,
        font=(fuente, 10),
    )
    estilo.configure(
        "Seccion.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        font=(fuente, 11, "bold"),
    )
    estilo.configure(
        "Campo.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_SECUNDARIO,
        font=(fuente, 9, "bold"),
    )
    estilo.configure(
        "TarjetaTitulo.TLabel",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=(fuente, 10, "bold"),
    )
    estilo.configure(
        "TarjetaValor.TLabel",
        background=COLOR_TARJETA,
        foreground=COLOR_PRIMARIO,
        font=(fuente, 22, "bold"),
    )
    estilo.configure(
        "VacioTabla.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_SECUNDARIO,
        font=(fuente, 11),
        justify="center",
        padding=(24, 16),
    )
    estilo.configure(
        "Primario.TButton",
        background=COLOR_PRIMARIO,
        foreground="#FFFFFF",
        borderwidth=0,
        padding=(18, 10),
        font=(fuente, 10, "bold"),
    )
    estilo.map(
        "Primario.TButton",
        background=[
            ("pressed", COLOR_PRIMARIO_ACTIVO),
            ("active", COLOR_PRIMARIO_ACTIVO),
        ],
    )
    estilo.configure(
        "Secundario.TButton",
        background=COLOR_PANEL,
        foreground=COLOR_PRIMARIO,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        borderwidth=1,
        relief="solid",
        padding=(17, 9),
        font=(fuente, 10, "bold"),
    )
    estilo.map(
        "Secundario.TButton",
        background=[
            ("pressed", COLOR_SECUNDARIO_ACTIVO),
            ("active", COLOR_SECUNDARIO_ACTIVO),
        ],
        bordercolor=[("active", COLOR_PRIMARIO)],
    )
    estilo.configure(
        "Cabecera.TButton",
        background="#FFFFFF",
        foreground=COLOR_PRIMARIO,
        borderwidth=0,
        padding=(16, 8),
        font=(fuente, 10, "bold"),
    )
    estilo.map(
        "Cabecera.TButton",
        background=[("pressed", "#DDF4F2"), ("active", "#DDF4F2")],
        foreground=[("pressed", COLOR_PRIMARIO), ("active", COLOR_PRIMARIO)],
    )
    estilo.configure(
        "CalendarioTitulo.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        font=(fuente, 12, "bold"),
    )
    estilo.configure(
        "CalendarioDiaSemana.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_SECUNDARIO,
        font=(fuente, 9, "bold"),
    )
    estilo.configure(
        "Calendario.TButton",
        background="#EDF3F7",
        foreground=COLOR_TEXTO,
        borderwidth=0,
        padding=7,
        font=(fuente, 9),
    )
    estilo.map(
        "Calendario.TButton",
        background=[("active", "#DDF4F2")],
        foreground=[("active", COLOR_PRIMARIO)],
    )
    estilo.configure(
        "CalendarioSeleccionado.TButton",
        background=COLOR_ACENTO,
        foreground="#FFFFFF",
        borderwidth=0,
        padding=7,
        font=(fuente, 9, "bold"),
    )
    estilo.configure(
        "CalendarioNavegacion.TButton",
        background=COLOR_PANEL,
        foreground=COLOR_PRIMARIO,
        borderwidth=0,
        padding=(12, 5),
        font=(fuente, 15, "bold"),
    )
    estilo.configure(
        "TEntry",
        fieldbackground=COLOR_PANEL,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        relief="flat",
        borderwidth=1,
        padding=7,
        font=(fuente, 10),
    )
    estilo.configure(
        "TCombobox",
        fieldbackground=COLOR_PANEL,
        background=COLOR_PANEL,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        relief="flat",
        borderwidth=1,
        arrowsize=13,
        padding=6,
        font=(fuente, 10),
    )
    estilo.map("TCombobox", fieldbackground=[("readonly", COLOR_PANEL)])
    for orientacion in ("Vertical", "Horizontal"):
        nombre_estilo = f"{orientacion}.TScrollbar"
        estilo.configure(
            nombre_estilo,
            background="#BCCAD5",
            troughcolor="#EDF2F6",
            bordercolor="#EDF2F6",
            lightcolor="#BCCAD5",
            darkcolor="#BCCAD5",
            arrowcolor=COLOR_SECUNDARIO,
            relief="flat",
            troughrelief="flat",
            borderwidth=0,
            width=12,
        )
        estilo.map(
            nombre_estilo,
            background=[
                ("pressed", COLOR_PRIMARIO_ACTIVO),
                ("active", COLOR_PRIMARIO),
            ],
            arrowcolor=[("pressed", "#FFFFFF"), ("active", "#FFFFFF")],
        )
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
        font=(fuente, 9, "bold"),
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
        rowheight=32,
        font=(fuente, 10),
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
        font=(fuente, 9, "bold"),
    )
    estilo.map("Treeview.Heading", background=[("active", COLOR_PRIMARIO_ACTIVO)])
