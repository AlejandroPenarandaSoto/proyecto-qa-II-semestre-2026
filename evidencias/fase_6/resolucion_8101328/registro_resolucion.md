# Corrección y verificación de Fase 6

Alejandro Vega Gamboa realizó la revisión central de los nueve defectos incluidos en la entrega de Fase 5 recibida el 2 de noviembre de 2026. Se confirmaron y corrigieron cinco; los otros cuatro se rechazaron con justificación y pruebas de contraste. La regresión de la versión corregida terminó con **248 ítems aprobados**, sin fallos, xfail, omisiones ni errores de preparación.

## Versión y alcance

El trabajo parte de `dev-vega`, commit `8101328`, que contiene el código de `cc9fab4` y los aportes de pruebas de Persona 1. Se corrigen salas, disponibilidad, inicialización y exportación CSV. Reservaciones, recurrencias, panel, controlador e interfaz conservan su código productivo. La entrega se prepara en `dev-vega`; no incluye una integración a `main` ni a `qa`.

La fuente de los reportes es el PDF de entrega de Fase 5, de 18 páginas. La revisión cubre los nueve identificadores de ese archivo. Una actualización posterior de Tamara deberá contrastarse antes de cerrar el informe grupal definitivo.

## Decisiones por defecto

| Defecto | Resolución |
| --- | --- |
| BUG-P1-SAL-01 | Corregido y verificado |
| BUG-P1-DIS-01 | Corregido y verificado |
| BUG-INI-01 | Corregido y verificado |
| BUG-INI-02 | Corregido y verificado |
| BUG-P5-REP-01 | Corregido y verificado |
| BUG-RES-01 | Rechazado con justificación |
| BUG-RES-02 | Rechazado con justificación |
| BUG-REC-01 | Rechazado con justificación |
| BUG-PAN-01 | Rechazado con justificación |

## Correcciones realizadas

### BUG-P1-SAL-01: Código de sala duplicado por capitalización

Se reprodujo el registro de `s01` cuando ya existía `S01`. El servicio ahora consulta el código sin distinguir mayúsculas antes de insertar. Rechaza el duplicado sin escribir datos ni generar un evento de auditoría. La prueba original CP-SAL-07 pasó después del arreglo; las nuevas verificaciones comprueban también el caso inverso y conservan el registro válido de un código nuevo en minúsculas. No se cambió el esquema ni se fusionaron duplicados históricos.

### BUG-P1-DIS-01: Disponibilidad incorrecta con la hora 9 00

Se reprodujo una respuesta de disponibilidad ante un traslape de 09:00 a 10:00. Después de interpretar la entrada, el servicio normaliza la hora a `HH:MM` antes de compararla. La prueba original F5-DIS-01 aprueba; las nuevas verificaciones comprueban que `9:00` y `09:00` coinciden en una franja libre y que una hora transcurrida del día actual se rechaza. Las consultas conservan la base sin cambios.

### BUG-INI-01: Ausencia de estudiantes iniciales

La reproducción sin la marca xfail confirmó una tabla vacía. Se incorporaron Andrea Solano, Carlos Méndez y Daniela Rojas, con los carnés, correos y estados del plan final de Fase 4 y su matriz v3. El PDF, página 11, establece las identidades y estados; la matriz, hoja Casos detallados y fila CP-INI-02, aporta los correos. No se atribuyen estos datos a un enunciado primario que no se haya comprobado.

La semilla se ejecuta solo si la tabla está vacía y conserva los registros propios o modificados. Salas y estudiantes se cargan en una transacción conjunta: un error al insertar estudiantes revierte ambas inserciones. La prueba original y cuatro verificaciones nuevas aprobaron. La garantía transaccional corresponde a los datos; el archivo y el esquema pueden permanecer creados tras un error.

### BUG-INI-02: Excepción con una ruta de base de datos inválida

Se reprodujo `NotADirectoryError` cuando un componente de la ruta era un archivo. El inicializador ahora incluye la comprobación de existencia dentro del bloque protegido y captura `sqlite3.Error` y `OSError`. Devuelve un resultado de fallo con mensaje informativo. La prueba original y dos verificaciones nuevas aprobaron, incluyendo permiso denegado simulado y recuperación posterior con una ruta válida. Se retiraron las dos marcas xfail de inicialización tras verificar las correcciones.

### BUG-P5-REP-01: Temporal CSV residual tras un error de escritura

La reproducción derivada del reporte confirmó residuos al fallar la escritura de encabezados o filas. El temporal se creaba, pero el llamador todavía desconocía su ruta. Ahora se registra la ruta al abrirlo y se limpia ante un error de escritura o cierre. Se conserva también la limpieza cuando falla el reemplazo del destino, la respuesta pública y el contexto de la excepción.

Antes del arreglo, las dos variantes de escritura fallaron y el control de reemplazo aprobó. Después aprobaron los 16 ítems de reportes y su diálogo, incluidos los tres escenarios nuevos. Se comprobó que el CSV anterior conserva sus bytes, la base y la auditoría permanecen intactas y no quedan temporales ocultos en los escenarios probados. Si el sistema operativo deniega una eliminación, se conserva la advertencia de limpieza.

## Reportes rechazados con justificación

### BUG-RES-01: Fecha inexistente

La llamada real con `2026-02-30` devuelve `exito=False` y un mensaje de formato, sin lanzar ValueError ni modificar datos o auditoría. La conversión de fecha ya estaba protegida en el código evaluado. Se rechaza el defecto descrito por no reproducirse y se incorpora una prueba que protege este comportamiento.

### BUG-RES-02: Cambio de sala y capacidad

Cambiar una reserva de cuatro personas de S02 a S05, de capacidad uno, se rechaza con un mensaje de capacidad. La fotografía de las tablas antes y después coincide. El servicio ya revalida los datos finales de la modificación; se rechaza el defecto descrito y se conserva el escenario como regresión.

### BUG-REC-01: Vínculo de una ocurrencia con su serie

Modificar únicamente la hora de la segunda ocurrencia conserva el mismo `serie_id` en las tres reservas y no altera las otras dos. El UPDATE productivo no escribe esa columna. La API real devuelve diccionarios con `serie_id`; no utiliza el atributo `id_serie` supuesto por la prueba publicada. Se rechaza el defecto descrito sin cambiar la lógica productiva.

### BUG-PAN-01: Ocupación después de cancelar una serie

Tras cancelar desde la primera ocurrencia, una consulta nueva devuelve próximas vacías y ocupación cero para la sala. Las salas siguen formando parte del catálogo aunque tengan cero reservas. Su presencia no demuestra ocupación. El servicio consulta SQLite en cada llamada; se rechaza el escenario descrito de datos sin actualizar. Esta prueba de servicio no certifica visualmente una ventana real.

Los cuatro escenarios aprobaron en un contraste independiente anterior a la nueva semilla y en la regresión final. Los archivos de reservaciones, panel, controlador e interfaz mantienen las mismas huellas que en `cc9fab4`. Las pruebas publicadas en `dev-ernesto`, commit `bcf1cfe`, producen cuatro errores de preparación por fixtures ausentes y presuponen una API distinta. Ese resultado se conserva por separado; no se cuenta como cuatro fallos productivos ni como cuatro aprobaciones. Las verificaciones de Fase 6 usan las funciones reales y se identifican como pruebas independientes.

## Regresión y conservación de evidencias

La carga de estudiantes hizo visibles diez fallos de preparación o expectativas que presuponían una tabla vacía. Se conservaron sus resultados. En cuatro fixtures se vacía exclusivamente la tabla estudiantes de su base temporal para construir ese escenario; las aserciones se mantienen. La prueba de persistencia utiliza el identificador realmente insertado y compara fotografías completas antes y después de reinicializar.

La suite final contiene los 231 ítems de la rama base y 17 nuevos. El 2 de noviembre, a las 18:46, hora de Costa Rica, aprobó sus 248 ítems con código de salida cero. Ambiente: macOS 27.0.1 ARM64, Python 3.14.7, pytest 9.1.1 y SQLite 3.50.4. Los ítems automatizados no equivalen al número de casos documentales; no se suman corridas sucesivas como pruebas nuevas.

El registro, las fuentes de requisitos y las salidas TXT, JUnit y JSON se conservan en la carpeta `evidencias/fase_6/resolucion_8101328`. Cada ejecución registra versión, comando, fechas y huellas antes y después. Las pruebas se realizaron con SQLite temporal. La base de datos original y las evidencias de Fase 5 permanecen intactas. No se abrieron ventanas ni se automatizaron clics; los casos manuales pendientes no se convierten en aprobados por estos resultados.

Los compañeros pueden utilizar este registro para documentar la resolución de sus módulos. Cualquier reproducción posterior que contradiga un rechazo deberá conservar su versión, datos y evidencia para reabrir el defecto correspondiente.
