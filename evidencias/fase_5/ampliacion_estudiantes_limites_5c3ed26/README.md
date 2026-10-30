# Fase 5: ampliación de límites de estudiantes

Persona 1 incorporó cuatro pruebas automatizadas de RF-02 que comprueban los límites de longitud previstos en CP-EST-04, CP-EST-05, CP-EST-07 y CP-EST-08. Se usa Python, pytest y la conexión SQLite existente, con una base temporal independiente para cada prueba. No se automatizan clics ni se abren ventanas.

## Versión y archivo de pruebas

- Repositorio: `AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026`.
- Rama local: `dev-vega`.
- Commit base: `5c3ed26239ce2b96484e2a6fa6e74411c9093831`.
- Archivo agregado: [`tests/test_estudiantes_limites_fase5.py`](../../../tests/test_estudiantes_limites_fase5.py).
- SHA-256 del archivo nuevo: `88470ea44380123280560a62d3bf9a89b783053843ed9f6ef033559534fff817`.
- Estado al verificar la integración: archivo nuevo todavía sin commit ni push. El commit base por sí solo no incluye estas cuatro pruebas.

El código productivo y las pruebas originales permanecen sin cambios. La ejecución inicial de Fase 5 continúa preservada por separado en [`ejecucion_inicial_cc9fab4`](../ejecucion_inicial_cc9fab4/README.md). Esta carpeta documenta una ampliación posterior y su regresión; no reemplaza aquella ejecución.

## Casos nuevos y resultados observados

| Caso | Requisito | Datos relevantes | Resultado esperado | Resultado obtenido | Estado |
| --- | --- | --- | --- | --- | --- |
| CP-EST-04 | RF-02 | Carné `C12345678`, 9 caracteres; nombre y correo válidos. | Rechazar el carné sin cambiar estudiantes ni auditoría. | `exito=False`; mensaje: «El carné debe tener exactamente 10 caracteres alfanuméricos.»; estudiantes y auditoría sin cambios. | Aprobado |
| CP-EST-05 | RF-02 | Carné `C1234567890`, 11 caracteres; nombre y correo válidos. | Rechazar el carné sin cambiar estudiantes ni auditoría. | `exito=False`; mismo mensaje de longitud del carné; estudiantes y auditoría sin cambios. | Aprobado |
| CP-EST-07 | RF-02 | Carné válido `C123456789`; nombre `Al`, 2 caracteres; correo válido. | Rechazar el nombre sin cambiar estudiantes ni auditoría. | `exito=False`; mensaje: «El nombre debe contener al menos 3 caracteres sin contar espacios.»; estudiantes y auditoría sin cambios. | Aprobado |
| CP-EST-08 | RF-02 | Carné `C123456789`; nombre `Ana`, 3 caracteres; correo `ana@tec.ac.cr`. | Registrar los datos del estudiante con estado activo. | `exito=True`; «Estudiante registrado correctamente.»; se consulta la fila persistida y se comprueban sus datos y estado `activo`. | Aprobado |

Los tres casos negativos comparan el contenido de estudiantes y auditoría antes y después del intento. El caso positivo comprueba los datos realmente almacenados. Estos resultados no implican cobertura completa de los casos de estudiantes.

### Primera ejecución de las cuatro pruebas

Se realizó el 30 de octubre de 2026, de 00:46:24 a 00:46:25, hora de Costa Rica, sobre una copia aislada del commit base y el archivo adicional externo. Resultado: **4 aprobadas**, sin fallos, errores ni omisiones; salida de pytest: `4 passed in 0.03s`.

Los siete archivos originales de esa ejecución se conservan sin modificar en [`ejecucion_cuatro_casos`](ejecucion_cuatro_casos/). Sus rutas absolutas corresponden al lugar donde se ejecutaron originalmente. El archivo externo mencionado allí es idéntico, byte por byte, al incorporado ahora en `tests/`.

## Regresión tras incorporar las pruebas

El 30 de octubre de 2026, de **06:02:08 a 06:02:10**, hora de Costa Rica, se ejecutó toda la carpeta `tests/` en otra copia aislada que contiene el commit base más el archivo nuevo. Se recolectaron **198 ítems**: los 194 originales más las 4 pruebas agregadas.

| Resultado | Cantidad |
| --- | ---: |
| Aprobados | 195 |
| Fallos inesperados | 0 |
| Errores de ejecución o colección | 0 |
| Fallos esperados preexistentes (`xfail`) | 2 |
| Omitidos ordinarios (`skipped`) | 1 |

Resumen exacto: `195 passed, 1 skipped, 2 xfailed in 1.24s`. Código de salida: 0. Las cuatro pruebas nuevas aprobaron. En los archivos originales se obtuvieron 191 aprobaciones, 2 `xfail` y 1 omisión.

La prueba omitida es `tests/test_reservaciones.py::test_rechazar_hora_ya_transcurrida_si_es_hoy`. Su condición existente indica: «Antes de las 08:00 no hay una hora válida del día que ya haya transcurrido.» La ejecución fue a las 06:02, por lo que esta prueba **no se contabiliza como aprobada**. No se cambió la prueba ni se alteró el reloj para obtener otro resultado. Su verificación queda pendiente de una ejecución con la condición horaria adecuada.

Los dos `xfail` son los mismos de la ejecución inicial, en `tests/test_inicializacion_persistencia.py`: `test_rf01_crea_estudiantes_iniciales` y `test_rf01_ruta_imposible_se_informa_sin_excepcion`. No son aprobaciones ni nuevos defectos confirmados por estas cuatro pruebas; sus razones declaradas y resultados se preservan en las salidas.

No se encontraron defectos nuevos en los cuatro escenarios añadidos. La omisión horaria y los `xfail` se registran por separado de los fallos inesperados. Este bloque no constituye el cierre de la Fase 5.

## Evidencias y reproducción

En [`regresion_integrada`](regresion_integrada/) se conservan:

- `resultado_pytest.txt`: salida completa con resultados por prueba y resumen.
- `resultado_pytest.xml`: reporte JUnit original. Distingue la omisión ordinaria de los dos `pytest.xfail`.
- `resultados_por_prueba.json`: clasificación derivada de los 198 ítems; identifica los cuatro casos nuevos.
- `informacion_version.json`: ambiente, commit base, huella de la prueba adicional, comando exacto y variables controladas.
- `registro_ejecucion.json`: fechas, conteos, código de salida y verificaciones de integridad.
- `fuentes_evaluadas_sha256.json`: huellas de `src/` y `tests/` de la copia evaluada, incluido el archivo nuevo.
- `integridad_antes.json` e `integridad_despues.json`: estado del repositorio original y huellas de sus archivos versionados, base SQLite y paquete inicial. La única adición de código es el archivo nuevo de pruebas.

Ambiente de regresión: Python 3.14.7, pytest 9.1.1, SQLite 3.50.4, macOS ARM64; zona horaria `America/Costa_Rica`. La plataforma exacta está en `informacion_version.json`. No se instalaron dependencias ni se modificó el entorno virtual original.

Para reproducir, usar el commit base más el archivo de pruebas cuya huella se indica arriba y ejecutar `python3 -m pytest tests -vv -rA` desde la raíz de una copia del proyecto con esas dependencias. La hora local influye en la prueba señalada. Para conservar evidencia equivalente, consultar el comando y las variables completos en `informacion_version.json`, asignando carpetas nuevas para reportes y temporales; no reutilizar las rutas de esta ejecución ni sobrescribir sus resultados.

`SHA256SUMS.txt` permite comprobar las copias de los archivos de esta carpeta, excluyendo el propio manifiesto. La incorporación y la verificación se realizaron sin commit ni push.
