"""Formato del manual de usuario de SmileeSync."""
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

AZUL = '1F3A5F'
GRIS = '475569'
RAIZ = Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs'
IMG = RAIZ / 'mockups'
SALIDA = RAIZ / 'SmileeSync_Manual_de_Usuario.docx'
ANCHO_UTIL = 6.3
ALTO_MAX = 4.6


def fuente(run, tam=11, negrita=False, color=None, cursiva=False):
    run.font.size = Pt(tam)
    run.bold = negrita
    run.italic = cursiva
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
      cursiva=False, centrado=False, sangria=0):
    par = doc.add_paragraph()
    pf = par.paragraph_format
    pf.space_before = Pt(antes); pf.space_after = Pt(despues); pf.line_spacing = 1.15
    if sangria:
        pf.left_indent = Inches(sangria)
    if centrado:
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if texto:
        fuente(par.add_run(texto), tam, negrita, color, cursiva)
    return par


def h(doc, texto, nivel=1, salto=False):
    if salto:
        doc.add_page_break()
    tam = {1: 17, 2: 13.5, 3: 11.5}[nivel]
    par = p(doc, texto, tam, True, AZUL, antes=0 if salto else (16 if nivel == 1 else 12),
            despues=5)
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return par


def pasos(doc, lista):
    for i, texto in enumerate(lista, 1):
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.left_indent = Inches(0.35); pf.first_line_indent = Inches(-0.35)
        pf.space_after = Pt(4); pf.line_spacing = 1.15
        fuente(par.add_run(f'{i}. '), 11, True, AZUL)
        fuente(par.add_run(texto), 11)


def nota(doc, texto, etiqueta='Importante'):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = t.rows[0].cells[0]
    celda.width = Inches(ANCHO_UTIL)
    par = celda.paragraphs[0]
    par.paragraph_format.space_before = Pt(3); par.paragraph_format.space_after = Pt(3)
    fuente(par.add_run(f'{etiqueta}. '), 10.5, True, AZUL)
    fuente(par.add_run(texto), 10.5)
    sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'EEF2F7')
    celda._tc.get_or_add_tcPr().append(sh)
    t.style = 'Table Grid'
    p(doc, '', despues=2)
    return t


def captura(doc, archivo, pie):
    ruta = IMG / archivo
    with Image.open(ruta) as im:
        ancho_px, alto_px = im.size
    ancho = ANCHO_UTIL
    if alto_px / ancho_px * ancho > ALTO_MAX:
        ancho = ALTO_MAX * ancho_px / alto_px
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(6); par.paragraph_format.space_after = Pt(2)
    par.add_run().add_picture(str(ruta), width=Inches(ancho))
    pc = p(doc, pie, 9, False, GRIS, despues=10, cursiva=True, centrado=True)
    return pc


def faq(doc, preguntas):
    for pregunta, respuesta in preguntas:
        par = p(doc, '', despues=2)
        fuente(par.add_run(pregunta), 11, True, AZUL)
        p(doc, respuesta, 11, despues=9)


SALIDA_TECNICO = RAIZ / 'SmileeSync_Manual_Tecnico.docx'


def codigo(doc, lineas, titulo=None):
    """Bloque de comandos en monoespaciada sobre fondo gris."""
    from docx.enum.table import WD_TABLE_ALIGNMENT
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = t.rows[0].cells[0]
    celda.width = Inches(ANCHO_UTIL)
    primero = True
    for linea in (([titulo] if titulo else []) + list(lineas)):
        par = celda.paragraphs[0] if primero else celda.add_paragraph()
        primero = False
        pf = par.paragraph_format
        pf.space_before = Pt(1); pf.space_after = Pt(1); pf.line_spacing = 1.0
        run = par.add_run(linea)
        run.font.size = Pt(9)
        run.font.name = 'Consolas'
        rpr = run._r.get_or_add_rPr()
        rf = rpr.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
            rf.set(qn(a), 'Consolas')
        if titulo and linea == titulo:
            run.font.color.rgb = RGBColor.from_string('475569')
            run.italic = True
    sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'F1F5F9')
    celda._tc.get_or_add_tcPr().append(sh)
    t.style = 'Table Grid'
    p(doc, '', despues=4)
    return t


def tabla(doc, filas, anchos):
    from docx.enum.table import WD_TABLE_ALIGNMENT
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
    p(doc, '', despues=6)
    return t


def imagen(doc, ruta, pie, ancho=None):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    with Image.open(ruta) as im:
        ancho_px, alto_px = im.size
    a = ancho or ANCHO_UTIL
    if alto_px / ancho_px * a > 6.6:
        a = 6.6 * ancho_px / alto_px
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(6); par.paragraph_format.space_after = Pt(2)
    par.add_run().add_picture(str(ruta), width=Inches(a))
    return p(doc, pie, 9, False, GRIS, despues=10, cursiva=True, centrado=True)
