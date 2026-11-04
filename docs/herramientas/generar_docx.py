"""Genera los entregables .docx (y .pdf) de la documentación a partir del Markdown.

Los archivos .md de docs/ son la fuente oficial. Este script les agrega la
portada institucional de la UMG y los convierte a Word; si Microsoft Word está
instalado, también exporta cada documento a PDF.

Uso (desde la raíz del repositorio):
    pip install -r docs/herramientas/requirements.txt
    python docs/herramientas/generar_docx.py            # todos
    python docs/herramientas/generar_docx.py SQA-Plan   # uno o varios
    python docs/herramientas/generar_docx.py --sin-pdf
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Emu, Inches, Pt, RGBColor
from markdown_it import MarkdownIt

DOCS = Path(__file__).resolve().parent.parent
SALIDA = DOCS / "entregables"
ESCUDO = Path(__file__).resolve().parent / "escudo-umg.png"

# --- Datos de la portada ---------------------------------------------------
CURSO = "ASEGURAMIENTO DE LA CALIDAD DE SOFTWARE"
PROYECTO = "SMILEESYNC: PIPELINE CI/CD CON ASEGURAMIENTO DE CALIDAD INTEGRADO"
ESTUDIANTE = "HEE SUNG LEE"
CARNE = "3190-11-342"
CATEDRATICO = "ING. EDGAR JEHOMIAS MATUL GARCÍA"
MESES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

# Documento de docs/ -> subtítulo de la portada.
DOCUMENTOS = {
    "SQA-Plan": "Plan de Aseguramiento de la Calidad del Software (SQA Plan)",
    "Linea-Base-Calidad": "Línea base de calidad",
    "Matriz-Pruebas": "Matriz de pruebas",
    "Reporte-Mejora": "Reporte de mejora: comparativa antes y después",
    "Manual-Tecnico": "Manual técnico del pipeline CI/CD",
}

FUENTE = "Times New Roman"
FUENTE_CODIGO = "Consolas"
GRIS_ENCABEZADO = "D9D9D9"


# =============================================================================
# Estilos y estructura del documento
# =============================================================================
def preparar_documento():
    doc = Document()
    seccion = doc.sections[0]
    seccion.page_width, seccion.page_height = Inches(8.5), Inches(11)
    for margen in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(seccion, margen, Inches(1))
    seccion.header_distance = Inches(0.5)
    seccion.different_first_page_header_footer = True  # portada sin número

    normal = doc.styles["Normal"]
    normal.font.name = FUENTE
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for nivel, tam in ((1, 16), (2, 14), (3, 12), (4, 12)):
        estilo = doc.styles[f"Heading {nivel}"]
        estilo.font.name = FUENTE
        estilo.font.size = Pt(tam)
        estilo.font.bold = True
        estilo.font.italic = False
        estilo.font.color.rgb = RGBColor(0, 0, 0)
        estilo.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
        estilo.element.rPr.rFonts.set(qn("w:hAnsiTheme"), "")
        estilo.paragraph_format.space_before = Pt(18 if nivel == 1 else 12)
        estilo.paragraph_format.space_after = Pt(6)
        estilo.paragraph_format.keep_with_next = True

    numero_de_pagina(seccion.header.paragraphs[0])
    return doc


def numero_de_pagina(parrafo):
    parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for tipo, texto in (
        ("begin", None),
        (None, " PAGE "),
        ("separate", None),
        (None, "1"),
        ("end", None),
    ):
        run = parrafo.add_run()
        if tipo:
            campo = OxmlElement("w:fldChar")
            campo.set(qn("w:fldCharType"), tipo)
            run._r.append(campo)
        elif texto.strip() == "PAGE":
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = texto
            run._r.append(instr)
        else:
            run.text = texto


# =============================================================================
# Portada (mismo formato que los manuales anteriores del estudiante)
# =============================================================================
def marca_de_agua(doc):
    """Escudo de la UMG detrás del texto, centrado en la página."""
    parrafo = doc.add_paragraph()
    run = parrafo.add_run()
    run.add_picture(str(ESCUDO), width=Emu(3810000))
    inline = run._r.find(".//" + qn("wp:inline"))
    grafico = inline.find(qn("a:graphic"))
    ancla = parse_xml(
        f'<wp:anchor {nsdecls("wp", "a")} behindDoc="1" distT="0" distB="0" '
        'distL="0" distR="0" simplePos="0" locked="0" layoutInCell="0" '
        'allowOverlap="1" relativeHeight="34">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="page"><wp:align>center</wp:align>'
        "</wp:positionH>"
        '<wp:positionV relativeFrom="page"><wp:posOffset>2880360</wp:posOffset>'
        "</wp:positionV>"
        '<wp:extent cx="3810000" cy="3810000"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
        '<wp:docPr id="1" name="sello" '
        'descr="Sello de la Universidad Mariano Gálvez de Guatemala"/>'
        "<wp:cNvGraphicFramePr>"
        '<a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        "</wp:anchor>"
    )
    ancla.append(grafico)
    inline.getparent().replace(inline, ancla)
    parrafo.paragraph_format.space_after = Pt(0)


def linea_portada(doc, texto, tam=12, antes=0):
    parrafo = doc.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    formato = parrafo.paragraph_format
    formato.space_before, formato.space_after, formato.line_spacing = (
        Pt(antes / 20),
        Pt(0),
        1.0,
    )
    run = parrafo.add_run(texto)
    run.bold = True
    run.font.size = Pt(tam)


def portada(doc, subtitulo):
    hoy = date.today()
    marca_de_agua(doc)
    linea_portada(doc, "UNIVERSIDAD MARIANO GÁLVEZ DE GUATEMALA")
    linea_portada(
        doc,
        "FACULTAD DE INGENIERÍA EN SISTEMAS DE INFORMACIÓN Y "
        "CIENCIAS DE LA COMPUTACIÓN",
    )
    linea_portada(doc, CURSO)
    linea_portada(doc, PROYECTO, tam=14, antes=5200)
    linea_portada(doc, subtitulo, tam=13)
    linea_portada(doc, ESTUDIANTE, antes=2900)
    linea_portada(doc, f"CARNÉ {CARNE}")
    linea_portada(doc, f"CATEDRÁTICO: {CATEDRATICO}", antes=240)
    linea_portada(doc, f"GUATEMALA, {MESES[hoy.month - 1]} {hoy.year}", antes=800)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# =============================================================================
# Conversión del Markdown
# =============================================================================
def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:color"), "auto")
    sombra.set(qn("w:fill"), color)
    tcPr.append(sombra)


class Conversor:
    """Recorre los tokens de markdown-it y escribe el documento de Word."""

    def __init__(self, doc):
        self.doc = doc
        self.listas = []  # pila: "bullet" / "ordered"
        self.cita = 0
        self.tabla = None
        self.fila = None
        self.celda_encabezado = False
        self.primer_titulo = True

    # --- texto en línea ------------------------------------------------------
    def escribir_en_linea(self, parrafo, hijos, negrita=False, tam=None):
        estado = {"b": negrita, "i": False}
        enlace = []
        for t in hijos:
            if t.type == "strong_open":
                estado["b"] = True
            elif t.type == "strong_close":
                estado["b"] = negrita
            elif t.type == "em_open":
                estado["i"] = True
            elif t.type == "em_close":
                estado["i"] = False
            elif t.type == "link_open":
                enlace.append(t.attrs.get("href", ""))
            elif t.type == "link_close":
                href = enlace.pop() if enlace else ""
                if href.startswith("http"):
                    self.run(parrafo, f" ({href})", tam=tam, gris=True)
            elif t.type in ("text", "html_inline"):
                texto = t.content
                if t.type == "html_inline":
                    continue
                texto = texto.replace("[x] ", "☑ ").replace("[ ] ", "☐ ")
                self.run(parrafo, texto, estado["b"], estado["i"], tam=tam)
            elif t.type == "code_inline":
                self.run(
                    parrafo, t.content, estado["b"], estado["i"], codigo=True, tam=tam
                )
            elif t.type in ("softbreak",):
                self.run(parrafo, " ", tam=tam)
            elif t.type == "hardbreak":
                parrafo.add_run().add_break()
            elif t.type == "image":
                self.run(
                    parrafo,
                    f"[Imagen: {t.content or t.attrs.get('src')}]",
                    tam=tam,
                    gris=True,
                )

    @staticmethod
    def run(
        parrafo, texto, negrita=False, cursiva=False, codigo=False, tam=None, gris=False
    ):
        r = parrafo.add_run(texto)
        r.bold, r.italic = negrita or None, cursiva or None
        if codigo:
            r.font.name = FUENTE_CODIGO
            r._r.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FUENTE_CODIGO)
            r.font.size = Pt((tam or 12) - 1.5)
        elif tam:
            r.font.size = Pt(tam)
        if gris:
            r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        return r

    # --- bloques ---------------------------------------------------------------
    def nuevo_parrafo(self, estilo=None):
        if self.listas:
            tipo = self.listas[-1]
            nombre = "List Bullet" if tipo == "bullet" else "List Number"
            nivel = min(len(self.listas), 3)
            estilo = nombre if nivel == 1 else f"{nombre} {nivel}"
        parrafo = self.doc.add_paragraph(style=estilo)
        if self.cita:
            parrafo.paragraph_format.left_indent = Inches(0.4)
            parrafo.paragraph_format.right_indent = Inches(0.2)
        if self.listas:
            parrafo.paragraph_format.space_after = Pt(2)
        return parrafo

    def convertir(self, texto):
        md = MarkdownIt("commonmark").enable("table")
        tokens = md.parse(texto)
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == "heading_open":
                nivel = int(t.tag[1])
                if self.primer_titulo and nivel == 1:
                    # El título del archivo ya está en la portada: se usa como
                    # encabezado del documento.
                    self.primer_titulo = False
                p = self.doc.add_paragraph(style=f"Heading {min(nivel, 4)}")
                self.escribir_en_linea(p, tokens[i + 1].children)
                i += 3
                continue
            if t.type == "paragraph_open":
                if self.tabla is None:
                    p = self.nuevo_parrafo()
                    if self.cita:
                        self.escribir_en_linea(p, tokens[i + 1].children, tam=11)
                        for r in p.runs:
                            r.italic = True if r.italic is None else r.italic
                    else:
                        self.escribir_en_linea(p, tokens[i + 1].children)
                i += 3
                continue
            if t.type == "bullet_list_open":
                self.listas.append("bullet")
            elif t.type == "ordered_list_open":
                self.listas.append("ordered")
            elif t.type in ("bullet_list_close", "ordered_list_close"):
                self.listas.pop()
            elif t.type == "blockquote_open":
                self.cita += 1
            elif t.type == "blockquote_close":
                self.cita -= 1
            elif t.type in ("fence", "code_block"):
                self.bloque_codigo(t.content)
            elif t.type == "table_open":
                i = self.tabla_md(tokens, i)
                continue
            elif t.type == "hr":
                pass
            i += 1

    def bloque_codigo(self, contenido):
        tabla = self.doc.add_table(rows=1, cols=1)
        tabla.style = "Table Grid"
        celda = tabla.rows[0].cells[0]
        sombrear(celda, "F2F2F2")
        lineas = contenido.rstrip("\n").split("\n")
        parrafo = celda.paragraphs[0]
        for n, linea in enumerate(lineas):
            r = self.run(parrafo, linea, codigo=True, tam=10)
            if n < len(lineas) - 1:
                r.add_break()
        self.doc.add_paragraph().paragraph_format.space_after = Pt(0)

    def tabla_md(self, tokens, i):
        """Convierte una tabla de Markdown en una tabla de Word con cuadrícula."""
        filas, fila, alineaciones, encabezados = [], None, [], 0
        i += 1
        while tokens[i].type != "table_close":
            t = tokens[i]
            if t.type == "tr_open":
                fila = []
            elif t.type == "tr_close":
                filas.append(fila)
            elif t.type in ("th_open", "td_open"):
                fila.append(tokens[i + 1].children or [])
                if t.type == "th_open":
                    estilo = t.attrs.get("style", "")
                    alineaciones.append(
                        "right"
                        if "right" in estilo
                        else "center" if "center" in estilo else "left"
                    )
            elif t.type == "thead_close":
                encabezados = len(filas)
            i += 1
        columnas = max(len(f) for f in filas)
        tabla = self.doc.add_table(rows=len(filas), cols=columnas)
        tabla.style = "Table Grid"
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r, fila in enumerate(filas):
            for c, hijos in enumerate(fila):
                celda = tabla.cell(r, c)
                parrafo = celda.paragraphs[0]
                parrafo.paragraph_format.space_after = Pt(0)
                parrafo.paragraph_format.line_spacing = 1.0
                alin = alineaciones[c] if c < len(alineaciones) else "left"
                parrafo.alignment = {
                    "right": WD_ALIGN_PARAGRAPH.RIGHT,
                    "center": WD_ALIGN_PARAGRAPH.CENTER,
                }.get(alin, WD_ALIGN_PARAGRAPH.LEFT)
                es_encabezado = r < encabezados
                self.escribir_en_linea(parrafo, hijos, negrita=es_encabezado, tam=9.5)
                if es_encabezado:
                    sombrear(celda, GRIS_ENCABEZADO)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(0)
        return i + 1


# =============================================================================
def exportar_pdf(docx):
    """Exporta a PDF con Microsoft Word (solo Windows, si está instalado)."""
    pdf = docx.with_suffix(".pdf")
    script = (
        "$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
        f"$d = $w.Documents.Open('{docx}'); "
        f"$d.SaveAs([ref]'{pdf}', [ref]17); $d.Close(); $w.Quit()"
    )
    resultado = subprocess.run(  # noqa: S603, S607 - comando fijo, sin datos externos
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=180,
    )
    return pdf if resultado.returncode == 0 and pdf.exists() else None


def generar(nombre, con_pdf=True):
    md = DOCS / f"{nombre}.md"
    if not md.exists():
        print(f"  - {nombre}.md no existe todavía; se omite")
        return
    doc = preparar_documento()
    portada(doc, DOCUMENTOS[nombre])
    texto = md.read_text(encoding="utf-8")
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    Conversor(doc).convertir(texto)
    SALIDA.mkdir(exist_ok=True)
    destino = SALIDA / f"{nombre}.docx"
    doc.save(destino)
    print(f"  ✓ {destino.relative_to(DOCS.parent)}")
    if con_pdf:
        pdf = exportar_pdf(destino)
        print(
            f"  ✓ {pdf.relative_to(DOCS.parent)}"
            if pdf
            else "  - no se pudo exportar a PDF (¿Word instalado?)"
        )


def main():
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    con_pdf = "--sin-pdf" not in sys.argv
    nombres = argumentos or list(DOCUMENTOS)
    for nombre in nombres:
        generar(nombre, con_pdf)


if __name__ == "__main__":
    main()
