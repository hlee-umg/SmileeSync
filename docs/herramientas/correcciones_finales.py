"""Correcciones de la revisión final previa a la entrega.

1. Espacio doble en los rótulos del diccionario de datos del Anexo B.
2. La remisión del marco teórico enviaba a 4.2.3.10 la razón por la que se
   descartó XGBoost, que se explica en 4.1.2.2.
3. La descripción de la integración continua enunciaba la práctica general y
   no lo que la canalización del proyecto ejecuta realmente.
"""
import pathlib

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')

CAMBIOS = [
    ('La comparación efectivamente realizada y la razón por la que XGBoost se '
     'descartó se documentan en la sección 4.2.3.10.',
     'La comparación efectivamente realizada se documenta en la sección '
     '4.2.3.10 y la razón por la que XGBoost se descartó, en la sección '
     '4.1.2.2.'),
    ('En SmileeSync este flujo se implementa con GitHub Actions, lo que reduce '
     'los errores manuales y agiliza la actualización del sistema en '
     'producción (Sommerville, 2011).',
     'En SmileeSync este flujo se implementa con GitHub Actions: cada cambio '
     'registrado en la rama principal ejecuta la revisión del proyecto y la '
     'comprobación de migraciones pendientes y, superadas ambas, actualiza el '
     'servidor de producción, lo que reduce los errores manuales y agiliza la '
     'actualización del sistema (Sommerville, 2011). El conjunto de '
     'verificaciones que la sección 4.3.2 describe se ejecuta sobre la base '
     'de datos de demostración como condición previa a cada entrega.'),
]


def main():
    doc = docx.Document(str(A))
    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))

    def parrafos():
        for o in items:
            if isinstance(o, Paragraph):
                yield o
            else:
                for f in o.rows:
                    for c in f.cells:
                        for p in c.paragraphs:
                            yield p

    hechos = {viejo: 0 for viejo, _ in CAMBIOS}
    dobles = 0
    for p in parrafos():
        for r in p.runs:
            for viejo, nuevo in CAMBIOS:
                if viejo in r.text:
                    r.text = r.text.replace(viejo, nuevo)
                    hechos[viejo] += 1
            if r.text.startswith('Entidad: ') and '  (' in r.text:
                r.text = r.text.replace('  (', ' (')
                dobles += 1

    for viejo, n in hechos.items():
        print(f'   {n} vez(ces): {viejo[:60]}…')
    print(f'   {dobles} rótulos del diccionario sin espacio doble')
    if any(n != 1 for n in hechos.values()) or dobles != 24:
        raise SystemExit('ALGO NO CUADRA: no se guarda el documento.')
    doc.save(str(A))
    print('Documento corregido.')


if __name__ == '__main__':
    main()
