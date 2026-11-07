"""Cuatro ajustes de formato pedidos tras la revisión.

1. Negrita de los encabezados. Los capítulos 3 y 4 se generaron con la negrita
   apagada explícitamente, de modo que salían en redonda mientras los de los
   capítulos 1 y 2 heredaban la negrita del estilo. Se quita esa marca para que
   todos hereden lo mismo.
2. Referencias empieza en página nueva, como el resto de los títulos de primer
   nivel y como exige el estilo de citación.
3. El pie de figura y de tabla deja más aire antes de lo que sigue.
4. Ninguna tabla ni recuadro de código se parte entre páginas si cabe completo
   en una; las pocas más altas que una página se dejan partir, que es lo que
   corresponde.
"""
import math
import pathlib

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
ESPACIO_PIE = Pt(18)
LINEAS_PAGINA = 50


def alto_estimado(t):
    """Altura de la tabla en líneas de 9 pt, estimada por el texto de cada celda."""
    total = 0
    for fila in t.rows:
        alto = 1
        for c in fila.cells:
            ancho = (c.width or 0) / 914400 or 2.0
            for p in c.paragraphs:
                largo = len(p.text)
                alto = max(alto, math.ceil(largo / max(1, ancho * 18)) or 1)
        total += alto
    return total


def main():
    doc = docx.Document(str(A))

    # 1. Negrita heredada en todos los encabezados.
    quitadas = 0
    for p in doc.paragraphs:
        if 'w:pStyle w:val="Heading' not in p._p.xml or not p.text.strip():
            continue
        for r in p.runs:
            rpr = r._r.find(qn('w:rPr'))
            if rpr is None:
                continue
            b = rpr.find(qn('w:b'))
            if b is not None and b.get(qn('w:val')) in ('0', 'false'):
                rpr.remove(b)
                quitadas += 1
    print(f'1. negrita restituida en {quitadas} series de encabezado')

    # 2. Referencias en página nueva.
    for p in doc.paragraphs:
        if p.text.strip() == 'Referencias' and 'w:pStyle w:val="Heading1"' in p._p.xml:
            ppr = p._p.get_or_add_pPr()
            if ppr.find(qn('w:pageBreakBefore')) is None:
                ppr.insert(0, OxmlElement('w:pageBreakBefore'))
                print('2. salto de página antes de «Referencias»')
            break
    else:
        raise SystemExit('No se encontró el encabezado «Referencias».')

    # 3. Aire después de los pies.
    pies = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith(('Figura ', 'Tabla ')) and ':' in t[:12] and 'Fuente:' in t:
            p.paragraph_format.space_after = ESPACIO_PIE
            pies += 1
    print(f'3. {pies} pies con {ESPACIO_PIE.pt:.0f} pt de separación')

    # 4. Tablas y recuadros de código sin partir.
    enteras = partibles = 0
    for t in doc.tables:
        if alto_estimado(t) > LINEAS_PAGINA:
            partibles += 1
            continue
        for fila in t.rows:
            trpr = fila._tr.get_or_add_trPr()
            if trpr.find(qn('w:cantSplit')) is None:
                trpr.append(OxmlElement('w:cantSplit'))
            for c in fila.cells:
                for p in c.paragraphs:
                    ppr = p._p.get_or_add_pPr()
                    if ppr.find(qn('w:keepNext')) is None:
                        ppr.insert(0, OxmlElement('w:keepNext'))
        enteras += 1
    print(f'4. {enteras} tablas se mantienen completas; '
          f'{partibles} más altas que una página se dejan partir')

    doc.save(str(A))
    print('Guardado.')


if __name__ == '__main__':
    main()
