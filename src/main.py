"""
Punto de entrada de la aplicación.
"""
import sys

from src.db.inicializador import inicializar_base_datos


def main() -> int:
    resultado = inicializar_base_datos()

    if not resultado.exito:
        print("No fue posible iniciar la aplicación.")
        print(resultado.mensaje)
        return 1

    print(resultado.mensaje)
    if resultado.salas_insertadas:
        print(f"Se cargaron {resultado.salas_insertadas} salas iniciales.")

    # Se importa después de inicializar la base de datos para mantener el
    # arranque de la capa de persistencia independiente de la interfaz.
    from src.view.app import iniciar_aplicacion

    iniciar_aplicacion()
    return 0


if __name__ == "__main__":
    sys.exit(main())
