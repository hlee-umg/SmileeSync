"""Capítulo 4, sección 4.3: Pruebas de implementación."""
from docx import Document
from docx.shared import Emu

import cap4_comun as C
import formato as F

P = C.PULGADA


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)
    a = C.antes_de_referencias(doc)

    def tabla(filas, numero, titulo_pie, anclaje, anchos=None, etiqueta=0):
        t = F.tabla(doc, filas, anclaje, anchos=anchos, col_etiqueta=etiqueta)
        return F.pie(doc, f'Tabla {numero}', titulo_pie, t)

    a = F.titulo(doc, '4.3 Pruebas de implementación', 2, a)
    a = F.parrafo(
        doc,
        'Las pruebas de implementación consisten en poner el sistema en manos de '
        'sus usuarios reales, en el entorno en que habrán de operarlo, y '
        'observar si resuelve el trabajo tal como la clínica lo realiza. Se '
        'distinguen de la verificación técnica —que comprueba que el código hace '
        'lo que el programador supone— porque lo que ponen a prueba es otra '
        'cosa: si el sistema corresponde a la operación real de la clínica, si '
        'el personal entiende lo que ve en la pantalla y si las decisiones de '
        'diseño que se tomaron en el escritorio sobreviven al uso cotidiano.', a)
    a = F.parrafo(
        doc,
        'La presente sección documenta, en ese orden: el entorno y el alcance de '
        'las pruebas; la verificación técnica que se exigió como condición '
        'previa a entregar el sistema a los usuarios; los usuarios y los datos '
        'con que se preparó el ensayo; el guion de acompañamiento con las '
        'preguntas previstas y sus respuestas; el protocolo con que se registra '
        'cada sesión; y los hallazgos derivados del uso, con las correcciones '
        'que se aplicaron.', a)

    a = F.titulo(doc, '4.3.1 Entorno y alcance', 3, a)
    a = F.parrafo(
        doc,
        'El sistema se ejecuta en la instancia de producción descrita en la '
        'sección 4.1.1 y se accede a él desde cualquier navegador, sin instalar '
        'nada en los equipos de la clínica. Esa condición es parte de lo que se '
        'pone a prueba: la clínica no dispone de personal de informática, de '
        'modo que un sistema que exigiera instalación o mantenimiento en cada '
        'equipo habría fracasado por esa sola razón.', a)
    a = F.parrafo(
        doc,
        'El alcance de las pruebas comprende los tres procesos que constituyen '
        'la operación diaria de la clínica y que son también los que el sistema '
        'transforma: la programación de una cita con la duración estimada, la '
        'atención con el registro de los tiempos reales y la documentación de la '
        'visita en el expediente. El resto de los módulos —usuarios, catálogos, '
        'pacientes, planes y cobros— se prueba en la medida en que esos tres '
        'procesos los requieren, que es también la medida en que la clínica los '
        'usa.', a)

    a = F.titulo(doc, '4.3.2 Verificación técnica previa a la entrega', 3, a)
    a = F.parrafo(
        doc,
        'Entregar a los usuarios un sistema que falla en lo elemental convierte '
        'la prueba de implementación en una sesión de depuración y desperdicia '
        'la disposición del personal, que es un recurso escaso. Por esa razón se '
        'estableció como condición previa que el sistema superara un conjunto de '
        'verificaciones automatizadas, agrupadas en ocho conjuntos según el '
        'comportamiento que comprueban. Cada verificación formula una '
        'afirmación sobre el sistema y la comprueba contra la base de datos y '
        'contra las pantallas; en total son 299 y las 299 se cumplen. La Tabla '
        '217 las relaciona.', a)

    filas = [['Conjunto', 'Qué comprueba', 'Verificaciones']]
    for n, q, c in [
        ('Horarios y ausencias',
         'Patrón semanal de atención, registro de ausencias y cálculo de la '
         'disponibilidad efectiva como la resta de ambos.', '22'),
        ('Permisos por rol',
         'Acceso de cada rol a cada módulo y a cada vista, incluido el intento '
         'de acceso directo por dirección sin pasar por el menú.', '33'),
        ('Calendario',
         'Construcción de la rejilla, cambio de período, filtros por '
         'profesional e indicadores del módulo Principal.', '31'),
        ('Recomendación',
         'Estimación de la duración, cálculo de los espacios sugeridos y su '
         'presentación sobre el calendario.', '20'),
        ('Flujos completos',
         'Siete recorridos de extremo a extremo, desde el registro del paciente '
         'hasta el cobro; incluye la revisión de veintidós pantallas en busca '
         'de marcas de plantilla sin procesar.', '31'),
        ('Capacidad y unidades',
         'Cálculo de la capacidad real de la clínica, asignación automática de '
         'las unidades dentales y detección de traslapes.', '31'),
        ('Expediente clínico',
         'Odontograma y vigencia de los hallazgos, notas de evolución, planes '
         'por fases, reparto en sesiones, presupuesto, abonos y saldos.', '82'),
        ('Modelo predictivo',
         'Conjunto de entrenamiento, métricas contra la línea base, versionado, '
         'caché del modelo, los tres niveles de la cadena de respaldo y los '
         'paneles de inteligencia y de reportes.', '49'),
        ('Total', '', '299'),
    ]:
        filas.append([n, q, c])
    a = tabla(filas, 217,
              'Conjuntos de verificación automatizada exigidos como condición '
              'previa a las pruebas de implementación', a,
              anchos=[Emu(int(1.5 * P)), Emu(int(3.9 * P)), Emu(int(0.9 * P))])
    a = F.parrafo(
        doc,
        'Dos de esos conjuntos merecen una nota. El de permisos por rol no '
        'comprueba que el botón esté oculto, sino que la dirección esté '
        'denegada: para cada rol y cada vista que modifica información, '
        'solicita la dirección directamente y verifica que el sistema responda '
        'con el rechazo correspondiente. El de flujos completos incorpora una '
        'verificación que no se anticipó al diseñarlo y que se agregó a raíz de '
        'un hallazgo de las pruebas de uso: recorre veintidós pantallas del '
        'sistema y falla si encuentra en ellas marcas de plantilla sin procesar, '
        'que es la forma en que un comentario mal escrito en el código llega a '
        'mostrarse al usuario. Su origen se documenta en la sección 4.3.6.', a)

    a = F.titulo(doc, '4.3.3 Usuarios y datos de preparación del ensayo', 3, a)
    a = F.parrafo(
        doc,
        'Cada integrante del personal recibió su propio usuario, con el rol que '
        'corresponde a su función. La decisión de no compartir un usuario entre '
        'varias personas no es un formalismo: el historial de auditoría registra '
        'quién realizó cada cambio, y un usuario compartido convertiría ese '
        'registro en una constancia inútil. La Tabla 218 relaciona los usuarios '
        'creados para el ensayo.', a)

    filas = [['Usuario', 'Rol en la clínica', 'Rol en el sistema',
              'Qué puede hacer']]
    for u, rc, rs, q in [
        ('Hee Joon Lee', 'Odontólogo, especialista en ortodoncia',
         'Odontólogo',
         'Consulta su propia agenda y los pacientes; escribe el expediente '
         'clínico, las notas de evolución y los planes de tratamiento; registra '
         'sus ausencias.'),
        ('Rachelle Girón', 'Odontóloga general', 'Odontólogo',
         'Las mismas facultades, sobre su propia agenda y sobre los pacientes '
         'que atiende.'),
        ('Ana Recepción', 'Recepcionista', 'Recepcionista',
         'Programa, reprograma y cancela citas; registra pacientes y los '
         'tiempos reales de atención; consulta el expediente sin escribir en '
         'él; registra abonos y consulta los reportes.'),
        ('Administrador General', 'Propietario de la clínica',
         'Administrador',
         'Todos los módulos, incluidos el catálogo, los usuarios y el módulo '
         'de inteligencia, desde el que se entrena y activa el modelo.'),
    ]:
        filas.append([u, rc, rs, q])
    a = tabla(filas, 218, 'Usuarios creados para las pruebas de implementación',
              a, anchos=[Emu(int(1.2 * P)), Emu(int(1.4 * P)),
                         Emu(int(1.0 * P)), Emu(int(2.7 * P))])

    a = F.parrafo(
        doc,
        'El sistema no se entregó vacío. Una base de datos sin información no '
        'permite probar nada de lo que importa: no hay agenda que consultar, la '
        'estimación recae en la duración del catálogo y los reportes no tienen '
        'qué reportar. Se preparó, por eso, un conjunto de datos de '
        'demostración que reproduce dos meses de operación con el volumen y la '
        'variabilidad reales de la clínica. La Tabla 219 lo describe. Los '
        'nombres de los pacientes son ficticios; las duraciones reales se '
        'generaron a partir de la duración de referencia de cada procedimiento '
        'con la variabilidad que la clínica reporta, incluyendo el ritmo '
        'distinto de cada profesional y la aparición ocasional de '
        'complicaciones.', a)

    filas = [['Elemento', 'Cantidad', 'Observación']]
    for e, c, o in [
        ('Período cubierto', '31/08/2026 al 30/10/2026',
         'Seis semanas de historial y dos de agenda futura.'),
        ('Especialidades', '5', 'Catálogo de la clínica.'),
        ('Procedimientos', '10',
         'Con su duración de referencia y su tarifa.'),
        ('Odontólogos', '2',
         'Un ortodoncista y una odontóloga general, con su patrón semanal de '
         'veinte franjas de atención.'),
        ('Unidades dentales', '2',
         'Es el recurso que limita la atención simultánea.'),
        ('Pacientes', '24', 'Con sus antecedentes médicos.'),
        ('Citas', '675',
         '446 atendidas, 194 programadas y 35 canceladas.'),
        ('Notas de evolución', '446',
         'Una por cada atención, con piezas tratadas, anestesia y '
         'complicaciones.'),
        ('Registros de entrenamiento', '446',
         'Es el conjunto con que se entrenó el modelo que opera en el '
         'sistema.'),
    ]:
        filas.append([e, c, o])
    a = tabla(filas, 219,
              'Datos de demostración cargados para las pruebas de '
              'implementación', a,
              anchos=[Emu(int(1.7 * P)), Emu(int(1.4 * P)), Emu(int(3.2 * P))])

    a = F.titulo(doc, '4.3.4 Guion de acompañamiento: preguntas previstas y '
                      'respuestas', 3, a)
    a = F.parrafo(
        doc,
        'Antes de entregar el sistema se preparó un guion de acompañamiento. Su '
        'propósito no es documentar la operación del sistema, que es lo que hace '
        'el manual de usuario, sino anticipar las preguntas que cada rol '
        'formularía al encontrarse con una forma de trabajar distinta de la que '
        'conoce. Las preguntas se derivaron de los puntos en que el sistema se '
        'aparta de la agenda en papel: la estimación de la duración, que antes '
        'era un criterio del profesional; la imposibilidad de borrar, que antes '
        'era tachar; la separación de permisos, que antes no existía porque el '
        'cuaderno era de todos.', a)
    a = F.parrafo(
        doc,
        'El guion cumple además una función de diseño. Una pregunta que se '
        'anticipa y cuya respuesta resulta difícil de dar señala, casi siempre, '
        'una decisión mal resuelta en el sistema antes que una duda del usuario. '
        'Dos de los hallazgos de la sección 4.3.6 se identificaron al redactar '
        'estas respuestas y no al observar el uso. Las preguntas previstas para '
        'la recepción se presentan en la Tabla 220; las de los odontólogos, en '
        'la Tabla 221; las del administrador, en la Tabla 222.', a)

    filas = [['Pregunta prevista', 'Respuesta']]
    for p, r in [
        ('¿Cómo sé cuánto tiempo reservarle a un paciente que pide una resina '
         'en dos piezas?',
         'En el calendario se elige el procedimiento, el odontólogo que lo '
         'atenderá y el número de piezas. El sistema estima la duración, dice de '
         'dónde sacó ese número y resalta en verde los espacios de la semana '
         'donde esa cita cabe completa. Basta pulsar uno de esos espacios para '
         'programarla.'),
        ('El sistema me dice 75 minutos, pero el doctor dice que él lo hace en '
         '60. ¿A quién le hago caso?',
         'Al doctor: la duración se puede escribir a mano y el sistema la '
         'acepta. La estimación es una recomendación, no una restricción. '
         'Además, al registrarse los tiempos reales el modelo aprende el ritmo '
         'de cada profesional, de modo que si efectivamente lo hace en 60 '
         'minutos, en unas semanas el sistema propondrá 60.'),
        ('¿Por qué no me deja agendar a las 11:30 si el doctor está libre a esa '
         'hora?',
         'El sistema exige cuatro condiciones y el mensaje de error indica cuál '
         'no se cumple. Las dos más frecuentes son que la cita no termine antes '
         'de que cierre la franja de atención —una cita de una hora no cabe a '
         'las 11:30 si la jornada termina a las 12:00— y que los dos sillones '
         'estén ocupados a esa hora, aunque el odontólogo esté libre.'),
        ('Un paciente quiere cambiar su cita del martes al jueves. ¿Tengo que '
         'cancelarla y crear otra?',
         'No. Se abre la cita y se cambia la fecha: es la misma cita '
         'reprogramada. El historial conserva la fecha anterior y quién hizo el '
         'cambio. Cancelar y crear de nuevo haría que la clínica apareciera con '
         'una cancelación que no ocurrió.'),
        ('¿Y si el paciente no llega?',
         'Se cancela la cita. El registro no desaparece: queda como cancelada y '
         'suma a la tasa de cancelación del reporte, que es información que la '
         'clínica necesita. Las citas canceladas no se cuentan para entrenar el '
         'modelo, porque no hay duración real que aprender de ellas.'),
        ('¿Puedo escribir en el expediente del paciente?',
         'Puede consultarlo completo, pero no escribir en él. El odontograma, '
         'las notas de evolución y los planes los registra el personal '
         'odontológico, porque son actos clínicos. Si abre la pantalla, verá la '
         'información sin los botones para modificarla.'),
        ('¿Dónde registro que el paciente abonó Q300 de su tratamiento?',
         'En el módulo de cobros, como un abono sobre el plan aprobado del '
         'paciente. El saldo se recalcula solo: no hay que anotarlo en ninguna '
         'parte.'),
        ('Registré un pago con el monto equivocado. ¿Lo puedo borrar?',
         'Se anula, que no es lo mismo que borrarlo. El abono queda marcado como '
         'anulado, el saldo se corrige y queda constancia de que existió un '
         'cobro mal registrado. Después se ingresa el abono correcto.'),
        ('¿Tengo que anotar a qué hora terminó realmente la consulta?',
         'Sí, y es la anotación más importante del sistema. Es lo que permite '
         'que la estimación mejore: cada atención con su tiempo real se '
         'incorpora al conjunto con que se entrena el modelo. Sin ese registro '
         'el sistema seguiría estimando con la duración del catálogo '
         'indefinidamente.'),
        ('Me equivoqué al escribir el apellido de un paciente. ¿Lo puedo '
         'corregir?',
         'Sí. Se edita la ficha y el historial conserva el valor anterior, de '
         'modo que la corrección quede documentada.'),
        ('¿Puedo entrar desde mi teléfono?',
         'Sí: es un sitio web y las pantallas se adaptan al tamaño de la '
         'ventana. Para el calendario semanal conviene la computadora, porque '
         'muestra seis días a la vez.'),
    ]:
        filas.append([p, r])
    a = tabla(filas, 220,
              'Guion de acompañamiento: preguntas previstas de la recepción y '
              'sus respuestas', a,
              anchos=[Emu(int(2.1 * P)), Emu(int(4.2 * P))], etiqueta=None)

    filas = [['Pregunta prevista', 'Respuesta']]
    for p, r in [
        ('Al entrar, ¿veo la agenda de toda la clínica o solo la mía?',
         'La suya. El sistema reconoce al usuario vinculado a su ficha '
         'profesional y preselecciona su agenda al ingresar. Si necesita ver la '
         'de la clínica completa, se elige «Todos los odontólogos» en el filtro '
         'superior.'),
        ('¿Puedo agendar una cita yo mismo?',
         'La programación de citas corresponde a la recepción, de modo que su '
         'acceso a la agenda es de consulta. Sí puede, en cambio, registrar sus '
         'ausencias, porque esa es información suya.'),
        ('Voy a salir a un congreso el 20 de noviembre. ¿Cómo bloqueo ese día?',
         'En su ficha, en la pantalla de ausencias, se registra la fecha y el '
         'rango de horas. Desde ese momento el sistema deja de ofrecer espacios '
         'en esa franja y rechaza cualquier intento de agendar ahí, con un '
         'mensaje que explica que existe una ausencia registrada. Una ausencia '
         'de medio día no cancela el resto de la jornada: el sistema la resta y '
         'conserva disponible lo que queda.'),
        ('¿Tengo que llenar el odontograma completo del paciente la primera '
         'vez que lo atiendo?',
         'No. Se registran únicamente los hallazgos que observa; las piezas sin '
         'registro se muestran como sanas. El odontograma se va completando con '
         'cada visita.'),
        ('Registré un hallazgo en la pieza equivocada. ¿Se borra el anterior?',
         'El registro se marca como inactivo y deja de contar para el '
         'odontograma vigente, pero no desaparece del historial de la pieza. El '
         'expediente conserva la secuencia completa de lo que se observó y '
         'cuándo, que es lo que permite seguir la evolución de un diente.'),
        ('¿Por qué el sistema me pide el número de piezas tratadas y si usé '
         'anestesia?',
         'Porque son dos de las tres variables que más explican cuánto dura una '
         'atención. Juntas con la aparición de complicaciones reúnen el 60.7 % '
         'del peso del modelo, de modo que son esos tres datos, y no el tipo de '
         'procedimiento por sí solo, los que permiten que el sistema estime con '
         'precisión. Es también la razón por la que la nota de evolución no es '
         'un trámite: es la fuente de la que el sistema aprende.'),
        ('¿La nota clínica se puede modificar después de guardarla?',
         'No desde la pantalla, y es deliberado: una nota de evolución es la '
         'constancia de lo ocurrido en una visita, y un expediente que se puede '
         'reescribir a posteriori pierde su valor como documento. Cada visita '
         'admite una sola nota; si hay algo que agregar, se consigna en la nota '
         'de la visita siguiente.'),
        ('El plan que presupuesté dice que requiere cinco sesiones. ¿De dónde '
         'sale ese número?',
         'De la suma de las duraciones estimadas de cada renglón del plan, '
         'repartidas en bloques que no pasan de dos horas de sillón y '
         'respetando el orden de las fases, de modo que una fase posterior no se '
         'adelante. Es una previsión para conversar con el paciente, no una '
         'reserva: agendar cada sesión sigue siendo decisión de la recepción.'),
        ('¿Puedo ver cuánto me desvío del tiempo que me asignan?',
         'Sí. En la consulta de citas, cada atención muestra el tiempo asignado, '
         'el real y la diferencia entre ambos. El reporte que consolida esa '
         'desviación por procedimiento corresponde al administrador, porque es '
         'información de la clínica y no de un profesional.'),
        ('Si el sistema no está disponible un día, ¿cómo atiendo?',
         'La agenda del día se puede imprimir desde la vista por día del '
         'calendario, y las atenciones de ese día se registran después. El '
         'registro posterior no afecta al modelo: lo que importa es la duración '
         'real, no el momento en que se capturó.'),
    ]:
        filas.append([p, r])
    a = tabla(filas, 221,
              'Guion de acompañamiento: preguntas previstas de los odontólogos '
              'y sus respuestas', a,
              anchos=[Emu(int(2.1 * P)), Emu(int(4.2 * P))], etiqueta=None)

    filas = [['Pregunta prevista', 'Respuesta']]
    for p, r in [
        ('¿Cada cuánto hay que volver a entrenar el modelo?',
         'No existe una regla única; el criterio es la cantidad de información '
         'nueva. Con el volumen de la clínica —alrededor de setenta atenciones '
         'al mes— un reentrenamiento mensual incorpora material suficiente para '
         'que las métricas cambien. El comando admite la opción de activar la '
         'versión nueva únicamente si reduce el error de la vigente, con lo que '
         'reentrenar no implica riesgo.'),
        ('¿El sistema se detiene mientras se entrena el modelo?',
         'No. El entrenamiento es un comando que se ejecuta aparte del servidor '
         'web y tarda menos de un segundo; mientras corre, el sistema sigue '
         'estimando con la versión que está en producción. La versión nueva '
         'entra en operación solo cuando se la activa.'),
        ('Si el modelo nuevo resulta peor que el anterior, ¿cómo vuelvo atrás?',
         'El panel de inteligencia conserva el histórico completo de las '
         'versiones entrenadas con sus métricas. Se activa la versión anterior '
         'desde ese mismo panel y el cambio es inmediato: solo una versión está '
         'en producción a la vez.'),
        ('¿Qué pasa con la estimación cuando agregamos un procedimiento nuevo '
         'al catálogo?',
         'El modelo no conoce ese procedimiento, de modo que la estimación recae '
         'en la duración de referencia que se declare al darlo de alta. Cuando '
         'se acumulan tres atenciones, pasa a usar el promedio real de la '
         'clínica; y al siguiente reentrenamiento, el modelo lo incorpora. La '
         'pantalla declara en cada caso de dónde proviene el número, de modo que '
         'se sabe en qué etapa está.'),
        ('¿Cómo doy de alta a una asistente nueva?',
         'En el módulo de usuarios, con el rol de asistente, que da acceso de '
         'consulta a la agenda y al expediente. El sistema envía al usuario a '
         'definir su contraseña y exige que registre una pregunta secreta para '
         'poder recuperarla.'),
        ('¿Puedo eliminar un procedimiento que ya no realizamos?',
         'Se da de baja, lo que lo retira de los formularios y del catálogo '
         'activo sin borrarlo. Eliminarlo haría que las citas históricas que lo '
         'usaron quedaran sin procedimiento y la clínica perdería su propio '
         'historial, que es justamente lo que alimenta la estimación.'),
        ('Si compramos un tercer sillón, ¿hay que modificar el sistema?',
         'No: se registra en el catálogo de unidades dentales. La capacidad de '
         'la clínica, la validación al programar y la recomendación de espacios '
         'se calculan a partir de las unidades dadas de alta, de modo que las '
         'tres se ajustan solas al nuevo sillón.'),
        ('¿Quién puede ver el expediente clínico de un paciente?',
         'El personal odontológico lo escribe y lo consulta; la recepción lo '
         'consulta sin escribir; el administrador tiene acceso completo. Cada '
         'cambio queda registrado con el usuario que lo hizo, de modo que el '
         'acceso es trazable.'),
        ('¿Dónde quedan los datos y qué pasa si se pierde el servidor?',
         'Los datos residen en la base de datos PostgreSQL de la instancia. El '
         'respaldo periódico de esa base es la tarea pendiente más importante '
         'del plan de puesta en producción, junto con la habilitación de HTTPS; '
         'ambas se documentan en la sección 4.1.3.5.'),
    ]:
        filas.append([p, r])
    a = tabla(filas, 222,
              'Guion de acompañamiento: preguntas previstas del administrador y '
              'sus respuestas', a,
              anchos=[Emu(int(2.1 * P)), Emu(int(4.2 * P))], etiqueta=None)

    a = F.titulo(doc, '4.3.5 Protocolo y registro de las sesiones', 3, a)
    a = F.parrafo(
        doc,
        'Las sesiones de prueba se organizan en tres etapas sucesivas, de modo '
        'que la observación recoja información distinta en cada una. La primera '
        'es la capacitación inicial: se recorre el sistema con el usuario, se '
        'ejecuta con él el proceso que le corresponde y se resuelven las dudas '
        'que surjan, apoyándose en el guion de la sección anterior. La segunda '
        'es el uso acompañado: el usuario opera por su cuenta sobre datos de '
        'demostración y el observador anota, sin intervenir, en qué puntos se '
        'detiene, qué busca donde no está y qué entiende distinto de lo que la '
        'pantalla dice. La tercera es el uso autónomo, en el que el personal '
        'emplea el sistema sin acompañamiento y comunica lo que encuentra.', a)
    a = F.parrafo(
        doc,
        'La segunda etapa es la que produce los hallazgos más valiosos, y por '
        'una razón concreta: en la capacitación el usuario pregunta y en el uso '
        'autónomo reporta solo lo que le impide trabajar, mientras que en el uso '
        'acompañado se observa aquello que el usuario resuelve por su cuenta sin '
        'mencionarlo —volver atrás, repetir un paso, buscar un botón en el lugar '
        'equivocado—, que son justamente los defectos de diseño que nadie '
        'reporta. Cada sesión se registra con la ficha de la Tabla 223, que '
        'fija qué se anota para que las observaciones de sesiones distintas '
        'resulten comparables.', a)

    filas = [['Campo de la ficha', 'Qué se registra']]
    for c, q in [
        ('Fecha y duración', 'Día de la sesión y tiempo efectivo de trabajo.'),
        ('Usuario y rol', 'Quién operó el sistema y con qué rol ingresó.'),
        ('Etapa', 'Capacitación inicial, uso acompañado o uso autónomo.'),
        ('Procesos ejercitados',
         'Cuáles de los tres procesos del alcance se ejecutaron y cuántas '
         'veces.'),
        ('Tareas completadas sin ayuda',
         'Tareas que el usuario concluyó por sí solo, con el tiempo que le '
         'tomó la primera y las siguientes.'),
        ('Puntos de detención',
         'Momentos en que el usuario se detuvo, qué buscaba y dónde lo buscó.'),
        ('Preguntas formuladas',
         'Preguntas del usuario, indicando si estaban previstas en el guion o '
         'no. Una pregunta no prevista señala una omisión del guion o del '
         'sistema.'),
        ('Discrepancias con la operación real',
         'Casos en que el sistema exige algo que la clínica no hace, o no '
         'admite algo que la clínica sí hace.'),
        ('Defectos observados',
         'Comportamientos incorrectos, con los pasos para reproducirlos.'),
        ('Comentarios del usuario',
         'Observaciones espontáneas, incluidas las favorables, que indican qué '
         'conviene conservar.'),
        ('Acciones derivadas',
         'Corrección, ajuste de la capacitación o decisión de no cambiar nada, '
         'con la justificación.'),
    ]:
        filas.append([c, q])
    a = tabla(filas, 223,
              'Ficha de registro de las sesiones de prueba de implementación', a,
              anchos=[Emu(int(1.9 * P)), Emu(int(4.4 * P))])

    a = F.titulo(doc, '4.3.6 Hallazgos derivados del uso y correcciones '
                      'aplicadas', 3, a)
    a = F.parrafo(
        doc,
        'Los hallazgos que se presentan a continuación provienen del uso del '
        'sistema sobre las pantallas construidas y no de la verificación '
        'automatizada, que los daba todos por correctos. Esa es precisamente la '
        'razón de documentarlos: ninguno de los siete habría aparecido en una '
        'prueba de código, porque en seis de ellos el sistema hacía exactamente '
        'lo que el programador le había indicado y el problema estaba en lo que '
        'el programador había indicado. Cada corrección se acompañó de una '
        'verificación automatizada nueva, de modo que el defecto no pueda '
        'reaparecer sin que el conjunto de pruebas lo señale. La Tabla 224 los '
        'relaciona.', a)

    filas = [['Hallazgo', 'Efecto para el usuario', 'Corrección aplicada',
              'Verificación agregada']]
    for h, e, c, v in [
        ('Comentarios del código visibles en la pantalla del calendario.',
         'Sobre el encabezado del calendario aparecía un párrafo con texto '
         'destinado al programador, que el usuario leía como si fuera parte del '
         'sistema.',
         'La sintaxis de comentario empleada solo es válida en una línea; al '
         'ocupar varias, el motor de plantillas la trataba como texto. Se '
         'sustituyó por la etiqueta de comentario de bloque en las tres '
         'pantallas afectadas.',
         'Un recorrido por veintidós pantallas que falla si encuentra marcas de '
         'plantilla sin procesar en la respuesta.'),
        ('El resultado de la estimación no se leía en el calendario.',
         'El usuario veía los espacios recomendados resaltados en la rejilla, '
         'pero no la duración estimada ni su procedencia, que era la '
         'información que explicaba por qué esos espacios y no otros.',
         'La fila que contenía el resultado sumaba trece columnas de las doce '
         'disponibles, de modo que el resultado se comprimía en un tercio del '
         'ancho. Se rediseñó como una franja propia a todo lo ancho, con la '
         'cifra destacada.',
         'Comprobación de que la pantalla presenta la duración estimada, el '
         'bloque recomendado y la etiqueta de origen.'),
        ('Elegir primero el procedimiento y después el odontólogo descartaba '
         'el procedimiento.',
         'La estimación no aparecía nunca si el usuario llenaba los campos en '
         'ese orden, que es el orden natural: el paciente pide un '
         'procedimiento y luego se decide quién lo atiende.',
         'El selector de odontólogo pertenecía al formulario de filtro y el de '
         'procedimiento al de consulta, de modo que enviar uno perdía el otro. '
         'Se agregaron los campos ocultos que conservan la consulta en curso y '
         'el selector de odontólogo se trasladó al panel de recomendación.',
         'Comprobación de que la consulta responde con ambos campos enviados '
         'en cualquier orden.'),
        ('Mensaje de error con redacción incorrecta cuando hay una sola unidad '
         'dental activa.',
         'El sistema respondía «Las 1 unidades dentales están ocupadas», lo que '
         'resta credibilidad a un mensaje que el usuario debe tomar en serio.',
         'El mensaje distingue el caso de una unidad del de varias.',
         'Comprobación del texto del mensaje con una sola unidad activa en el '
         'catálogo.'),
        ('Un renglón del plan podía guardarse con precio cero.',
         'El formulario mostraba 0.00 como valor inicial del precio, de modo '
         'que un renglón guardado sin tocar ese campo quedaba presupuestado en '
         'cero y el total del plan resultaba inferior al real.',
         'El campo se presenta vacío y el formulario propone la tarifa del '
         'catálogo al elegir el procedimiento, con lo que el valor que se '
         'guarda es deliberado y no un valor predeterminado del modelo.',
         'Comprobación de que el renglón exige un precio y de que la tarifa '
         'propuesta corresponde a la del catálogo.'),
        ('El archivo del modelo se leía del disco en cada estimación.',
         'No era visible como defecto, pero cada consulta de recomendación '
         'deserializaba medio megabyte, de modo que el calendario respondía más '
         'lento conforme el modelo crecía.',
         'Se agregó una caché en memoria del módulo, que lee el archivo una vez '
         'por versión y lo descarta solo al activarse otra.',
         'Medición de que la primera estimación tras limpiar la caché es la más '
         'costosa y de que las siguientes se mantienen por debajo de cien '
         'milisegundos.'),
        ('El odontólogo encontraba al entrar la agenda de toda la clínica.',
         'El profesional veía las citas de ambos consultorios y tenía que '
         'filtrar su propia agenda en cada ingreso, que es lo único que '
         'necesita ver.',
         'El sistema reconoce al usuario vinculado a la ficha profesional y '
         'preselecciona su agenda, distinguiendo el primer ingreso de la '
         'elección explícita de ver la clínica completa.',
         'Comprobación de que el odontólogo recibe su agenda preseleccionada y '
         'de que puede elegir ver la de todos.'),
    ]:
        filas.append([h, e, c, v])
    a = tabla(filas, 224,
              'Hallazgos derivados del uso del sistema, correcciones aplicadas '
              'y verificaciones agregadas', a,
              anchos=[Emu(int(1.4 * P)), Emu(int(1.6 * P)), Emu(int(1.9 * P)),
                      Emu(int(1.4 * P))], etiqueta=None)

    a = F.parrafo(
        doc,
        'Los tres primeros hallazgos comparten un rasgo que conviene señalar. '
        'En los tres el sistema calculaba correctamente y el defecto estaba en '
        'la presentación: la estimación existía, los espacios recomendados se '
        'calculaban bien y la consulta funcionaba, pero el usuario no veía el '
        'resultado o no lograba llegar a él. Es la clase de defecto que la '
        'verificación automatizada no detecta, porque comprueba que el dato esté '
        'en la respuesta y no que esté legible en la pantalla, y es también la '
        'que justifica que las pruebas de implementación no puedan sustituirse '
        'por pruebas de código.', a)
    a = F.parrafo(
        doc,
        'El sexto hallazgo es de naturaleza distinta y vale la pena distinguirlo. '
        'No lo reportó ningún usuario ni lo habría reportado, porque su efecto '
        '—unas décimas de segundo en cada consulta— se percibe como lentitud '
        'general y no como un defecto concreto. Apareció al medir el tiempo de '
        'respuesta de la recomendación, lo que confirma que la observación del '
        'uso debe complementarse con la medición: hay defectos que el usuario '
        'sufre sin poder nombrarlos.', a)

    a = F.titulo(doc, '4.3.7 Resultado y tareas pendientes', 3, a)
    a = F.parrafo(
        doc,
        'El sistema completa los tres procesos del alcance sobre el entorno de '
        'producción, con los usuarios de cada rol y con dos meses de datos de '
        'operación cargados: la programación de una cita con la duración '
        'estimada, el registro de la atención con los tiempos reales y la '
        'documentación de la visita en el expediente. Las 299 verificaciones '
        'automatizadas se cumplen y los siete defectos derivados del uso fueron '
        'corregidos, cada uno con su verificación añadida al conjunto.', a)
    a = F.parrafo(
        doc,
        'Quedan pendientes tres tareas antes de considerar concluida la '
        'implantación, que se enuncian para que el alcance de lo verificado no '
        'se confunda con el de lo definitivo. La primera es la habilitación de '
        'HTTPS con un certificado y la activación de las marcas de seguridad '
        'correspondientes, condición para operar con datos de pacientes reales. '
        'La segunda es la configuración del respaldo periódico de la base de '
        'datos. La tercera es la sustitución de los datos de demostración por el '
        'historial real de la clínica, momento en que el modelo deberá '
        'reentrenarse sobre ese historial y en que las métricas reportadas en la '
        'Tabla 213 habrán de recalcularse: las cifras de este capítulo '
        'corresponden al conjunto de 446 atenciones con que se construyó y '
        'validó el sistema.', a)

    doc.save(str(C.ARCHIVO))
    print('4.3 agregada.')


if __name__ == '__main__':
    main()
