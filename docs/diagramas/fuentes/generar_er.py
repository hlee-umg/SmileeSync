"""Genera el diagrama entidad-relación a partir de los modelos reales.

Se construye leyendo el esquema que Django tiene cargado, de modo que el
diagrama del documento no pueda quedar desfasado del código: cualquier campo
nuevo aparece en el ER en cuanto se vuelve a generar.
"""
import os
import sys

sys.path.insert(0, '/tmp/smilee/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost')

import django                                                      # noqa: E402
django.setup()

from django.apps import apps                                       # noqa: E402

APLICACIONES = ['usuarios', 'catalogo', 'pacientes', 'agenda', 'clinico',
                'inteligencia', 'reportes']

TIPOS = {
    'AutoField': 'serial', 'BigAutoField': 'bigserial',
    'CharField': 'varchar', 'EmailField': 'varchar', 'SlugField': 'varchar',
    'TextField': 'text', 'BooleanField': 'boolean',
    'DateField': 'date', 'TimeField': 'time', 'DateTimeField': 'timestamp',
    'IntegerField': 'integer', 'PositiveIntegerField': 'integer',
    'SmallIntegerField': 'smallint', 'PositiveSmallIntegerField': 'smallint',
    'BigIntegerField': 'bigint', 'DecimalField': 'numeric',
    'FloatField': 'double', 'ForeignKey': 'bigint', 'OneToOneField': 'bigint',
}

# Relaciones de auditoría: las tablas de histórico referencian por identificador
# entero, sin llave foránea, para que el registro sobreviva a lo que describe.
AUDITORIA = [
    ('USUARIO', 'HISTORIAL_USUARIO'),
    ('PACIENTE', 'HISTORIAL_PACIENTE'),
    ('CITA', 'HISTORIAL_CITA'),
    ('PLAN_TRATAMIENTO', 'HISTORIAL_PLAN'),
]

VERBOS = {
    ('ROL', 'USUARIO'): 'asigna permisos a',
    ('USUARIO', 'ODONTOLOGO'): 'es cuenta de',
    ('ESPECIALIDAD', 'PROCEDIMIENTO'): 'clasifica',
    ('ESPECIALIDAD', 'ODONTOLOGO'): 'define perfil de',
    ('PACIENTE', 'ANTECEDENTE_MEDICO'): 'presenta',
    ('ODONTOLOGO', 'HORARIO_DISPONIBILIDAD'): 'declara',
    ('ODONTOLOGO', 'AUSENCIA_ODONTOLOGO'): 'registra',
    ('PACIENTE', 'CITA'): 'solicita',
    ('ODONTOLOGO', 'CITA'): 'atiende',
    ('PROCEDIMIENTO', 'CITA'): 'se aplica en',
    ('UNIDAD_DENTAL', 'CITA'): 'se ocupa en',
    ('CITA', 'DATO_ENTRENAMIENTO'): 'genera dataset',
    ('CITA', 'PREDICCION'): 'recibe',
    ('MODELO_VERSION', 'PREDICCION'): 'produce',
    ('PACIENTE', 'HALLAZGO'): 'presenta en su odontograma',
    ('NOTA_CLINICA', 'HALLAZGO'): 'documenta',
    ('CITA', 'NOTA_CLINICA'): 'se documenta en',
    ('PACIENTE', 'NOTA_CLINICA'): 'acumula',
    ('ODONTOLOGO', 'NOTA_CLINICA'): 'redacta',
    ('PACIENTE', 'PLAN_TRATAMIENTO'): 'acuerda',
    ('ODONTOLOGO', 'PLAN_TRATAMIENTO'): 'responde por',
    ('PLAN_TRATAMIENTO', 'DETALLE_PLAN'): 'se desglosa en',
    ('PROCEDIMIENTO', 'DETALLE_PLAN'): 'se presupuesta en',
    ('CITA', 'DETALLE_PLAN'): 'ejecuta',
    ('PLAN_TRATAMIENTO', 'PAGO'): 'se abona con',
}


def tabla(modelo):
    return modelo._meta.db_table.upper()


def tipo_sql(campo):
    nombre = type(campo).__name__
    base = TIPOS.get(nombre, 'varchar')
    if nombre == 'DecimalField':
        return f'numeric_{campo.max_digits}_{campo.decimal_places}'
    return base


def main():
    modelos = []
    for etiqueta in APLICACIONES:
        try:
            cfg = apps.get_app_config(etiqueta)
        except LookupError:
            continue
        modelos.extend(cfg.get_models())

    nombres = {m: tabla(m) for m in modelos}
    lineas = ['erDiagram']

    # ------------------------------------------------------------ relaciones
    vistas = set()
    for m in modelos:
        for campo in m._meta.fields:
            if not campo.is_relation or campo.related_model is None:
                continue
            destino = campo.related_model
            if destino not in nombres:
                continue
            origen, hijo = nombres[destino], nombres[m]
            uno_a_uno = type(campo).__name__ == 'OneToOneField'
            izq = '|o' if campo.null else '||'
            der = 'o|' if uno_a_uno else 'o{'
            verbo = VERBOS.get((origen, hijo), 'se relaciona con')
            clave = (origen, hijo, campo.name)
            if clave in vistas:
                continue
            vistas.add(clave)
            lineas.append(f'    {origen} {izq}--{der} {hijo} : "{verbo}"')

    for padre, historico in AUDITORIA:
        lineas.append(f'    {padre} ||..o{{ {historico} : "auditado por"')

    # -------------------------------------------------------------- entidades
    for m in sorted(modelos, key=lambda x: nombres[x]):
        lineas.append('')
        lineas.append(f'    {nombres[m]} {{')
        for campo in m._meta.fields:
            nombre = campo.attname
            tipo = tipo_sql(campo)
            marca = ''
            if campo.primary_key:
                marca = ' PK'
            elif campo.is_relation:
                marca = ' FK'
            elif campo.unique:
                marca = ' UK'
            lineas.append(f'        {tipo} {nombre}{marca}')
        lineas.append('    }')

    salida = '\n'.join(lineas) + '\n'
    with open('entidad_relacion.mmd', 'w', encoding='utf-8') as f:
        f.write(salida)

    # Vista de relaciones, sin la lista de atributos: es la que entra en el
    # capítulo, donde el ER completo resultaría ilegible a tamaño de página.
    corte = lineas.index('') if '' in lineas else len(lineas)
    with open('entidad_relacion_vista.mmd', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas[:corte]) + '\n')
    print(f'{len(modelos)} entidades, '
          f'{sum(1 for l in lineas if "--" in l or "..o" in l)} relaciones')
    for m in sorted(modelos, key=lambda x: nombres[x]):
        print('  ', nombres[m])


if __name__ == '__main__':
    main()


# ─────────────────────────── vista por módulos ───────────────────────────
MODULOS = {
    'usuarios': ('Seguridad y Usuarios', '#EEF2FF', '#4F46E5'),
    'catalogo': ('Catálogo Odontológico', '#F0FDF4', '#059669'),
    'pacientes': ('Pacientes', '#FEF3C7', '#D97706'),
    'agenda': ('Agenda y Citas', '#FEE2E2', '#DC2626'),
    'clinico': ('Expediente Clínico y Cobros', '#F3E8FF', '#7C3AED'),
    'inteligencia': ('Inteligencia', '#E0F2FE', '#0284C7'),
    'reportes': ('Reportes', '#F1F5F9', '#64748B'),
}


def grafo_modulos():
    """Modelo de datos agrupado por módulo, para la figura del capítulo."""
    por_app, nombres = {}, {}
    for etiqueta in APLICACIONES:
        try:
            cfg = apps.get_app_config(etiqueta)
        except LookupError:
            continue
        por_app[etiqueta] = list(cfg.get_models())
        for m in por_app[etiqueta]:
            nombres[m] = tabla(m)

    l = ['digraph modelo {',
         '  rankdir=LR;', '  bgcolor="white";', '  splines=spline;',
         '  nodesep=0.30; ranksep=0.85; pad=0.3;',
         '  fontname="Arial"; fontsize=11;',
         '  node [shape=box style="rounded,filled" fontname="Arial" '
         'fontsize=11 margin="0.14,0.09" penwidth=1.2];',
         '  edge [fontname="Arial" fontsize=9 color="#475569" '
         'arrowsize=0.7 penwidth=1.0];']

    for i, (etiqueta, modelos) in enumerate(por_app.items()):
        if not modelos:
            continue
        titulo, relleno, borde = MODULOS.get(etiqueta, (etiqueta, '#F8FAFC', '#94A3B8'))
        l.append(f'  subgraph cluster_{i} {{')
        l.append(f'    label="{titulo}"; labelloc=t; fontsize=12.5;')
        l.append(f'    fontcolor="{borde}"; color="{borde}"; penwidth=1.4;')
        l.append('    style="rounded"; margin=12;')
        for m in modelos:
            l.append(f'    "{nombres[m]}" [fillcolor="{relleno}" '
                     f'color="{borde}" fontcolor="#0F172A"];')
        l.append('  }')

    vistas = set()
    for m in nombres:
        for campo in m._meta.fields:
            if not campo.is_relation or campo.related_model is None:
                continue
            if campo.related_model not in nombres:
                continue
            a, b = nombres[campo.related_model], nombres[m]
            if (a, b, campo.name) in vistas:
                continue
            vistas.add((a, b, campo.name))
            etiq = VERBOS.get((a, b), '')
            estilo = 'dashed' if campo.null else 'solid'
            l.append(f'  "{a}" -> "{b}" [label="{etiq}" style={estilo}];')

    for padre, historico in AUDITORIA:
        l.append(f'  "{padre}" -> "{historico}" '
                 f'[label="auditado por" style=dotted color="#94A3B8"];')

    l.append('}')
    with open('modelo_datos.dot', 'w', encoding='utf-8') as f:
        f.write('\n'.join(l) + '\n')
    print('modelo_datos.dot generado')


grafo_modulos()
