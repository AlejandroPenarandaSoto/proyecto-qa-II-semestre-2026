
import re

#Para validar carne
def validar_carne(carne):
    """Normaliza y valida el carné del estudiante."""

    carne = carne.strip().upper() #strip() elimina espacios en blanco al inicio y final del texto

    if not re.fullmatch(r"[A-Z0-9]{10}", carne): #re.fullmatch cumprueba que cumpla lo que est adentro
        return False, "El carné debe tener exactamente 10 caracteres alfanuméricos."

    return True, carne

#Para validar nombre
def validar_nombre(nombre):
    """Valida el nombre completo del estudiante."""

    nombre = nombre.strip()

    if len(nombre.replace(" ", "")) < 3:
        return False, "El nombre debe contener al menos 3 caracteres sin contar espacios."

    return True, nombre

#Para validar correo
def validar_correo(correo):
    """Valida el formato básico del correo electrónico."""

    correo = correo.strip()

    if correo.count("@") != 1:
        return False, "El correo debe contener exactamente un @."

    usuario, dominio = correo.split("@")

    if not usuario or "." not in dominio:
        return False, "El correo electrónico no es válido."

    return True, correo

#Para validar estado
def validar_estado(estado):
    """Valida que el estado sea activo o inactivo."""

    estado = estado.strip().lower()

    if estado not in ("activo", "inactivo"):
        return False, "El estado debe ser activo o inactivo."

    return True, estado
