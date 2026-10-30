# BUG-P1-DIS-01: disponibilidad incorrecta al consultar `9:00`

| Campo | Registro |
| --- | --- |
| Estado | Abierto; reproducido, sin corrección productiva. |
| Caso | F5-DIS-01, ampliación de robustez de Fase 5; no sustituye CP-DIS-01. |
| Requisitos afectados | RF-08, consulta de disponibilidad; RN-09, rechazo de superposiciones. |
| Versión | `dev-vega`, base `1e26149877598d2699de52b14834fd88eb01da09`, más los tres archivos nuevos de pruebas identificados en `fuentes_evaluadas_sha256.json`. |
| Ambiente | macOS 27.0.1 ARM64, Python 3.14.7, pytest 9.1.1, SQLite 3.50.4; zona `America/Costa_Rica`. La plataforma y el comando completos se conservan en los metadatos de cada corrida. |
| Fecha | 30 de octubre de 2026; ejecuciones ampliada y de regresión entre 06:40:50 y 06:40:53, hora de Costa Rica. |
| Severidad propuesta | Alta: el resultado central de disponibilidad es incorrecto para una franja realmente ocupada. No se observó un cierre del proceso ni una doble reservación persistida. |
| Prioridad propuesta | Alta: revisar antes de utilizar la disponibilidad para orientar nuevas reservas; una entrada con un solo dígito en la hora evita la detección del conflicto. |

## Precondiciones y datos

SQLite temporal inicializado con las salas del proyecto. Se inserta un estudiante activo `C123456789` y una reservación activa de prueba en `S01`, para dos personas, el **2026-10-31**, desde **08:00**, por **2 horas**. Los INSERT preparan el escenario y no prueban el flujo de creación de reservas.

Datos de consulta: código `S01`, fecha `2026-10-31`, hora **`9:00`**, duración **1 hora**. La fecha del test se calcula como hoy más un día; se registra aquí el valor obtenido en estas corridas.

## Pasos para reproducir

1. Preparar una copia del commit base junto con `tests/test_disponibilidad_ampliacion_fase5.py` cuya huella figura en `fuentes_evaluadas_sha256.json`.
2. Desde la raíz del proyecto ejecutar `python3 -m pytest tests/test_disponibilidad_ampliacion_fase5.py::test_f5_dis_01_hora_sin_cero_no_ignora_conflicto -vv -rA` con las dependencias indicadas. La prueba crea y cierra su base temporal.
3. La prueba prepara la reservación 08:00–10:00 y llama a `consultar_disponibilidad("S01", fecha, "9:00", 1)`.
4. Comparar la respuesta con el horario ocupado y revisar la observación `OBSERVACION_CP` incluida en la salida.

## Resultado esperado

`disponible=False`: el servicio debe rechazar `9:00` por no respetar el formato `HH:MM`, o interpretar esa entrada como 09:00 y detectar el traslape 09:00–10:00. Ninguna de esas interpretaciones permite declarar libre la sala ocupada de 08:00 a 10:00.

## Resultado obtenido

La respuesta real fue:

```json
{"disponible": true, "motivo": "La sala está disponible."}
```

La prueba falla al comprobar `resultado["disponible"] is False`. El mismo resultado se obtuvo al ejecutar los 33 ítems nuevos y al ejecutar los 231 ítems de la suite ampliada. En ambas corridas, los registros de estudiantes, salas, reservaciones y auditoría permanecieron iguales antes y después de la consulta. El defecto observado es la respuesta incorrecta; no se ha demostrado que permita guardar una reserva duplicada mediante otro servicio.

## Evidencia

- [`../ampliacion/resultado_pytest.txt`](../ampliacion/resultado_pytest.txt): traza y observación de F5-DIS-01.
- [`../ampliacion/resultado_pytest.xml`](../ampliacion/resultado_pytest.xml): fallo JUnit y salida capturada.
- [`../ampliacion/resultados_por_prueba.json`](../ampliacion/resultados_por_prueba.json): datos de entrada, respuesta y estados completos antes y después.
- [`../regresion/resultado_pytest.txt`](../regresion/resultado_pytest.txt) y [`../regresion/resultados_por_prueba.json`](../regresion/resultados_por_prueba.json): reproducción dentro de la suite completa.
- Identificador: `tests/test_disponibilidad_ampliacion_fase5.py::test_f5_dis_01_hora_sin_cero_no_ignora_conflicto`.

## Análisis de causa

La lectura de `src/model/salas/servicio.py` muestra que se analiza la hora con `strptime`, pero en la condición de traslape se compara el texto original `hora_inicio` con horas formateadas como `HH:MM`. La comparación textual entre `9:00` y `10:00` explica de forma consistente el resultado observado. Esta es una inferencia del código y de las evidencias; no se implementó ni verificó una corrección en esta fase.

El efecto observado no debe atribuirse a la interfaz gráfica, ya que la prueba invoca directamente el servicio, conforme al alcance de Fase 5.
