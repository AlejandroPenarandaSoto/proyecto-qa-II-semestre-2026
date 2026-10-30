# Fase 5 Ejecución inicial de pruebas automatizadas

Evidencias de la ejecución centralizada realizada por Persona 1 para que cada integrante analice sus módulos. Este registro no es el informe final de Fase 5.

## Versión evaluada

- Repositorio: `AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026`.
- Rama indicada al realizar la ejecución: `dev-alejandro`.
- Commit evaluado: `cc9fab4cd268782cbdc9eb9921aa350903ce1e61`.
- Rama donde se publican estas evidencias: `dev-vega`, sincronizada posteriormente con ese mismo commit.
- Inicio: 29 de octubre de 2026, 23:02:48, Costa Rica (UTC-06:00).
- Fin: 29 de octubre de 2026, 23:02:49, Costa Rica.

El nombre de la rama registrado en los reportes originales se conserva para no alterar la trazabilidad. Las pruebas se ejecutaron sobre una copia aislada del commit indicado, sin modificar código productivo ni agregar, editar o eliminar pruebas.

## Ambiente

macOS 27.0.1 ARM64, Python 3.14.7, pytest 9.1.1, SQLite 3.50.4 y Tk/Tcl 9.0. El intérprete, las dependencias, el comando exacto y las variables controladas están registrados en `informacion_version.txt` y `informacion_version.json`.

Se utilizó el Python global que ya disponía de pytest y tkinter. No se instaló nada en la `.venv` original. Se desactivó la carga automática de plugins externos y no se heredó `PYTHONPATH`. Las bases de datos de las pruebas fueron temporales o en memoria. No se abrieron ventanas ni se automatizaron clics en la interfaz.

## Resultados

| Resultado | Cantidad |
| --- | ---: |
| Ítems automatizados recolectados | 194 |
| Aprobados (`passed`) | 192 |
| Fallos inesperados (`failed`) | 0 |
| Errores de ejecución o colección | 0 |
| Fallos esperados (`xfail`) | 2 |
| Omitidos ordinarios (`skipped`) | 0 |
| Éxitos inesperados (`xpass`) | 0 |

Resumen original de pytest: `192 passed, 2 xfailed in 0.79s`. Código de salida: 0. Los dos `xfail` no son aprobaciones; sus marcas ya existían en el código evaluado.

| Prueba con fallo esperado | Caso indicado en su código | Motivo declarado por la marca original |
| --- | --- | --- |
| `test_rf01_crea_estudiantes_iniciales` | CP-INI-02 | La semilla solo inserta salas; la prueba espera estudiantes iniciales. |
| `test_rf01_ruta_imposible_se_informa_sin_excepcion` | CP-INI-06 | Una ruta inválida puede producir un `OSError` no controlado en la inicialización. |

Ambas pertenecen a `tests/test_inicializacion_persistencia.py`. El responsable del módulo debe analizar las causas y documentar o actualizar los defectos con severidad y prioridad separadas. Las salidas conservadas contienen los motivos declarados de `xfail`, no un diagnóstico detallado nuevo de Persona 1.

JUnit representa estos dos resultados mediante elementos `skipped` de tipo `pytest.xfail`. No deben interpretarse como omisiones ordinarias ni como casos bloqueados.

## Cómo utilizar las evidencias

- `resultado_pytest.txt`: salida íntegra de la ejecución inicial, con resultados por ítem y resumen.
- `resultado_pytest.xml`: resultados originales en formato JUnit.
- `resultados_por_prueba.json`: 194 registros con identificador, estado, duración y motivo cuando corresponde.
- `registro_ejecucion.json`: fechas, duración, código de salida, conteos por módulo y limitaciones.
- `informacion_version.txt` e `informacion_version.json`: versión, ambiente y comando de ejecución.
- `integridad_antes.json` e `integridad_despues.json`: huellas SHA-256 y verificaciones de conservación de fuentes, pruebas y base de datos original en el momento de la corrida.
- `SHA256SUMS.txt`: huellas de los archivos de esta carpeta, excluyendo el propio manifiesto.

Los ocho archivos originales se copiaron sin modificar su contenido. Los identificadores de los dos `xfail` en el JSON derivado se completaron previamente a partir del resumen original de pytest; esa operación está anotada en `registro_ejecucion.json`. No se repitió la ejecución ni se editaron los archivos TXT/XML originales para ese ajuste.

Los caminos absolutos registrados describen el entorno donde se hizo la corrida. Para reproducirla, usar el mismo commit y las versiones indicadas, con rutas nuevas para los reportes y los temporales; no sobrescribir la evidencia inicial ni usar `--basetemp` sobre una carpeta con datos que se quieran conservar.

## Alcance y pendientes

Los 194 ítems pytest no equivalen a los 174 casos documentales de la matriz. La parametrización y las relaciones entre casos y pruebas impiden igualar ambos totales. No se marcan automáticamente todos los casos documentales como ejecutados o aprobados.

En los cuatro archivos asignados a Persona 1 aprobaron 35 ítems: estudiantes 24, salas 6, selector de fecha 2 y tema 3. Las pruebas del calendario verifican funciones y las del tema usan archivos y objetos simulados; no sustituyen la inspección visual ni demuestran cobertura total de los casos del plan.

Quedan pendientes el contraste detallado de cada caso con sus resultados, las ampliaciones justificadas de pruebas, la documentación de defectos y la integración del informe final. No se incluyen borradores de pruebas adicionales en este commit.

La suite inicial terminó sin impedimentos de ejecución observados. La aplicación del criterio de suspensión sobre los casos documentales requiere su clasificación posterior, sin mezclar sus cantidades con las de pytest.
