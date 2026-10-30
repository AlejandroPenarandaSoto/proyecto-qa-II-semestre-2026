# BUG-P1-SAL-01: se acepta «s01» aunque ya existe la sala «S01»

## Identificación y clasificación

- ID: BUG-P1-SAL-01.
- Módulo: gestión de salas, `registrar_sala`.
- Requisito: RF-12.
- Caso trazado: CP-SAL-07, «Registrar sala con código duplicado en minúscula», de `Matriz_Casos_Prueba_Equipo_final_v3.xlsx`.
- Oráculo documental: rechazar el duplicado independientemente de la capitalización y no guardar otro registro. La ampliación también comprueba que un rechazo no cambie salas, estudiantes, reservaciones ni auditoría.
- Estado: Abierto; sin corrección implementada ni verificación posterior de una corrección.
- Severidad: Media. La operación permite duplicar un identificador lógico del catálogo e incumple la unicidad esperada. En estas ejecuciones no se observó cierre inesperado, pérdida de registros anteriores ni corrupción del archivo SQLite.
- Prioridad: Alta, propuesta para su revisión por afectar la unicidad de los códigos de sala; no implica una prioridad formalmente acordada.
- Fecha de detección: 30 de octubre de 2026, 06:40:50, America/Costa_Rica (UTC-06:00).
- Confirmación en regresión: 30 de octubre de 2026, 06:40:53, en el mismo ambiente y versión evaluada.

## Ambiente y versión reproducible

- Repositorio: `AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026`.
- Rama de referencia: `dev-vega`.
- Commit base: `1e26149877598d2699de52b14834fd88eb01da09`.
- Versión evaluada: commit base más tres archivos nuevos de pruebas, todavía sin commit ni push al realizar estas ejecuciones. No se modificó código productivo.
- Archivo que reproduce este defecto: `tests/test_salas_ampliacion_fase5.py`.
- SHA-256 de ese archivo: `f07b367448754258890b5c706ae41f00bd8e619a0f1ec5069d84752473016197`.
- Sistema: macOS 27.0.1, ARM64.
- Python: 3.14.7; pytest: 9.1.1; SQLite: 3.50.4.
- Base de datos: archivo SQLite temporal individual, inicializado por el fixture de la prueba. Nunca se utiliza la base real de la aplicación.
- Interacción: llamada al servicio, sin GUI ni clics simulados.

El ambiente, comando de la ronda y hashes de los archivos nuevos constan en [informacion_version.json](../ampliacion/informacion_version.json). Los hashes de las fuentes evaluadas constan en [fuentes_evaluadas_sha256.json](../fuentes_evaluadas_sha256.json).

## Precondiciones

1. Disponer de la copia de evaluación del commit base y del archivo de pruebas con el hash indicado.
2. Inicializar una base SQLite temporal con el esquema y las cinco salas iniciales.
3. Verificar que existe `S01`, nombre `Sala Biblioteca 1`, capacidad `4`, estado `disponible`, y que todavía no existe `s01`.
4. Capturar el contenido de salas, estudiantes, reservaciones y auditoría antes de la operación. En ambas ejecuciones del caso había cinco salas y la auditoría estaba vacía.

## Pasos de reproducción

1. El fixture guarda la ruta de base de datos configurada y cierra la conexión anterior.
2. Configura `tmp_path / "salas_fase5.db"` e invoca `inicializar_base_datos()` sobre ese archivo temporal.
3. Registra el estado inicial mediante consultas de solo lectura a las cuatro tablas.
4. Ejecuta exactamente:

   ```python
   registrar_sala("s01", "Duplicada", 5)
   ```

5. Consulta nuevamente las cuatro tablas y registra la respuesta y ambas fotografías antes de las aserciones, en una línea JSON con prefijo `OBSERVACION_CP `.
6. Comprueba que `exito` sea `False` y que no haya cambios persistidos ni nuevos eventos de auditoría.
7. Al terminar, incluso si falla una aserción, el fixture cierra la conexión temporal y restaura la ruta original sin abrir ni modificar la base real.

Para repetir solamente este caso, desde la copia de evaluación que contenga `src/` y `tests/`, puede utilizarse:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD" TZ=America/Costa_Rica python3 -B -m pytest tests/test_salas_ampliacion_fase5.py::test_cp_sal_07_rechaza_duplicado_en_minusculas -vv -rA --tb=long --import-mode=importlib -p no:cacheprovider
```

Este comando aislado se ofrece para reproducción; las ejecuciones documentadas a continuación fueron la ronda de ampliación y la regresión completa, no una tercera ejecución aislada.

## Resultado esperado y observado

| Aspecto | Esperado según el caso | Observado en ambas ejecuciones |
| --- | --- | --- |
| Respuesta | Rechazo, `exito: false`, con mensaje informativo. | `exito: true`; mensaje: `Sala s01 registrada exitosamente.` |
| Catálogo | Conservar cinco filas, sin una nueva sala equivalente a `S01`. | Pasa de cinco a seis filas. Coexisten `S01` y `s01`. |
| Fila original | Mantener `S01`, `Sala Biblioteca 1`, capacidad 4, disponible. | La fila original permanece con esos datos e ID 1. |
| Fila nueva | No crearla. | Se inserta ID 6, código `s01`, nombre `Duplicada`, capacidad 5 y estado `disponible`. |
| Auditoría | Sin evento nuevo por una operación que debería rechazarse. | Se agrega un evento `creacion`, entidad `sala`, identificador `s01`, detalle `Sala s01 registrada correctamente.` |
| Comprobación | La aserción de rechazo debe cumplirse. | Falla en `assert resultado["exito"] is False`, con `assert True is False`. |

Estudiantes y reservaciones permanecieron vacíos. La evidencia demuestra una aceptación incorrecta y un duplicado lógico de código; no demuestra corrupción del archivo ni alteración de las reservas.

La auditoría refleja la creación que el servicio de salas aceptó y confirmó. No se clasifica este evento como un defecto independiente del módulo de auditoría: el fallo documentado es la validación de unicidad de la sala.

## Evidencia y repetición

- [Ampliación: resultados por prueba](../ampliacion/resultados_por_prueba.json): objeto `id_caso = CP-SAL-07`, con respuesta, fotografías completas y estado `fallido`.
- [Ampliación: registro de pytest](../ampliacion/resultado_pytest.txt) y [XML](../ampliacion/resultado_pytest.xml): nodo `tests/test_salas_ampliacion_fase5.py::test_cp_sal_07_rechaza_duplicado_en_minusculas`.
- [Ampliación: registro de ejecución](../ampliacion/registro_ejecucion.json): 33 pruebas, 31 aprobadas y 2 fallidas; este caso corresponde a una de esas dos fallas.
- [Regresión: resultados por prueba](../regresion/resultados_por_prueba.json): el mismo nodo vuelve a fallar con el mismo cambio de datos y respuesta.
- [Regresión: registro de pytest](../regresion/resultado_pytest.txt) y [XML](../regresion/resultado_pytest.xml).
- [Regresión: registro de ejecución](../regresion/registro_ejecucion.json): 231 pruebas, 226 aprobadas, 2 fallidas, 2 `xfail` y 1 omitida. Esta falla no se marcó como `xfail` ni se omitió.
- [Integridad original antes](../integridad_original_antes.json) y [después](../integridad_original_despues.json): respaldan el control de integridad del repositorio original durante estas ejecuciones.

Las dos reproducciones se realizaron en bases temporales separadas del mismo ambiente. No equivalen a una comprobación en otros sistemas operativos ni a un recorrido real por interfaz.

## Análisis estático separado de la observación

En las fuentes evaluadas, `src/model/salas/servicio.py`, función `registrar_sala`, inserta el valor de `codigo` recibido sin normalizarlo ni comprobar de forma explícita la equivalencia entre mayúsculas y minúsculas. En `src/db/esquema.py`, `salas.codigo` se declara `TEXT NOT NULL UNIQUE`, sin una intercalación insensible a mayúsculas especificada en esa columna.

Esto es una explicación estática compatible con el comportamiento observado, no una verificación experimental de una corrección ni una atribución de corrupción a SQLite. El control esperado debe preservar la unicidad insensible a capitalización indicada por CP-SAL-07.

## Condición propuesta de cierre

Corregir la validación o la restricción correspondiente sin modificar el oráculo del caso; repetir CP-SAL-07 y comprobar rechazo, catálogo intacto y ausencia de evento nuevo. Ejecutar también el duplicado exacto CP-SAL-06 y la regresión relacionada. El defecto permanece abierto hasta disponer de evidencia de esa verificación.
