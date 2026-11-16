# Revisión de cierre – Fase 8

Verificación manual del criterio de finalización (sección 21 del enunciado): los datos persisten, las reglas se aplican y los errores de entrada no terminan el programa.

| Elemento | Detalle |
|---|---|
| Versión verificada | Rama `dev-vega`, commit `63911b6` |
| Fecha | 15 de noviembre de 2026 |
| Equipo | MacBook Air, macOS |
| Ejecución | `python3 -m src.main` desde la raíz del repositorio |
| Estado inicial | Se eliminó `src/db/reservas.db`; la aplicación la volvió a crear con los datos iniciales (5 salas y 3 estudiantes) |
| Responsable | Alejandro Vega Gamboa (Persona 5) |

Todas las reservaciones se hicieron para el 20 de noviembre de 2026, con duración de 1 hora salvo que se indique otra.

## A. Persistencia

| # | Paso y datos | Resultado esperado | Resultado obtenido | Evidencia |
|---|---|---|---|---|
| 1 | Abrir Gestión → Estudiantes con la base recién creada | Aparecen los 3 estudiantes iniciales | A001234567, B009876543 y C004567890 (inactivo) | `01_estudiantes_iniciales.jpg` |
| 2 | Registrar B123456789, María Pérez, maria@estudiantec.cr | Se registra como activo | "Estudiante registrado correctamente." | `02_registro_estudiante.jpg` |
| 3 | Nueva reservación: B123456789, S02, 10:00, 3 personas | Se crea R0001 y aparece en el panel | R0001, María Pérez, S02, 10:00–11:00, activa | `03_reserva_creada_R0001.jpg` |
| 4 | Salir y volver a abrir la aplicación | R0001 y María Pérez se conservan | R0001 sigue en el panel con el nombre de María Pérez | `04_reserva_persiste_al_reabrir.jpg` |

## B. Reglas de negocio

| # | Paso y datos | Resultado esperado | Resultado obtenido | Evidencia |
|---|---|---|---|---|
| 5 | Nueva reservación: A001234567, S02, 10:00, 2 personas | Rechazo por choque con R0001 (RN-09) | "Conflicto: la sala tiene una reservación activa de 10:00 a 11:00." | `05_rechazo_choque_horario.jpg` |
| 6 | Nueva reservación: A001234567, S05 (capacidad 1), 3 personas | Rechazo por capacidad (RN-07) | "La cantidad de personas no puede ser mayor que la capacidad de la sala." | `06_rechazo_capacidad.jpg` |
| 7 | Nueva reservación: A001234567, S04, 2 personas | Rechazo por sala fuera de servicio (RN-08) | "La sala se encuentra fuera de servicio." | `07_rechazo_sala_fuera_servicio.jpg` |
| 8 | Nueva reservación: C004567890 (inactivo), S01, 2 personas | Rechazo por estudiante inactivo (RN-01) | "Solo un estudiante activo puede crear reservaciones." | `08_rechazo_estudiante_inactivo.jpg` |
| 9 | Consultar disponibilidad: S02, 10:00, 1 hora | No disponible por R0001 (RF-08) | "No disponible. Conflicto: la sala tiene una reservación activa de 10:00 a 11:00." | `09_disponibilidad_conflicto.jpg` |

## C. Entradas inválidas

| # | Paso y datos | Resultado esperado | Resultado obtenido | Evidencia |
|---|---|---|---|---|
| 10 | Registrar estudiante con carné `ABC`, nombre Ana, correo ana@correo | Mensaje de error sin cerrar la aplicación (RF-02, RNF-05) | "El carné debe tener exactamente 10 caracteres alfanuméricos." | `10_rechazo_carne_invalido.jpg` |
| 11 | Registrar sala con código ` S01 ` (con espacios), nombre Prueba, capacidad 3 | Rechazo por código duplicado (RF-12, DEF-F5-P4-01) | "El código de sala ya se encuentra registrado." | `11_rechazo_codigo_sala_duplicado.jpg` |
| 12 | Registrar sala S07 con nombre vacío, capacidad 3 | Rechazo por nombre vacío (RF-12, DEF-F5-P4-02) | "El nombre de la sala es obligatorio." | `12_rechazo_nombre_sala_vacio.jpg` |
| 13 | Nueva reservación: A001234567, S01, 19:00, 2 horas, 2 personas | Rechazo porque termina después de las 20:00 (RN-05) | "El horario permitido de uso es de 08:00 a 20:00." | `13_rechazo_horario_fuera_de_rango.jpg` |

## Resultado

13 de 13 verificaciones correctas. Después de cada rechazo, el panel, la lista de estudiantes y la lista de salas no cambiaron, y la aplicación siguió abierta.

Observaciones:

- En las capturas 5 a 8 y 11 el mensaje cubre parte del formulario; los datos usados son los indicados en la tabla.
- En la captura 11 los espacios del código no son visibles. El rechazo de códigos con espacios también está cubierto por `tests/test_salas_verificacion_fase8.py`.
- Las reglas de reservaciones RN-11 (series y límite de 3) y la normalización de horas como `9:00` (DEF-F5-P2-01 y DEF-F7-P2-01) no forman parte de esta revisión, porque su corrección estaba pendiente al momento de ejecutarla.
