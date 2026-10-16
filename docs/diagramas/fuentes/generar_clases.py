"""Genera el diagrama de clases a partir de los modelos de Django.

A diferencia del entidad-relación, que describe el almacenamiento, aquí se
incluyen los métodos y propiedades que cada clase expone: son la lógica de
dominio del sistema y lo que distingue un diagrama de clases de uno de datos.
"""
import inspect
import os
import sys

sys.path.insert(0, '/tmp/smilee/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost')

import django                                                      # noqa: E402
django.setup()

from django.apps import apps                                       # noqa: E402
from django.db import models as djm                                # noqa: E402

PAQUETES = [
    ('usuarios', 'Seguridad y Usuarios', '#EEF2FF', '#4F46E5'),
    ('catalogo', 'Catálogo Odontológico', '#F0FDF4', '#059669'),
    ('pacientes', 'Pacientes', '#FEF3C7', '#D97706'),
    ('agenda', 'Agenda y Citas', '#FEE2E2', '#DC2626'),
    ('clinico', 'Expediente Clínico y Cobros', '#F3E8FF', '#7C3AED'),
    ('inteligencia', 'Inteligencia', '#E0F2FE', '#0284C7'),
    ('reportes', 'Reportes', '#F1F5F9', '#64748B'),
]

TIPOS = {
    'CharField': 'str', 'EmailField': 'str', 'TextField': 'str',
    'BooleanField': 'bool', 'DateField': 'date', 'TimeField': 'time',
    'DateTimeField': 'datetime', 'IntegerField': 'int',
    'PositiveIntegerField': 'int', 'PositiveSmallIntegerField': 'int',
    'SmallIntegerField': 'int', 'BigIntegerField': 'int',
    'DecimalField': 'Decimal', 'FloatField': 'float',
    'AutoField': 'int', 'BigAutoField': 'int',
}

# Atributos de apoyo que no aportan al diagrama; se omiten para que cada clase
# quepa en pantalla sin perder lo que la caracteriza.
OMITIR = {'id', 'creado', 'password', 'last_login', 'is_superuser', 'username',
          'is_staff', 'is_active', 'date_joined', 'first_name', 'last_name'}

MAX_ATRIBUTOS = 8


def publicos(cls):
    """Métodos y propiedades definidos en la clase, no heredados."""
    metodos, propiedades = [], []
    for nombre, valor in vars(cls).items():
        if nombre.startswith('_') and nombre != '__str__':
            continue
        if isinstance(valor, property):
            propiedades.append(nombre)
        elif inspect.isfunction(valor):
            firma = inspect.signature(valor)
            args = [p for p in firma.parameters if p not in ('self', 'cls')]
            metodos.append(f'{nombre}({", ".join(args)})')
        elif isinstance(valor, classmethod):
            firma = inspect.signature(valor.__func__)
            args = [p for p in firma.parameters if p not in ('self', 'cls')]
            metodos.append(f'{nombre}({", ".join(args)}) [clase]')
    return sorted(propiedades), sorted(metodos)


def main():
    l = ['@startuml', 'title Diagrama de clases del sistema SmileeSync', '',
         'skinparam shadowing false', 'skinparam backgroundColor white',
         'skinparam defaultFontName Arial', 'skinparam defaultFontSize 11',
         'skinparam dpi 150', 'skinparam ArrowColor #334155',
         'skinparam classAttributeIconSize 0',
         'skinparam package {', '  BorderColor #94A3B8',
         '  BackgroundColor #FCFCFD', '  FontStyle bold', '}',
         'hide empty members', '']

    nombres, relaciones = {}, []
    for etiqueta, titulo, relleno, borde in PAQUETES:
        try:
            cfg = apps.get_app_config(etiqueta)
        except LookupError:
            continue
        modelos = list(cfg.get_models())
        if not modelos:
            continue
        l.append(f'package "{titulo}" {{')
        for m in modelos:
            cls = m.__name__
            nombres[m] = cls
            l.append(f'  class {cls} #{relleno.lstrip("#")} {{')

            mostrados = 0
            for campo in m._meta.fields:
                if campo.attname in OMITIR or campo.primary_key:
                    continue
                if campo.is_relation:
                    continue
                if mostrados >= MAX_ATRIBUTOS:
                    l.append('    ...')
                    break
                tipo = TIPOS.get(type(campo).__name__, 'str')
                l.append(f'    +{campo.name}: {tipo}')
                mostrados += 1

            props, metodos = publicos(m)
            if props or metodos:
                l.append('    --')
            for p in props:
                l.append(f'    +{p} «propiedad»')
            for me in metodos:
                if me == '__str__()':
                    continue
                l.append(f'    +{me}')
            l.append('  }')
        l.append('}')
        l.append('')

    for m in nombres:
        for campo in m._meta.fields:
            if not campo.is_relation or campo.related_model is None:
                continue
            if campo.related_model not in nombres:
                continue
            a, b = nombres[campo.related_model], nombres[m]
            cardinalidad = '"1" --> "0..*"'
            if type(campo).__name__ == 'OneToOneField':
                cardinalidad = '"1" --> "0..1"'
            relaciones.append(f'{a} {cardinalidad} {b} : {campo.name}')

    l.extend(sorted(set(relaciones)))
    l.append('@enduml')

    with open('clases.puml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(l) + '\n')
    print(f'{len(nombres)} clases, {len(set(relaciones))} asociaciones')


if __name__ == '__main__':
    main()
