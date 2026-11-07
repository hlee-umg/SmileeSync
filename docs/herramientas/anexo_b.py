"""Regenera el Anexo B desde el diccionario extraído de los modelos.

También sustituye la captura del panel de Inteligencia, que cambió al
incorporarse la validación de la hipótesis.
"""
import json
import pathlib

from docx import Document
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

import cap4_comun as C
import cifras as X
import formato as F

JSON = pathlib.Path.home() / ('mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/'
                              'diagramas/fuentes/diccionario.json')


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)

    def frac(*partes):
        total = sum(partes)
        return [Emu(int(ancho * x / total)) for x in partes]

    # ── captura del panel de Inteligencia ──
    pie = X.pie_de(doc, 'Figura', 53)
    anterior = pie._p.getprevious()
    if anterior is not None and 'graphicData' in anterior.xml:
        viejo = Paragraph(anterior, doc)
        F.reemplazar_imagen(doc, viejo, C.IMG / '26_inteligencia.png',
                            ancho, alto)
        print('Figura 53 actualizada con el panel que valida la hipótesis')

    # ── Anexo B ──
    entidades = json.load(open(JSON, encoding='utf-8'))
    inicio = None
    for p in doc.paragraphs:
        if p.text.strip().startswith('Tabla 80: Diccionario de datos'):
            inicio = p
            break
    if inicio is None:
        raise SystemExit('No se localizó el pie del diccionario de datos.')

    borrados = 0
    actual = inicio._p.getnext()
    while actual is not None:
        texto = ''.join(actual.itertext()).strip()
        if not (actual.tag.endswith('}tbl') or texto.startswith('Entidad:')):
            break
        siguiente = actual.getnext()
        actual.getparent().remove(actual)
        actual = siguiente
        borrados += 1

    a = inicio
    for e in entidades:
        a = F.parrafo(doc, f'Entidad: {e["tabla"]}  ({e["modulo"]})', a,
                      sangria=False, justificado=False, negrita=True, tam=10,
                      espacio_antes=8)
        filas = [['Campo', 'Tipo', 'Nulo', 'Descripción']]
        for c in e['campos']:
            filas.append([c['nombre'], c['tipo'], c['nulo'], c['descripcion']])
        a = F.tabla(doc, filas, a, anchos=frac(2.6, 2.2, 1, 7.2))

    doc.save(str(C.ARCHIVO))
    print(f'Anexo B regenerado: {borrados} elementos sustituidos por '
          f'{len(entidades)} entidades y '
          f'{sum(len(e["campos"]) for e in entidades)} campos')


if __name__ == '__main__':
    main()
