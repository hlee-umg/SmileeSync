"""Completa la sección 3.3 con las interfaces de los módulos agregados.

El documento de la segunda entrega describía las interfaces de los cuatro
módulos que existían entonces. Este script incorpora las de los módulos de
expediente clínico, plan de tratamiento y cobros, agrega al catálogo y a la
agenda las pantallas que faltaban, y renumera las dos secciones finales que se
desplazan.
"""
import sys
from pathlib import Path

from docx import Document
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402

RAIZ = Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs'
ARCHIVO = RAIZ / 'SmileeSync_Cuarta_Entrega.docx'
IMG = RAIZ / 'mockups'


def main():
    doc = Document(str(ARCHIVO))
    s = doc.sections[0]
    ancho = s.page_width - s.left_margin - s.right_margin
    alto = s.page_height - s.top_margin - s.bottom_margin - Emu(int(1.4 * 914400))

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
        raise SystemExit(f'No se encontró: {texto!r}')

    def fig(archivo, numero, titulo_pie, ancla):
        p = F.imagen(doc, IMG / archivo, ancla, ancho, alto)
        return F.pie(doc, f'Figura {numero}', titulo_pie, p)

    # ══════════════ 3.3.3 catálogo: odontólogos y unidades dentales ══════════════
    ancla = buscar('Figura 18: Interfaz del formulario de registro de odontólogo',
                   exacto=False)
    a = F.parrafo(
        doc,
        'El listado de odontólogos (Figura 300) presenta a los profesionales '
        'registrados con su número de colegiado, su especialidad y el usuario del '
        'sistema con que cada uno ingresa. La columna del usuario vinculado es la '
        'que permite que el profesional vea su propia agenda al iniciar sesión y '
        'que registre sus ausencias sin intervención de la recepción.', ancla)
    a = fig('17_catalogo_odontologos.png', 300,
            'Interfaz del catálogo de odontólogos', a)
    a = F.parrafo(
        doc,
        'El catálogo de unidades dentales (Figura 301) registra los sillones con '
        'que cuenta la clínica. Es el catálogo más breve del sistema y, al mismo '
        'tiempo, el que impone la restricción física de la operación: la capacidad '
        'de atención simultánea no la determina el número de profesionales, sino '
        'el menor entre ese número y el de unidades activas. Dar de alta un sillón '
        'nuevo es un registro en esta pantalla y el sistema ajusta en consecuencia '
        'la validación de las citas, la recomendación de bloques y el indicador de '
        'utilización, sin modificar el código.', a)
    a = fig('18_catalogo_unidades.png', 301,
            'Interfaz del catálogo de unidades dentales', a)

    # ══════════════ 3.3.4 agenda: recomendación y cierre de la cita ══════════════
    ancla = buscar('Figura 19: Interfaz del módulo Principal con la agenda semanal',
                   exacto=False)
    a = F.parrafo(
        doc,
        'Sobre esa misma pantalla opera la consulta de recomendación (Figura 302). '
        'El usuario elige un procedimiento, el profesional que lo atenderá y el '
        'número de piezas; el sistema estima la duración, declara de qué fuente '
        'proviene la estimación y resalta en la rejilla los espacios de la semana '
        'donde ese procedimiento cabe completo. La consulta responde antes de que '
        'exista una cita, de modo que la recepción puede ofrecer al paciente una '
        'hora concreta durante la misma llamada telefónica.', ancla)
    a = fig('03_principal_recomendacion.png', 302,
            'Interfaz de consulta de recomendación de espacios sobre el '
            'calendario (datos de demostración)', a)

    ancla = buscar('Figura 21: Interfaz de consulta y seguimiento de citas',
                   exacto=False)
    a = F.parrafo(
        doc,
        'La pantalla de detalle de la cita (Figura 303) es donde el ciclo se '
        'cierra. Al concluir la atención se registran la hora real de inicio y la '
        'de finalización, y el sistema calcula la duración efectiva y la contrasta '
        'con la que había asignado. Ese registro cumple dos funciones: documenta '
        'la atención y constituye el dato con que el modelo predictivo se vuelve a '
        'entrenar, de modo que la estimación de la clínica mejora con su propia '
        'operación.', ancla)
    a = fig('06_cita_detalle.png', 303,
            'Interfaz de detalle de la cita con registro de tiempos reales', a)

    # ══════════════ nuevas secciones 3.3.5 a 3.3.7 ══════════════
    ancla = buscar('3.3.5 Reportes del sistema')
    # Se insertan antes de la sección de reportes, que se renumera más abajo.
    cursor = ancla._p.getprevious()
    cursor = Paragraph(cursor, doc)

    t = F.titulo(doc, '3.3.5 Módulo de Expediente Clínico', 3, cursor)
    a = F.parrafo(
        doc,
        'El expediente clínico responde a una pregunta distinta de la que resuelve '
        'la agenda: no cuándo se atiende al paciente, sino qué se le ha hecho y en '
        'qué estado se encuentra. La pantalla del expediente (Figura 304) reúne en '
        'una sola vista el odontograma vigente, el resumen de hallazgos por '
        'atender y la última nota de evolución, de modo que el profesional '
        'reconstruya la situación del paciente antes de comenzar la consulta.', t)
    a = fig('19_expediente.png', 304,
            'Interfaz del expediente clínico del paciente (datos de demostración)', a)
    a = F.parrafo(
        doc,
        'El odontograma (Figura 305) representa las treinta y dos piezas de la '
        'dentición permanente conforme a la notación de dos dígitos de la '
        'Federación Dental Internacional, en la que el primer dígito identifica el '
        'cuadrante y el segundo la posición de la pieza desde la línea media. La '
        'rejilla se dispone en cuatro cuadrantes con la orientación habitual del '
        'expediente odontológico, y el color de cada pieza resume el hallazgo '
        'vigente, con una letra que distingue entre hallazgos del mismo color. La '
        'Tabla 200 recoge esa simbología.', a)
    a = fig('20_odontograma.png', 305,
            'Interfaz del odontograma con el registro de hallazgos por pieza', a)

    filas = [['Hallazgo', 'Símbolo', 'Color de la pieza', 'Significado clínico']]
    for simbolo, nombre, color, significado in [
        ('·', 'Sana', 'Gris', 'Pieza sin hallazgos registrados.'),
        ('C', 'Caries', 'Rojo', 'Lesión activa pendiente de tratamiento.'),
        ('F', 'Fractura', 'Rojo', 'Pérdida de estructura pendiente de atención.'),
        ('X', 'Indicada para extracción', 'Rojo',
         'Pieza cuya exodoncia está indicada.'),
        ('O', 'Obturada', 'Azul', 'Restauración de resina o amalgama colocada.'),
        ('S', 'Sellante', 'Azul', 'Sellante de fosas y fisuras aplicado.'),
        ('E', 'Endodoncia', 'Azul', 'Tratamiento de conducto concluido.'),
        ('K', 'Corona', 'Azul', 'Corona protésica colocada.'),
        ('P', 'Prótesis', 'Azul', 'Pieza sustituida por prótesis.'),
        ('I', 'Implante', 'Azul', 'Implante colocado.'),
        ('—', 'Ausente', 'Gris oscuro', 'Pieza no presente en la boca.'),
    ]:
        filas.append([nombre, simbolo, color, significado])
    tab = F.tabla(doc, filas, a,
                  anchos=[Emu(int(1.5 * 914400)), Emu(int(0.7 * 914400)),
                          Emu(int(1.1 * 914400)), Emu(int(3.0 * 914400))])
    a = F.pie(doc, 'Tabla 200',
              'Simbología del odontograma y su correspondencia con el hallazgo '
              'registrado', tab)
    a = F.parrafo(
        doc,
        'La tabla de hallazgos es de solo agregado: cada observación se registra '
        'con su fecha y no se modifica después. El odontograma vigente es el '
        'último hallazgo activo de cada combinación de pieza y cara, de modo que '
        'el expediente conserva la evolución completa de cada diente sin requerir '
        'una tabla de auditoría aparte y sin que una corrección borre lo que se '
        'observó antes.', a)
    a = F.parrafo(
        doc,
        'La hoja de evolución (Figura 306) presenta las notas clínicas en orden '
        'cronológico inverso. Cada nota corresponde a una visita atendida y '
        'registra el motivo, el diagnóstico, el procedimiento realizado, las '
        'piezas tratadas, el uso de anestesia y la aparición de complicaciones. '
        'Las tres últimas variables cumplen una doble función: documentan el acto '
        'clínico y alimentan al modelo predictivo, pues son las que explican por '
        'qué dos atenciones del mismo procedimiento no duran lo mismo.', a)
    a = fig('21_evolucion.png', 306,
            'Interfaz de la hoja de evolución clínica del paciente '
            '(datos de demostración)', a)

    t = F.titulo(doc, '3.3.6 Módulo de Plan de Tratamiento', 3, a)
    a = F.parrafo(
        doc,
        'El plan de tratamiento es el documento con que la clínica acuerda con el '
        'paciente el trabajo por realizar y su costo. El listado de planes '
        '(Figura 307) presenta los planes abiertos con su estado, su avance y su '
        'saldo pendiente.', t)
    a = fig('22_planes.png', 307,
            'Interfaz del listado de planes de tratamiento (datos de demostración)', a)
    a = F.parrafo(
        doc,
        'El detalle del plan (Figura 308) organiza el tratamiento en renglones '
        'agrupados por fases. Cada renglón corresponde a un procedimiento sobre '
        'una pieza determinada y conserva la duración que el modelo estimó al '
        'presupuestarlo, junto con la fuente de esa estimación. Es el punto donde '
        'el componente predictivo deja de resolver una cita aislada y pasa a '
        'planificar un tratamiento completo: con la duración de cada renglón, el '
        'sistema reparte el trabajo pendiente en sesiones que no exceden las dos '
        'horas de sillón, respetando el orden de las fases, y anticipa cuántas '
        'visitas requerirá el plan antes de agendar la primera.', a)
    a = fig('23_plan_detalle.png', 308,
            'Interfaz del detalle del plan de tratamiento con fases, renglones y '
            'sesiones sugeridas (datos de demostración)', a)

    t = F.titulo(doc, '3.3.7 Módulo de Cobros', 3, a)
    a = F.parrafo(
        doc,
        'El módulo de cobros (Figura 309) presenta el estado financiero de los '
        'planes aprobados: el total presupuestado, lo abonado y el saldo '
        'pendiente de cada paciente. Los pagos se registran como abonos '
        'aplicados al plan, de modo que el saldo se deriva siempre de la suma de '
        'los abonos vigentes y no de un campo que deba mantenerse al día. La '
        'anulación de un pago no borra el registro: lo marca como inactivo, con '
        'lo que la trazabilidad del cobro se conserva.', t)
    a = fig('24_cobros.png', 309,
            'Interfaz del control de cobros y saldos por plan (datos de '
            'demostración)', a)

    # ══════════════ renumeración de las secciones desplazadas ══════════════
    for viejo, nuevo in [('3.3.5 Reportes del sistema', '3.3.8 Reportes del sistema'),
                         ('3.3.6 Conjunto de pruebas', '3.3.9 Conjunto de pruebas')]:
        p = buscar(viejo)
        p.runs[0].text = nuevo
        for r in p.runs[1:]:
            r.text = ''

    doc.save(str(ARCHIVO))
    print('3.3 completada: 10 figuras y 1 tabla nuevas; 3 secciones agregadas.')


if __name__ == '__main__':
    main()
