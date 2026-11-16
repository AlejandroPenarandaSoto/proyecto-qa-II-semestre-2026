# Sistema de reservación de salas de estudio - QA

Aplicación de escritorio con interfaz gráfica en Python para administrar estudiantes, salas y reservaciones de salas de estudio universitarias. Proyecto Final - Calidad en Sistemas de Información, Semestre II 2026.

## Descripción

La universidad cuenta con varias salas destinadas al estudio individual y grupal. Este sistema reemplaza el registro manual de reservaciones, evitando choques de horario, reservas para salas fuera de servicio, grupos que exceden la capacidad y falta de trazabilidad sobre cancelaciones y disponibilidad.

## Estructura del repositorio

```
proyecto-qa-II-semestre-2026/
├── info.txt
├── README.md
├── requirements.txt
├── .gitignore
│
├── docs/
│
├── src/                    # Código fuente (patrón MVC)
│   ├── main.py                  # Punto de entrada
│   ├── modelo/                  # MODEL: entidades, reglas de negocio, persistencia
│   ├── vista/                   # VIEW: pantallas y widgets de la GUI
│   ├── controlador/             # CONTROLLER: conecta la Vista con el Modelo
│   ├── util/                    # UTIL: lógica utilitaria del sistema
│   └── db/                      # DB: lógica de acceso a datos
│
├── tests/                       # Pruebas aplicadas al sistema
│
└── evidencias/
```

## Requisitos

- Python 3.10 o superior
- pip
- Tkinter (incluido con Python en Windows y macOS; en Linux: `sudo apt install python3-tk`)

## Instrucciones de ejecución

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026.git
   cd proyecto-qa-II-semestre-2026
   ```

2. (Opcional, recomendado) Crear y activar un entorno virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Linux / macOS
   venv\Scripts\activate           # Windows
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:

   ```bash
   python3 -m src.main             # en Windows: python -m src.main
   ```

En la primera ejecución, el sistema crea automáticamente la base de datos SQLite (`src/db/reservas.db`) con la estructura y los datos iniciales (salas y estudiantes de ejemplo). En ejecuciones posteriores, reutiliza la base existente sin duplicar registros.

## Ejecución de las pruebas

Desde la raíz del repositorio:

```bash
python3 -m pytest tests
```

## Restaurar datos iniciales

Para volver al estado inicial de datos (por ejemplo, antes de una ronda de pruebas):

1. Cerrar la aplicación si está en ejecución.
2. Eliminar el archivo `src/db/reservas.db`.
3. Volver a ejecutar `python3 -m src.main` desde la raíz del repositorio; la base se regenera con la estructura y los datos iniciales definidos en `src/db/semilla.py`.

## Descripción de las opciones del menú

| Opción | Descripción |
|---|---|
| **Estudiantes** | Registrar, consultar, modificar y eliminar estudiantes (carné, nombre y datos de contacto). |
| **Salas** | Administrar las salas de estudio: capacidad, tipo (individual o grupal) y estado (disponible o fuera de servicio). |
| **Nueva reservación** | Reservar una sala para un estudiante indicando fecha, hora de inicio, hora de fin y cantidad de personas. El sistema valida choques de horario, salas fuera de servicio y capacidad máxima. |
| **Consultar reservaciones** | Ver y filtrar las reservaciones por estudiante, sala, fecha o estado. |
| **Cancelar reservación** | Cancelar una reservación activa, dejando registro de la cancelación para mantener la trazabilidad. |
| **Disponibilidad** | Consultar qué salas están libres en una fecha y franja horaria. |
| **Reportes** | Exportar reportes en formato CSV (reservaciones, cancelaciones y ocupación por sala). |
| **Salir** | Cierra la aplicación. |

## Control de versiones

- **Ramas:** `main` (versión estable en producción), `dev` (integración por miembro), `qa` (entorno de pruebas).
- **Commits:** con formato breve y descriptivo de lo realizado.
- Cada commit debe quedar asociado a la persona autora real.

## Estado del proyecto

**Fase 8 - Final: FINALIZADO.** Versión 1.0.0 entregada. Detalle de la declaración en `info.txt`.

## Fase 8 - Final

**Estado: Finalizada.** En esta fase se ejecutaron escenarios completos, se demostró el cumplimiento de los requisitos, se consolidaron las métricas y se reflexionó sobre el proceso.

| Producto de la fase | Estado | Ubicación |
|---|---|---|
| Informe final | Entregado | `documentos/fase_8/Informe_final.pdf` |
| Demostración | Realizada | `documentos/fase_8/Demostracion.md` |
| Acta de aceptación académica | Firmada | `documentos/fase_8/Acta_aceptacion.pdf` |
