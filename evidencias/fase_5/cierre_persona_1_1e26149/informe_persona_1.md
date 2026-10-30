# Análisis y ampliación de pruebas de Persona 1

## Alcance y versión evaluada

Se analizaron los módulos de estudiantes, salas, disponibilidad, selector de fecha y tema de la aplicación. La ejecución inicial de 194 ítems, descrita anteriormente, se conserva sin modificaciones. Posteriormente se agregaron cuatro pruebas de límites de estudiantes, aprobadas y publicadas en el commit `1e26149` de `dev-vega`.

Para completar el análisis se diseñaron otros **33 ítems automatizados** en tres archivos: cinco de consulta, modificación e historial de estudiantes; trece de catálogo y mantenimiento de salas; y quince de disponibilidad, incluidos los límites horarios y una condición adicional de formato. La versión evaluada fue el commit base **`1e26149877598d2699de52b14834fd88eb01da09`**, más esos tres archivos nuevos identificados mediante SHA-256. El commit base por sí solo no los contiene.

Se utilizaron macOS 27.0.1 ARM64, Python 3.14.7, pytest 9.1.1 y SQLite 3.50.4. Las pruebas se ejecutaron en una copia aislada y con bases temporales. No se modificó código productivo ni pruebas previas; tampoco se abrieron ventanas ni se automatizaron clics.

Las técnicas aplicadas fueron partición de equivalencia, valores límite, escenarios de estados e historial y regresión automatizada. Los resultados esperados se definieron a partir del plan y sus reglas, antes de observar las respuestas. Las filas SQL usadas en algunos escenarios preparan datos controlados para probar una consulta o modificación; no sustituyen una prueba del flujo de creación de reservaciones.

## Resultados obtenidos

El 30 de octubre de 2026, entre las 06:40:50 y las 06:40:51, hora de Costa Rica, la ampliación produjo **31 aprobaciones y 2 fallos** entre sus 33 ítems. A continuación, entre las 06:40:51 y las 06:40:53, se ejecutó la suite completa ampliada:

| Clasificación | Cantidad |
| --- | ---: |
| Ítems recolectados | 231 |
| Aprobados | 226 |
| Fallidos | 2 |
| Fallos esperados preexistentes (`xfail`) | 2 |
| Omitidos por condición horaria (`skipped`) | 1 |
| Errores de colección o preparación | 0 |

Resumen de pytest: `2 failed, 226 passed, 1 skipped, 2 xfailed in 1.82s`. El código de salida fue 1 por los dos fallos documentados; no se interpreta como una ejecución totalmente aprobada. Los 231 ítems contienen los 194 originales, las cuatro pruebas añadidas previamente y las 33 de este bloque. No deben sumarse los resultados de distintas corridas como si fueran pruebas nuevas.

En los ocho archivos del alcance de Persona 1 se obtuvieron **70 aprobaciones y 2 fallos entre 72 ítems**:

| Módulo | Aprobados | Fallidos |
| --- | ---: | ---: |
| Estudiantes, incluidos límites e historial | 33 | 0 |
| Salas y disponibilidad | 32 | 2 |
| Selector de fecha | 2 | 0 |
| Tema de la aplicación | 3 | 0 |

Las comprobaciones de estudiantes incluyen rechazo de carnés y nombres fuera de sus límites, consulta de activos e inactivos, búsqueda sin distinguir mayúsculas, presencia de reservas activas y canceladas, modificación de nombre y correo conservando carné y estado, e inactivación sin perder el historial. No se observaron defectos en esos escenarios ejecutados.

En salas se comprobaron los cinco registros iniciales y su orden, registro y modificación, rechazo de capacidades cero, negativas y decimales, reducción de capacidad sin reservas futuras y límites frente a una reserva futura de cinco personas. En disponibilidad se verificaron horarios libres, fechas y horas pasadas, jornada de uso, duración, superposiciones, horarios consecutivos y ausencia de escrituras durante las consultas. CP-DIS-04 utiliza un reloj simulado únicamente en el módulo para comprobar las 14:00 cuando son las 14:25; se restaura al terminar y no modifica el reloj del sistema.

## Defectos confirmados

### BUG-P1-SAL-01: código de sala duplicado con distinta capitalización

**Requisito y caso:** RF-12 y CP-SAL-07 del plan, cuyo resultado esperado exige identificar el código sin distinguir capitalización.

**Ambiente y versión:** los indicados en este apartado, commit base `1e26149` más las pruebas adicionales. Reproducido en la ampliación y en la regresión del 30 de octubre de 2026.

**Precondición y datos:** base temporal inicializada, con `S01` existente. Se solicita registrar código `s01`, nombre `Duplicada` y capacidad 5.

**Pasos:** consultar las salas iniciales; invocar `registrar_sala("s01", "Duplicada", 5)`; consultar nuevamente las salas y la auditoría. La reproducción automatizada corresponde a `tests/test_salas_ampliacion_fase5.py::test_cp_sal_07_rechaza_duplicado_en_minusculas`.

**Esperado:** rechazar el duplicado y conservar los registros existentes.

**Obtenido:** `exito=True`, mensaje «Sala s01 registrada exitosamente.»; el catálogo pasa de cinco a seis salas y contiene `S01` y `s01`. Se genera un evento de creación para la operación aceptada. El defecto es de validación de unicidad de salas; no se atribuye un defecto independiente a auditoría.

**Severidad propuesta:** media, porque permite duplicidad lógica de un identificador sin detener la aplicación. **Prioridad propuesta:** alta, para preservar la unicidad antes de continuar usando el mantenimiento de salas. **Estado:** abierto, sin corrección productiva.

**Evidencia:** informe `defectos/BUG-P1-SAL-01.md`, salida y JUnit de `ampliacion/` y `regresion/`, y la observación CP-SAL-07 en `resultados_por_prueba.json`.

### BUG-P1-DIS-01: disponibilidad incorrecta con la hora `9:00`

**Requisito y caso:** RF-08 y RN-09; caso adicional F5-DIS-01, distinto del caso CP-DIS-01 del plan.

**Ambiente y versión:** los indicados en este apartado, commit base `1e26149` más las pruebas adicionales. Reproducido en ambas corridas del 30 de octubre de 2026.

**Precondición y datos:** reservación activa en `S01` el 31 de octubre de 2026, de 08:00 a 10:00. La prueba calcula la fecha como hoy más un día. Se consulta `S01` en esa fecha, hora `9:00` y duración de una hora.

**Pasos:** preparar la reserva en SQLite temporal; invocar `consultar_disponibilidad("S01", fecha, "9:00", 1)`; revisar respuesta y persistencia. Reproducción: `tests/test_disponibilidad_ampliacion_fase5.py::test_f5_dis_01_hora_sin_cero_no_ignora_conflicto`.

**Esperado:** `disponible=False`, ya sea por formato inválido o por reconocer el traslape 09:00–10:00 con la reserva 08:00–10:00.

**Obtenido:** `disponible=True`, motivo «La sala está disponible.». Los datos permanecen sin cambios, pero la respuesta es incorrecta. Esta evidencia no demuestra que otro servicio permita guardar una reservación superpuesta.

**Severidad propuesta:** alta, por afectar el resultado central de disponibilidad. **Prioridad propuesta:** alta, para revisar esta validación antes de usarla para orientar nuevas reservas. **Estado:** abierto, sin corrección productiva.

**Evidencia:** informe `defectos/BUG-P1-DIS-01.md`, salidas TXT y JUnit de ambas corridas y observación F5-DIS-01 con los estados antes y después en los JSON individuales.

## Trazabilidad y límites

La relación individual contiene 60 casos del plan del alcance de Persona 1: **54 aprobados en sus comprobaciones automatizadas, 1 fallido y 5 no ejecutados**. Además, F5-DIS-01 es un caso nuevo y fallido. Los casos documentales no equivalen al número de ítems pytest; las variantes parametrizadas y los apoyos compartidos impiden igualar ambas cantidades.

Los cinco no ejecutados son CP-EST-25, CP-EST-26, CP-SAL-04, CP-SAL-12 y CP-SAL-16. Requieren comprobar vistas o confirmaciones gráficas ausentes en la versión evaluada. Se conserva el motivo y no se marcan como aprobados. La firma de los servicios identifica estudiantes y salas por carné o código, pero esa lectura no sustituye ejecutar una interfaz.

En el selector se comprobaron la matriz de septiembre de 2026 y dos cambios de mes entre años. En el tema se comprobaron la existencia de recursos y la selección/configuración de fuentes simuladas. Estas cinco aprobaciones no certifican la apariencia, nitidez del logo, fuentes realmente instaladas ni interacción en ventanas.

Los dos `xfail` originales corresponden a inicialización y deben analizarse por Persona 3. La omisión de `test_rechazar_hora_ya_transcurrida_si_es_hoy` corresponde a reservaciones: antes de las 08:00 no hay una hora válida transcurrida; se informa a Persona 2 y no se contabiliza como aprobada. No hubo bloqueos de preparación o colección en este aporte; no se deduce de este subconjunto el porcentaje de bloqueo de todo el equipo.

## Conservación y entrega de evidencias

El paquete individual se organiza en `evidencias/fase_5/cierre_persona_1_1e26149/`, con salidas completas TXT, reportes JUnit, resultados por prueba y por caso, versión, ambiente, comandos, fechas, huellas de las fuentes y comprobaciones de integridad antes y después. La relación detallada está en `casos_resultados.json` y `cobertura_casos.md`. Los registros iniciales y la base de datos original se conservan intactos.

Las pruebas y evidencias de este último bloque están preparadas para revisión y publicación en `dev-vega`. La incorporación de este texto al documento compartido y la entrega de enlaces a Persona 5 completan el traspaso del aporte individual; la integración del informe global corresponde a esa persona. Los dos defectos confirmados permanecen abiertos para su gestión posterior.
