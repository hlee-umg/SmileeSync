"""Capítulo 6, sección 6.2: contrastación de la hipótesis."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_REGLA = (
    'La sección 3.4.4 enunció la hipótesis de trabajo en dos proposiciones. La '
    'alternativa, H1, sostiene que un modelo predictivo construido sobre datos '
    'históricos permite estimar con mayor precisión la duración de los '
    'procedimientos y, en consecuencia, reducir el desajuste entre el tiempo '
    'asignado en la agenda y el tiempo real de atención. La nula, H0, sostiene que '
    'ese modelo no produce una diferencia significativa frente al método que la '
    'clínica utiliza hoy. La regla de decisión quedó fijada con dos condiciones que '
    'deben cumplirse de forma conjunta: que la reducción del error absoluto medio '
    'alcance al menos el 25 % y que la diferencia por pares resulte estadísticamente '
    'significativa en la prueba de rangos con signo de Wilcoxon con un nivel de '
    'significancia de 0.05.')

P_PROCEDIMIENTO = (
    'El contraste se ejecutó sobre el conjunto congelado de 446 atenciones. Las '
    'predicciones no se tomaron de una partición única de entrenamiento y prueba, '
    'como las que reporta la Tabla 68, sino de una validación cruzada repetida de '
    'cinco repeticiones de diez pliegues: en cada pliegue el modelo se entrena sin '
    'las atenciones que después estima, de modo que ninguna se predice con un modelo '
    'que la haya visto, y las cinco predicciones de cada atención se promedian antes '
    'del contraste para que cada registro aporte un único par. El procedimiento es '
    'más exigente que la partición simple porque somete a prueba la totalidad de los '
    'registros y no un subconjunto, y evita que el resultado dependa de lo afortunada '
    'que haya sido una división particular de los datos.')

P_WILCOXON = (
    'La prueba empleada es no paramétrica porque los errores de predicción de '
    'duraciones clínicas no siguen una distribución normal: se concentran cerca de '
    'cero y presentan una cola larga hacia los desvíos grandes. La prueba de rangos '
    'con signo de Wilcoxon no supone normalidad y opera sobre los rangos de las '
    'diferencias por pares, que es exactamente la estructura de este contraste, pues '
    'cada atención aporta el error de los dos métodos sobre el mismo caso. La prueba '
    'se implementó dentro del propio sistema, sin incorporar una biblioteca de '
    'cómputo científico adicional, mediante la aproximación normal del estadístico '
    'con corrección por empates y por continuidad, válida para los tamaños de muestra '
    'de este proyecto; su resultado se verificó contra una implementación de '
    'referencia antes de emplearlo. La Tabla 406 presenta el contraste completo.')

P_DECISION = (
    'Las dos condiciones de la regla de decisión se cumplen. La reducción del error '
    'absoluto medio es de 43.5 %, muy por encima del umbral de 25 % declarado antes '
    'de ejecutar la prueba, y el valor p obtenido es de 4.9 × 10⁻¹⁵, varios órdenes '
    'de magnitud inferior al nivel de significancia de 0.05. En consecuencia, se '
    'rechaza la hipótesis nula: la diferencia entre el modelo predictivo y el método '
    'de bloques fijos no es atribuible al azar. Conviene reparar en que la mediana de '
    'la diferencia por pares es de 1.13 minutos mientras que la media es de 3.06, '
    'asimetría que confirma lo observado en la Tabla 405: en la mayoría de las '
    'atenciones la ventaja del modelo es modesta, y es en la minoría de citas mal '
    'estimadas donde se vuelve decisiva.')

P_PRINCIPAL = (
    'La pregunta principal de la investigación indagaba en qué medida un sistema web '
    'con un modelo predictivo basado en datos históricos mejora la precisión de la '
    'asignación de tiempos frente al método de bloques fijos. La respuesta, en los '
    'términos en que el proyecto se propuso medirla, es que la mejora en un 43.5 % '
    'del error absoluto medio, equivalente a tres minutos por atención, y que esa '
    'mejora es estadísticamente significativa. Las preguntas auxiliares se responden '
    'en la Tabla 407 con la evidencia que cada una admite.')

P_ALCANCE = (
    'Esa respuesta tiene un alcance que conviene precisar para no excederla. El '
    'contraste se ejecutó sobre un conjunto de demostración construido con el volumen '
    'y la variabilidad que la clínica reporta, no sobre su historial efectivo, de '
    'modo que lo demostrado es que el procedimiento funciona y que la arquitectura '
    'del modelo captura la estructura del problema. La magnitud exacta de la mejora '
    'sobre los datos reales de la Clínica Dental Smilee deberá recalcularse cuando '
    'esos datos se incorporen, y el sistema está preparado para hacerlo: el '
    'reentrenamiento mensual deja constancia de cada versión con sus métricas, de '
    'modo que la comparación entre el modelo de hoy y el que opere con datos reales '
    'será directa. Esta limitación se recoge entre las recomendaciones.')

CONTRASTE = [
    ['Elemento del contraste', 'Valor'],
    ['Procedimiento de estimación',
     'Validación cruzada repetida: cinco repeticiones de diez pliegues, promediadas '
     'por registro'],
    ['Atenciones contrastadas', '446'],
    ['Pares con diferencia no nula', '446'],
    ['MAE del método de bloques fijos', '7.02 minutos'],
    ['MAE del modelo predictivo', '3.97 minutos'],
    ['Reducción del error absoluto medio', '43.5 %'],
    ['Umbral declarado en la sección 3.4.4', '25 %'],
    ['Estadístico W+ de Wilcoxon', '71 170.0'],
    ['Valor z (aproximación normal con corrección por empates y continuidad)', '7.8312'],
    ['Valor p bilateral', '4.9 × 10⁻¹⁵'],
    ['Nivel de significancia declarado', '0.05'],
    ['Mediana de la diferencia por pares', '1.13 minutos'],
    ['Decisión', 'Se rechaza H0'],
]

AUXILIARES = [
    ['Pregunta auxiliar', 'Respuesta obtenida'],
    ['¿Qué variables influyen de forma significativa en la duración real de los '
     'procedimientos?',
     'El número de piezas tratadas concentra el 42.6 % del peso del modelo; el tipo '
     'de procedimiento, el 33.6 % sumadas sus categorías; y el uso de anestesia, el '
     '15.5 %. Las tres explican cuatro quintas partes de la capacidad predictiva. La '
     'aparición de complicaciones aporta 1.9 %, la hora de inicio 1.1 % y el '
     'odontólogo responsable 0.8 %. El día de la semana no alcanzó peso apreciable, '
     'contra lo que el planteamiento inicial suponía.'],
    ['¿Qué algoritmo de regresión ofrece la mayor precisión?',
     'El bosque aleatorio, en las tres métricas: error absoluto medio de 3.53 minutos '
     'frente a 4.92 de la regresión lineal múltiple, raíz del error cuadrático medio '
     'de 4.72 frente a 6.20 y coeficiente de determinación de 0.945 frente a 0.905. '
     'XGBoost, el tercer candidato de la pregunta, se descartó por las razones '
     'expuestas en la sección 4.1.2.2.'],
    ['¿En qué grado el sistema de recomendación reduce el desajuste entre el tiempo '
     'asignado y el real?',
     'El desajuste medio por atención cae de 7.02 a 3.97 minutos, una reducción del '
     '43.5 %. La reducción asciende al 71.1 % en las atenciones que el método de '
     'bloques fijos estimaba con más de quince minutos de desvío.'],
    ['¿Cómo contribuye la centralización de la información al control de la operación '
     'y a la toma de decisiones?',
     'El sistema produce indicadores que antes no existían en forma consultable: '
     'utilización de la agenda, desviación entre duración asignada y real, desviación '
     'por procedimiento e histórico clínico por paciente. La agenda en papel '
     'registraba la hora de la cita, pero no la duración efectiva de la atención, de '
     'modo que la clínica carecía del dato con el cual corregir sus propias '
     'estimaciones.'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'En el plano operativo, el sistema produce indicadores', exacto=False)

    a = titulo(doc, '6.2 Contrastación de la hipótesis', 2, a)
    for texto in (P_REGLA, P_PROCEDIMIENTO, P_WILCOXON):
        a = F.parrafo(doc, texto, a)
    t = F.tabla(doc, CONTRASTE, a, anchos=[int(ancho * p) for p in (0.42, 0.58)],
                col_etiqueta=0)
    a = F.pie(doc, 'Tabla 406', 'Contraste de la hipótesis nula mediante la prueba de '
              'rangos con signo de Wilcoxon', t)
    a = F.parrafo(doc, P_DECISION, a)
    a = F.parrafo(doc, P_PRINCIPAL, a)
    t = F.tabla(doc, AUXILIARES, a, anchos=[int(ancho * p) for p in (0.33, 0.67)])
    a = F.pie(doc, 'Tabla 407', 'Respuestas obtenidas a las preguntas auxiliares de la '
              'investigación', t)
    a = F.parrafo(doc, P_ALCANCE, a)
    doc.save(str(C.ARCHIVO))
    print('Sección 6.2 agregada.')


if __name__ == '__main__':
    main()
