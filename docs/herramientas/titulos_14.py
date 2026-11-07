"""Lleva a 14 pt los títulos de primer nivel.

Cada encabezado trae el tamaño escrito directamente sobre el estilo, de modo
que no basta con tocar el estilo: hay que cambiar el tamaño en los runs. Solo
se tocan los de nivel 1; los demás se quedan en 12 pt.
"""
import pathlib

import docx
from docx.shared import Pt

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')


def main():
    doc = docx.Document(str(A))
    tocados = []
    for p in doc.paragraphs:
        if 'w:pStyle w:val="Heading1"' not in p._p.xml or not p.text.strip():
            continue
        for r in p.runs:
            r.font.size = Pt(14)
        tocados.append(p.text.strip()[:45])
    doc.save(str(A))
    print(f'{len(tocados)} títulos a 14 pt:')
    for t in tocados:
        print('   ', t)


if __name__ == '__main__':
    main()
