"""Evita que la Tabla 2 derrame dos filas en una página casi vacía.

La tabla empieza a media página 18 y deja en la 19 una fila y media con el
resto en blanco. Con un salto de página antes, la tabla cabe completa en una
sola página. Se corrige además la celda que atribuía a la canalización de
integración continua la ejecución de las pruebas: lo que ejecuta es la
revisión del proyecto.
"""
import pathlib

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
VIEJO = ('Versionan el código fuente y automatizan las pruebas y el despliegue '
         'en el servidor de producción.')
NUEVO = ('Versionan el código fuente y automatizan la revisión del proyecto y '
         'el despliegue en el servidor de producción.')


def main():
    doc = docx.Document(str(A))
    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))

    tabla = None
    for i, o in enumerate(items):
        if isinstance(o, Paragraph) and o.text.strip().startswith('Tabla 2:'):
            tabla = items[i - 1]
            break
    if not isinstance(tabla, Table):
        raise SystemExit('No se encontró la Tabla 2.')

    cambiados = 0
    for fila in tabla.rows:
        for celda in fila.cells:
            for p in celda.paragraphs:
                for r in p.runs:
                    if VIEJO in r.text:
                        r.text = r.text.replace(VIEJO, NUEVO)
                        cambiados += 1
    print(f'   celda de integración continua: {cambiados} cambio(s)')

    p = tabla.rows[0].cells[0].paragraphs[0]
    ppr = p._p.get_or_add_pPr()
    if ppr.find(qn('w:pageBreakBefore')) is None:
        ppr.insert(0, OxmlElement('w:pageBreakBefore'))
        print('   salto de página antes de la Tabla 2')

    doc.save(str(A))
    print('Listo.')


if __name__ == '__main__':
    main()
