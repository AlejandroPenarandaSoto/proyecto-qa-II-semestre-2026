# Fase 6 Corrección y verificación

Entrega central de Alejandro Vega Gamboa sobre `dev-vega`, base `8101328cb52d2ae018d486fafc37576433b042f8`. Se analizaron los **9 reportes** del PDF de Fase 5 recibido el 2 de noviembre de 2026: **5 corregidos y verificados; 4 rechazados con justificación**. La suite corregida aprueba **248 ítems**, sin fallos, xfail, omisiones ni errores.

- [Informe en Word](Registro_resolucion_Fase_6.docx) para incorporar al documento grupal.
- [Registro legible de resolución](registro_resolucion.md).
- [Registro estructurado por defecto](registro_resolucion.json), con decisión, justificación, cambio, límites, requisitos y pruebas.
- [Archivos corregidos y huellas](archivos_corregidos.json) y [parche del código y las pruebas](cambios_fase6.patch).
- [Regresión final](regresion_final/resultado_pytest.txt), [JUnit](regresion_final/resultado_pytest.xml) y [resultados individuales](regresion_final/resultados_por_prueba.json).
- [Índice de corridas](indice_corridas.json) y [fuentes de la entrega y del requisito de semilla](fuentes/).

## Uso y reproducción

Desde la raíz del repositorio, con las dependencias instaladas:

```sh
python3 -m pytest tests
```

La versión exacta corregida es el commit que incorpora este directorio y los archivos de `archivos_corregidos.json`. Las huellas de `regresion_final/integridad_antes.json` identifican las fuentes probadas antes de versionarlas. Las corridas conservan sus rutas y comandos originales como evidencia; las rutas temporales de otra máquina no se deben copiar literalmente para repetir la suite.

## Lectura de los resultados

`antes_correccion/` reproduce los dos fallos de salas y disponibilidad. `antes_ini01/` y `antes_ini02/` reproducen los defectos de inicialización con `--runxfail`, sin ocultarlos. Sus carpetas `despues_*` contienen los retests. `antes_reportes/` registra dos fallos de escritura y un control de reemplazo aprobado; `despues_reportes/` contiene 16 aprobaciones.

`impacto_semilla/` conserva los 10 fallos derivados de escenarios que presuponían estudiantes vacíos. Se ajustó la preparación temporal y una comparación de persistencia, sin debilitar las aserciones de negocio. `regresion_tras_aislamiento/` aprobó 245 ítems; tras añadir los 3 de CSV, `regresion_final/` aprobó 248. Las corridas anteriores son historial, no resultados de la versión final.

`contraste_otros_antes_semilla/` contiene los cuatro contrastes independientes sobre la API real, sin cambios al módulo de reservaciones ni panel. `comparacion_modulos_no_corregidos.json` prueba que reservaciones, panel, controlador e interfaz conservan las fuentes de cc9fab4. Los mismos cuatro escenarios aprueban en la suite final. El rechazo se limita a las reproducciones descritas; no certifica una GUI real y puede reabrirse ante una reproducción distinta.

`contraste_pruebas_publicadas/` conserva 4 errores de preparación al ejecutar los archivos publicados en dev-ernesto, commit bcf1cfe, sin inventar sus fixtures o adaptadores ausentes. Las entradas originales se conservan como `.py.txt` en `entradas_pruebas_publicadas/`; la extensión evita que pytest las recolecte como pruebas operativas. No pertenecen a la rama base evaluada ni a las 248 pruebas finales. Las comprobaciones equivalentes implementadas con la API real están en `tests/test_contraste_reportes_fase6.py`.

## Verificación después de incorporar al repositorio

`verificacion_integracion/` registra una ejecución desde el repositorio original, después de aplicar los cambios: **248 aprobados** a las 18:57 del 2 de noviembre. Se ejecutó con SQLite temporal, sin modificar fuentes ni la base real durante la corrida.

## Integridad y alcance

Las salidas históricas de Fase 5 permanecen sin cambios. La base real no se borra ni se utiliza para los escenarios de prueba. Las corridas conservan sus comprobaciones antes/después. Los 231 ítems de la rama base y los 17 nuevos constituyen los 248 ítems finales; no equivalen a 248 casos documentales distintos.

Se cambiaron cuatro archivos productivos: inicializador, semilla, salas y reportes. Se ajustaron cinco archivos de pruebas y se añadieron cinco con 17 ítems. No se integró esta entrega a main ni a qa. La actualización posterior que Tamara anunció deberá contrastarse antes de cerrar el informe grupal definitivo.

`SHA256SUMS.txt` permite verificar los archivos del paquete. Los archivos Word y PDF son documentos; las copias `.py.txt` son entradas preservadas, no pruebas adicionales.
