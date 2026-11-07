"""Fija el ancho de las columnas de las tablas que lo declaran.

python-docx escribe el ancho de cada celda, pero sin la rejilla de la tabla ni
el modo de disposición fijo, Word y LibreOffice reparten las columnas según el
contenido y el ancho declarado se ignora. Este paso construye la rejilla a
partir de los anchos ya escritos y fija la disposición.
"""
import pathlib

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

A = pathlib.Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx'


def anchos_de(tabla):
    fila = tabla.rows[0]
    valores = []
    for celda in fila.cells:
        tc_w = celda._tc.find(qn('w:tcPr'))
        w = tc_w.find(qn('w:tcW')) if tc_w is not None else None
        if w is None or w.get(qn('w:type')) != 'dxa':
            return None
        try:
            valores.append(int(w.get(qn('w:w'))))
        except (TypeError, ValueError):
            return None
    return valores if valores and all(v > 0 for v in valores) else None


def main():
    doc = docx.Document(str(A))
    fijadas = omitidas = 0
    for tabla in doc.tables:
        anchos = anchos_de(tabla)
        if not anchos:
            omitidas += 1
            continue
        pr = tabla._tbl.tblPr
        for etiqueta in ('w:tblLayout',):
            viejo = pr.find(qn(etiqueta))
            if viejo is not None:
                pr.remove(viejo)
        disposicion = OxmlElement('w:tblLayout')
        disposicion.set(qn('w:type'), 'fixed')
        pr.append(disposicion)

        viejo = tabla._tbl.find(qn('w:tblGrid'))
        if viejo is not None:
            tabla._tbl.remove(viejo)
        rejilla = OxmlElement('w:tblGrid')
        for ancho in anchos:
            col = OxmlElement('w:gridCol')
            col.set(qn('w:w'), str(ancho))
            rejilla.append(col)
        pr.addnext(rejilla)
        fijadas += 1

    doc.save(str(A))
    print(f'{fijadas} tablas con ancho fijo; {omitidas} sin anchos declarados')


if __name__ == '__main__':
    main()
