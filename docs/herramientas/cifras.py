"""Fija en el documento las cifras del entrenamiento del 15/10/2026."""
import re

from docx import Document
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

import cap4_comun as C
import formato as F

P = C.PULGADA
PIE = re.compile(r'^(Figura|Tabla)\s+(\d+)\s*:')


def pie_de(doc, tipo, numero):
    for o in C.recorrer(doc):
        if isinstance(o, Paragraph):
            m = PIE.match(o.text.strip())
            if m and m.group(1) == tipo and int(m.group(2)) == numero:
                return o
    raise SystemExit(f'No se encontró el pie de {tipo} {numero}')


def reemplazar_tabla(doc, numero, filas, anchos=None, etiqueta=0):
    """Sustituye el contenido de una tabla conservando su pie y su posición."""
    pie = pie_de(doc, 'Tabla', numero)
    previo = pie._p.getprevious()
    while previo is not None and not previo.tag.endswith('}tbl'):
        previo = previo.getprevious()
    if previo is None:
        raise SystemExit(f'La Tabla {numero} no tiene tabla antes del pie')
    ancla = previo.getprevious()
    previo.getparent().remove(previo)
    nueva = F.tabla(doc, filas, ancla, anchos=anchos, col_etiqueta=etiqueta)
    return nueva


def texto(doc, inicio, nuevo):
    """Sustituye el párrafo que comienza con `inicio` por un texto nuevo."""
    for p in doc.paragraphs:
        if p.text.strip().startswith(inicio):
            p.runs[0].text = nuevo
            for r in p.runs[1:]:
                r.text = ''
            return p
    raise SystemExit(f'No se encontró el párrafo: {inicio!r}')


def main():
    doc = Document(str(C.ARCHIVO))

    # ── 4.1.2.2: el coeficiente que se cita al descartar XGBoost ──
    texto(doc, 'Se consideró además la biblioteca XGBoost',
          'Se consideró además la biblioteca XGBoost, mencionada en las '
          'preguntas auxiliares de la investigación como algoritmo candidato. '
          'Se decidió no incorporarla al sistema por dos razones. La primera es '
          'que introduce una dependencia con código nativo compilado, más '
          'pesada de instalar y de mantener en la instancia de producción. La '
          'segunda es que, sobre el conjunto de datos disponible, el bosque '
          'aleatorio alcanzó un coeficiente de determinación de 0.939 y redujo '
          'en 41.8 % el error del método que la clínica emplea hoy, de modo que '
          'el margen de mejora que podría aportar un algoritmo de potenciación '
          'del gradiente no justificaba el costo de la dependencia. La '
          'comparación entre los dos algoritmos efectivamente implementados se '
          'presenta en la sección 4.2.3.10.')

    # ── 4.2.3.10: comparación de algoritmos ──
    texto(doc, 'La Tabla 68 presenta el resultado',
          'La Tabla 68 presenta el resultado del entrenamiento de los dos '
          'algoritmos implementados sobre el conjunto de 472 atenciones '
          'registradas en el sistema, de las cuales 118 se reservaron para '
          'evaluar y no intervinieron en el entrenamiento. La tabla reporta dos '
          'comparaciones distintas y conviene no confundirlas. La primera es '
          'contra la línea base estadística —estimar siempre el promedio '
          'global—, que indica si el modelo aprendió algo: ambos algoritmos la '
          'reducen en más del setenta por ciento. La segunda es contra la '
          'duración de referencia del catálogo, que es el método de bloques '
          'fijos que la clínica emplea hoy, y es la que resuelve la hipótesis '
          'del proyecto. Ahí los dos algoritmos se separan: la regresión lineal '
          'reduce el error un 26.4 %, apenas por encima de la meta del 25 %, '
          'mientras que el bosque aleatorio lo reduce un 41.8 %. Esa diferencia, '
          'y no el coeficiente de determinación, es la razón por la que el '
          'bosque aleatorio es el que opera en producción; su costo —un archivo '
          'doscientas setenta veces mayor y un entrenamiento veintisiete veces '
          'más largo— no resulta limitante en esta escala.')

    filas = [['Métrica', 'Regresión lineal múltiple', 'Bosque aleatorio']]
    for m, lin, rf in [
        ('Registros de entrenamiento / de prueba', '354 / 118', '354 / 118'),
        ('Error absoluto medio (MAE)', '5.91 minutos', '4.67 minutos'),
        ('Raíz del error cuadrático medio (RMSE)', '8.53 minutos',
         '6.47 minutos'),
        ('Coeficiente de determinación (R²)', '0.894', '0.939'),
        ('MAE de la línea base (promedio global)', '19.62 minutos',
         '19.62 minutos'),
        ('Reducción frente a la línea base', '69.9 %', '76.2 %'),
        ('MAE de los bloques del catálogo', '8.03 minutos', '8.03 minutos'),
        ('Reducción frente al catálogo (hipótesis)', '26.4 %', '41.8 %'),
        ('Meta del proyecto', '25 %', '25 %'),
        ('Tiempo de entrenamiento', '0.008 segundos', '0.221 segundos'),
        ('Tamaño del archivo serializado', '2.0 KB', '539.3 KB'),
    ]:
        filas.append([m, lin, rf])
    reemplazar_tabla(doc, 68, filas,
                     anchos=[Emu(int(2.6 * P)), Emu(int(1.9 * P)),
                             Emu(int(1.8 * P))])

    # ── 4.2.3.10: peso de las variables ──
    texto(doc, 'El bosque aleatorio permite',
          'El bosque aleatorio permite, además, examinar el peso de cada '
          'variable en la predicción, que la Tabla 69 presenta. El resultado '
          'tiene una consecuencia metodológica directa: las tres variables de '
          'mayor peso son el número de piezas tratadas, el uso de anestesia y '
          'el tipo de procedimiento, y dos de ellas provienen de la nota '
          'clínica de la visita y no de la cita. Es la justificación empírica '
          'de haber incorporado el módulo de expediente clínico al sistema: las '
          'variables que aporta la nota de evolución reúnen el 66.2 % del peso '
          'del modelo, de modo que sin ella la estimación tendría que renunciar '
          'a la mayor parte de lo que hoy le permite acertar.')

    filas = [['Variable', 'Peso en el modelo', 'Procedencia del dato']]
    for v, peso, orig in [
        ('Número de piezas tratadas', '43.6 %', 'Nota clínica de la visita'),
        ('Uso de anestesia', '19.4 %', 'Nota clínica de la visita'),
        ('Procedimiento: tratamiento de conducto', '16.5 %', 'Cita'),
        ('Procedimiento: colocación de brackets', '6.0 %', 'Cita'),
        ('Procedimiento: retiro de brackets', '5.4 %', 'Cita'),
        ('Aparición de complicaciones', '3.2 %', 'Nota clínica de la visita'),
        ('Hora de inicio de la cita', '0.9 %', 'Cita'),
        ('Procedimiento: sellante de fosas y fisuras', '0.8 %', 'Cita'),
    ]:
        filas.append([v, peso, orig])
    reemplazar_tabla(doc, 69, filas,
                     anchos=[Emu(int(2.8 * P)), Emu(int(1.4 * P)),
                             Emu(int(2.1 * P))])

    doc.save(str(C.ARCHIVO))
    print('cifras del modelo actualizadas (Tablas 68 y 69)')


if __name__ == '__main__':
    main()
