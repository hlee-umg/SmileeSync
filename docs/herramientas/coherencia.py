"""Corrige afirmaciones del documento que dejaron de ser ciertas.

    · XGBoost figura como biblioteca del sistema en el objetivo específico y en
      cuatro tablas, pero no se implementó; el capítulo 4 explica por qué. Las
      menciones del marco teórico, de las preguntas de investigación, del
      glosario y de las referencias se conservan: plantear tres candidatos y
      justificar el descarte de uno es parte del método.
    · La base de datos tiene veinticuatro tablas, no dieciséis.
    · El último renglón de la Tabla 2 se acorta para que no derrame una línea
      sola a la página siguiente.
"""
import pathlib

import docx

A = pathlib.Path.home() / ('mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/'
                           'SmileeSync_Cuarta_Entrega.docx')


def reescribir(parrafo, texto):
    """Sustituye el texto conservando el formato del primer fragmento."""
    if not parrafo.runs:
        return False
    parrafo.runs[0].text = texto
    for r in parrafo.runs[1:]:
        r.text = ''
    return True


def main():
    doc = docx.Document(str(A))
    hechos = []

    parrafos = {
        'Construir un modelo predictivo':
            'Construir un modelo predictivo que estime la duración de los '
            'procedimientos odontológicos mediante la biblioteca scikit-learn, '
            'comparando los algoritmos de regresión lineal múltiple y Random '
            'Forest, e integrarlo a un sistema de recomendación que sugiera los '
            'bloques de tiempo más adecuados para la agenda.',
        'El rendimiento de los algoritmos candidatos':
            'El rendimiento de los algoritmos implementados —regresión lineal '
            'múltiple y Random Forest— se evalúa sobre el subconjunto de prueba '
            'mediante tres métricas. El error absoluto medio (MAE) expresa el '
            'error promedio en minutos, por lo que resulta directamente '
            'interpretable en términos del impacto sobre la agenda. La raíz del '
            'error cuadrático medio (RMSE) es más sensible a los errores de gran '
            'magnitud. El coeficiente de determinación (R²) indica la proporción '
            'de varianza explicada por el modelo (Willmott y Matsuura, 2005).',
        'El proyecto contempla la comparación de tres algoritmos':
            'El proyecto contempla la comparación de tres algoritmos: la '
            'regresión lineal múltiple, utilizada como modelo de referencia por '
            'su interpretabilidad; Random Forest, un método de ensamble que '
            'combina múltiples árboles de decisión para reducir la varianza y '
            'capturar relaciones no lineales (Breiman, 2001); y XGBoost, una '
            'implementación optimizada del gradient boosting que ha demostrado '
            'un rendimiento sobresaliente con datos tabulares (Chen y Guestrin, '
            '2016). El desempeño de estos modelos se evaluará con métricas como '
            'el Error Absoluto Medio (MAE), la Raíz del Error Cuadrático Medio '
            '(RMSE) y el Coeficiente de Determinación (R²). El desarrollo de '
            'este componente se apoya en las bibliotecas de Python '
            'scikit-learn, pandas y joblib. La comparación efectivamente '
            'realizada y la razón por la que XGBoost se descartó se documentan '
            'en la sección 4.2.3.10.',
    }
    for inicio, nuevo in parrafos.items():
        for p in doc.paragraphs:
            if p.text.strip().startswith(inicio):
                reescribir(p, nuevo)
                hechos.append(inicio[:46])
                break

    celdas = {
        'scikit-learn, XGBoost, pandas y NumPy':
            'scikit-learn, pandas y joblib',
        'scikit-learn, XGBoost, pandas y NumPy. Licencias de código abierto, '
        'sin costo.':
            'scikit-learn, pandas y joblib. Licencias de código abierto, sin '
            'costo.',
        'Python, Django, PostgreSQL, Bootstrap, scikit-learn y XGBoost: '
        'software de código abierto.':
            'Python, Django, PostgreSQL, Bootstrap y scikit-learn: software de '
            'código abierto.',
        'Entrenamiento y comparación de la regresión lineal múltiple, Random '
        'Forest y XGBoost mediante validación cruzada, ajuste de '
        'hiperparámetros y selección del modelo con mejor desempeño.':
            'Entrenamiento y comparación de los algoritmos de regresión '
            'candidatos mediante validación cruzada, ajuste de hiperparámetros '
            'y selección del modelo con mejor desempeño.',
        'Almacena las dieciséis tablas del modelo relacional y garantiza el '
        'cumplimiento de las propiedades ACID en las transacciones de la '
        'agenda, evitando que dos citas se programen simultáneamente sobre la '
        'misma franja horaria.':
            'Almacena las veinticuatro tablas del modelo relacional y garantiza '
            'el cumplimiento de las propiedades ACID en las transacciones de la '
            'agenda, evitando que dos citas se programen simultáneamente sobre '
            'la misma franja horaria.',
        'Versionan el código fuente y automatizan la ejecución de las pruebas y '
        'el despliegue del sistema en el servidor de producción tras cada '
        'cambio aprobado.':
            'Versionan el código fuente y automatizan las pruebas y el '
            'despliegue en el servidor de producción.',
    }
    for tabla in doc.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                actual = celda.text.strip()
                if actual in celdas:
                    reescribir(celda.paragraphs[0], celdas[actual])
                    for p in celda.paragraphs[1:]:
                        reescribir(p, '')
                    hechos.append(actual[:46])

    doc.save(str(A))
    for h in hechos:
        print('   corregido:', h)
    print(f'{len(hechos)} correcciones')


if __name__ == '__main__':
    main()
