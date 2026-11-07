"""Rebalancea las columnas de la Tabla 2 para que quepa donde empieza.

La segunda columna sobraba de ancho y la tercera, que lleva descripciones de
hasta doscientos caracteres, se partía en demasiadas líneas: la tabla
derramaba dos filas en la página siguiente. Al repartir el ancho según el
contenido, la tabla cabe completa y se retira el salto de página.
"""
import pathlib

import docx
from docx.oxml.ns import qn
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
ANCHOS = [Emu(int(1.55 * 914400)), Emu(int(1.70 * 914400)), Emu(int(3.26 * 914400))]


def main():
    doc = docx.Document(str(A))
    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))
    t = None
    for i, o in enumerate(items):
        if isinstance(o, Paragraph) and o.text.strip().startswith('Tabla 2:'):
            t = items[i - 1]
            break
    if not isinstance(t, Table):
        raise SystemExit('No se encontró la Tabla 2.')

    p = t.rows[0].cells[0].paragraphs[0]
    ppr = p._p.get_or_add_pPr()
    salto = ppr.find(qn('w:pageBreakBefore'))
    if salto is not None:
        ppr.remove(salto)
        print('   salto de página retirado')

    for fila in t.rows:
        for j, ancho in enumerate(ANCHOS):
            fila.cells[j].width = ancho
    print('   anchos:', [round(c.width / 914400, 2) for c in t.rows[0].cells])
    doc.save(str(A))


if __name__ == '__main__':
    main()
