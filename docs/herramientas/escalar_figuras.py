"""Reduce lo justo las figuras que no caben en la página anterior por poco.

Cuando una figura no entra en el espacio que queda, Word la manda entera a la
página siguiente y deja un hueco. Para las que se quedan cerca, basta con
reducirlas una fracción —conservando la proporción— para que quepan y el hueco
desaparezca. Se aplica solo a figuras, nunca a tablas, y solo a las que no
pierden legibilidad: todas conservan más de 250 puntos por pulgada.

Uso: python escalar_figuras.py 7=0.88 43=0.81 51=0.81
"""
import pathlib
import re
import sys

import docx
from docx.shared import Emu

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')


def main(peticiones):
    doc = docx.Document(str(A))
    ps = doc.paragraphs
    formas = {}
    for f in doc.inline_shapes:
        formas[f._inline.getparent().getparent().getparent()] = f
    hechas = 0
    for i, p in enumerate(ps):
        m = re.match(r'^Figura (\d+):', p.text.strip())
        if not m or m.group(1) not in peticiones:
            continue
        forma = formas.get(ps[i - 1]._p)
        if forma is None:
            raise SystemExit(f'La Figura {m.group(1)} no tiene imagen antes del pie.')
        e = peticiones[m.group(1)]
        ancho, alto = forma.width, forma.height
        forma.width = Emu(int(ancho * e))
        forma.height = Emu(int(alto * e))
        print(f'   Figura {m.group(1)}: {ancho/914400:.2f}x{alto/914400:.2f}" → '
              f'{forma.width/914400:.2f}x{forma.height/914400:.2f}"')
        hechas += 1
    if hechas != len(peticiones):
        raise SystemExit('No se encontraron todas las figuras pedidas.')
    doc.save(str(A))
    print(f'{hechas} figuras ajustadas.')


if __name__ == '__main__':
    pet = dict(a.split('=') for a in sys.argv[1:])
    main({k: float(v) for k, v in pet.items()})
