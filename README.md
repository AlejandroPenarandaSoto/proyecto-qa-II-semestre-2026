# Sistema de reservación de salas de estudio

Aplicación de escritorio con interfaz gráfica en Python para administrar estudiantes, salas y reservaciones de salas de estudio universitarias. Proyecto Final — Calidad en Sistemas de Información, Semestre II 2026.

## Descripción

La universidad cuenta con varias salas destinadas al estudio individual y grupal. Este sistema reemplaza el registro manual de reservaciones, evitando choques de horario, reservas para salas fuera de servicio, grupos que exceden la capacidad y falta de trazabilidad sobre cancelaciones y disponibilidad.

## Estructura del repositorio

```
Grupo##_ProyectoFinal/
├── info.txt
├── README.md
├── requirements.txt
├── .gitignore
│
├── docs/
│
├── solucion/                    # Código fuente (patrón MVC)
│   ├── main.py                  # Punto de entrada
│   ├── modelo/                  # MODEL: entidades, reglas de negocio, persistencia
│   ├── vista/                   # VIEW: pantallas y widgets de la GUI
│   ├── controlador/             # CONTROLLER: conecta la Vista con el Modelo
│   ├── util/                    # UTIL: lógica utilitaria del sistema
│   └── db/                      # DB: lógica de acceso a datos
│
├── test/                        # Pruebas aplicadas al sistema
│
└── evidencias/
    ├── capturas/
    └── reportes_csv/
```

## Instalación y ejecución

En la primera ejecución, el sistema crea automáticamente la base de datos SQLite (`db/reservaciones.db`) con la estructura y los datos iniciales (salas y estudiantes de ejemplo). En ejecuciones posteriores, reutiliza la base existente sin duplicar registros.

## Restaurar datos iniciales

Para volver al estado inicial de datos (por ejemplo, antes de una ronda de pruebas):

1. Cerrar la aplicación si está en ejecución.
2. Eliminar el archivo `solucion/db/reservaciones.db`.
3. Volver a ejecutar `python main.py`; la base se regenera con la estructura y los datos iniciales definidos en `solucion/data/datos_iniciales.sql`.

## Descripción de las opciones del menú

Pendiente de definir...

## Pruebas

- Pruebas unitarias e integración: `pruebas/unitarias/` y `pruebas/integracion/`.
- Ejecutar la suite completa:
  ```bash
  pytest pruebas/
  ```
- La lógica de negocio (`solucion/modelo/`) se prueba de forma independiente de la interfaz gráfica, sin necesidad de automatizar clics.

## Control de versiones

- **Ramas:** `main` (versión estable en producción), `dev` (integración por miembro), `qa` (entorno de pruebas).
- **Commits:** con formato breve y descriptivo de lo realizado.
- Cada commit debe quedar asociado a la persona autora real.

## Estado del proyecto

En desarrollo...
