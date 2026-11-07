"""Catálogo de requerimientos funcionales de SmileeSync, clasificado por módulo.

Cada requerimiento sigue la estructura del DERCAS Visión: identificador,
clasificación o prioridad, nombre, referencia y el desglose numerado de las
funcionalidades que comprende.

La prioridad se asigna con un criterio explícito:

    Alta    El sistema no puede operar sin ella. Comprende la autenticación,
            el control de acceso y todo lo que sostiene el ciclo de la cita,
            que es el objeto del proyecto.
    Media   Aporta valor operativo comprobable, pero la clínica puede seguir
            atendiendo si se difiere.
    Baja    Mejora la gestión sin condicionar la operación diaria.
"""

MODULOS = [
    ('SEG', 'Seguridad y Usuarios',
     'Resuelve la identificación de quien usa el sistema y el alcance de lo que '
     'cada perfil puede consultar y modificar.'),
    ('PAC', 'Pacientes',
     'Centraliza la información de las personas atendidas, que hasta ahora se '
     'encontraba dispersa entre la agenda en papel y las fichas individuales.'),
    ('CAT', 'Catálogo Odontológico',
     'Administra los elementos que la clínica declara una vez y reutiliza en '
     'cada cita: especialidades, procedimientos, profesionales y sillones.'),
    ('AGE', 'Agenda y Citas',
     'Es el módulo principal del sistema. Concentra la programación, la '
     'consulta y el cierre de las citas, así como la disponibilidad real de '
     'cada profesional.'),
    ('EXP', 'Expediente Clínico',
     'Registra qué se le hace al paciente y cómo evoluciona, y traduce el '
     'diagnóstico en un plan de tratamiento presupuestado en tiempo y en '
     'dinero.'),
    ('COB', 'Cobros',
     'Controla lo acordado con el paciente y lo efectivamente abonado, de modo '
     'que el saldo de cada tratamiento sea consultable sin revisar expedientes '
     'uno por uno.'),
    ('INT', 'Inteligencia',
     'Contiene el componente predictivo: estima la duración de cada '
     'procedimiento y recomienda el bloque de tiempo que conviene reservar.'),
    ('REP', 'Reportes e Indicadores',
     'Expone las cifras con que la clínica puede evaluar su operación y la '
     'precisión del modelo.'),
]

# (id, nombre, prioridad, referencia, [funcionalidades])
REQUERIMIENTOS = [
    # ─────────────────────────── Seguridad y Usuarios ───────────────────────────
    ('REQ-SEG-01', 'Inicio de sesión', 'Alta', 'Caso de uso UC01', [
        'Permitir el acceso únicamente a los usuarios registrados y activos.',
        'Solicitar el correo electrónico como identificador de la cuenta.',
        'Solicitar la contraseña, que se almacena cifrada y nunca en texto claro.',
        'Verificar el correo, la contraseña y el estado del usuario contra la base de datos.',
        'Mostrar un mensaje genérico ante credenciales inválidas, sin revelar si el '
        'error estuvo en el correo o en la contraseña.',
        'Crear la sesión y dirigir al usuario al módulo Principal.',
        'Cerrar la sesión a solicitud del usuario e impedir que el navegador '
        'recupere las pantallas desde la caché.',
    ]),
    ('REQ-SEG-02', 'Mantenimiento de usuarios', 'Alta', 'Caso de uso UC03', [
        'Registrar usuarios con nombres, apellidos, correo electrónico, teléfono y rol.',
        'Validar que el correo electrónico no esté asignado a otro usuario.',
        'Exigir que la contraseña cumpla las reglas de longitud y complejidad.',
        'Permitir la edición de los datos de un usuario existente.',
        'Aplicar borrado lógico: el usuario dado de baja deja de acceder al sistema '
        'pero conserva su vínculo con los registros que generó.',
        'Registrar la pregunta y la respuesta secretas, esta última cifrada.',
    ]),
    ('REQ-SEG-03', 'Control de acceso por rol', 'Alta', 'Caso de uso UC04', [
        'Administrar los roles del sistema y los módulos habilitados para cada uno.',
        'Distinguir entre el acceso de consulta y el de escritura mediante un '
        'indicador de solo consulta.',
        'Habilitar por separado la escritura del expediente clínico, que corresponde '
        'al personal con competencia profesional y no a quien tiene más privilegios '
        'administrativos.',
        'Mostrar en el menú lateral únicamente los módulos habilitados para el rol.',
        'Ocultar las acciones de modificación a los roles de consulta.',
        'Denegar el acceso directo por dirección web a una vista no autorizada, con '
        'independencia de lo que muestre la interfaz.',
    ]),
    ('REQ-SEG-04', 'Historial de auditoría', 'Media', 'Tablas de histórico', [
        'Registrar una copia del estado previo antes de cada actualización, '
        'desactivación o activación.',
        'Conservar en el histórico el identificador, el nombre, la acción, el '
        'responsable y la fecha.',
        'Referenciar el registro auditado por identificador entero, sin llave foránea, '
        'de modo que el histórico sobreviva al registro que describe.',
        'Permitir la consulta del historial desde la pantalla del módulo.',
    ]),
    ('REQ-SEG-05', 'Recuperación de contraseña', 'Media', 'Caso de uso UC02', [
        'Permitir el ingreso del correo electrónico registrado.',
        'Validar que el correo exista y corresponda a un usuario activo.',
        'Presentar la pregunta secreta asociada a la cuenta.',
        'Comparar la respuesta con el valor cifrado almacenado.',
        'Permitir el establecimiento de una contraseña nueva tras la verificación.',
        'Aplicar a la contraseña nueva las mismas reglas de seguridad del registro.',
    ]),

    # ──────────────────────────────── Pacientes ────────────────────────────────
    ('REQ-PAC-01', 'Mantenimiento de pacientes', 'Alta', 'Caso de uso UC06', [
        'Registrar pacientes con código único, nombres, apellidos, fecha de '
        'nacimiento, sexo, teléfono, correo y dirección.',
        'Validar que el código del paciente no esté asignado a otro registro.',
        'Permitir la búsqueda por código, nombre, apellido o teléfono.',
        'Permitir la edición de los datos del paciente.',
        'Aplicar borrado lógico, conservando el historial de citas del paciente.',
        'Registrar cada operación en el historial de auditoría del módulo.',
    ]),
    ('REQ-PAC-02', 'Antecedentes médicos', 'Media', 'Caso de uso UC08', [
        'Registrar los antecedentes médicos relevantes del paciente, indicando tipo '
        'y descripción.',
        'Presentar los antecedentes vigentes en la ficha clínica del paciente.',
        'Permitir retirar un antecedente mediante borrado lógico.',
        'Mostrar los antecedentes al consultar el expediente, de modo que estén a la '
        'vista antes de cualquier procedimiento.',
    ]),

    # ─────────────────────────── Catálogo Odontológico ───────────────────────────
    ('REQ-CAT-01', 'Administración de especialidades', 'Media', 'Caso de uso UC10', [
        'Registrar las especialidades odontológicas con nombre y descripción.',
        'Validar que el nombre de la especialidad no se repita.',
        'Permitir la edición y el borrado lógico de cada especialidad.',
        'Impedir la eliminación física de una especialidad vinculada a procedimientos '
        'o profesionales.',
    ]),
    ('REQ-CAT-02', 'Administración de procedimientos', 'Alta', 'Caso de uso UC09', [
        'Registrar procedimientos con código único, nombre, especialidad, nivel de '
        'complejidad y duración promedio de referencia.',
        'Registrar el precio de lista con que se presupuestan los planes de tratamiento.',
        'Validar que la duración declarada esté dentro de un rango admisible.',
        'Permitir la edición y el borrado lógico del procedimiento.',
        'Ofrecer únicamente los procedimientos activos al programar una cita.',
    ]),
    ('REQ-CAT-03', 'Administración de odontólogos', 'Alta', 'Caso de uso UC11', [
        'Registrar odontólogos con nombres, apellidos, número de colegiado, '
        'especialidad y teléfono.',
        'Validar que el número de colegiado no esté asignado a otro profesional.',
        'Permitir vincular al odontólogo con una cuenta de usuario del sistema.',
        'Advertir en el listado cuando un profesional no tiene horarios configurados, '
        'pues en ese estado el sistema rechaza todas sus citas.',
        'Permitir la edición y el borrado lógico del profesional.',
    ]),
    ('REQ-CAT-04', 'Administración de unidades dentales', 'Alta', 'Caso de uso UC22', [
        'Registrar las unidades dentales o sillones con código único, nombre y ubicación.',
        'Administrar las unidades como registros del catálogo, de modo que incorporar '
        'un sillón adicional amplíe la capacidad de la clínica sin modificar el sistema.',
        'Permitir dar de baja una unidad mediante borrado lógico, conservando su '
        'vínculo con las citas históricas.',
        'Derivar de las unidades activas la capacidad máxima de atención simultánea.',
    ]),

    # ──────────────────────────────── Agenda y Citas ────────────────────────────────
    ('REQ-AGE-01', 'Horarios de disponibilidad', 'Alta', 'Caso de uso UC16', [
        'Definir las franjas de atención de cada odontólogo por día de la semana.',
        'Permitir replicar una misma franja de lunes a viernes en una sola operación.',
        'Validar que la hora de finalización sea posterior a la de inicio.',
        'Impedir el registro de franjas que se traslapen entre sí.',
        'Permitir retirar una franja mediante borrado lógico, advirtiendo cuántas '
        'citas futuras quedan dentro de ella.',
        'Totalizar las horas semanales declaradas por cada profesional.',
    ]),
    ('REQ-AGE-02', 'Ausencias puntuales', 'Media', 'Caso de uso UC23', [
        'Registrar la ausencia de un odontólogo en una fecha concreta, por toda la '
        'jornada o por un rango de horas.',
        'Permitir que el propio odontólogo registre sus ausencias, aunque su rol sea '
        'de consulta para el resto de la agenda.',
        'Impedir que un profesional registre o retire ausencias de otro.',
        'Calcular la disponibilidad efectiva como el patrón semanal menos las '
        'ausencias de esa fecha.',
        'Advertir cuántas citas ya programadas caen dentro de la ausencia, sin '
        'cancelarlas automáticamente.',
    ]),
    ('REQ-AGE-03', 'Programación de citas', 'Alta', 'Caso de uso UC12', [
        'Registrar citas asociando paciente, odontólogo, procedimiento, fecha, hora '
        'de inicio y duración asignada.',
        'Impedir el registro de citas en fechas anteriores al día en curso.',
        'Validar que la cita completa quepa dentro de una franja de disponibilidad '
        'efectiva del odontólogo.',
        'Impedir el traslape con otra cita vigente del mismo profesional.',
        'Verificar que exista una unidad dental libre en el intervalo solicitado y '
        'asignar la primera disponible de forma automática.',
        'Calcular la hora de finalización a partir de la duración asignada.',
        'Aplicar las mismas validaciones con independencia de la pantalla desde la '
        'cual se origine la cita.',
    ]),
    ('REQ-AGE-04', 'Reprogramación y cancelación', 'Alta', 'Caso de uso UC14', [
        'Permitir modificar la fecha, la hora o la duración de una cita vigente.',
        'Aplicar a la reprogramación las mismas validaciones del registro inicial.',
        'Marcar la cita reprogramada con un estado que la distinga de la original.',
        'Permitir la cancelación registrando el motivo.',
        'Conservar la cita cancelada mediante borrado lógico, de modo que siga '
        'disponible para el análisis posterior.',
        'Liberar la unidad dental y el espacio en la agenda al cancelar.',
    ]),
    ('REQ-AGE-05', 'Registro de tiempos reales', 'Alta', 'Caso de uso UC15', [
        'Registrar la hora de inicio real y la hora de finalización real de la atención.',
        'Validar que la hora de finalización sea posterior a la de inicio.',
        'Calcular la duración real en minutos y marcar la cita como atendida.',
        'Presentar la desviación entre la duración asignada y la real.',
        'Incorporar la atención al conjunto de entrenamiento del modelo predictivo.',
        'Cerrar el renglón del plan de tratamiento que la cita atiende, si procede.',
    ]),
    ('REQ-AGE-06', 'Calendario operativo', 'Alta', 'Caso de uso UC13', [
        'Presentar las citas en una rejilla por semana o por día, con navegación '
        'entre períodos y retorno al día en curso.',
        'Distinguir por color el estado de cada cita.',
        'Preseleccionar la agenda propia cuando el usuario está vinculado a una ficha '
        'de odontólogo, permitiéndole consultar la de toda la clínica.',
        'Permitir abrir el detalle de una cita desde la rejilla.',
        'Permitir programar una cita pulsando una casilla libre, con la fecha y la '
        'hora precargadas.',
        'Presentar los indicadores de citas del día, utilización de la agenda, '
        'pacientes activos y error medio del modelo.',
    ]),

    # ───────────────────────────── Expediente Clínico ─────────────────────────────
    ('REQ-EXP-01', 'Odontograma', 'Alta', 'Caso de uso UC25', [
        'Presentar la arcada completa de treinta y dos piezas permanentes en '
        'nomenclatura FDI, agrupadas por cuadrante.',
        'Registrar hallazgos por pieza y por cara, indicando tipo, fecha y observación.',
        'Agregar cada hallazgo sin modificar los anteriores, de modo que la pieza '
        'conserve su historia y el odontograma muestre el registro vigente.',
        'Validar que la pieza pertenezca a la nomenclatura y que la fecha no sea futura.',
        'Impedir que un hallazgo que describe la pieza completa se registre sobre una '
        'sola cara.',
        'Permitir retirar un hallazgo mal capturado, con lo que vuelve a regir el '
        'registro previo.',
        'Resumir el número de piezas registradas, tratadas, ausentes y con hallazgos '
        'por atender.',
    ]),
    ('REQ-EXP-02', 'Notas clínicas de evolución', 'Alta', 'Caso de uso UC26', [
        'Registrar por visita el motivo, los hallazgos clínicos, el procedimiento '
        'realizado, los materiales y las indicaciones al paciente.',
        'Vincular la nota a la cita atendida que la origina, admitiendo una sola nota '
        'por cita.',
        'Registrar el número de piezas tratadas, el uso de anestesia y la aparición de '
        'complicaciones, que son las variables que explican la variabilidad de la '
        'duración.',
        'Validar que las piezas enumeradas coincidan con el número declarado.',
        'Exigir la descripción de la complicación cuando se marca que la hubo.',
        'Presentar la evolución del paciente en orden cronológico.',
    ]),
    ('REQ-EXP-03', 'Plan de tratamiento', 'Alta', 'Caso de uso UC27', [
        'Registrar el plan con su diagnóstico, el odontólogo responsable y la fecha '
        'de elaboración.',
        'Desglosar el plan en renglones con fase, procedimiento, pieza, número de '
        'piezas y precio unitario.',
        'Proponer el precio de lista del catálogo y permitir ajustarlo, conservando en '
        'el renglón la tarifa con que se presupuestó.',
        'Obtener del componente predictivo la duración estimada de cada renglón y '
        'registrar el origen de esa estimación.',
        'Administrar el estado del plan: borrador, aprobado, en curso, finalizado o '
        'rechazado.',
        'Exigir al menos un renglón antes de aprobar el plan.',
        'Actualizar el avance del plan conforme se completan sus renglones.',
    ]),
    ('REQ-EXP-04', 'Planificación del tratamiento en sesiones', 'Media',
     'Caso de uso UC29', [
        'Repartir los renglones pendientes en sesiones de sillón, respetando el orden '
        'de las fases.',
        'Limitar cada sesión a un máximo de ciento veinte minutos de sillón.',
        'Totalizar los minutos estimados del plan y los que quedan pendientes.',
        'Permitir agendar un renglón enviando al formulario de cita el paciente, el '
        'odontólogo, el procedimiento y la duración estimada al presupuestar.',
        'Vincular la cita creada con el renglón y marcarlo como agendado.',
        'Impedir el agendado de renglones de un plan que no esté vigente.',
    ]),

    # ────────────────────────────────── Cobros ──────────────────────────────────
    ('REQ-COB-01', 'Presupuesto del tratamiento', 'Media', 'Caso de uso UC30', [
        'Calcular el subtotal del plan como la suma de los importes de sus renglones.',
        'Aplicar el descuento acordado y obtener el total.',
        'Excluir del cálculo los renglones anulados.',
        'Presentar el presupuesto junto con las sesiones estimadas, de modo que el '
        'paciente conozca el costo y el número de visitas antes de aceptar.',
    ]),
    ('REQ-COB-02', 'Registro de abonos', 'Media', 'Caso de uso UC31', [
        'Registrar abonos con fecha, monto, forma de pago, referencia y observaciones.',
        'Validar que el monto sea mayor que cero y no exceda el saldo pendiente.',
        'Impedir el registro de abonos con fecha posterior al día en curso.',
        'Recalcular el saldo del plan con cada abono.',
        'Permitir la anulación lógica de un abono mal registrado, conservando su traza '
        'en el estado de cuenta.',
        'Restringir el registro y la anulación de abonos al personal con competencia '
        'de cobro.',
    ]),
    ('REQ-COB-03', 'Estado de cuenta', 'Media', 'Caso de uso UC30', [
        'Listar los planes vigentes ordenados por saldo pendiente.',
        'Presentar para cada plan el total presupuestado, lo abonado y el saldo.',
        'Totalizar el monto por cobrar y el cobrado en el mes en curso.',
        'Permitir filtrar entre los planes con saldo y la totalidad de los vigentes.',
        'Advertir cuando un plan se cierra conservando saldo por cobrar.',
    ]),

    # ──────────────────────────────── Inteligencia ────────────────────────────────
    ('REQ-INT-01', 'Estimación de duración', 'Alta', 'Caso de uso UC17', [
        'Estimar la duración de un procedimiento a partir del procedimiento, el '
        'odontólogo, el día, la hora y el número de piezas.',
        'Aplicar una cadena de respaldo de tres niveles: modelo entrenado, promedio '
        'histórico de atenciones reales y, en última instancia, duración de referencia '
        'del catálogo.',
        'Exigir un mínimo de tres atenciones registradas para considerar fiable el '
        'promedio histórico.',
        'Preferir el promedio del propio odontólogo cuando dispone de registros '
        'suficientes, pues el ritmo de trabajo varía entre profesionales.',
        'Declarar en la interfaz el origen de cada estimación.',
        'Continuar operando si el modelo no está disponible, sin impedir el agendado.',
    ]),
    ('REQ-INT-02', 'Recomendación de bloques de tiempo', 'Alta', 'Caso de uso UC18', [
        'Calcular un bloque mínimo y un bloque máximo recomendados alrededor de la '
        'duración estimada.',
        'Identificar sobre el calendario los espacios donde el procedimiento consultado '
        'cabe completo.',
        'Descartar los espacios que ya pasaron, los que se traslapan con una cita '
        'vigente y aquellos en que no queda una unidad dental libre.',
        'Informar cuántos espacios disponibles existen en el período mostrado.',
        'Permitir programar la cita directamente desde un espacio sugerido.',
    ]),
    ('REQ-INT-03', 'Administración de versiones del modelo', 'Media',
     'Caso de uso UC19', [
        'Registrar cada modelo entrenado con su algoritmo, su fecha de entrenamiento y '
        'la ruta del archivo serializado.',
        'Almacenar las métricas de error absoluto medio, raíz del error cuadrático '
        'medio y coeficiente de determinación.',
        'Mantener una sola versión activa en producción.',
        'Conservar las versiones anteriores para efectos comparativos.',
        'Registrar cada predicción generada junto con la cita a la que corresponde, '
        'de modo que pueda contrastarse después con la duración real.',
    ]),

    # ────────────────────────── Reportes e Indicadores ──────────────────────────
    ('REQ-REP-01', 'Indicadores operativos', 'Media', 'Caso de uso UC20', [
        'Calcular el número de citas atendidas por período.',
        'Calcular el porcentaje de utilización de la agenda, tomando como capacidad el '
        'menor valor entre los odontólogos disponibles y las unidades dentales activas.',
        'Calcular la desviación media entre la duración asignada y la real.',
        'Presentar los indicadores en la pantalla principal del sistema.',
    ]),
    ('REQ-REP-02', 'Reporte de utilización', 'Baja', 'Caso de uso UC21', [
        'Generar el detalle de utilización por odontólogo y por período.',
        'Presentar los procedimientos más frecuentes de la clínica.',
        'Comparar la precisión del modelo contra la duración de referencia del catálogo.',
        'Permitir la exportación del reporte para su consulta fuera del sistema.',
    ]),
]


def por_modulo():
    """Agrupa los requerimientos por el prefijo de módulo de su identificador."""
    grupos = []
    for prefijo, nombre, descripcion in MODULOS:
        propios = [r for r in REQUERIMIENTOS if r[0].split('-')[1] == prefijo]
        grupos.append((prefijo, nombre, descripcion, propios))
    return grupos


if __name__ == '__main__':
    total = 0
    for prefijo, nombre, _, propios in por_modulo():
        prioridades = {}
        for r in propios:
            prioridades[r[2]] = prioridades.get(r[2], 0) + 1
        detalle = ', '.join(f'{v} {k.lower()}' for k, v in sorted(prioridades.items()))
        print(f'{nombre:30} {len(propios):2} requerimientos  ({detalle})')
        total += len(propios)
    print(f'{"TOTAL":30} {total:2} requerimientos, '
          f'{sum(len(r[4]) for r in REQUERIMIENTOS)} funcionalidades')
