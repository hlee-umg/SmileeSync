"""Manual de usuario: capítulos del personal odontológico y del administrador."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import SALIDA, captura, h, nota, p, pasos        # noqa: E402


def main():
    doc = Document(str(SALIDA))

    h(doc, '6. Guía para el personal odontológico', salto=True)
    p(doc, 'El odontólogo consulta su agenda y escribe el expediente clínico. No '
      'programa citas —eso corresponde a la recepción— pero sí registra sus propias '
      'ausencias, porque esa es información suya.')

    h(doc, '6.1 Consultar mi agenda', 2)
    p(doc, 'Al ingresar, el sistema reconoce al usuario vinculado a la ficha '
      'profesional y preselecciona su agenda. En el selector de la parte superior '
      'derecha aparece «Mi agenda» con su nombre. Para ver la agenda completa de la '
      'clínica, elija «Todos los odontólogos» en ese mismo selector.')
    captura(doc, '04_principal_dia.png', 'Vista por día de la agenda propia')

    h(doc, '6.2 Registrar hallazgos en el odontograma', 2)
    pasos(doc, [
        'Entre a «Expedientes» y localice al paciente.',
        'Abra la pestaña del odontograma.',
        'Pulse sobre la pieza que desea registrar.',
        'Elija el hallazgo y la superficie o superficies afectadas.',
        'Guarde. La pieza queda marcada en el odontograma vigente.',
    ])
    captura(doc, '20_odontograma.png', 'Odontograma con el registro de hallazgos')
    nota(doc, 'No hace falta llenar el odontograma completo la primera vez. Se '
         'registran solo los hallazgos observados; las piezas sin registro se muestran '
         'como sanas y el odontograma se completa con cada visita. Si se equivocó de '
         'pieza, el registro se marca como inactivo: deja de contar para el '
         'odontograma vigente pero no desaparece del historial de esa pieza.')

    h(doc, '6.3 Escribir la nota de evolución', 2)
    p(doc, 'La nota de evolución documenta lo ocurrido en la visita. Además del texto '
      'clínico, el sistema pide tres datos que conviene no omitir.')
    pasos(doc, [
        'Desde el expediente del paciente, pulse «Nueva nota de evolución».',
        'Seleccione la cita atendida a la que corresponde la nota.',
        'Escriba el motivo de consulta, los hallazgos y el procedimiento realizado.',
        'Indique el número de piezas tratadas.',
        'Indique si se utilizó anestesia.',
        'Indique si se presentó alguna complicación.',
        'Guarde.',
    ])
    captura(doc, '21_evolucion.png', 'Formulario de la nota de evolución')
    nota(doc, 'Esos tres últimos datos —piezas, anestesia y complicación— son los que '
         'más explican cuánto dura una atención: juntos reúnen alrededor del sesenta '
         'por ciento del peso del modelo. Son los que permiten que el sistema estime '
         'bien la próxima vez, así que omitirlos degrada las estimaciones de toda la '
         'clínica.', 'Por qué el sistema pide esos datos')
    nota(doc, 'La nota no puede modificarse después de guardarla, y es deliberado: una '
         'nota de evolución es la constancia de lo ocurrido en una visita. Si necesita '
         'corregir o ampliar algo, registre una nota nueva.')

    h(doc, '6.4 Elaborar un plan de tratamiento', 2)
    pasos(doc, [
        'Desde el expediente del paciente, pulse «Nuevo plan de tratamiento».',
        'Agregue cada procedimiento con la pieza y la fase a la que pertenece.',
        'El sistema calcula el total y la cantidad de sesiones que el plan requiere.',
        'Guarde el plan y preséntelo al paciente para su aprobación.',
        'Conforme se ejecuta, registre el avance de cada renglón.',
    ])
    captura(doc, '23_plan_detalle.png', 'Detalle de un plan de tratamiento por fases')
    p(doc, 'El número de sesiones que el plan indica sale de sumar las duraciones '
      'estimadas de cada renglón, repartidas en bloques que no superan dos horas de '
      'sillón y respetando el orden de las fases.')

    h(doc, '6.5 Registrar una ausencia', 2)
    pasos(doc, [
        'Entre a su ficha profesional, en la pantalla de ausencias.',
        'Registre la fecha y el rango de horas en que no estará disponible.',
        'Guarde.',
    ])
    captura(doc, '09_ausencias.png', 'Registro de ausencias del odontólogo')
    p(doc, 'Desde ese momento el sistema deja de ofrecer espacios en esa franja y '
      'rechaza cualquier intento de agendar en ella. Las citas ya programadas en ese '
      'horario no se cancelan solas: hay que reprogramarlas con la recepción.')

    h(doc, '7. Guía para el administrador', salto=True)
    p(doc, 'El administrador mantiene los usuarios, el catálogo de la clínica y los '
      'horarios, y supervisa el modelo predictivo y los reportes.')

    h(doc, '7.1 Dar de alta un usuario', 2)
    pasos(doc, [
        'Entre al módulo de seguridad y usuarios.',
        'Pulse «Nuevo usuario» y registre el nombre y el correo electrónico.',
        'Asigne el rol que corresponde al puesto: administrador, recepcionista, '
        'odontólogo o asistente.',
        'Si es odontólogo, vincúlelo con su ficha profesional del catálogo para que el '
        'sistema reconozca su agenda.',
        'Guarde. El usuario definirá su contraseña y su pregunta secreta al primer '
        'ingreso.',
    ])
    captura(doc, '11_usuarios_form.png', 'Formulario de alta de usuario')

    h(doc, '7.2 Mantener el catálogo', 2)
    p(doc, 'El catálogo reúne cuatro cosas: las especialidades, los procedimientos con '
      'su duración de referencia y su tarifa, los odontólogos y las unidades '
      'dentales. Todas se mantienen igual: alta, edición y baja.')
    captura(doc, '16_catalogo_proc_form.png',
            'Formulario de procedimiento con su duración de referencia')
    nota(doc, 'Los procedimientos no se eliminan: se dan de baja. Eliminarlos dejaría '
         'sin procedimiento a las citas históricas que los usaron y la clínica '
         'perdería su propio historial. Lo mismo vale para pacientes, usuarios y '
         'unidades dentales.')
    p(doc, 'Si la clínica adquiere una unidad dental más, basta con registrarla: la '
      'capacidad de la clínica, la validación al programar y la recomendación de '
      'espacios se calculan a partir de las unidades dadas de alta.')

    h(doc, '7.3 Configurar los horarios de atención', 2)
    p(doc, 'Cada odontólogo tiene un patrón semanal de franjas de atención. El sistema '
      'solo ofrece espacios dentro de esas franjas, de modo que mantenerlas al día es '
      'lo que hace confiable la recomendación.')
    captura(doc, '08_horarios.png', 'Configuración del patrón semanal de atención')

    h(doc, '7.4 Consultar los reportes', 2)
    p(doc, 'El panel de reportes reúne los indicadores del período, las gráficas de '
      'ocupación y la desviación por procedimiento. Esa última tabla es la más útil '
      'para la administración: muestra qué procedimientos se desvían de forma '
      'sistemática de su duración de referencia, que es la señal para corregir el '
      'catálogo.')
    captura(doc, '25_reportes.png', 'Panel de reportes e indicadores')

    h(doc, '7.5 Supervisar el modelo predictivo', 2)
    p(doc, 'El panel de inteligencia muestra el error del modelo vigente, su '
      'comparación con el método de bloques fijos y el histórico de versiones '
      'entrenadas con sus métricas.')
    captura(doc, '26_inteligencia.png', 'Panel del módulo de inteligencia')
    pasos(doc, [
        'Revise el error del modelo vigente y su reducción frente al catálogo.',
        'Si una versión anterior tenía mejores métricas, actívela desde el histórico: '
        'el cambio es inmediato y las estimaciones siguientes la usan.',
        'El reentrenamiento se ejecuta solo, el primer día de cada mes, e incorpora '
        'todas las atenciones registradas desde la última vez.',
    ])
    nota(doc, 'El entrenamiento no detiene el sistema: corre aparte del servidor web y '
         'tarda menos de un segundo. Mientras corre, el sistema sigue estimando con la '
         'versión vigente.')
    doc.save(str(SALIDA))
    print('Manual: capítulos del odontólogo y del administrador.')


if __name__ == '__main__':
    main()
