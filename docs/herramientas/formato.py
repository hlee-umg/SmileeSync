"""Construcción de elementos con el formato del documento de graduación.

El documento no usa estilos de Word para el cuerpo: todo el formato es directo.
Aquí se centraliza ese formato para que cada párrafo, tabla y pie que se agregue
sea indistinguible de los que ya existen.

    Cuerpo      Times New Roman 12 pt, interlineado 1.5, justificado,
                sangría de primera línea de 0.5", espacio posterior 6 pt.
    Tablas      Times New Roman 9 pt, interlineado sencillo; encabezado en
                blanco sobre el azul institucional 1F3A5F.
    Pies        Times New Roman 9 pt; el rótulo en negrita, luego el título,
                un tabulador y la fuente.
"""
import copy

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

AZUL = '1F3A5F'
FUENTE = 'Times New Roman'


def _rpr(run, tam, negrita=False, color=None):
    run.font.name = FUENTE
    run.font.size = Pt(tam)
    run.bold = negrita
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.insert(0, rfonts)
    for atrib in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rfonts.set(qn(atrib), FUENTE)
    return run


def _elemento(objeto):
    """Devuelve el elemento XML de un párrafo, una tabla o el elemento mismo.

    Permite encadenar inserciones pasando como ancla lo que devolvió la
    llamada anterior, sea cual sea su tipo.
    """
    for atributo in ('_p', '_tbl', '_element'):
        if hasattr(objeto, atributo):
            return getattr(objeto, atributo)
    return objeto


def _nuevo_p(doc, despues_de):
    """Crea un párrafo vacío inmediatamente después del elemento indicado."""
    from docx.text.paragraph import Paragraph
    p = OxmlElement('w:p')
    _elemento(despues_de).addnext(p)
    return Paragraph(p, doc)


def parrafo(doc, texto, despues_de, sangria=True, justificado=True,
            tam=12, negrita=False, espacio_antes=None, centrado=False):
    p = _nuevo_p(doc, despues_de)
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(6)
    if espacio_antes is not None:
        pf.space_before = Pt(espacio_antes)
    if sangria:
        pf.first_line_indent = Pt(36)
    if centrado:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif justificado:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if texto:
        _rpr(p.add_run(texto), tam, negrita)
    return p


def titulo(doc, texto, nivel, despues_de):
    """Encabezado con el mismo formato directo que usa el documento."""
    p = _nuevo_p(doc, despues_de)
    # El estilo se escribe directamente: el documento identifica los encabezados
    # como «Heading3», sin espacio, y la búsqueda por nombre visible no los
    # encuentra.
    ps = OxmlElement('w:pStyle')
    ps.set(qn('w:val'), f'Heading{nivel}')
    p._p.get_or_add_pPr().insert(0, ps)
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    _rpr(p.add_run(texto), 12, negrita=False, color='000000')
    return p


def pie(doc, rotulo, titulo_texto, despues_de, fuente='Fuente: elaboración propia.'):
    """Pie de tabla o de figura: «Tabla N: Título<tab>Fuente: …»."""
    p = _nuevo_p(doc, despues_de)
    pf = p.paragraph_format
    pf.line_spacing = 1.0
    pf.space_after = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _rpr(p.add_run(f'{rotulo}: '), 9, negrita=True)
    _rpr(p.add_run(titulo_texto), 9)
    _rpr(p.add_run('\t'), 9)
    _rpr(p.add_run(fuente), 9)
    return p


def _sombrear(celda, color):
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    celda._tc.get_or_add_tcPr().append(shd)


def _escribir(celda, texto, negrita=False, color=None, tam=9):
    celda.text = ''
    p = celda.paragraphs[0]
    pf = p.paragraph_format
    pf.line_spacing = 1.0
    pf.space_after = Pt(2)
    for i, linea in enumerate(str(texto).split('\n')):
        if i:
            p = celda.add_paragraph()
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
        _rpr(p.add_run(linea), tam, negrita, color)


def _bordes(tabla, color='9CA3AF'):
    bordes = OxmlElement('w:tblBorders')
    for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{lado}')
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:color'), color)
        bordes.append(el)
    tabla._tbl.tblPr.append(bordes)


def tabla(doc, filas, despues_de, anchos=None, encabezado=True,
          col_etiqueta=None):
    """Inserta una tabla después del elemento indicado.

    `filas` es una lista de listas. Si `encabezado` es verdadero, la primera
    fila se pinta como encabezado. `col_etiqueta` marca en negrita las celdas
    de esa columna, para las tablas de tipo ficha donde la primera columna es
    el nombre del campo.
    """
    t = doc.add_table(rows=len(filas), cols=len(filas[0]))
    _bordes(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            celda = t.cell(i, j)
            es_enc = encabezado and i == 0
            es_etiq = col_etiqueta is not None and j == col_etiqueta and not es_enc
            _escribir(celda, valor,
                      negrita=es_enc or es_etiq,
                      color='FFFFFF' if es_enc else None)
            if es_enc:
                _sombrear(celda, AZUL)
            elif es_etiq:
                _sombrear(celda, 'F1F5F9')

    if anchos:
        for fila in t.rows:
            for j, ancho in enumerate(anchos):
                if j < len(fila.cells):
                    fila.cells[j].width = ancho

    _elemento(despues_de).addnext(t._tbl)
    return t


def figura(doc, ruta, despues_de, ancho):
    """Inserta una imagen centrada después del elemento indicado."""
    p = _nuevo_p(doc, despues_de)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture(str(ruta), width=ancho)
    return p


def eliminar_rango(inicio, fin):
    """Borra los elementos del cuerpo entre dos marcadores, sin incluirlos."""
    inicio, fin = _elemento(inicio), _elemento(fin)
    actual = inicio.getnext()
    borrados = 0
    while actual is not None and actual is not fin:
        siguiente = actual.getnext()
        actual.getparent().remove(actual)
        actual = siguiente
        borrados += 1
    return borrados


def figura_ajustada(doc, ruta, despues_de, ancho_util, alto_util):
    """Inserta una imagen escalándola para que quepa completa en la página.

    Los diagramas de actividad son muy altos y estrechos: ajustarlos por ancho
    los dejaría fuera del área de texto. Se escoge la dimensión que limite.
    """
    from PIL import Image
    from docx.shared import Emu
    with Image.open(ruta) as im:
        ancho_px, alto_px = im.size
    if alto_px / ancho_px > alto_util / ancho_util:
        return figura(doc, ruta, despues_de, None), _por_alto(doc, alto_util)
    return figura(doc, ruta, despues_de, ancho_util), None


def imagen(doc, ruta, despues_de, ancho_util, alto_util):
    """Inserta la imagen centrada, limitada por ancho o por alto."""
    from PIL import Image
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Emu, Pt
    with Image.open(ruta) as im:
        ancho_px, alto_px = im.size
    p = _nuevo_p(doc, despues_de)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    if alto_px / ancho_px > alto_util / ancho_util:
        p.add_run().add_picture(str(ruta), height=Emu(int(alto_util)))
    else:
        p.add_run().add_picture(str(ruta), width=Emu(int(ancho_util)))
    return p


def reemplazar_imagen(doc, parrafo, ruta, ancho_util, alto_util):
    """Sustituye la imagen de un párrafo conservando su posición."""
    nuevo = imagen(doc, ruta, parrafo, ancho_util, alto_util)
    parrafo._p.getparent().remove(parrafo._p)
    return nuevo


MONO = 'Consolas'


def _mono(run, tam=8.5, negrita=False):
    run.font.size = Pt(tam)
    run.bold = negrita
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.insert(0, rfonts)
    for atrib in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rfonts.set(qn(atrib), MONO)
    return run


def codigo(doc, ruta, cuerpo, despues_de, tam=8.5):
    """Recuadro de código fuente: encabezado con el archivo y el fragmento.

    Se construye como una tabla de una sola celda porque es lo único que en
    Word admite a la vez un fondo y un borde propios, de modo que el fragmento
    se distingue del cuerpo del texto sin depender de un estilo del documento.
    """
    t = doc.add_table(rows=1, cols=1)
    _bordes(t, color='C7CBD1')
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = t.cell(0, 0)
    _sombrear(celda, 'F6F7F9')
    celda.text = ''

    p = celda.paragraphs[0]
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(4)
    _mono(p.add_run(ruta), tam=tam, negrita=True)

    for linea in cuerpo.rstrip('\n').split('\n'):
        p = celda.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        _mono(p.add_run(linea.replace('\t', '    ')), tam=tam)

    _elemento(despues_de).addnext(t._tbl)
    return t
