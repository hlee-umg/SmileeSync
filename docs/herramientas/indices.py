"""Regenera el índice general y los índices de figuras y tablas.

Los números de página se toman del documento convertido a PDF, de modo que el
archivo entregado no dependa de que alguien actualice campos en Word. Como el
propio índice ocupa páginas, el proceso se ejecuta dos veces: la primera fija la
extensión del índice y la segunda escribe los números definitivos.
"""
import pathlib
import re
import subprocess
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

A = pathlib.Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx'
TMP = pathlib.Path.home() / 'tesis/salida'
FUENTE = 'Times New Roman'
SANGRIAS = {1: 0, 2: 18, 3: 36, 4: 54}
PIE = re.compile(r'^(Figura|Tabla)\s+(\d+)\s*:\s*(.+?)\s*$')


def nivel(p):
    m = re.search(r'w:pStyle w:val="Heading(\d)"', p._p.xml)
    return int(m.group(1)) if m else None


def fijar(run, tam=11, negrita=False):
    run.font.name = FUENTE
    run.font.size = Pt(tam)
    run.font.bold = negrita
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.insert(0, rfonts)
    for atrib in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rfonts.set(qn(atrib), FUENTE)
    return run


def entrada(doc, texto, pagina, sangria, negrita=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.0
    pf.space_after = Pt(2)
    pf.left_indent = Pt(sangria)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.tab_stops.add_tab_stop(Inches(6.3), WD_TAB_ALIGNMENT.RIGHT,
                              WD_TAB_LEADER.DOTS)
    fijar(p.add_run(texto), negrita=negrita)
    r = fijar(p.add_run())
    r._r.append(OxmlElement('w:tab'))
    fijar(p.add_run(str(pagina)))
    return p._p


def a_pdf():
    TMP.mkdir(exist_ok=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', str(TMP), str(A)],
                   check=True, capture_output=True, timeout=600)
    return TMP / (A.stem + '.pdf')


def folios(ruta):
    import pypdf
    lector = pypdf.PdfReader(str(ruta))
    textos, impresos = [], []
    for pag in lector.pages:
        t = pag.extract_text() or ''
        textos.append(re.sub(r'\s+', ' ', t))
        lineas = [l.strip() for l in t.strip().split('\n') if l.strip()]
        # El pie de página se extrae antes del cuerpo, de modo que el folio
        # impreso aparece como primera línea del texto de la página.
        f = ''
        for candidata in (lineas[:1] + lineas[-1:]):
            if re.fullmatch(r'\d{1,3}', candidata):
                f = candidata
                break
        impresos.append(f)
    desfases = {}
    for i, f in enumerate(impresos):
        if f:
            desfases[i - int(f)] = desfases.get(i - int(f), 0) + 1
    if desfases:
        desfase = max(desfases, key=desfases.get)
        for i in range(len(impresos)):
            if i - desfase >= 1:
                impresos[i] = str(i - desfase)
        print(f'   desfase PDF → folio impreso: {desfase} '
              f'(coincide en {desfases[desfase]} de {len(impresos)} páginas)')
    return textos, impresos


def inicio_cuerpo(impresos):
    for i, f in enumerate(impresos):
        if f == '1':
            return i
    return 0


def pagina_de(fragmento, textos, impresos, desde):
    limpio = re.sub(r'\s+', ' ', fragmento).strip()[:45]
    if not limpio:
        return '', desde
    for i in range(desde, len(textos)):
        if limpio in textos[i]:
            return (impresos[i] or str(i + 1)), i
    return '', desde


def recorrer(doc):
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            yield Paragraph(h, doc)
        elif h.tag.endswith('}tbl'):
            yield Table(h, doc)


def limpiar(doc, rotulo, fin):
    """Borra las entradas existentes entre un rótulo de índice y el siguiente."""
    items = [o for o in recorrer(doc)]
    inicio = None
    for i, o in enumerate(items):
        if isinstance(o, Paragraph) and o.text.strip() == rotulo:
            inicio = i
            break
    if inicio is None:
        raise SystemExit(f'No se encontró el rótulo {rotulo!r}')
    for o in items[inicio + 1:]:
        if isinstance(o, Paragraph) and o.text.strip() in fin:
            break
        if isinstance(o, Paragraph) and o.text.strip():
            o._p.getparent().remove(o._p)
    return items[inicio]._p


def construir(pdf=None):
    doc = docx.Document(str(A))

    textos = impresos = None
    cuerpo = 0
    if pdf:
        textos, impresos = folios(pdf)
        cuerpo = inicio_cuerpo(impresos)
        print(f'   el cuerpo inicia en la página {cuerpo + 1} del PDF')

    # Recolección en orden: encabezados del cuerpo y pies de figura y tabla.
    encabezados, figuras, tablas = [], [], []
    en_cuerpo = False
    for o in recorrer(doc):
        if not isinstance(o, Paragraph):
            continue
        t = o.text.strip()
        n = nivel(o)
        if n == 1 and t == 'Introducción':
            en_cuerpo = True
        if not en_cuerpo:
            continue
        if n and 1 <= n <= 4 and t:
            encabezados.append((n, t))
        m = PIE.match(t)
        if m:
            titulo = m.group(3).split('\t')[0].strip()
            destino = figuras if m.group(1) == 'Figura' else tablas
            destino.append((f'{m.group(1)} {m.group(2)}', titulo))

    print(f'   {len(encabezados)} encabezados, {len(figuras)} figuras, '
          f'{len(tablas)} tablas')

    def numerar(items, buscar, cursor):
        salida = []
        for clave, texto in items:
            if textos:
                pagina, cursor = pagina_de(buscar(clave, texto), textos,
                                           impresos, cursor)
            else:
                pagina = '0'
            salida.append((clave, texto, pagina or '0'))
        return salida

    cur = cuerpo
    enc = []
    for n, t in encabezados:
        if textos:
            pagina, cur = pagina_de(t, textos, impresos, cur)
        else:
            pagina = '0'
        enc.append((n, t, pagina or '0'))

    figs = numerar(figuras, lambda c, t: f'{c}: {t}'[:45], cuerpo)
    tabs = numerar(tablas, lambda c, t: f'{c}: {t}'[:45], cuerpo)

    # Índice general
    ancla = limpiar(doc, 'ÍNDICE GENERAL', {'ÍNDICE DE ILUSTRACIONES'})
    nuevos = [entrada(doc, t, p, SANGRIAS.get(n, 0), negrita=(n == 1))
              for n, t, p in enc]
    siguiente = ancla.getnext()
    for el in nuevos:
        siguiente.addprevious(el)

    # Índice de figuras
    ancla = limpiar(doc, 'Índice de figuras', {'Índice de tablas'})
    nuevos = [entrada(doc, f'{c}. {t}', p, 0) for c, t, p in figs]
    siguiente = ancla.getnext()
    for el in nuevos:
        siguiente.addprevious(el)

    # Índice de tablas
    ancla = limpiar(doc, 'Índice de tablas', {'Introducción'})
    nuevos = [entrada(doc, f'{c}. {t}', p, 0) for c, t, p in tabs]
    siguiente = ancla.getnext()
    for el in nuevos:
        siguiente.addprevious(el)

    doc.save(str(A))
    return len(enc), len(figs), len(tabs)


if __name__ == '__main__':
    print('Pase 1: se fija la extensión de los índices')
    construir(None)
    print('   convirtiendo a PDF...')
    pdf = a_pdf()
    print('Pase 2: se escriben los números de página reales')
    construir(pdf)
    print('   verificando con una segunda conversión...')
    pdf = a_pdf()
    construir(pdf)
    print('Índices regenerados.')
