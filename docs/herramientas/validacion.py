"""Incorpora al capítulo 4 la validación de la hipótesis y actualiza 4.3."""
import re

from docx import Document
from docx.shared import Emu
from docx.text.paragraph import Paragraph

import cap4_comun as C
import cifras as X
import formato as F

P = C.PULGADA


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)

    # ── 4.2.3.10: medición de la hipótesis, después del peso de las variables ──
    a = X.pie_de(doc, 'Tabla', 69)
    a = F.parrafo(
        doc,
        'Las dos comparaciones de la Tabla 68 responden preguntas distintas y la '
        'segunda merece detenerse. Medir el modelo contra el promedio global '
        'dice si aprendió, pero no si sirve: la clínica no estima con el '
        'promedio de todos sus procedimientos, sino reservando el bloque que '
        'declara el catálogo. Por eso el entrenamiento arrastra, junto a cada '
        'atención, la duración de referencia que el catálogo le asignaba, y '
        'calcula con ella el error que la clínica habría cometido sobre '
        'exactamente las mismas 118 atenciones del subconjunto de prueba. Esa '
        'duración no es una variable del modelo —se separa antes de entrenar, '
        'de modo que no pueda influir en la predicción— y solo se emplea para '
        'medir.', a)
    a = F.codigo(doc, 'app/inteligencia/entrenamiento.py — función entrenar', r'''
df = pd.DataFrame(filas)
# La duración del catálogo no es una variable del modelo: se arrastra para
# medir contra ella en el mismo subconjunto de prueba.
catalogo = df['duracion_catalogo']
X = df.drop(columns=['duracion_real_min', 'duracion_catalogo'])
y = df['duracion_real_min']
X_ent, X_pru, y_ent, y_pru, _, cat_pru = train_test_split(
    X, y, catalogo, test_size=PROPORCION_PRUEBA, random_state=42)
...
resultado = Resultado(
    ...
    mae=round(float(mean_absolute_error(y_pru, prediccion)), 2),
    mae_base=round(float(mean_absolute_error(y_pru, base)), 2),
    mae_catalogo=round(float(mean_absolute_error(y_pru, cat_pru)), 2))
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'El resultado es el que resuelve la hipótesis de trabajo enunciada en la '
        'sección 3.4.4. Sobre esas 118 atenciones, reservar el bloque del '
        'catálogo produce un error absoluto medio de 8.03 minutos y el modelo '
        'uno de 4.67, lo que representa una reducción de 41.8 %. El criterio de '
        'decisión declarado era una reducción de al menos 25 %, de modo que la '
        'hipótesis nula se rechaza con holgura. Conviene subrayar que la '
        'medición se hace sobre registros que el modelo no vio al entrenarse: '
        'medirla sobre el conjunto completo arrojaría una cifra mejor y '
        'carecería de valor, porque el modelo ya conoce esas atenciones.', a)
    a = F.parrafo(
        doc,
        'La cifra no queda en el informe del entrenamiento: se almacena con la '
        'versión del modelo y el panel del módulo la presenta en una franja '
        'propia, con el error de cada método, la reducción obtenida, la meta del '
        'proyecto y el veredicto. Así, quien administra el sistema puede '
        'comprobar en cualquier momento si la versión en producción sigue '
        'cumpliendo el criterio, que es la pregunta que importa cuando el '
        'modelo se reentrena con datos nuevos.', a)
    a = F.parrafo(
        doc,
        'Esa medición es retrospectiva: se hace sobre atenciones ya ocurridas. '
        'El sistema incorpora además una medición prospectiva, que es la que '
        'corresponde a la operación real. Cada vez que se programa una cita con '
        'el modelo en producción, la predicción emitida queda registrada con el '
        'bloque que se recomendó; cuando esa cita se atiende y se registran sus '
        'tiempos reales, la predicción queda contrastada contra lo que '
        'efectivamente duró. El panel informa entonces tres cifras: el error del '
        'modelo en operación, el del catálogo sobre las mismas citas y la '
        'proporción de atenciones que cayeron dentro del bloque recomendado. La '
        'última es la que importa en la agenda: una estimación que falla por dos '
        'minutos no desordena el día, pero una que se sale del bloque reservado '
        'sí. Esta medición se llena conforme la clínica usa el sistema, de modo '
        'que al momento de esta entrega está vacía y la pantalla lo declara así '
        'en lugar de presentar un resultado que no existe.', a)
    a = F.codigo(doc, 'app/inteligencia/evaluacion.py', r'''
def desempeno_en_operacion():
    """Lectura prospectiva: qué tan cerca quedó cada predicción emitida."""
    filas = list(contrastables())
    if not filas:
        return None

    errores_modelo, errores_catalogo, dentro = [], [], 0
    for p in filas:
        real = p.cita.duracion_real_min
        errores_modelo.append(abs(p.duracion_estimada_min - real))
        errores_catalogo.append(
            abs(p.cita.procedimiento.duracion_promedio_min - real))
        if p.bloque_min_recomendado <= real <= p.bloque_max_recomendado:
            dentro += 1
    ...
'''.strip('\n'), a)

    doc.save(str(C.ARCHIVO))
    print('validación de la hipótesis incorporada a 4.2.3.10')


if __name__ == '__main__':
    main()
