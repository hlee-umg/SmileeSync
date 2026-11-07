"""Limita el alto de las figuras para que no dejen páginas en blanco.

Los diagramas de actividad y los de casos de uso se insertaron ocupando 8.10"
de alto en un área de texto de 9.00". Con el párrafo que los presenta y su pie,
el conjunto no cabe en una página, de modo que Word empuja la figura a la
siguiente y deja la anterior con tres líneas de texto y el resto en blanco.

Reducir el alto máximo a 7.20" deja 1.80" para el párrafo y el pie, que es
suficiente incluso para una presentación de cinco líneas. La reducción es del
11 % y no compromete la legibilidad: los diagramas se generaron a 300 ppp.
"""
import pathlib

import docx
from docx.shared import Emu

A = pathlib.Path.home() / ('mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/'
                           'SmileeSync_Cuarta_Entrega.docx')
ALTO_MAX = Emu(int(7.20 * 914400))


def main():
    doc = docx.Document(str(A))
    ajustadas = 0
    for figura in doc.inline_shapes:
        if figura.height <= ALTO_MAX:
            continue
        escala = ALTO_MAX / figura.height
        ancho = Emu(int(figura.width * escala))
        anterior = figura.height / 914400
        figura.height = ALTO_MAX
        figura.width = ancho
        ajustadas += 1
        print(f'   {anterior:.2f}" → 7.20"  (ancho {ancho/914400:.2f}")')
    doc.save(str(A))
    print(f'{ajustadas} figuras ajustadas de {len(doc.inline_shapes)}')


if __name__ == '__main__':
    main()
