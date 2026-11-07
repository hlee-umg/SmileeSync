"""Mantiene cada imagen junto a su pie.

Las tablas ya tenían la última fila unida a su rótulo, pero las imágenes no:
la Figura 44 quedó al final de una página con su pie en la siguiente. Se marca
el párrafo de cada imagen para que no se separe del pie que le sigue.
"""
import pathlib
import re

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')


def main():
    doc = docx.Document(str(A))
    ps = doc.paragraphs
    n = 0
    for i, p in enumerate(ps):
        if not re.match(r'^Figura \d+:', p.text.strip()):
            continue
        img = ps[i - 1]
        ppr = img._p.get_or_add_pPr()
        if ppr.find(qn('w:keepNext')) is None:
            ppr.insert(0, OxmlElement('w:keepNext'))
            n += 1
    doc.save(str(A))
    print(f'{n} imágenes unidas a su pie')


if __name__ == '__main__':
    main()
