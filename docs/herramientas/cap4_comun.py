"""Utilidades compartidas por los scripts del capítulo 4."""
import sys
from pathlib import Path

from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).parent))

RAIZ = Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs'
ARCHIVO = RAIZ / 'SmileeSync_Cuarta_Entrega.docx'
IMG = RAIZ / 'mockups'
PULGADA = 914400


def medidas(doc):
    s = doc.sections[0]
    ancho = s.page_width - s.left_margin - s.right_margin
    alto = s.page_height - s.top_margin - s.bottom_margin - Emu(int(1.4 * PULGADA))
    return ancho, alto


def recorrer(doc):
    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))
    return items


def buscar(doc, texto, exacto=True):
    for o in recorrer(doc):
        if isinstance(o, Paragraph):
            t = o.text.strip()
            if (t == texto) if exacto else t.startswith(texto):
                return o
    raise SystemExit(f'No se encontró: {texto!r}')


def antes_de_referencias(doc):
    """Último elemento del cuerpo antes del apartado de Referencias."""
    ref = buscar(doc, 'Referencias')
    previo = ref._p.getprevious()
    while previo is not None and not (previo.tag.endswith('}p')
                                      or previo.tag.endswith('}tbl')):
        previo = previo.getprevious()
    if previo.tag.endswith('}tbl'):
        return Table(previo, doc)
    return Paragraph(previo, doc)
