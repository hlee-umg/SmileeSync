"""Conclusiones y recomendaciones del proyecto."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

CONCLUSIONES = [
    'El objetivo general del proyecto se cumplió. SmileeSync opera sobre un entorno '
    'de producción y resuelve los tres procesos que delimitaban su alcance: la '
    'programación de una cita con la duración estimada por un modelo predictivo, el '
    'registro de la atención con sus tiempos reales y la documentación de la visita '
    'en el expediente clínico. El sistema se construyó con las tecnologías '
    'declaradas en el objetivo —Python, Django y PostgreSQL— y el componente '
    'predictivo se integró al sistema de recomendación de bloques de tiempo, de '
    'manera que la estimación no queda como una cifra informativa sino como el '
    'insumo con que el sistema sugiere dónde cabe cada procedimiento en la agenda.',

    'La hipótesis nula se rechaza. Sobre el conjunto congelado de 446 atenciones, el '
    'modelo reduce en 43.5 % el error absoluto medio del método de bloques fijos que '
    'la clínica emplea, frente al umbral de 25 % declarado antes de ejecutar la '
    'prueba, y la diferencia por pares resulta significativa con un valor p de '
    '4.9 × 10⁻¹⁵ en la prueba de rangos con signo de Wilcoxon. Las dos condiciones '
    'de la regla de decisión se cumplen de forma conjunta, que era la exigencia.',

    'De los dos algoritmos implementados, solo el bosque aleatorio alcanza la meta '
    'del proyecto. La regresión lineal múltiple reduce el error del catálogo en un '
    '23.8 %, por debajo del 25 % exigido, mientras que el bosque aleatorio lo reduce '
    'en un 45.4 % sobre el mismo subconjunto de prueba. La conclusión no es que la '
    'regresión lineal sea un mal método, sino que la duración de un procedimiento '
    'odontológico no se comporta de forma lineal respecto de sus variables '
    'explicativas, y que esa no linealidad es la que decide el resultado.',

    'El aporte del modelo no se distribuye de manera uniforme entre las citas, y '
    'reconocerlo es lo que permite aprovecharlo. En el 62.3 % de las atenciones el '
    'método de bloques fijos ya acertaba con un margen de cinco minutos y el modelo '
    'no mejora esa estimación. Es en el 13.5 % de las citas que el catálogo estimaba '
    'con más de quince minutos de desvío donde el error cae de 25.77 a 7.46 minutos. '
    'Dado que son precisamente esas citas las que desplazan toda la agenda del día, '
    'el beneficio operativo del modelo es mayor que lo que su promedio sugiere.',

    'Las variables que explican la duración provienen del acto clínico y no del '
    'registro administrativo de la cita. El número de piezas tratadas, el uso de '
    'anestesia y la aparición de complicaciones concentran el 60 % del peso del '
    'modelo y los tres se capturan al documentar la visita, no al programarla. De '
    'ahí se sigue una conclusión operativa: la precisión del sistema depende de que '
    'el profesional registre la nota clínica, de modo que una funcionalidad que '
    'podría parecer secundaria resulta ser la condición de la que depende el '
    'componente central del proyecto.',

    'La implantación demostró que el personal de la clínica puede operar el sistema. '
    'Las once sesiones realizadas entre el 2 y el 23 de octubre de 2026 con los tres '
    'perfiles de usuario concluyeron con las tres personas trabajando de forma '
    'autónoma, sin detenciones ni preguntas en sus últimas sesiones. El caso más '
    'ilustrativo es el de la recepción, que es el usuario principal del sistema: '
    'manifestó en la primera sesión que prefería la hoja de cálculo que venía '
    'utilizando y cerró la cuarta, quince días después, sin registrar una sola '
    'dificultad.',

    'De las quince observaciones recogidas en las sesiones, una sola constituyó un '
    'defecto del sistema y cinco correspondían a funcionalidad que el sistema ya '
    'ofrecía y que el usuario suponía ausente. Esa proporción admite una lectura '
    'favorable sobre la etapa de análisis, porque lo que el personal pidió al operar '
    'el sistema coincidía con lo que el levantamiento de requerimientos había '
    'previsto meses antes; y una lectura exigente sobre la interfaz, porque una '
    'funcionalidad que el usuario no encuentra equivale, para él, a una funcionalidad '
    'que no existe.',

    'El sistema no sustituye hoy al expediente en papel, y la razón no es técnica. '
    'La odontóloga general advirtió durante la primera sesión que en Guatemala el '
    'expediente clínico electrónico no reemplaza por sí solo al registro físico, '
    'restricción jurídica ajena al sistema que determinó la estrategia de '
    'implantación paralela. El proyecto entrega, en consecuencia, un sistema que '
    'opera junto al registro existente y no en su lugar, lo que constituye una '
    'delimitación del alcance y no una carencia del desarrollo.',

    'La principal limitación del trabajo es que las cifras se obtuvieron sobre un '
    'conjunto de datos de demostración construido con el volumen y la variabilidad '
    'que la clínica reporta, y no sobre su historial efectivo. Lo demostrado es que '
    'el procedimiento funciona y que la arquitectura del modelo captura la estructura '
    'del problema; la magnitud exacta de la mejora sobre los datos reales deberá '
    'recalcularse cuando el historial se incorpore, para lo cual el sistema ya '
    'contempla el reentrenamiento periódico con registro de cada versión.',
]

RECOMENDACIONES = [
    'Habilitar el cifrado en tránsito antes de operar con información de pacientes '
    'reales. Requiere adquirir un nombre de dominio, emitir el certificado '
    'correspondiente y activar las marcas de seguridad de la sesión que el sistema ya '
    'contempla en su configuración. Mientras esta tarea no se ejecute, el navegador '
    'advertirá que la conexión no es segura y la clínica no debe cargar datos de '
    'pacientes identificables.',

    'Configurar el respaldo periódico de la base de datos con una política de '
    'retención declarada y verificar su restauración al menos una vez. Un respaldo '
    'que nunca se ha restaurado no es un respaldo, es una suposición.',

    'Migrar el historial real de la clínica una vez habilitado el cifrado, y '
    'recalcular sobre él las métricas del modelo y el contraste de la hipótesis. La '
    'migración exige una depuración previa de los registros existentes, '
    'particularmente de las duraciones efectivas, que hoy la clínica no registra de '
    'forma sistemática.',

    'Registrar los tiempos reales de cada atención de manera sistemática desde el '
    'primer día de operación con datos reales. Es el dato del que depende el '
    'aprendizaje del modelo y el único que el sistema no puede obtener por sí mismo; '
    'sin él, la estimación recae en el promedio histórico o en la duración del '
    'catálogo y el proyecto pierde su componente distintivo.',

    'Revisar periódicamente las duraciones de referencia del catálogo con el reporte '
    'de desviación por procedimiento. Cuando un procedimiento muestra un desvío '
    'sistemático, corregir su duración de referencia mejora de inmediato la '
    'estimación de las citas que todavía no tienen historial suficiente.',

    'Incorporar a la interfaz del módulo de inteligencia dos acciones solicitadas por '
    'el administrador durante las sesiones: lanzar un reentrenamiento cuando él lo '
    'decida y configurar su periodicidad. Hoy el reentrenamiento se ejecuta el primer '
    'día de cada mes mediante una tarea programada en el servidor, de modo que '
    'cualquier cambio exige acceso por consola.',

    'Desarrollar la importación de citas y expedientes desde una hoja de cálculo, '
    'solicitada por la recepción. Es la vía por la que la clínica puede trasladar al '
    'sistema la información que hoy mantiene en archivos propios sin transcribirla '
    'manualmente, y reduce de forma considerable la barrera de adopción.',

    'Agregar la impresión del expediente del paciente, solicitada por la odontóloga '
    'general. Mientras el expediente electrónico no tenga validez jurídica autónoma, '
    'la posibilidad de imprimirlo es la que permite que el registro del sistema y el '
    'del papel coincidan sin doble digitación.',

    'Permitir adjuntar la imagen del comprobante de pago, complemento del campo de '
    'referencia que el módulo de cobros ya ofrece, y habilitar reportes '
    'configurables por período y por procedimiento. Ambas solicitudes surgieron de '
    'las sesiones y ninguna afecta al núcleo del sistema.',

    'Extender el período de observación antes de dar por concluida la implantación. '
    'Las once sesiones documentadas cubren un mes; un ciclo completo de operación '
    'con datos reales, que incluya los períodos de mayor demanda de la clínica, '
    'permitirá verificar si la mejora medida se sostiene cuando el volumen de citas '
    'aumenta.',
]


def main():
    doc = Document(str(C.ARCHIVO))
    a = C.buscar(doc, 'Esa respuesta tiene un alcance', exacto=False)

    a = titulo(doc, 'Conclusiones', 1, a)
    a.alignment = 1
    for texto in CONCLUSIONES:
        a = F.parrafo(doc, texto, a)
    a = titulo(doc, 'Recomendaciones', 1, a)
    a.alignment = 1
    for texto in RECOMENDACIONES:
        a = F.parrafo(doc, texto, a)
    doc.save(str(C.ARCHIVO))
    print(f'{len(CONCLUSIONES)} conclusiones y {len(RECOMENDACIONES)} recomendaciones agregadas.')


if __name__ == '__main__':
    main()
