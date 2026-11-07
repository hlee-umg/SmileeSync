"""Reduce las cuatro fotografías de la sección 4.3.5 a una altura uniforme.

A 6 pulgadas de ancho cada fotografía ocupa media página y la siguiente ya no
cabe, de modo que el documento quedaba con dos páginas a medio llenar. Con una
altura de 3.6 pulgadas entran dos por página y el texto vuelve a fluir.
"""
import pathlib

import docx
from docx.shared import Emu

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
ALTO = Emu(int(3.6 * 914400))
PIES = ('Figura 54:', 'Figura 55:', 'Figura 56:', 'Figura 57:')


def main():
    doc = docx.Document(str(A))
    ps = doc.paragraphs
    objetivo = set()
    for i, p in enumerate(ps):
        if p.text.strip().startswith(PIES):
            objetivo.add(ps[i - 1]._p)
    ajustadas = 0
    for forma in doc.inline_shapes:
        if forma._inline.getparent().getparent().getparent() in objetivo:
            ancho, alto = forma.width, forma.height
            if alto > ALTO:
                forma.width = Emu(int(ancho * ALTO / alto))
                forma.height = ALTO
                ajustadas += 1
                print(f'   {ancho/914400:.2f}x{alto/914400:.2f} -> '
                      f'{forma.width/914400:.2f}x{forma.height/914400:.2f}')
    doc.save(str(A))
    print(f'{ajustadas} fotografías ajustadas de {len(objetivo)} previstas.')


if __name__ == '__main__':
    main()
