"""Actualiza el capítulo 3 con los diagramas nuevos y las cifras corregidas.

    3.1.2.1  Incorpora el diagrama de arquitectura de software, que el documento
             describía en prosa pero no ilustraba.
    3.2.1    Sustituye el diagrama de casos de uso por las dos vistas en que se
             dividió al crecer a treinta y dos casos.
    3.2.2    Sustituye el entidad-relación por la vista agrupada por módulo y
             corrige el número de tablas y de módulos.
    3.2.3    Actualiza el diagrama de clases.
    3.2.5    Agrega la sección de diagramas de actividad por proceso, que es lo
             que el asesor señaló como faltante, y desplaza la de componentes.
"""
import sys
from pathlib import Path

from docx import Document
from docx.shared import Emu, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, '.')
import formato as F                                                # noqa: E402

RAIZ = Path('../mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs')
ARCHIVO = RAIZ / 'SmileeSync_Cuarta_Entrega.docx'
DIAG = RAIZ / 'diagramas'
NUM_FIG = 200

PROCESOS = [
    ('act_01_login', 'Inicio de sesión y control de acceso',
     'El usuario se identifica con su correo electrónico; el sistema verifica la '
     'contraseña cifrada y el estado de la cuenta, y construye el menú a partir de '
     'los módulos habilitados para su rol.'),
    ('act_02_usuarios', 'Mantenimiento de usuarios',
     'El administrador captura los datos del usuario; el sistema valida que el '
     'correo no esté asignado, exige una contraseña conforme a las reglas de '
     'seguridad y deja constancia de la creación en el historial de auditoría.'),
    ('act_03_recuperar', 'Recuperación de contraseña',
     'La recuperación se resuelve con la pregunta secreta registrada al dar de alta '
     'la cuenta, cuya respuesta se compara contra el valor cifrado almacenado.'),
    ('act_04_paciente', 'Registro de paciente y antecedentes médicos',
     'El proceso comienza por la búsqueda, para evitar el registro duplicado, y '
     'concluye con la captura iterativa de los antecedentes médicos relevantes.'),
    ('act_05_catalogo', 'Mantenimiento del catálogo odontológico',
     'Las cuatro entidades del catálogo comparten el mismo comportamiento, de modo '
     'que el proceso se representa una sola vez. La baja nunca elimina el registro: '
     'lo marca como inactivo para conservar su vínculo con las citas históricas.'),
    ('act_06_horarios', 'Configuración de horarios y ausencias',
     'El patrón semanal define la disponibilidad habitual y la ausencia la descuenta '
     'en una fecha concreta. La disponibilidad efectiva es la diferencia entre ambos.'),
    ('act_07_agendar', 'Programación de cita con estimación predictiva',
     'Es el proceso central del módulo principal. Antes de guardar, el sistema '
     'verifica cuatro condiciones: que la fecha no sea pasada, que la cita quepa en '
     'una franja efectiva, que no se traslape con otra cita del profesional y que '
     'quede una unidad dental libre.'),
    ('act_08_recomendacion', 'Recomendación de bloques de tiempo',
     'El sistema recorre las franjas disponibles en pasos de quince minutos y '
     'descarta los inicios que ya pasaron, los que chocan con una cita vigente y '
     'aquellos en que no queda sillón libre.'),
    ('act_09_atencion', 'Registro de la atención y realimentación del modelo',
     'Al cerrar la cita, la duración real se incorpora al conjunto de entrenamiento. '
     'Si la cita atendía un renglón de un plan de tratamiento, el renglón se cierra '
     'y el avance del plan se recalcula sin intervención del usuario.'),
    ('act_10_reprogramar', 'Reprogramación y cancelación de citas',
     'La reprogramación aplica las mismas validaciones del registro inicial. La '
     'cancelación conserva la cita mediante borrado lógico y libera la unidad dental.'),
    ('act_11_odontograma', 'Registro del odontograma',
     'Cada hallazgo se agrega sin modificar los anteriores, de modo que la pieza '
     'conserva su historia clínica y el odontograma presenta el registro vigente.'),
    ('act_12_plan', 'Elaboración del plan de tratamiento',
     'Cada renglón recibe del componente predictivo su duración estimada, con lo que '
     'el plan queda presupuestado en tiempo además de en dinero, y se reparte en '
     'sesiones antes de agendar la primera cita.'),
    ('act_13_ejecucion', 'Ejecución del plan de tratamiento',
     'El renglón aprobado se agenda con sus datos precargados, se atiende y se cierra '
     'automáticamente, de modo que el avance del plan no dependa de una marca manual.'),
    ('act_14_nota', 'Registro de la nota clínica de evolución',
     'La nota documenta la visita y aporta al modelo las tres variables que el '
     'registro de tiempos no puede conocer: piezas tratadas, uso de anestesia y '
     'aparición de complicaciones.'),
    ('act_15_cobros', 'Registro de abonos y control de saldo',
     'El abono no puede exceder el saldo vigente ni fecharse en el futuro. La '
     'corrección de un abono se resuelve por anulación lógica, conservando la traza '
     'en el estado de cuenta.'),
    ('act_16_modelo', 'Entrenamiento y versionado del modelo predictivo',
     'La versión nueva se activa únicamente si reduce el error frente a la que está '
     'en producción; en caso contrario se conserva como histórico para efectos '
     'comparativos.'),
]


def main():
    doc = Document(str(ARCHIVO))
    s = doc.sections[0]
    ancho = s.page_width - s.left_margin - s.right_margin
    alto = s.page_height - s.top_margin - s.bottom_margin - Emu(int(0.9 * 914400))

    def recorrer():
        items = []
        for h in doc.element.body.iterchildren():
            if h.tag.endswith('}p'):
                items.append(Paragraph(h, doc))
            elif h.tag.endswith('}tbl'):
                items.append(Table(h, doc))
        return items

    def buscar(texto, exacto=True):
        for o in recorrer():
            if isinstance(o, Paragraph):
                t = o.text.strip()
                if (t == texto) if exacto else t.startswith(texto):
                    return o
        return None

    global NUM_FIG

    def fig(ruta, titulo_pie, ancla):
        global NUM_FIG
        p = F.imagen(doc, ruta, ancla, ancho, alto)
        pie = F.pie(doc, f'Figura {NUM_FIG}', titulo_pie, p)
        NUM_FIG += 1
        return pie

    # ─────────────── 3.1.2.1 diagrama de arquitectura de software ───────────────
    ancla = buscar('Internamente, la capa de aplicación se estructura', exacto=False)
    intro = F.parrafo(
        doc,
        'La Figura 200 presenta la arquitectura de software del sistema. Cada capa '
        'depende únicamente de la inmediata inferior, de modo que una modificación '
        'en la presentación no alcanza a las reglas de negocio ni al '
        'almacenamiento. La capa de dominio concentra el criterio de disponibilidad '
        'y el servicio de estimación, que son consumidos por la validación de la '
        'cita, por la recomendación de bloques y por el indicador de utilización; '
        'centralizarlos evita que cada consumidor resuelva por su cuenta la misma '
        'pregunta con criterios distintos. El componente predictivo se representa '
        'fuera de la pila porque se consulta como un servicio y porque su ausencia '
        'no interrumpe la operación: la estimación recae entonces en el promedio '
        'histórico o en la duración del catálogo.', ancla)
    fig(DIAG / 'arquitectura_software.png',
        'Arquitectura de software de SmileeSync por capas', intro)
    print('3.1.2.1  diagrama de arquitectura insertado')

    # cifras del modelo de datos
    p = buscar('El modelo de datos se compone de dieciséis tablas', exacto=False)
    if p is not None:
        for r in p.runs:
            r.text = (r.text
                      .replace('dieciséis tablas', 'veinticuatro tablas')
                      .replace('los seis módulos', 'los ocho módulos'))
        print('3.1.2.1  cifras del modelo de datos actualizadas')

    # ────────────────────────── 3.2.1 casos de uso ──────────────────────────
    pie_viejo = buscar('Figura 3: Diagrama de casos de uso', exacto=False)
    if pie_viejo is not None:
        anterior = pie_viejo._p.getprevious()
        img = Paragraph(anterior, doc) if anterior is not None else None
        ancla = F.parrafo(
            doc,
            'El sistema comprende treinta y dos casos de uso distribuidos en ocho '
            'módulos. Para conservar su legibilidad, el diagrama se presenta en dos '
            'vistas complementarias: la Figura 201 reúne los casos de uso '
            'administrativos y la Figura 202 los de la operación clínica, donde se '
            'concentra el componente predictivo.', pie_viejo)
        a = fig(DIAG / 'casos_uso_admin.png',
                'Casos de uso de los módulos administrativos', ancla)
        fig(DIAG / 'casos_uso_operacion.png',
            'Casos de uso de la agenda, el expediente clínico, los cobros y la '
            'inteligencia', a)
        if img is not None and 'graphicData' in img._p.xml:
            img._p.getparent().remove(img._p)
        pie_viejo._p.getparent().remove(pie_viejo._p)
        print('3.2.1    casos de uso sustituidos por dos vistas')

    # ─────────────────────── 3.2.2 modelo de datos ───────────────────────
    pie_viejo = buscar('Figura 4: Diagrama entidad-relación', exacto=False)
    if pie_viejo is not None:
        anterior = pie_viejo._p.getprevious()
        img = Paragraph(anterior, doc) if anterior is not None else None
        nuevo = F.imagen(doc, DIAG / 'modelo_datos.png', pie_viejo, ancho, alto)
        F.pie(doc, f'Figura {NUM_FIG}',
              'Modelo de datos de SmileeSync agrupado por módulo', nuevo)
        NUM_FIG += 1
        if img is not None and 'graphicData' in img._p.xml:
            img._p.getparent().remove(img._p)
        pie_viejo._p.getparent().remove(pie_viejo._p)
        print('3.2.2    modelo de datos sustituido por la vista por módulos')

    # ───────────────────────── 3.2.3 diagrama de clases ─────────────────────────
    pie_viejo = buscar('Figura 5: Diagrama de clases', exacto=False)
    if pie_viejo is not None:
        anterior = pie_viejo._p.getprevious()
        img = Paragraph(anterior, doc) if anterior is not None else None
        nuevo = F.imagen(doc, DIAG / 'clases.png', pie_viejo, ancho, alto)
        F.pie(doc, f'Figura {NUM_FIG}',
              'Diagrama de clases del sistema SmileeSync', nuevo)
        NUM_FIG += 1
        if img is not None and 'graphicData' in img._p.xml:
            img._p.getparent().remove(img._p)
        pie_viejo._p.getparent().remove(pie_viejo._p)
        print('3.2.3    diagrama de clases actualizado')

    # ──────────────── 3.2.5 diagramas de actividad por proceso ────────────────
    componentes = buscar('3.2.5 Diagrama de componentes y arquitectura de despliegue')
    if componentes is None:
        raise SystemExit('No se localizó la sección de componentes.')
    for r in componentes.runs:
        r.text = r.text.replace('3.2.5 ', '3.2.6 ')

    ancla = F.titulo(doc, '3.2.5 Diagramas de actividad de los procesos', 3,
                     componentes._p.getprevious())
    ancla = F.parrafo(
        doc,
        'Los diagramas de secuencia de la sección anterior describen el '
        'intercambio de mensajes entre los componentes del sistema. Esta sección '
        'los complementa con el flujo de trabajo de cada proceso, expresado en '
        'diagramas de actividad con calles por responsable. La distinción importa '
        'porque permite verificar dos cosas que la secuencia no muestra: el orden '
        'en que se aplican las validaciones y quién ejecuta cada actividad. Se '
        f'documentan los {len(PROCESOS)} procesos del sistema, uno por cada '
        'funcionalidad principal de los ocho módulos.', ancla)

    for archivo, titulo_proceso, descripcion in PROCESOS:
        ancla = F.parrafo(
            doc, f'{titulo_proceso}. {descripcion}', ancla, espacio_antes=8)
        ancla = fig(DIAG / f'{archivo}.png',
                    f'Diagrama de actividad: {titulo_proceso.lower()}', ancla)
    print(f'3.2.5    sección de actividad creada con {len(PROCESOS)} diagramas')

    doc.save(str(ARCHIVO))
    print(f'Figuras nuevas: 200 a {NUM_FIG - 1}')
    print('Documento guardado.')


if __name__ == '__main__':
    main()
