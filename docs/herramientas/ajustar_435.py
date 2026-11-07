"""Pone la sección 4.3.5 en línea con la serie completa de sesiones.

La tercera entrega documentaba dos sesiones realizadas y una pendiente. El
capítulo 5 documenta las once que se ejecutaron entre el 2 y el 23 de octubre,
de modo que este apartado conserva el protocolo y remite a aquel para el
registro.
"""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import cap4_comun as C                                             # noqa: E402

P_SESIONES = (
    'Con esa ficha se organizaron las sesiones de prueba, una por cada perfil de '
    'usuario del sistema y en el orden en que la operación las requiere: primero el '
    'profesional que escribe el expediente, después la profesional que lo consulta y '
    'lo continúa, y por último la recepción, que es quien convierte todo eso en '
    'citas. La Tabla 79 las describe con su objetivo, las tareas que se ejercitan en '
    'cada una, lo que se observa y las fechas en que se ejecutaron. La serie '
    'completa, once sesiones realizadas entre el 2 y el 23 de octubre de 2026 sobre '
    'el entorno de producción descrito en la sección 4.3.1, se documenta en la '
    'sección 5.1.3 con sus observaciones y resultados; este apartado presenta el '
    'protocolo con que se condujeron y el registro fotográfico de la jornada del 16 '
    'de octubre.')

P_PENDIENTE = (
    'Las tres primeras sesiones de cada perfil siguieron el orden de las etapas: '
    'capacitación inicial, uso acompañado y uso autónomo. A partir de la segunda, '
    'los participantes emplearon el sistema por su cuenta entre una sesión y la '
    'siguiente, de modo que las fichas recogen tanto lo observado durante la sesión '
    'como lo que el usuario reportó de ese uso intermedio. Los siete hallazgos que '
    'presenta la sección siguiente se identificaron durante la construcción y la '
    'verificación de las pantallas; las observaciones que produjeron las sesiones se '
    'presentan, por separado y con su resultado verificado, en la Tabla 402.')

ESTADOS = ['Realizada el 02/10, el 09/10 y el 16/10/2026.',
           'Realizada el 02/10 y el 09/10/2026.',
           'Realizada el 02/10, el 09/10, el 16/10 y el 17/10/2026.']


def reemplazar(p, nuevo):
    destino = [r for r in p.runs if r.text.strip()][-1]
    destino.text = nuevo
    for r in p.runs:
        if r is not destino:
            r.text = ''


def main():
    doc = Document(str(C.ARCHIVO))
    reemplazar(C.buscar(doc, 'Con esa ficha se organizaron tres sesiones', exacto=False),
               P_SESIONES)
    reemplazar(C.buscar(doc, 'Queda pendiente la tercera sesión', exacto=False), P_PENDIENTE)

    items = C.recorrer(doc)
    tabla = None
    for i, o in enumerate(items):
        if hasattr(o, 'text') and o.text.strip().startswith('Tabla 79:'):
            tabla = items[i - 1]
            break
    for fila, estado in zip(tabla.rows[1:], ESTADOS):
        p = fila.cells[1].paragraphs[2]
        reemplazar(p, estado)
    for r in C.buscar(doc, 'Tabla 79:', exacto=False).runs:
        if 'su estado de ejecución' in r.text:
            r.text = r.text.replace('su estado de ejecución', 'las fechas en que se ejecutaron')
    doc.save(str(C.ARCHIVO))
    print('Sección 4.3.5 actualizada con la serie completa de sesiones.')


if __name__ == '__main__':
    main()
