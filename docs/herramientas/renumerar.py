"""Renumera en orden todas las figuras y tablas del documento.

Las secciones agregadas en distintos momentos usaron rangos provisionales
(100, 200, 300) para no colisionar entre sí. Este paso recorre el cuerpo del
documento en orden, asigna a cada pie el número que le corresponde y actualiza
las referencias del texto con el mismo cambio.
"""
import pathlib
import re

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

ARCHIVO = pathlib.Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx'
PIE = re.compile(r'^(Figura|Tabla)\s+(\d+)\s*:')
REF = re.compile(r'\b(Figura|Tabla)\s+(\d+)\b')


def cuerpo(doc):
    """Elementos del cuerpo en orden, a partir de la Introducción."""
    items = []
    for h in doc.element.body.iterchildren():
        if h.tag.endswith('}p'):
            items.append(Paragraph(h, doc))
        elif h.tag.endswith('}tbl'):
            items.append(Table(h, doc))
    inicio = 0
    for i, o in enumerate(items):
        if isinstance(o, Paragraph) and o.text.strip() == 'Introducción' \
                and 'Heading1' in o._p.xml:
            inicio = i
            break
    return items[inicio:]


def parrafos_con_celdas(items):
    for o in items:
        if isinstance(o, Paragraph):
            yield o
        else:
            for fila in o.rows:
                for celda in fila.cells:
                    for p in celda.paragraphs:
                        yield p


def main():
    doc = docx.Document(str(ARCHIVO))
    items = cuerpo(doc)

    # 1. Numeración en orden de aparición de los pies.
    contador = {'Figura': 0, 'Tabla': 0}
    mapa = {'Figura': {}, 'Tabla': {}}
    pies = []
    for o in items:
        if not isinstance(o, Paragraph):
            continue
        m = PIE.match(o.text.strip())
        if not m:
            continue
        tipo, viejo = m.group(1), int(m.group(2))
        contador[tipo] += 1
        nuevo = contador[tipo]
        if viejo in mapa[tipo] and mapa[tipo][viejo] != nuevo:
            print(f'   AVISO: {tipo} {viejo} aparece más de una vez como pie')
        mapa[tipo][viejo] = nuevo
        pies.append((tipo, viejo, nuevo, o.text.strip()[:60]))

    print(f'Pies encontrados: {contador["Figura"]} figuras, '
          f'{contador["Tabla"]} tablas')
    for tipo in ('Figura', 'Tabla'):
        cambios = {v: n for v, n in mapa[tipo].items() if v != n}
        print(f'   {tipo}: {len(cambios)} cambian de número')

    # 2. Reescritura de pies y referencias en un solo pase por cada fragmento.
    def nueva(m):
        tipo, num = m.group(1), int(m.group(2))
        destino = mapa[tipo].get(num)
        return f'{tipo} {destino}' if destino else m.group(0)

    reescritos = sueltos = 0
    for p in parrafos_con_celdas(items):
        if not REF.search(p.text):
            continue
        tocado = False
        for r in p.runs:
            if REF.search(r.text):
                nuevo_texto = REF.sub(nueva, r.text)
                if nuevo_texto != r.text:
                    r.text = nuevo_texto
                tocado = True
        if tocado:
            reescritos += 1
        else:
            # La referencia quedó partida entre varios fragmentos de formato.
            sueltos += 1
            print(f'   PARTIDA: {p.text.strip()[:90]!r}')

    doc.save(str(ARCHIVO))
    print(f'Párrafos reescritos: {reescritos}; referencias partidas: {sueltos}')


if __name__ == '__main__':
    main()
