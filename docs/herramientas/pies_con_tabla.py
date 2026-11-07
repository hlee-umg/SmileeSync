"""Impide que el pie de una tabla se separe de su última fila.

La Tabla 73 terminaba al pie de una página y su rótulo quedaba solo en la
siguiente; la Tabla 77 partía su última fila y dejaba un renglón suelto. Se
marca la última fila de cada tabla como indivisible y unida al párrafo
siguiente, que es su pie. Se excluyen los recuadros de código, cuya única fila
puede ser más alta que una página.
"""
import pathlib

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
LIMITE = 1200


def main():
    doc = docx.Document(str(A))
    tocadas = omitidas = 0
    for t in doc.tables:
        fila = t.rows[-1]
        celdas = fila.cells
        texto = sum(len(c.text) for c in celdas)
        mono = any(r.font.name == 'Consolas'
                   for c in celdas for p in c.paragraphs for r in p.runs)
        if mono or texto > LIMITE:
            omitidas += 1
            continue
        trpr = fila._tr.get_or_add_trPr()
        if trpr.find(qn('w:cantSplit')) is None:
            trpr.append(OxmlElement('w:cantSplit'))
        for c in celdas:
            for p in c.paragraphs:
                ppr = p._p.get_or_add_pPr()
                if ppr.find(qn('w:keepNext')) is None:
                    ppr.insert(0, OxmlElement('w:keepNext'))
        tocadas += 1
    doc.save(str(A))
    print(f'{tocadas} tablas con la última fila unida a su pie; '
          f'{omitidas} omitidas (código o filas muy altas).')


if __name__ == '__main__':
    main()
