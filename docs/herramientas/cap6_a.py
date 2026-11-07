"""Capítulo 6, sección 6.1: análisis de resultados."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_APERTURA = (
    'Los resultados del proyecto se analizan en cuatro planos, porque un sistema de '
    'información no se evalúa con una sola métrica. El primero es funcional: si el '
    'sistema hace lo que se especificó. El segundo es el del componente predictivo: '
    'cuánto mejora la estimación de la duración frente al método que la clínica '
    'emplea. El tercero es el de la implantación: si el personal puede operarlo. El '
    'cuarto es el operativo: qué muestra el sistema sobre la propia operación de la '
    'clínica una vez en marcha.')

P_FUNCIONAL = (
    'En el plano funcional, los tres procesos del alcance operan sobre el entorno de '
    'producción: la programación de una cita con la duración estimada, el registro de '
    'la atención con los tiempos reales y la documentación de la visita en el '
    'expediente clínico. Los nueve módulos del sistema están construidos y '
    'accesibles, las 336 verificaciones automatizadas agrupadas en los ocho conjuntos '
    'de la Tabla 72 se cumplen, y los 29 requerimientos funcionales levantados en el '
    'análisis tienen correspondencia con funcionalidad entregada. La Tabla 404 '
    'relaciona cada objetivo específico del proyecto con el resultado que lo acredita '
    'y con el apartado del documento donde ese resultado se presenta.')

P_PREDICTIVO = (
    'En el plano predictivo, el entrenamiento sobre el conjunto congelado de 446 '
    'atenciones separa con claridad a los dos algoritmos implementados. La regresión '
    'lineal múltiple reduce el error absoluto medio del método de bloques fijos en un '
    '23.8 %, cifra que queda por debajo de la meta del 25 % que el proyecto se fijó; '
    'el bosque aleatorio lo reduce en un 45.4 % sobre el mismo subconjunto de prueba. '
    'La diferencia no se explica por la capacidad de ajuste —ambos alcanzan '
    'coeficientes de determinación altos— sino por la naturaleza del fenómeno: la '
    'duración de un procedimiento odontológico no crece de forma lineal con el número '
    'de piezas ni con el uso de anestesia, y el bosque aleatorio captura esas '
    'interacciones que la regresión lineal, por construcción, no puede representar.')

P_DONDE_GANA = (
    'Ahora bien, el promedio esconde el hallazgo más útil para la clínica. Si se '
    'clasifican las atenciones según la magnitud del desvío que habría cometido el '
    'método de bloques fijos, se observa que la ganancia del modelo no se reparte de '
    'manera uniforme: se concentra justamente en las citas que el catálogo estima '
    'peor. La Tabla 405 presenta esa distribución.')

P_LECTURA = (
    'La lectura de esa tabla es la siguiente. En el 62.3 % de las atenciones el '
    'catálogo ya acertaba con un margen de cinco minutos, y en esa franja el modelo '
    'no aporta nada: su error medio es incluso cuatro décimas de minuto mayor. Pero '
    'en el 13.5 % de las atenciones en que el catálogo se desviaba más de quince '
    'minutos —que son las que desbaratan la agenda del día, porque el retraso se '
    'arrastra a todas las citas siguientes— el error cae de 25.77 a 7.46 minutos. '
    'Dicho de otro modo: el modelo no mejora la estimación de la cita sencilla, que '
    'ya estaba bien estimada; mejora la de la cita complicada, que es la que cuesta '
    'dinero y disculpas. Considerado el conjunto, el modelo acierta mejor que el '
    'catálogo en el 66.6 % de las atenciones y deja tres de cada cuatro con un error '
    'menor o igual a cinco minutos.')

P_LIMITE = (
    'La honestidad del análisis exige señalar también dónde el modelo pierde. Su peor '
    'estimación individual sobre el conjunto de contraste se desvía 61.2 minutos, '
    'frente a los 50.0 minutos de la peor estimación del catálogo: ante una atención '
    'atípica, cuyas circunstancias no están representadas en el historial, el modelo '
    'puede equivocarse más que el método fijo. Esa es la contrapartida de aprender de '
    'los datos y es la razón por la que la estimación se presenta al usuario como una '
    'sugerencia revisable y no como un valor impuesto, conforme al diseño descrito en '
    'la sección 4.2.3.2.')

P_IMPLANTACION = (
    'En el plano de la implantación, las once sesiones documentadas en el capítulo '
    'anterior produjeron quince observaciones, de las cuales una sola constituyó un '
    'defecto del sistema. El indicador más significativo no es, sin embargo, ese '
    'recuento sino la evolución de cada participante a lo largo del mes: las tres '
    'personas terminaron en sesiones de uso autónomo sin detenciones ni preguntas, y '
    'la recepcionista —que en la primera sesión manifestó que prefería la hoja de '
    'cálculo que venía usando— concluyó la cuarta sin registrar una sola dificultad. '
    'Quince días separan ambas sesiones.')

P_OPERATIVO = (
    'En el plano operativo, el sistema produce indicadores que la clínica no tenía. '
    'La pantalla principal informa las citas del día, el porcentaje de utilización de '
    'la agenda, los pacientes activos y la desviación media entre la duración asignada '
    'y la real; el módulo de reportes desagrega esa desviación por procedimiento, que '
    'es el dato con que la administración puede corregir las duraciones de referencia '
    'del catálogo. Antes del sistema esa información no existía en ninguna forma '
    'consultable: la agenda en papel registra la hora de la cita, pero no la duración '
    'efectiva de la atención.')

OBJETIVOS = [
    ['Objetivo específico', 'Resultado que lo acredita', 'Dónde se presenta'],
    ['Analizar los procesos administrativos y los datos históricos para identificar '
     'requerimientos y los factores que inciden en la duración.',
     'Veintinueve requerimientos funcionales con sus criterios de aceptación y la '
     'identificación de las siete variables que explican la duración, con su peso '
     'medido sobre el modelo entrenado.',
     'Secciones 3.1.1 y 4.2.3.10; Tablas 7 a 35 y Tabla 69.'],
    ['Diseñar la arquitectura en tres capas y el modelo de datos relacional en '
     'PostgreSQL bajo criterios de normalización e integridad referencial.',
     'Arquitectura en tres capas implementada y modelo de veinticuatro entidades con '
     'sus relaciones, claves foráneas y restricciones.',
     'Secciones 3.1.2 y 4.1.2.1; Anexos A y B.'],
    ['Desarrollar los módulos con Python y Django aplicando el patrón '
     'Modelo-Vista-Plantilla, con operaciones CRUD, borrado lógico e historial.',
     'Nueve módulos en operación sobre el entorno de producción, con borrado lógico e '
     'historial de auditoría, y 336 verificaciones automatizadas que se cumplen.',
     'Secciones 4.2.3 y 4.3.2; Tabla 72.'],
    ['Construir el modelo predictivo con scikit-learn comparando regresión lineal '
     'múltiple y bosque aleatorio, e integrarlo al sistema de recomendación.',
     'Los dos algoritmos entrenados y comparados sobre el mismo conjunto, con el '
     'bosque aleatorio en producción, y la cascada de estimación de tres niveles '
     'integrada al buscador de espacios de la agenda.',
     'Secciones 4.2.3.2, 4.2.3.3 y 4.2.3.10; Tabla 68.'],
    ['Evaluar el desempeño contrastando el modelo con el método de bloques fijos '
     'mediante MAE, RMSE y R².',
     'Las tres métricas calculadas sobre el subconjunto de prueba y el contraste '
     'formal de la hipótesis nula mediante la prueba de rangos con signo de Wilcoxon.',
     'Tabla 68 y sección 6.2; Tabla 406.'],
]

BANDAS = [
    ['Desvío del método de bloques fijos', 'Atenciones', 'MAE del catálogo',
     'MAE del modelo', 'Reducción'],
    ['Hasta 5 minutos', '278 (62.3 %)', '2.32 min', '2.73 min', '−17.5 %'],
    ['Más de 5 y hasta 10 minutos', '81 (18.2 %)', '7.42 min', '4.98 min', '32.9 %'],
    ['Más de 10 y hasta 15 minutos', '27 (6.1 %)', '12.63 min', '5.94 min', '52.9 %'],
    ['Más de 15 minutos', '60 (13.5 %)', '25.77 min', '7.46 min', '71.1 %'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'De las seis eventualidades', exacto=False)

    a = titulo(doc, 'Capítulo 6. Pruebas', 1, a)
    a.alignment = 1
    a = titulo(doc, '6.1 Análisis de resultados', 2, a)
    a = F.parrafo(doc, P_APERTURA, a)
    a = F.parrafo(doc, P_FUNCIONAL, a)
    t = F.tabla(doc, OBJETIVOS, a,
                anchos=[int(ancho * p) for p in (0.33, 0.42, 0.25)])
    a = F.pie(doc, 'Tabla 404', 'Objetivos específicos del proyecto y resultados que '
              'los acreditan', t)
    a = F.parrafo(doc, P_PREDICTIVO, a)
    a = F.parrafo(doc, P_DONDE_GANA, a)
    t = F.tabla(doc, BANDAS, a,
                anchos=[int(ancho * p) for p in (0.30, 0.17, 0.18, 0.18, 0.17)])
    a = F.pie(doc, 'Tabla 405', 'Error de cada método según la magnitud del desvío del '
              'método de bloques fijos, sobre las 446 atenciones del conjunto '
              'congelado', t)
    for texto in (P_LECTURA, P_LIMITE, P_IMPLANTACION, P_OPERATIVO):
        a = F.parrafo(doc, texto, a)
    doc.save(str(C.ARCHIVO))
    print('Sección 6.1 agregada.')


if __name__ == '__main__':
    main()
