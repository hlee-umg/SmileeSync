"""Quita los párrafos vacíos sobrantes dentro de las celdas.

Las fichas de requerimientos se generaron con dos párrafos vacíos detrás del
texto en las celdas combinadas. Cada uno ocupa un renglón completo, de modo que
cada fila cargaba dos líneas de aire. Se conserva siempre al menos un párrafo
por celda, que es lo que exige el formato de Word.
"""
import pathlib

import docx

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')


def main():
    doc = docx.Document(str(A))
    celdas = quitados = 0
    for t in doc.tables:
        vistos = set()
        for f in t.rows:
            for c in f.cells:
                if c._tc in vistos:
                    continue
                vistos.add(c._tc)
                ps = c.paragraphs
                i = len(ps) - 1
                n = 0
                while i > 0 and not ps[i].text.strip():
                    ps[i]._p.getparent().remove(ps[i]._p)
                    i -= 1
                    n += 1
                if n:
                    celdas += 1
                    quitados += n
    doc.save(str(A))
    print(f'{quitados} párrafos vacíos eliminados en {celdas} celdas')


if __name__ == '__main__':
    main()
