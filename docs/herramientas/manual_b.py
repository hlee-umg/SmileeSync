"""Manual de usuario: capítulo de la recepción."""
import json
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import SALIDA, captura, faq, h, nota, p, pasos   # noqa: E402


def main():
    doc = Document(str(SALIDA))

    h(doc, '5. Guía para la recepción', salto=True)
    p(doc, 'La recepción es quien opera la agenda a diario: registra pacientes, '
      'programa las citas, las reprograma o cancela cuando hace falta, anota los '
      'tiempos reales de cada atención y registra los abonos. También consulta el '
      'expediente clínico, aunque no escribe en él.')

    h(doc, '5.1 Registrar un paciente nuevo', 2)
    pasos(doc, [
        'Entre al módulo «Pacientes» desde el menú lateral.',
        'Antes de crear uno nuevo, busque al paciente por su nombre o apellido: si ya '
        'existe, evitará duplicarlo.',
        'Pulse «Nuevo paciente».',
        'Complete los datos de identificación y de contacto. El nombre, el apellido y '
        'el teléfono son obligatorios.',
        'Registre los antecedentes médicos que el paciente declare. Esta información '
        'la verá el odontólogo al atenderlo.',
        'Pulse «Guardar».',
    ])
    captura(doc, '13_pacientes_form.png', 'Formulario de registro de paciente')
    nota(doc, 'Si se equivocó al escribir un dato, edite la ficha: el sistema conserva '
         'el valor anterior en el historial, de modo que la corrección queda '
         'documentada y no se pierde el rastro.')

    h(doc, '5.2 Programar una cita', 2)
    p(doc, 'Esta es la tarea central del puesto y conviene hacerla desde el buscador '
      'de espacios, porque así el sistema calcula la duración y muestra dónde cabe la '
      'atención.')
    pasos(doc, [
        'En la pantalla principal, en «¿Dónde cabe este procedimiento?», elija el '
        'procedimiento que el paciente solicita.',
        'Elija el odontólogo que lo atenderá.',
        'Indique el número de piezas que se tratarán, si el procedimiento lo requiere.',
        'Pulse «Buscar espacio». El sistema muestra la duración estimada, explica de '
        'dónde salió ese número y resalta en el calendario los espacios libres donde '
        'cabe la atención.',
        'Pulse sobre el espacio elegido: el formulario de la cita se abre con la '
        'fecha, la hora y la duración ya cargadas.',
        'Seleccione al paciente y confirme con «Guardar».',
    ])
    captura(doc, '05_cita_nueva.png', 'Formulario de programación de una cita')
    nota(doc, 'La duración que propone el sistema es una recomendación, no una '
         'obligación. Si el odontólogo indica otra, escríbala a mano: el sistema la '
         'acepta. Lo que no conviene es dejar una duración que se sabe equivocada, '
         'porque de esas diferencias aprende el sistema.')
    p(doc, 'Si el sistema no permite guardar la cita, el mensaje indica cuál de las '
      'condiciones no se cumple. Las dos más frecuentes son que la atención terminaría '
      'después de que cierra la franja de atención del odontólogo, o que las dos '
      'unidades dentales ya están ocupadas en ese horario.')

    h(doc, '5.3 Reprogramar o cancelar una cita', 2)
    pasos(doc, [
        'Entre a «Agenda y Citas» y localice la cita, o púlsela directamente en el '
        'calendario.',
        'Para reprogramar, cambie la fecha o la hora y guarde. Es la misma cita: el '
        'historial conserva la fecha anterior y quién hizo el cambio.',
        'Para cancelar, use la acción «Cancelar». La cita no desaparece: queda '
        'registrada como cancelada.',
    ])
    captura(doc, '07_citas_lista.png', 'Consulta de citas con su estado')
    nota(doc, 'No cancele y vuelva a crear una cita para moverla de día. Reprogramar '
         'conserva la historia de esa cita; cancelar y crear otra hace que la clínica '
         'aparezca con una cancelación que nunca ocurrió.')

    h(doc, '5.4 Registrar la atención con sus tiempos reales', 2)
    p(doc, 'Cuando el paciente termina su consulta hay que anotar a qué hora empezó y '
      'a qué hora terminó realmente. Es la anotación más importante del sistema: es '
      'la que permite que las estimaciones mejoren con el tiempo.')
    pasos(doc, [
        'Abra la cita atendida desde el calendario o desde la consulta de citas.',
        'Registre la hora real de inicio y la de finalización.',
        'Marque la cita como atendida y guarde.',
    ])
    captura(doc, '06_cita_detalle.png',
            'Detalle de la cita con el registro de los tiempos reales')
    p(doc, 'El sistema muestra enseguida la diferencia entre el tiempo que se había '
      'reservado y el que la atención tomó en realidad. Esa diferencia es la que '
      'alimenta al modelo y la que aparece después en el reporte de desviación por '
      'procedimiento.')

    h(doc, '5.5 Registrar un abono', 2)
    pasos(doc, [
        'Entre al módulo de cobros y localice el plan de tratamiento del paciente.',
        'Pulse «Registrar abono».',
        'Indique el monto, la fecha y la forma de pago.',
        'Escriba el número de recibo o la referencia del depósito en el campo '
        'correspondiente.',
        'Guarde. El saldo del plan se recalcula solo.',
    ])
    captura(doc, '24_cobros.png', 'Registro de abonos sobre un plan de tratamiento')
    nota(doc, 'El abono se aplica al plan de tratamiento completo, no a un '
         'procedimiento concreto. Si registró un monto equivocado, anúlelo en lugar de '
         'borrarlo: el saldo se corrige y queda constancia de que hubo un cobro mal '
         'registrado.')

    h(doc, '5.6 Consultar el expediente de un paciente', 2)
    p(doc, 'La recepción puede abrir el expediente clínico completo para saber qué '
      'procede en la siguiente visita, pero no puede escribir en él: el odontograma, '
      'las notas de evolución y los planes los registra el personal odontológico, '
      'porque son actos clínicos. Si abre el expediente y no encuentra el botón para '
      'editar, no es una falla: su usuario no tiene ese permiso.')
    doc.save(str(SALIDA))
    print('Manual: capítulo de la recepción.')


if __name__ == '__main__':
    main()
