# Casos y resultados de Persona 1

Esta relación corresponde al alcance automatizado de Persona 1; no modifica la matriz grupal de Fase 4 ni declara aprobada la GUI.

| Caso | Requisito | Estado | Pruebas / motivo |
| --- | --- | --- | --- |
| CP-EST-01 | RF-02 | aprobado | `tests/test_estudiantes.py::test_registrar_estudiante_correctamente`<br>`tests/test_estudiantes.py::test_consultar_estudiantes_registrados` |
| CP-EST-02 | RF-02 | aprobado | `tests/test_auditoria_entidades.py::test_operaciones_fallidas_no_generan_eventos` |
| CP-EST-03 | RF-02 | aprobado | `tests/test_estudiantes.py::test_rechazar_carne_duplicado` |
| CP-EST-04 | RF-02 | aprobado | `tests/test_estudiantes_limites_fase5.py::test_cp_est_04_rechaza_carne_de_9_caracteres` |
| CP-EST-05 | RF-02 | aprobado | `tests/test_estudiantes_limites_fase5.py::test_cp_est_05_rechaza_carne_de_11_caracteres` |
| CP-EST-06 | RF-02 | aprobado | `tests/test_estudiantes.py::test_rechazar_datos_invalidos[123456789!-Ana Rodr\xedguez-ana@tec.ac.cr]` |
| CP-EST-07 | RF-02 | aprobado | `tests/test_estudiantes_limites_fase5.py::test_cp_est_07_rechaza_nombre_de_2_caracteres` |
| CP-EST-08 | RF-02 | aprobado | `tests/test_estudiantes_limites_fase5.py::test_cp_est_08_acepta_nombre_de_3_caracteres` |
| CP-EST-09 | RF-02 | aprobado | `tests/test_estudiantes.py::test_rechazar_datos_invalidos[C123456789-Ana Rodr\xedguez-anatec.ac.cr]`<br>`tests/test_estudiantes.py::test_rechazar_datos_invalidos[C123456789-Ana Rodr\xedguez-ana@]`<br>`tests/test_estudiantes.py::test_rechazar_datos_invalidos[C123456789-Ana Rodr\xedguez-ana@@tec.ac.cr]` |
| CP-EST-10 | RF-02 | aprobado | `tests/test_estudiantes.py::test_registrar_con_espacios` |
| CP-EST-11 | RF-03 | aprobado | `tests/test_estudiantes.py::test_consultar_estudiantes_registrados` |
| CP-EST-12 | RF-03 | aprobado | `tests/test_estudiantes.py::test_consultar_sin_estudiantes` |
| CP-EST-13 | RF-03 | aprobado | `tests/test_estudiantes_historial_fase5.py::test_cp_est_13_consulta_incluye_estudiantes_activos_e_inactivos` |
| CP-EST-14 | RF-03 | aprobado | `tests/test_estudiantes.py::test_consultar_estudiantes_ordenados` |
| CP-EST-15 | RF-07 | aprobado | `tests/test_estudiantes.py::test_buscar_reservaciones_existentes` |
| CP-EST-16 | RF-07 | aprobado | `tests/test_estudiantes.py::test_estudiante_sin_reservaciones` |
| CP-EST-17 | RF-07 | aprobado | `tests/test_estudiantes.py::test_buscar_reservaciones_estudiante_inexistente` |
| CP-EST-18 | RF-07 | aprobado | `tests/test_estudiantes_historial_fase5.py::test_cp_est_18_buscar_carne_en_minusculas_devuelve_mismo_historial` |
| CP-EST-19 | RF-07 | aprobado | `tests/test_estudiantes_historial_fase5.py::test_cp_est_19_busqueda_incluye_reservacion_activa_y_cancelada` |
| CP-EST-20 | RF-11 | aprobado | `tests/test_estudiantes_historial_fase5.py::test_cp_est_20_modificar_nombre_y_correo_mantiene_carne_y_estado_activo` |
| CP-EST-21 | RF-11 | aprobado | `tests/test_estudiantes_historial_fase5.py::test_cp_est_21_inactivar_estudiante_conserva_historial_e_identificadores` |
| CP-EST-22 | RF-11 | aprobado | `tests/test_estudiantes.py::test_modificar_estado_a_activo` |
| CP-EST-23 | RF-11 | aprobado | `tests/test_estudiantes.py::test_modificar_estudiante_datos_invalidos[A-ana@tec.ac.cr-activo]`<br>`tests/test_estudiantes.py::test_modificar_estudiante_datos_invalidos[   -ana@tec.ac.cr-activo]`<br>`tests/test_estudiantes.py::test_modificar_estudiante_datos_invalidos[Ana Rodr\xedguez-correo_invalido-activo]`<br>`tests/test_estudiantes.py::test_modificar_estudiante_datos_invalidos[Ana Rodr\xedguez-ana@tec.ac.cr-pendiente]` |
| CP-EST-24 | RF-11; RF-05; RN-01 | aprobado | `tests/test_reservaciones.py::test_rechazar_estudiante_inactivo` |
| CP-EST-25 | RF-11 | no_ejecutado | El caso del plan requiere intentar cambiar el carné en la pantalla de estudiantes, ausente en la versión evaluada. La API identifica por carné y no recibe uno nuevo; esa lectura no sustituye ejecutar el caso gráfico. |
| CP-EST-26 | RF-11 | no_ejecutado | Requiere confirmación/cancelación en una pantalla de modificación de estudiantes ausente. No se implementó una GUI para realizar esta fase. |
| CP-SAL-01 | RF-04 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_01_catalogo_inicial_completo` |
| CP-SAL-02 | RF-04 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_02_orden_ascendente_de_todos_los_codigos` |
| CP-SAL-03 | RF-04; RN-08 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_03_incluye_sala_fuera_de_servicio` |
| CP-SAL-04 | RF-04; RNF-04 | no_ejecutado | Claridad de estados visuales en una vista de salas ausente en la versión evaluada; no se automatizaron clics ni se comprobó apariencia. |
| CP-SAL-05 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_05_registro_valido_aparece_en_catalogo` |
| CP-SAL-06 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_06_rechaza_duplicado_exacto` |
| CP-SAL-07 | RF-12 | fallido | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_07_rechaza_duplicado_en_minusculas` |
| CP-SAL-08 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_08_rechaza_capacidad_cero` |
| CP-SAL-09 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_09_rechaza_capacidad_negativa` |
| CP-SAL-10 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_10_rechaza_capacidad_decimal` |
| CP-SAL-11 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_11_modifica_nombre_y_estado` |
| CP-SAL-12 | RF-12 | no_ejecutado | El caso prevé intentar cambiar un código desde la interfaz. La firma de modificar_sala no recibe un código nuevo, pero no demuestra el caso gráfico. |
| CP-SAL-13 | RF-12 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_13_reduce_capacidad_sin_reservas_futuras` |
| CP-SAL-14 | RF-12; RN-07 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_14_rechaza_capacidad_menor_a_reserva_futura` |
| CP-SAL-15 | RF-12; RN-07 | aprobado | `tests/test_salas_ampliacion_fase5.py::test_cp_sal_15_acepta_capacidad_igual_a_reserva_futura` |
| CP-SAL-16 | RF-12; RNF-04 | no_ejecutado | Confirmación/cancelación de la modificación de sala: requiere una vista específica ausente en la versión evaluada. |
| CP-DIS-01 | RF-08 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_01_consulta_horario_libre` |
| CP-DIS-02 | RF-08; RN-08 | aprobado | `tests/test_salas.py::test_rf08_disponibilidad_sala_fuera_servicio` |
| CP-DIS-03 | RF-08; RN-02 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_03_rechaza_fecha_pasada` |
| CP-DIS-04 | RF-08; RN-03 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_04_rechaza_hora_pasada_de_hoy` |
| CP-DIS-05 | RF-08; RN-04 | aprobado | `tests/test_salas.py::test_rf08_disponibilidad_hora_incompleta` |
| CP-DIS-06 | RF-08; RN-05 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_06_rechaza_horarios_fuera_de_jornada[07:00-1]`<br>`tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_06_rechaza_horarios_fuera_de_jornada[20:00-1]`<br>`tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_06_rechaza_horarios_fuera_de_jornada[19:00-2]` |
| CP-DIS-07 | RF-08; RN-06 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_07_rechaza_tres_horas` |
| CP-DIS-08 | RF-08; RN-09 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_08_rechaza_superposicion_total` |
| CP-DIS-09 | RF-08; RN-09 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_09_rechaza_superposicion_inicial` |
| CP-DIS-10 | RF-08; RN-09 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_10_rechaza_superposicion_final` |
| CP-DIS-11 | RF-08; RN-09 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_11_rechaza_superposicion_envolvente` |
| CP-DIS-12 | RF-08; RN-10 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_12_permite_horarios_consecutivos[12:00-1]`<br>`tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_12_permite_horarios_consecutivos[08:00-2]` |
| CP-DIS-13 | RF-08; RNF-06 | aprobado | `tests/test_disponibilidad_ampliacion_fase5.py::test_cp_dis_13_consulta_no_persiste_cambios` |
| CP-INT-08 | RNF-04 | aprobado | `tests/test_selector_fecha.py::test_calendario_inicia_en_lunes_y_mantiene_seis_filas` |
| CP-INT-09 | RNF-04 | aprobado | `tests/test_selector_fecha.py::test_navegacion_de_meses_cambia_de_anio_correctamente` |
| CP-INT-10 | RNF-04 | aprobado | `tests/test_tema.py::test_recursos_de_identidad_visual_estan_disponibles` |
| CP-INT-11 | RNF-04 | aprobado | `tests/test_tema.py::test_fuente_interfaz_elige_primera_geometrica_disponible` |
| CP-INT-12 | RNF-04 | aprobado | `tests/test_tema.py::test_tipografia_global_actualiza_fuentes_nativas` |
| F5-DIS-01 | RF-08; RN-09 | fallido | `tests/test_disponibilidad_ampliacion_fase5.py::test_f5_dis_01_hora_sin_cero_no_ignora_conflicto` |

Resultados del plan: 54 aprobados, 1 fallido y 5 no ejecutados. Caso adicional F5-DIS-01: fallido.

Los datos esperados, observaciones obtenidas, límites y evidencias están en `casos_resultados.json`. Se preservan especialmente los límites del calendario, las fuentes simuladas y los casos que necesitan una vista gráfica ausente.
