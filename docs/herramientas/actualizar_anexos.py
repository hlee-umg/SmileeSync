"""Actualiza los anexos y las tablas del capítulo 3 afectadas por los módulos nuevos.

    Anexo A   Sustituye el entidad-relación ampliado por el de veinticuatro tablas.
    Anexo B   Regenera el diccionario de datos completo desde los modelos, de modo
              que incluya las ocho entidades incorporadas y los campos agregados a
              las existentes.
    Tabla 1   Amplía la relación de módulos de seis a ocho.
    Tabla 16  Rehace la trazabilidad entre requerimientos y elementos del modelo.
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, '.')
import formato as F                                                # noqa: E402

RAIZ = Path('../mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs')
ARCHIVO = RAIZ / 'SmileeSync_Cuarta_Entrega.docx'
DIAG = RAIZ / 'diagramas'

MODULOS_TABLA = [
    ['Módulo', 'Procesos (cada uno con CRUD)', 'Estrategia de eliminación'],
    ['1. Seguridad y Usuarios (obligatorio)',
     'Gestión de usuarios; gestión de roles y permisos; control de acceso por '
     'módulo; recuperación de contraseña; consulta del historial de auditoría.',
     'Borrado lógico (estado activo o inactivo) + tabla de histórico'],
    ['2. Pacientes',
     'Gestión de pacientes; gestión de antecedentes médicos; consulta de la ficha '
     'clínica y del historial de atenciones.',
     'Borrado lógico + tabla de histórico'],
    ['3. Catálogo Odontológico',
     'Gestión de especialidades; gestión de procedimientos y sus tarifas; gestión '
     'de odontólogos; gestión de unidades dentales.',
     'Borrado lógico (estado activo o inactivo)'],
    ['4. Agenda y Citas (módulo principal)',
     'Gestión de citas; gestión de horarios de disponibilidad; registro de '
     'ausencias puntuales; registro de tiempos reales de atención; calendario '
     'operativo.',
     'Borrado lógico + tabla de histórico'],
    ['5. Expediente Clínico',
     'Registro del odontograma por pieza y cara; notas clínicas de evolución; '
     'elaboración y seguimiento del plan de tratamiento.',
     'Registro de solo agregado (odontograma) y borrado lógico + histórico'],
    ['6. Cobros',
     'Presupuesto del tratamiento; registro de abonos; consulta del estado de '
     'cuenta por paciente.',
     'Anulación lógica del abono + tabla de histórico'],
    ['7. Inteligencia (Predicción y Recomendación)',
     'Gestión del conjunto de entrenamiento; estimación de duración; '
     'recomendación de bloques; versionado del modelo.',
     'Tabla de histórico (versiones del modelo)'],
    ['8. Reportes e Indicadores (obligatorio)',
     'Indicadores de la agenda; reportes de utilización; comparativo de precisión '
     'del modelo.',
     'Solo consulta'],
]

TRAZABILIDAD = [
    ['Requerimientos', 'Elemento del modelo', 'Descripción'],
    ['REQ-SEG-03', 'rol', 'Registra los roles del sistema, los módulos habilitados '
     'para cada uno y los indicadores de solo consulta y de escritura clínica.'],
    ['REQ-SEG-01, REQ-SEG-02, REQ-SEG-05', 'usuario', 'Registra a los usuarios, sus '
     'credenciales cifradas, su rol y la pregunta secreta de recuperación.'],
    ['REQ-SEG-04', 'historial_usuario', 'Conserva el estado previo de cada usuario '
     'antes de su modificación o cambio de estado.'],
    ['REQ-PAC-01', 'paciente', 'Registra los datos de identificación y contacto de '
     'las personas atendidas por la clínica.'],
    ['REQ-PAC-02', 'antecedente_medico', 'Registra las condiciones médicas '
     'relevantes del paciente que condicionan la atención.'],
    ['REQ-PAC-01', 'historial_paciente', 'Conserva el estado previo de cada ficha de '
     'paciente antes de su modificación.'],
    ['REQ-CAT-01', 'especialidad', 'Clasifica los procedimientos y define el perfil '
     'de cada profesional.'],
    ['REQ-CAT-02', 'procedimiento', 'Registra el catálogo de tratamientos con su '
     'complejidad, su duración de referencia y su tarifa.'],
    ['REQ-CAT-03', 'odontologo', 'Registra a los profesionales y su vínculo con una '
     'cuenta de usuario del sistema.'],
    ['REQ-CAT-04', 'unidad_dental', 'Registra los sillones de la clínica, de los que '
     'se deriva la capacidad de atención simultánea.'],
    ['REQ-AGE-01', 'horario_disponibilidad', 'Define el patrón semanal de atención '
     'de cada odontólogo.'],
    ['REQ-AGE-02', 'ausencia_odontologo', 'Registra las excepciones puntuales al '
     'patrón semanal, por jornada completa o por rango de horas.'],
    ['REQ-AGE-03, REQ-AGE-04, REQ-AGE-05', 'cita', 'Registra la cita con sus tiempos '
     'programados y reales, el procedimiento, el profesional y la unidad asignada.'],
    ['REQ-SEG-04, REQ-AGE-04', 'historial_cita', 'Conserva el estado previo de cada '
     'cita antes de su reprogramación, cancelación o cierre.'],
    ['REQ-EXP-01', 'hallazgo', 'Registra el estado de cada pieza dental por cara. Es '
     'una tabla de solo agregado: el odontograma vigente es el último registro de '
     'cada combinación.'],
    ['REQ-EXP-02', 'nota_clinica', 'Documenta la visita y aporta al modelo las '
     'variables de piezas tratadas, anestesia y complicación.'],
    ['REQ-EXP-03', 'plan_tratamiento', 'Registra el tratamiento acordado con su '
     'diagnóstico, su estado y su descuento.'],
    ['REQ-EXP-03, REQ-EXP-04', 'detalle_plan', 'Desglosa el plan en renglones con su '
     'precio y la duración que el modelo estimó al presupuestarlos.'],
    ['REQ-COB-02', 'pago', 'Registra los abonos aplicados al plan y admite su '
     'anulación lógica.'],
    ['REQ-COB-01, REQ-COB-03', 'historial_plan', 'Conserva la traza de los cambios de '
     'estado del plan y de los cobros aplicados.'],
    ['REQ-INT-03', 'modelo_version', 'Registra cada versión entrenada del modelo con '
     'su algoritmo y sus métricas de error.'],
    ['REQ-INT-01', 'dato_entrenamiento', 'Acumula las atenciones cerradas que '
     'constituyen el conjunto de entrenamiento.'],
    ['REQ-INT-01, REQ-INT-02', 'prediccion', 'Registra cada estimación generada para '
     'contrastarla después con la duración real.'],
    ['REQ-REP-01, REQ-REP-02', 'indicador_desempeno', 'Almacena las cifras '
     'consolidadas de la operación y de la precisión del modelo.'],
]


def reemplazar_tabla(doc, tabla, filas, anchos, col_etiqueta=None):
    """Sustituye el contenido de una tabla existente conservando su posición."""
    nueva = F.tabla(doc, filas, tabla._tbl, anchos=anchos,
                    col_etiqueta=col_etiqueta)
    tabla._tbl.getparent().remove(tabla._tbl)
    return nueva


def main():
    doc = Document(str(ARCHIVO))
    s = doc.sections[0]
    ancho = s.page_width - s.left_margin - s.right_margin
    alto = s.page_height - s.top_margin - s.bottom_margin - Emu(int(0.9 * 914400))

    def frac(*partes):
        total = sum(partes)
        return [Emu(int(ancho * x / total)) for x in partes]

    # ─────────────────────────── Tabla 1: módulos ───────────────────────────
    t0 = doc.tables[0]
    if [c.text.strip() for c in t0.rows[0].cells][:1] == ['Módulo']:
        reemplazar_tabla(doc, t0, MODULOS_TABLA, frac(3, 6, 3))
        print('Tabla 1   módulos ampliados a ocho')

    # ────────────────────── Tabla 16: trazabilidad del modelo ──────────────────────
    for t in doc.tables:
        enc = [c.text.strip() for c in t.rows[0].cells]
        if enc[:2] == ['ID del requerimiento', 'Elemento']:
            reemplazar_tabla(doc, t, TRAZABILIDAD, frac(3.2, 2.6, 7))
            print('Tabla 16  trazabilidad rehecha con los requerimientos nuevos')
            break

    # ───────────────────── Anexo A: entidad-relación ampliado ─────────────────────
    for p in doc.paragraphs:
        if p.text.strip().startswith('Figura 22: Diagrama entidad-relación completo'):
            anterior = p._p.getprevious()
            img = Paragraph(anterior, doc) if anterior is not None else None
            nuevo = F.imagen(doc, DIAG / 'entidad_relacion.png', p, ancho, alto)
            F.pie(doc, 'Figura 230',
                  'Diagrama entidad-relación completo del sistema SmileeSync '
                  '(vista ampliada)', nuevo)
            if img is not None and 'graphicData' in img._p.xml:
                img._p.getparent().remove(img._p)
            p._p.getparent().remove(p._p)
            print('Anexo A   entidad-relación sustituido por el de 24 tablas')
            break

    # ───────────────────────── Anexo B: diccionario ─────────────────────────
    entidades = json.load(open('diccionario.json', encoding='utf-8'))

    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))

    inicio = None
    for i, o in enumerate(items):
        if isinstance(o, Paragraph) and o.text.strip().startswith(
                'Tabla 25: Diccionario de datos'):
            inicio = o
            break
    if inicio is None:
        raise SystemExit('No se localizó el pie del diccionario de datos.')

    # Se eliminan los pares «Entidad: …» + tabla que siguen al pie.
    borrados = 0
    actual = inicio._p.getnext()
    while actual is not None:
        texto = ''.join(actual.itertext()).strip()
        es_tabla = actual.tag.endswith('}tbl')
        if not (es_tabla or texto.startswith('Entidad:')):
            break
        siguiente = actual.getnext()
        actual.getparent().remove(actual)
        actual = siguiente
        borrados += 1
    print(f'Anexo B   elementos del diccionario anterior eliminados: {borrados}')

    a = inicio
    for e in entidades:
        a = F.parrafo(doc, f'Entidad: {e["tabla"]}  ({e["modulo"]})', a,
                      sangria=False, justificado=False, negrita=True, tam=10,
                      espacio_antes=8)
        filas = [['Campo', 'Tipo', 'Nulo', 'Descripción']]
        for c in e['campos']:
            filas.append([c['nombre'], c['tipo'], c['nulo'], c['descripcion']])
        t = F.tabla(doc, filas, a, anchos=frac(2.6, 2.2, 1, 7.2))
        a = t
    print(f'Anexo B   diccionario regenerado: {len(entidades)} entidades, '
          f'{sum(len(e["campos"]) for e in entidades)} campos')

    doc.save(str(ARCHIVO))
    print('Documento guardado.')


if __name__ == '__main__':
    main()
