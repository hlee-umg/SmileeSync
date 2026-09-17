"""Validadores compartidos por los módulos del sistema.

Centralizar aquí estas reglas evita que cada módulo implemente su propia
versión: el criterio con que se valida el nombre de un usuario debe ser el
mismo con que se valida el nombre de un paciente.
"""
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# Letras (con tildes y ñ), espacios, apóstrofos y guiones, para admitir nombres
# compuestos como "María José" o apellidos como "López-García".
NOMBRE_REGEX = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[\s'-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")

# Un código alfanumérico con guiones, por ejemplo PAC-0001 o PROC-014.
CODIGO_REGEX = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]$')


def validar_nombre(valor, etiqueta='nombre'):
    """Rechaza números y caracteres especiales en nombres y apellidos."""
    valor = (valor or '').strip()
    if not valor:
        raise ValidationError(f'El campo {etiqueta} es obligatorio.')
    if not NOMBRE_REGEX.match(valor):
        raise ValidationError(
            f'El {etiqueta} solo puede contener letras y espacios '
            '(no se permiten números ni caracteres especiales).')
    return valor


# Mensaje único de correo inválido. Se aplica también al campo del formulario
# (no solo al método clean) para que el usuario vea siempre el mismo texto, sea
# que falle la validación del campo o la del formulario.
MENSAJE_EMAIL = 'Ingrese un correo electrónico válido, con el formato usuario@dominio.com.'


def unificar_mensaje_email(campo):
    """Sustituye el mensaje genérico de Django por el mensaje del sistema."""
    campo.error_messages['invalid'] = MENSAJE_EMAIL
    return campo


def validar_email_real(valor, obligatorio=True):
    """Exige el formato usuario@dominio.com. Si no es obligatorio, admite vacío."""
    valor = (valor or '').strip().lower()
    if not valor:
        if obligatorio:
            raise ValidationError('El correo electrónico es obligatorio.')
        return valor
    try:
        validate_email(valor)
    except ValidationError:
        raise ValidationError(MENSAJE_EMAIL)
    return valor


def validar_codigo(valor, etiqueta='código'):
    """Valida un código de identificación alfanumérico."""
    valor = (valor or '').strip().upper()
    if not valor:
        raise ValidationError(f'El {etiqueta} es obligatorio.')
    if not CODIGO_REGEX.match(valor):
        raise ValidationError(
            f'El {etiqueta} solo admite letras, números y guiones '
            '(por ejemplo, PAC-0001).')
    return valor


def validar_telefono(valor):
    """Admite dígitos, espacios, guiones y el signo más; permite dejarlo vacío."""
    valor = (valor or '').strip()
    if not valor:
        return valor
    if not re.match(r'^[\d\s\-+()]{7,20}$', valor):
        raise ValidationError(
            'El teléfono solo puede contener números, espacios y guiones.')
    return valor
