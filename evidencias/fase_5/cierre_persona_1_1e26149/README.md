# Fase 5: aporte de Persona 1

Alejandro Vega Gamboa. Ejecución centralizada, análisis de estudiantes, salas, disponibilidad, selector de fecha y tema; ampliación de pruebas y documentación de resultados y defectos. Esta carpeta contiene el aporte individual para su integración por Persona 5, no el informe global del equipo.

## Versión y alcance

Se evaluó una copia aislada del repositorio `AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026`, rama `dev-vega`, commit base **`1e26149877598d2699de52b14834fd88eb01da09`**, más estos tres archivos adicionales:

- [`tests/test_estudiantes_historial_fase5.py`](../../../tests/test_estudiantes_historial_fase5.py): 5 ítems.
- [`tests/test_salas_ampliacion_fase5.py`](../../../tests/test_salas_ampliacion_fase5.py): 13 ítems.
- [`tests/test_disponibilidad_ampliacion_fase5.py`](../../../tests/test_disponibilidad_ampliacion_fase5.py): 15 ítems, incluidas variantes parametrizadas.

Las huellas exactas están en `fuentes_evaluadas_sha256.json` y en los metadatos de cada corrida. El commit base por sí solo no contiene estos tres archivos. Al preparar este paquete no se había hecho commit ni push de esta ampliación.

No se modificaron fuentes productivas ni pruebas previas. Las bases son temporales; no se abrieron ventanas ni se automatizaron clics. CP-DIS-04 usa un reloj simulado únicamente dentro del módulo para comprobar una hora pasada del mismo día y lo restaura al terminar. El reloj del sistema no se altera.

La primera ejecución completa y la ampliación anterior de cuatro límites de estudiantes siguen preservadas en [`ejecucion_inicial_cc9fab4`](../ejecucion_inicial_cc9fab4/README.md) y [`ampliacion_estudiantes_limites_5c3ed26`](../ampliacion_estudiantes_limites_5c3ed26/README.md).

## Resultados separados por ejecución

| Ejecución | Fecha/hora de Costa Rica | Ítems | Aprobados | Fallidos | xfail | Omitidos |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Inicial, preservada previamente | 29/10/2026, 23:02 | 194 | 192 | 0 | 2 | 0 |
| Primera ampliación de límites, preservada previamente | 30/10/2026, 00:46 | 4 | 4 | 0 | 0 | 0 |
| Regresión anterior, preservada previamente | 30/10/2026, 06:02 | 198 | 195 | 0 | 2 | 1 |
| Ampliación de este bloque | 30/10/2026, 06:40:50–06:40:51 | 33 | 31 | 2 | 0 | 0 |
| Regresión de este bloque | 30/10/2026, 06:40:51–06:40:53 | 231 | 226 | 2 | 2 | 1 |

Las ejecuciones no se suman: la última suite contiene 194 ítems originales, 4 agregados anteriormente y 33 de este bloque. Los fallos nuevos permanecen como `FAILED`, sin ocultarlos con `xfail`. Los dos `xfail` ya existían antes de la ampliación. Ambas corridas de este bloque terminaron con código de salida de pytest **1**, debido a los dos fallos registrados; no hubo errores de colección o preparación.

Resumen literal de la regresión: `2 failed, 226 passed, 1 skipped, 2 xfailed in 1.82s`.

Los ocho archivos de pruebas correspondientes a Persona 1 reúnen **72 ítems: 70 aprobados y 2 fallidos**. Son 33 aprobaciones de estudiantes, 32 aprobaciones y 2 fallos de salas/disponibilidad, 2 aprobaciones del selector y 3 del tema. Los casos de estudiantes apoyados también por pruebas de auditoría o reservaciones se referencian sin contarlos como pruebas nuevas propias.

## Casos del plan y limitaciones

[`casos_resultados.json`](casos_resultados.json) y [`cobertura_casos.md`](cobertura_casos.md) relacionan los 60 casos del plan del alcance de Persona 1: **54 aprobados en su comprobación automatizada, 1 fallido y 5 no ejecutados**. Se registra además el caso nuevo F5-DIS-01, fallido. Estos casos documentales no equivalen a los 72 ítems de los archivos propios ni a los 231 de toda la suite.

Los cinco no ejecutados son CP-EST-25, CP-EST-26, CP-SAL-04, CP-SAL-12 y CP-SAL-16. Requieren comprobar una pantalla o confirmación gráfica ausente en la versión evaluada. No se inventó una vista ni se consideró su ausencia una aprobación. Los límites de la API sobre carné y código no sustituyen una ejecución de esos casos gráficos.

Las cinco pruebas del selector y el tema comprueban una matriz de calendario, cambios de año, existencia de recursos y selección/configuración de fuentes simuladas. No certifican apariencia, nitidez del PNG, fuentes realmente instaladas ni interacción del calendario. No se requieren capturas para respaldar las comprobaciones automatizadas realizadas; sus limitaciones quedan explícitas.

No hubo bloqueos de preparación ni colección en las corridas. Las exclusiones gráficas se registran como no ejecutadas dentro de este aporte; no se certifica a partir de ellas el porcentaje de bloqueo de los casos de todo el equipo.

## Defectos confirmados

| ID | Caso | Hallazgo observado | Severidad propuesta | Prioridad propuesta |
| --- | --- | --- | --- | --- |
| [BUG-P1-SAL-01](defectos/BUG-P1-SAL-01.md) | CP-SAL-07 | Se acepta `s01` aunque existe `S01`; se almacena otra sala. | Media | Alta |
| [BUG-P1-DIS-01](defectos/BUG-P1-DIS-01.md) | F5-DIS-01 | Se informa disponible al consultar `9:00` pese a una reserva 08:00–10:00. | Alta | Alta |

Ambos se reprodujeron en la ampliación y la regresión. Los informes separan severidad y prioridad, contienen los datos y pasos de reproducción, y enlazan resultados reales y evidencias. Permanecen abiertos. No se modificó el código para corregirlos.

La auditoría de la nueva sala refleja una operación aceptada por el servicio: el defecto se atribuye a su validación de unicidad, no a un fallo independiente de auditoría. El segundo hallazgo demuestra una consulta incorrecta, no que otro servicio haya guardado una reserva superpuesta.

## Resultados ajenos que deben comunicarse

- A Persona 3: los dos `xfail` originales de inicialización, `test_rf01_crea_estudiantes_iniciales` y `test_rf01_ruta_imposible_se_informa_sin_excepcion`; no cuentan como aprobados.
- A Persona 2: `test_rechazar_hora_ya_transcurrida_si_es_hoy` se omitió por su condición existente: antes de las 08:00 no hay una hora válida transcurrida. Las corridas fueron a las 06:40; no se marca como aprobada ni como defecto nuevo.
- A Persona 5: integrar este aporte junto con los de los demás responsables; los resultados de una misma prueba en distintas corridas no deben sumarse como pruebas distintas.

## Evidencia y reproducción

Las carpetas `ampliacion/` y `regresion/` contienen cada una salida completa TXT, JUnit XML, resultados individuales JSON, ambiente/comando, registro de ejecución y verificaciones antes/después. JUnit conserva también las observaciones JSON impresas, incluidos los resultados fallidos. Los archivos originales de cada corrida se conservan sin editar.

En la raíz están las huellas de las fuentes evaluadas, las verificaciones del repositorio original, el resumen de corridas, los casos y sus resultados, y el texto individual preparado para el documento compartido en [`informe_persona_1.md`](informe_persona_1.md). `SHA256SUMS.txt` permite verificar las copias de esta carpeta, excluyendo el propio manifiesto.

Para reproducir, usar el commit base más los tres archivos nuevos cuyas huellas se especifican. Desde la raíz de esa copia, con Python 3.14.7 y pytest 9.1.1, ejecutar `python3 -m pytest tests -vv -rA`. El resultado esperado de estas pruebas, mientras no se corrijan los defectos, incluye ambos fallos. La omisión horaria depende de la hora real. Para repetir guardando evidencia equivalente, consultar el comando y las variables completos de `informacion_version.json`, usando rutas nuevas para reportes y temporales.

## Estado de entrega

Pruebas, análisis, resultados y defectos de Persona 1 preparados. Queda incorporar el texto al documento compartido y entregar los enlaces al responsable de integración. La publicación de los nuevos archivos mediante commit y push requiere el siguiente paso autorizado por Alejandro. Esta entrega de pruebas no implica que los defectos estén corregidos ni que el informe global esté terminado.
