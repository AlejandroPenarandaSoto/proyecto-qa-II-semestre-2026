"""
Punto de entrada de la aplicación.
"""
import sys

from db.inicializador import inicializar_base_datos


def main() -> int:
    resultado = inicializar_base_datos()

    if not resultado.exito:
        print("No fue posible iniciar la aplicación.")
        print(resultado.mensaje)
        return 1

    print(resultado.mensaje)
    if resultado.salas_insertadas:
        print(f"Se cargaron {resultado.salas_insertadas} salas iniciales.")

    # La interfaz gráfica (Tkinter/CustomTkinter/PySide) se conecta aquí
    # una vez que el módulo de vista esté implementado por el equipo.
    try:
        from vista.app import iniciar_aplicacion  # type: ignore
    except ModuleNotFoundError:
        print(
            "Módulo de interfaz gráfica aún no disponible; "
            "la base de datos quedó lista para operar."
        )
        return 0

    iniciar_aplicacion()
    return 0


if __name__ == "__main__":
    sys.exit(main())
