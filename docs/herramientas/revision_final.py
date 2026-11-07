"""Revisión estructural del documento antes de la entrega."""
import collections
import pathlib
import re

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

A = (pathlib.Path.home()
     / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx')
PIE = re.compile(r'^(Figura|Tabla)\s+(\d+)\s*:')
REF = re.compile(r'\b(Figura|Tabla)\s+(\d+)\b')
NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

doc = docx.Document(str(A))
items = []
for h in doc.element.body.iterchildren():
    if h.tag.endswith('}p'):
        items.append(Paragraph(h, doc))
    elif h.tag.endswith('}tbl'):
        items.append(Table(h, doc))

avisos = []


def aviso(clase, texto):
    avisos.append((clase, texto))


# --- 1. pies correlativos y anclados a su objeto -----------------------------
cont = collections.Counter()
pies = {'Figura': [], 'Tabla': []}
for i, o in enumerate(items):
    if not isinstance(o, Paragraph):
        continue
    m = PIE.match(o.text.strip())
    if not m:
        continue
    tipo, num = m.group(1), int(m.group(2))
    cont[tipo] += 1
    pies[tipo].append(num)
    if num != cont[tipo]:
        aviso('numeración', f'{tipo} {num} aparece en la posición {cont[tipo]}')
    if 'Fuente:' not in o.text:
        aviso('pie', f'{tipo} {num} sin «Fuente:»')
    previo = items[i - 1] if i else None
    if tipo == 'Tabla':
        if not isinstance(previo, Table):
            aviso('ancla', f'Tabla {num}: el elemento anterior no es una tabla')
    else:
        tiene = isinstance(previo, Paragraph) and previo._p.findall(f'.//{NS}drawing')
        if not tiene:
            aviso('ancla', f'Figura {num}: el elemento anterior no es una imagen')

for tipo in ('Figura', 'Tabla'):
    dup = [n for n, c in collections.Counter(pies[tipo]).items() if c > 1]
    if dup:
        aviso('numeración', f'{tipo} duplicadas: {dup}')

print(f'Pies: {cont["Figura"]} figuras, {cont["Tabla"]} tablas')

# --- 2. referencias cruzadas -------------------------------------------------
def fragmentos():
    for o in items:
        if isinstance(o, Paragraph):
            yield o.text
        else:
            for f in o.rows:
                for c in f.cells:
                    yield c.text

refs = collections.Counter()
for t in fragmentos():
    if PIE.match(t.strip()):
        continue
    for tipo, num in REF.findall(t):
        num = int(num)
        refs[(tipo, num)] += 1
        if num > cont[tipo] or num < 1:
            aviso('referencia', f'«{tipo} {num}» no existe (hay {cont[tipo]})')

sin_citar = [f'{t} {n}' for t in ('Figura', 'Tabla')
             for n in range(1, cont[t] + 1) if (t, n) not in refs]
if sin_citar:
    aviso('referencia', f'nunca se citan en el texto: {", ".join(sin_citar)}')

# --- 3. numeración de los encabezados ---------------------------------------
NIVEL = re.compile(r'w:pStyle w:val="Heading(\d)"')
previo = {}
for o in items:
    if not isinstance(o, Paragraph):
        continue
    m = NIVEL.search(o._p.xml)
    if not m:
        continue
    texto = o.text.strip()
    n = re.match(r'^(\d+(?:\.\d+)*)\s', texto)
    if not n:
        continue
    partes = tuple(int(x) for x in n.group(1).split('.'))
    padre = partes[:-1]
    esperado = previo.get(padre, 0) + 1
    if partes[-1] != esperado:
        aviso('encabezado', f'«{texto[:50]}» rompe la secuencia '
                            f'(se esperaba {".".join(map(str, padre + (esperado,)))})')
    previo[padre] = partes[-1]
    for k in list(previo):
        if len(k) > len(padre) and k[:len(padre)] == padre:
            del previo[k]

# --- 4. formato: fuentes y tamaños ------------------------------------------
tam = collections.Counter()
fuentes = collections.Counter()
for o in items:
    ps = ([o] if isinstance(o, Paragraph)
          else [p for f in o.rows for c in f.cells for p in c.paragraphs])
    for p in ps:
        for r in p.runs:
            if not r.text.strip():
                continue
            fuentes[r.font.name] += 1
            tam[None if r.font.size is None else r.font.size.pt] += 1
            if r.font.name not in ('Times New Roman', 'Consolas', None):
                aviso('fuente', f'«{r.text[:30]}» usa {r.font.name}')
            if r.font.name is None:
                aviso('fuente', f'«{r.text[:40]}» sin fuente declarada')
print('Tamaños:', dict(sorted(tam.items(), key=lambda x: -x[1])))
print('Fuentes:', dict(fuentes))

# --- 5. párrafos vacíos consecutivos ----------------------------------------
racha = 0
for i, o in enumerate(items):
    vacio = (isinstance(o, Paragraph) and not o.text.strip()
             and not o._p.findall(f'.//{NS}drawing'))
    if vacio:
        racha += 1
    else:
        if racha >= 3:
            aviso('espacio', f'{racha} párrafos vacíos seguidos antes de '
                             f'«{(o.text[:40] if isinstance(o, Paragraph) else "una tabla")}»')
        racha = 0

# --- 6. restos de numeración provisional y espacios dobles ------------------
def fragmentos_prosa():
    for o in items:
        ps = ([o] if isinstance(o, Paragraph)
              else [p for f in o.rows for c in f.cells for p in c.paragraphs])
        for p in ps:
            if any(r.font.name == 'Consolas' for r in p.runs):
                continue
            yield p.text

for t in fragmentos():
    if re.search(r'\b(Figura|Tabla)\s+(1\d\d|2\d\d|3\d\d)\b', t):
        aviso('provisional', t[:80])
for t in fragmentos_prosa():
    limpio = t.replace('\t', '|')
    if '  ' in limpio:
        aviso('tipografía', f'espacio doble en «{t.strip()[:60]}»')
    if re.search(r'\s+[,;.]', limpio):
        aviso('tipografía', f'espacio antes de signo en «{t.strip()[:60]}»')

print()
if not avisos:
    print('Sin avisos.')
for clase, texto in avisos:
    print(f'[{clase}] {texto}')
print(f'\nTotal de avisos: {len(avisos)}')
