"""Reglas de negocio de las reservaciones, sin acceso a la base de datos.

Todas las funciones son puras: reciben valores (incluida la hora actual) y
devuelven un resultado o lanzan ``ReservacionInvalida`` con el mensaje para
el usuario.
"""

from datetime import datetime, timedelta

FORMATO_FECHA = "%Y-%m-%d"
FORMATO_HORA = "%H:%M"
HORA_APERTURA = 8
HORA_CIERRE = 20
DURACIONES_PERMITIDAS = (1, 2)
LIMITE_RESERVACIONES_ACTIVAS = 3
SEMANAS_MINIMAS = 2
SEMANAS_MAXIMAS = 8


class ReservacionInvalida(Exception):
    """Una regla de negocio impide la operación. El texto es para el usuario."""


def es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_cantidad_personas(cantidad):
    """RN-07: la cantidad de personas es un entero positivo."""
    if not es_entero(cantidad) or cantidad <= 0:
        raise ReservacionInvalida(
            "La cantidad de personas debe ser un entero mayor que cero."
        )


def validar_horario(fecha, hora_inicio, duracion, ahora):
    """RN-02 a RN-06. Devuelve la fecha y la hora listas para guardar."""
    if not es_entero(duracion) or duracion not in DURACIONES_PERMITIDAS:
        raise ReservacionInvalida("La duración permitida es únicamente de 1 o 2 horas.")

    fecha, hora_inicio = _normalizar_fecha_y_hora(fecha, hora_inicio)
    inicio = datetime.strptime(hora_inicio, FORMATO_HORA)

    if inicio.minute != 0:
        raise ReservacionInvalida(
            "La hora debe comenzar exactamente en una hora completa (ej. 08:00)."
        )
    hoy = ahora.strftime(FORMATO_FECHA)
    if fecha < hoy:
        raise ReservacionInvalida("La fecha no puede ser anterior a la fecha actual.")
    if fecha == hoy and hora_inicio <= ahora.strftime(FORMATO_HORA):
        raise ReservacionInvalida("El horario solicitado para hoy ya transcurrió.")
    if inicio.hour < HORA_APERTURA or inicio.hour + duracion > HORA_CIERRE:
        raise ReservacionInvalida("El horario permitido de uso es de 08:00 a 20:00.")

    return fecha, hora_inicio


def _normalizar_fecha_y_hora(fecha, hora_inicio):
    """DEF-F7-P2-01: convierte '2027-1-5' y '9:00' a '2027-01-05' y '09:00'.

    Con el formato canónico, comparar fechas u horas como texto equivale a
    compararlas en el tiempo, y lo que se guarda coincide con lo que se busca.
    """
    fecha_dt = _interpretar(fecha, FORMATO_FECHA)
    hora_dt = _interpretar(hora_inicio, FORMATO_HORA)
    if fecha_dt is None or hora_dt is None:
        raise ReservacionInvalida("Formato de fecha (AAAA-MM-DD) u hora (HH:MM) inválido.")
    return fecha_dt.strftime(FORMATO_FECHA), hora_dt.strftime(FORMATO_HORA)


def _interpretar(texto, formato):
    """Convierte el texto a datetime, o devuelve None si no cumple el formato."""
    if not isinstance(texto, str):
        return None
    try:
        return datetime.strptime(texto.strip(), formato)
    except ValueError:
        return None


def calcular_hora_fin(hora_inicio, duracion):
    inicio = datetime.strptime(hora_inicio, FORMATO_HORA)
    return (inicio + timedelta(hours=duracion)).strftime(FORMATO_HORA)


def se_traslapan(inicio, fin, otro_inicio, otro_fin):
    """RN-09 y RN-10: dos franjas chocan si se superponen; las consecutivas no."""
    return inicio < otro_fin and fin > otro_inicio


def esta_vigente(fecha, hora_inicio, duracion, ahora):
    """Una reservación es presente o futura mientras no haya terminado."""
    inicio = datetime.strptime(f"{fecha} {hora_inicio}", f"{FORMATO_FECHA} {FORMATO_HORA}")
    return inicio + timedelta(hours=duracion) > ahora


def contar_cupos_ocupados(reservaciones_activas, ahora):
    """RN-11 (DEF-F5-P2-01): cada reservación activa presente o futura ocupa un
    cupo, también cada ocurrencia de una serie."""
    return sum(
        esta_vigente(
            reservacion["fecha"],
            reservacion["hora_inicio"],
            reservacion["duracion_horas"],
            ahora,
        )
        for reservacion in reservaciones_activas
    )


def validar_limite(cupos_ocupados, cupos_nuevos=1):
    """RN-11: un estudiante no puede superar el límite de reservaciones activas."""
    if cupos_ocupados + cupos_nuevos > LIMITE_RESERVACIONES_ACTIVAS:
        raise ReservacionInvalida(
            f"El estudiante ya tiene el máximo de {LIMITE_RESERVACIONES_ACTIVAS} "
            "reservaciones activas."
        )


def fechas_semanales(fecha, semanas):
    """RF-14: fechas de una serie semanal de 2 a 8 ocurrencias."""
    if not es_entero(semanas) or not SEMANAS_MINIMAS <= semanas <= SEMANAS_MAXIMAS:
        raise ReservacionInvalida(
            f"La recurrencia debe abarcar entre {SEMANAS_MINIMAS} y {SEMANAS_MAXIMAS} semanas."
        )
    fecha_inicial = _interpretar(fecha, FORMATO_FECHA)
    if fecha_inicial is None:
        raise ReservacionInvalida("La fecha debe utilizar el formato AAAA-MM-DD.")
    return [
        (fecha_inicial + timedelta(weeks=semana)).strftime(FORMATO_FECHA)
        for semana in range(semanas)
    ]


def siguiente_id_serie(series_existentes):
    numeros = [
        int(serie[2:])
        for serie in series_existentes
        if serie.startswith("SR") and serie[2:].isdigit()
    ]
    return f"SR{max(numeros, default=0) + 1:04d}"


def formatear_id(identificador):
    return f"R{int(identificador):04d}"


def parsear_id(id_reservacion):
    """Acepta 'R0001', 'r0001', '1' o 1. Devuelve el entero interno o None."""
    if isinstance(id_reservacion, str):
        texto = id_reservacion.strip().upper().removeprefix("R")
        id_reservacion = int(texto) if texto.isdigit() else None
    if es_entero(id_reservacion) and id_reservacion > 0:
        return id_reservacion
    return None
