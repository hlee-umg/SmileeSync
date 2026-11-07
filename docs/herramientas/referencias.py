"""Agrupa las referencias en libros, artículos, tesis y sitios web.

La cuarta entrega pide separar las referencias por tipo de fuente. Se conserva
el formato de sangría francesa y el orden alfabético dentro de cada grupo, y se
agregan las tres fuentes que las secciones nuevas incorporaron.
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402

NUEVAS = [
    'OWASP Foundation. (2025). OWASP Top 10:2025: Los diez riesgos más críticos en '
    'aplicaciones web. https://top10.owasp.org/2025/',
    'Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., '
    'Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, '
    'A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). '
    'Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, '
    '12, 2825–2830.',
    'Wilcoxon, F. (1945). Individual comparisons by ranking methods. Biometrics '
    'Bulletin, 1(6), 80–83. https://doi.org/10.2307/3001968',
]

TESIS = ['Fielding']
SITIOS = ['Django Software Foundation', 'Mell, P.', 'OWASP Foundation',
          'PostgreSQL Global Development Group', 'Schwaber, K.']
LIBROS = ['Chapman, P.', 'Date, C. J.', 'Elmasri, R.', 'Erdogan, S. A.', 'Géron, A.',
          'Han, J.', 'Hastie, T.', 'Laudon, K. C.', 'Mitchell, T. M.',
          'Montgomery, D. C.', 'Pressman, R. S.', 'Ricci, F.', 'Sebesta, R. W.',
          'Sommerville, I.', 'Van Rossum, G.']

GRUPOS = [
    ('Libros', LIBROS),
    ('Artículos científicos', None),
    ('Otras tesis', TESIS),
    ('Sitios web y documentación técnica', SITIOS),
]


def clasificar(ref):
    for nombre, prefijos in GRUPOS:
        if prefijos and any(ref.startswith(p) for p in prefijos):
            return nombre
    return 'Artículos científicos'


def referencia(doc, texto, despues_de):
    p = F.parrafo(doc, texto, despues_de, sangria=False)
    pf = p.paragraph_format
    pf.left_indent = Pt(36)
    pf.first_line_indent = Pt(-36)
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def main():
    doc = Document(str(C.ARCHIVO))
    ps = doc.paragraphs
    i = next(k for k, p in enumerate(ps)
             if p.text.strip() == 'Referencias' and 'Heading1' in p._p.xml)

    refs, ultimo = [], None
    for p in ps[i + 1:]:
        if 'Heading1' in p._p.xml and p.text.strip():
            break
        if p.text.strip():
            refs.append(p.text.strip())
        ultimo = p
    print(f'{len(refs)} referencias encontradas')

    refs = sorted(set(refs) | set(NUEVAS), key=lambda r: r.lower())
    for p in ps[i + 1:]:
        if 'Heading1' in p._p.xml and p.text.strip():
            break
        p._p.getparent().remove(p._p)

    ancla = ps[i]
    for nombre, _ in GRUPOS:
        delgrupo = [r for r in refs if clasificar(r) == nombre]
        if not delgrupo:
            continue
        ancla = F.titulo(doc, nombre, 2, ancla)
        for r in delgrupo:
            ancla = referencia(doc, r, ancla)
        print(f'   {nombre}: {len(delgrupo)}')
    doc.save(str(C.ARCHIVO))


if __name__ == '__main__':
    main()
