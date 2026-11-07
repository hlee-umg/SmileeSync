"""Agrega a 4.3.5 el plan de las tres sesiones de prueba previstas."""
from docx import Document
from docx.shared import Emu

import cap4_comun as C
import cifras as X
import formato as F

P = C.PULGADA


def main():
    doc = Document(str(C.ARCHIVO))

    a = X.pie_de(doc, 'Tabla', 78)
    a = F.parrafo(
        doc,
        'Con esa ficha se planificaron tres sesiones, una por cada perfil de '
        'usuario del sistema y en el orden en que la operación las requiere: '
        'primero el profesional que escribe el expediente, después la '
        'profesional que lo consulta y lo continúa, y por último la recepción, '
        'que es quien convierte todo eso en citas. La Tabla 79 las describe con '
        'su objetivo, las tareas que se ejercitan en cada una y lo que se '
        'observa. Al momento de esta entrega las sesiones están planificadas y '
        'no ejecutadas, de modo que lo que se reporta es el diseño del ensayo y '
        'no sus resultados; estos se incorporarán conforme se realicen, con la '
        'ficha de la Tabla 78 como instrumento de registro.', a)

    filas = [['Sesión', 'Participante y etapa', 'Objetivo y tareas',
              'Qué se observa']]
    for s, pa, ob, qo in [
        ('1',
         'Dr. Hee Joon Lee, ortodoncista.\nCapacitación inicial.\n'
         'Duración prevista: 45 minutos.',
         'Validar el módulo de expediente clínico con el profesional que lo '
         'escribirá. Tareas: recorrer el expediente de un paciente, registrar '
         'hallazgos sobre el odontograma en al menos tres piezas, redactar la '
         'nota de evolución de una visita atendida y elaborar un plan de '
         'tratamiento por fases con su presupuesto.',
         'Si la secuencia de la pantalla corresponde al orden en que el '
         'profesional trabaja; si la notación del odontograma le resulta '
         'familiar sin explicación previa; si entiende por qué el sistema le '
         'pide el número de piezas y el uso de anestesia; y qué información del '
         'expediente en papel no encuentra en la pantalla.'),
        ('2',
         'Dra. Rachelle Girón, odontóloga general.\nUso acompañado.\n'
         'Duración prevista: 60 minutos.',
         'Ejercitar el expediente sin acompañamiento en las tareas y con '
         'observación silenciosa. Tareas: consultar el odontograma vigente de '
         'un paciente que la Dra. no atendió, continuar un tratamiento '
         'registrado por otro profesional, documentar una visita con '
         'complicación y consultar su propia agenda.',
         'En qué puntos se detiene y qué busca donde no está; si distingue el '
         'hallazgo vigente del histórico de la pieza; si advierte que la nota '
         'no se puede modificar después de guardarla y cómo reacciona a ello; '
         'y qué preguntas formula que no estén previstas en el guion de la '
         'Tabla 76, pues cada una de ellas señala una omisión del guion o del '
         'sistema.'),
        ('3',
         'Ana Recepción, recepcionista.\nUso acompañado y autónomo.\n'
         'Duración prevista: 60 minutos.',
         'Ejercitar el ciclo completo de la agenda con datos de prueba. '
         'Tareas: registrar pacientes ficticios, consultar la recomendación de '
         'espacios para tres procedimientos de distinta duración, programar '
         'citas a ambos profesionales hasta ocupar las dos unidades dentales, '
         'reprogramar una cita, cancelar otra y registrar los tiempos reales de '
         'una atención concluida.',
         'Si la recomendación de espacios resulta comprensible sin explicación; '
         'si los mensajes de validación indican qué hacer cuando un espacio se '
         'rechaza; cuánto tarda en programar la primera cita y cuánto la '
         'quinta; y si registra los tiempos reales sin que se le recuerde, que '
         'es la tarea de la que depende el aprendizaje del modelo.'),
    ]:
        filas.append([s, pa, ob, qo])
    tab = F.tabla(doc, filas, a,
                  anchos=[Emu(int(0.45 * P)), Emu(int(1.5 * P)),
                          Emu(int(2.2 * P)), Emu(int(2.15 * P))],
                  col_etiqueta=0)
    a = F.pie(doc, 'Tabla 79',
              'Sesiones de prueba de implementación previstas, con su objetivo '
              'y los aspectos por observar', tab)
    a = F.parrafo(
        doc,
        'El orden de las sesiones no es arbitrario. La primera y la segunda '
        'recaen sobre el expediente clínico porque es el módulo que incorpora '
        'el acto profesional y, al mismo tiempo, el que alimenta al modelo '
        'predictivo: si el profesional no documenta la visita, el sistema '
        'pierde las tres variables que explican dos terceras partes de la '
        'duración, conforme a la Tabla 69. La tercera cierra el ciclo con el '
        'perfil que opera la agenda a diario y que es, en la práctica, el '
        'usuario principal del sistema.', a)

    doc.save(str(C.ARCHIVO))
    print('plan de sesiones agregado a 4.3.5')


if __name__ == '__main__':
    main()
