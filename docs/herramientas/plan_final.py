"""Documento de preparación para la entrega final y la presentación."""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

AZUL = '1F3A5F'
SALIDA = (Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/'
          'docs/SmileeSync_Plan_Entrega_Final.docx')


def fuente(run, tam=11, negrita=False, color=None):
    run.font.name = 'Calibri'
    run.font.size = Pt(tam)
    run.bold = negrita
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._r.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rf.set(qn(a), 'Calibri')
    return run


def p(doc, texto='', tam=11, negrita=False, color=None, antes=0, despues=6,
      alineacion=None):
    par = doc.add_paragraph()
    pf = par.paragraph_format
    pf.space_before = Pt(antes); pf.space_after = Pt(despues); pf.line_spacing = 1.15
    if alineacion is not None:
        par.alignment = alineacion
    if texto:
        fuente(par.add_run(texto), tam, negrita, color)
    return par


def h(doc, texto, nivel=1):
    tam = {1: 16, 2: 13, 3: 11.5}[nivel]
    return p(doc, texto, tam, True, AZUL, antes=14 if nivel == 1 else 10, despues=4)


def tabla(doc, filas, anchos):
    t = doc.add_table(rows=0, cols=len(filas[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, fila in enumerate(filas):
        celdas = t.add_row().cells
        for j, valor in enumerate(fila):
            celdas[j].width = Inches(anchos[j])
            par = celdas[j].paragraphs[0]
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.space_before = Pt(2)
            fuente(par.add_run(str(valor)), 9.5, i == 0,
                   'FFFFFF' if i == 0 else None)
            if i == 0:
                sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), AZUL)
                celdas[j]._tc.get_or_add_tcPr().append(sh)
    t.style = 'Table Grid'
    return t


def vinetas(doc, puntos):
    for texto in puntos:
        par = doc.add_paragraph(style='List Bullet')
        par.paragraph_format.space_after = Pt(3)
        par.paragraph_format.line_spacing = 1.15
        fuente(par.add_run(texto), 11)


ANEXOS = [
    ['Anexo exigido', 'Qué debe contener', 'Estado', 'Esfuerzo'],
    ['Manual de usuario',
     'Guía por rol —recepción, odontólogo y administrador— con el recorrido de cada '
     'proceso, capturas de pantalla y la respuesta a las preguntas frecuentes que '
     'ya recogen las Tablas 75 a 77.',
     'No existe. Hay insumos: las capturas del capítulo 3 y el guion de '
     'acompañamiento.', 'Alto'],
    ['Manual técnico',
     'Requisitos del servidor, instalación, variables de entorno, despliegue, '
     'respaldo y restauración, tareas programadas y procedimiento ante fallas.',
     'Parcial. Existen DESPLIEGUE_AWS.md e infra/README.md; falta consolidarlos y '
     'completar respaldo y recuperación.', 'Medio'],
    ['Fuentes',
     'El código fuente entregado, con la descripción de la organización del '
     'repositorio y las instrucciones para ejecutarlo.',
     'El repositorio existe y la sección 4.1.2.4 lo describe. Falta el anexo que lo '
     'presente y la limpieza de credenciales.', 'Bajo'],
    ['Arquitectura de software',
     'Las vistas de arquitectura: capas, componentes, despliegue y modelo de datos.',
     'Existe y está completa: secciones 3.1.2, 4.1.2.1 y los Anexos A y B, con los '
     'dos diagramas nuevos. Falta solo consolidarla como anexo.', 'Bajo'],
]

PENDIENTES = [
    ['Tarea', 'Por qué importa', 'Urgencia'],
    ['Rotar las credenciales expuestas en claude/ONBOARDING.md',
     'El archivo contiene en texto plano la llave de acceso de Amazon Web Services, '
     'la contraseña de la base de datos de producción y la clave secreta de Django. '
     'Están en el historial del repositorio. Debe rotarse cada una y limpiarse el '
     'historial antes de que el repositorio se entregue como anexo de fuentes.',
     'Inmediata'],
    ['Habilitar HTTPS con un nombre de dominio',
     'Mientras el servidor atienda sin cifrado, las credenciales y la información '
     'clínica viajan legibles. Es la primera recomendación del documento y el '
     'ingeniero evalúa seguridad en la presentación.', 'Alta'],
    ['Configurar y probar el respaldo de la base de datos',
     'Todos los componentes viven en una sola instancia: la base es el único activo '
     'irrecuperable. Un respaldo nunca restaurado no cuenta como respaldo.', 'Alta'],
    ['Redactar el manual de usuario por rol',
     'Es uno de los cuatro anexos que la presentación califica y el único que no '
     'tiene insumos directos.', 'Alta'],
    ['Consolidar el manual técnico',
     'Segundo anexo calificado. Los insumos existen y hay que completarlos con '
     'respaldo, restauración y procedimiento ante fallas.', 'Media'],
    ['Acciones de reentrenamiento en la interfaz',
     'Solicitud del administrador en las sesiones del 16 y 17 de octubre: lanzar el '
     'reentrenamiento y configurar su periodicidad sin entrar por consola.', 'Media'],
    ['Importación de citas y expedientes desde hoja de cálculo',
     'Solicitud de la recepción. Reduce la barrera de adopción, pero no condiciona '
     'la presentación.', 'Baja'],
    ['Impresión del expediente y adjuntar el comprobante de pago',
     'Solicitudes recogidas en las sesiones, documentadas entre las recomendaciones.',
     'Baja'],
]

CRONOGRAMA = [
    ['Fechas', 'Trabajo', 'Resultado'],
    ['28 y 29 de octubre', 'Revisión de la cuarta entrega: lectura completa, ajuste '
     'de redacción y verificación de cifras.', 'Documento listo para entregar.'],
    ['30 de octubre', 'Entrega de la cuarta versión antes de las 23:59.',
     'Cuarta entrega presentada.'],
    ['31 de octubre al 3 de noviembre',
     'Rotación de credenciales, limpieza del historial del repositorio, HTTPS y '
     'respaldo de la base de datos.',
     'Las tres tareas técnicas pendientes del documento, resueltas.'],
    ['4 al 7 de noviembre', 'Redacción del manual de usuario por rol y consolidación '
     'del manual técnico.', 'Los dos anexos que faltan.'],
    ['8 al 10 de noviembre',
     'Incorporación de los anexos al documento final, revisión de coherencia y '
     'regeneración de índices.', 'Documento final completo.'],
    ['11 al 13 de noviembre',
     'Ensayo de la presentación sobre el sistema en producción y preparación de los '
     'datos de demostración para el día.', 'Presentación ensayada.'],
    ['14 de noviembre', 'Presentación final.', '—'],
]

PRESENTACION = [
    ['Aspecto que se califica', 'Qué mostrar', 'Dónde está la evidencia'],
    ['Funcionalidad',
     'El ciclo completo en vivo: programar una cita con la duración estimada, '
     'atenderla, registrar los tiempos reales y documentar la visita en el '
     'expediente.', 'Sistema en producción; secciones 4.2.3.1 a 4.2.3.5.'],
    ['Procesos de gestión del tema',
     'Cómo los tres procesos del alcance corresponden a la operación real de la '
     'clínica y qué cambió frente a la agenda en papel.',
     'Capítulo 3 y sección 5.1.2.'],
    ['Software desarrollado por modulación',
     'Los nueve módulos y el diagrama de componentes obtenido del código, con la '
     'explicación del acoplamiento entre agenda, expediente e inteligencia.',
     'Sección 4.1.2.1 y la figura de componentes.'],
    ['Buenas prácticas en el desarrollo',
     'Borrado lógico e historial de auditoría, las 336 verificaciones automatizadas, '
     'la integración continua y el congelamiento del conjunto de datos.',
     'Secciones 4.1.2.4, 4.3.2 y 4.2.3.10.'],
    ['Seguridad',
     'El control de acceso por rol demostrado en vivo: intentar programar una cita '
     'con el usuario del odontólogo, incluso escribiendo la dirección a mano, y '
     'mostrar que el servidor la rechaza. Luego la correspondencia con el OWASP Top '
     '10:2025, incluyendo lo pendiente.', 'Sección 4.1.3 y la tabla del OWASP.'],
    ['Revisión de los anexos',
     'Manual de usuario, manual técnico, fuentes y arquitectura de software.',
     'Anexos A, B y C; los dos manuales están por redactarse.'],
]


def main():
    doc = Document()
    s = doc.sections[0]
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)

    p(doc, 'SmileeSync', 20, True, AZUL, despues=0)
    p(doc, 'Preparación de la entrega final y de la presentación', 13, False, '475569',
      despues=2)
    p(doc, 'Documento de trabajo · 27 de octubre de 2026', 9.5, False, '64748B',
      despues=10)

    h(doc, '1. Qué cambia entre la cuarta entrega y la final')
    p(doc, 'La estructura que el ingeniero comunicó para la entrega final es idéntica '
      'a la de la cuarta: carátula, índice, introducción, los capítulos 5 y 6, '
      'conclusiones, recomendaciones, referencias separadas por tipo de fuente y '
      'glosario. En consecuencia, el documento de la cuarta entrega sirve como base '
      'de la final y el trabajo entre una y otra no consiste en escribir capítulos '
      'nuevos sino en tres cosas: incorporar las correcciones que el ingeniero '
      'devuelva, completar los anexos que la presentación califica y resolver las '
      'tareas técnicas que el propio documento declara pendientes.')

    h(doc, '2. Estado del documento al 27 de octubre')
    vinetas(doc, [
        '235 páginas, 71 figuras y 91 tablas, con los índices regenerados y '
        'verificados contra el PDF.',
        'Capítulos 5 y 6 completos, con las once sesiones documentadas y el contraste '
        'estadístico de la hipótesis.',
        'Nueve conclusiones y diez recomendaciones, todas trazables a evidencia del '
        'propio documento.',
        'Las tres observaciones del ingeniero sobre el capítulo 4 atendidas: '
        'plataforma con alternativas y criterios, arquitectura con diagramas de '
        'componentes y de despliegue, y seguridad contrastada con el OWASP Top '
        '10:2025.',
        'Referencias separadas en libros, artículos científicos, otras tesis y sitios '
        'web, con tres fuentes nuevas.',
        'Redacción en tercera persona verificada en todo el documento.',
    ])

    h(doc, '3. Anexos que la presentación califica')
    p(doc, 'El sexto aspecto de la presentación del 14 de noviembre es la revisión de '
      'los anexos, y nombra cuatro. Dos están resueltos y dos no existen.')
    tabla(doc, ANEXOS, [1.5, 3.0, 2.3, 0.8])

    h(doc, '4. Tareas pendientes, por urgencia')
    tabla(doc, PENDIENTES, [2.0, 4.6, 1.0])
    p(doc, 'La primera de esa lista no admite demora y conviene insistir en ella: las '
      'credenciales de producción están en texto plano dentro del repositorio y en su '
      'historial. Entregar el repositorio como anexo de fuentes con esas llaves '
      'dentro equivale a publicarlas.', 10.5, False, '991B1B', antes=4)

    h(doc, '5. Cronograma propuesto')
    tabla(doc, CRONOGRAMA, [1.6, 3.9, 2.1])

    h(doc, '6. Guion de la presentación')
    p(doc, 'La presentación califica seis aspectos. Conviene preparar una '
      'demostración en vivo sobre el entorno de producción para los cinco primeros y '
      'reservar el último para recorrer los anexos.')
    tabla(doc, PRESENTACION, [1.7, 3.7, 2.2])

    doc.save(str(SALIDA))
    print('Plan guardado en', SALIDA.name)


if __name__ == '__main__':
    main()
