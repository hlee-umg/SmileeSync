"""Genera los diagramas de actividad UML de cada proceso de SmileeSync."""
import pathlib

ESTILO = """skinparam shadowing false
skinparam backgroundColor white
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam ArrowColor #334155
skinparam ActivityBackgroundColor #EEF2FF
skinparam ActivityBorderColor #4F46E5
skinparam ActivityFontColor #1E1B4B
skinparam ActivityDiamondBackgroundColor #FEF3C7
skinparam ActivityDiamondBorderColor #D97706
skinparam ActivityDiamondFontColor #78350F
skinparam ActivityStartColor #1F3A5F
skinparam ActivityEndColor #991B1B
skinparam NoteBackgroundColor #FFFBEB
skinparam NoteBorderColor #D97706
skinparam swimlaneBorderColor #94A3B8
skinparam swimlaneTitleBackgroundColor #F1F5F9
skinparam swimlaneTitleFontColor #0F172A
skinparam swimlaneTitleFontStyle bold
skinparam dpi 160
"""


def restaurar_calles(cuerpo):
    """Devuelve la calle activa al cerrar cada bifurcación o ciclo.

    PlantUML conserva la última calle declarada, de modo que una rama de
    corrección que ocurre en la calle del usuario dejaría las actividades
    siguientes —que son del sistema— dibujadas en la calle equivocada. Aquí se
    recuerda la calle vigente antes de abrir el bloque y se vuelve a declarar
    al cerrarlo.
    """
    import re
    calle = re.compile(r'^\s*\|([^|]+)\|\s*$')
    abre = re.compile(r'^\s*(if|while|repeat)\b')
    cierra = re.compile(r'^\s*(endif|endwhile|repeat while)\b')

    salida, pila, actual = [], [], None
    for linea in cuerpo.split('\n'):
        m = calle.match(linea)
        if m:
            actual = m.group(1)
            salida.append(linea)
            continue
        if cierra.match(linea):
            previa = pila.pop() if pila else None
            salida.append(linea)
            if previa and previa != actual:
                salida.append(f'|{previa}|')
                actual = previa
            continue
        if abre.match(linea):
            pila.append(actual)
        salida.append(linea)
    return '\n'.join(salida)


PROCESOS = {}

# ───────────────────────── Seguridad y Usuarios ─────────────────────────
PROCESOS['act_01_login'] = ("Proceso de inicio de sesión y control de acceso", """
|Usuario|
start
:Solicitar la pantalla de acceso;
:Ingresar correo electrónico
y contraseña;
|Sistema|
:Buscar el usuario por correo;
if (¿El correo existe?) then (no)
  |Usuario|
  :Visualizar el mensaje
  de credenciales inválidas;
  stop
else (sí)
endif
:Verificar la contraseña cifrada;
if (¿La contraseña coincide?) then (no)
  |Usuario|
  :Visualizar el mensaje
  de credenciales inválidas;
  stop
else (sí)
endif
if (¿El usuario está activo?) then (no)
  |Usuario|
  :Visualizar el aviso de
  cuenta desactivada;
  stop
else (sí)
endif
:Crear la sesión del usuario;
:Leer el rol asignado
y sus módulos habilitados;
:Determinar si el rol es
de solo consulta;
:Construir el menú lateral
según los permisos;
|Usuario|
:Visualizar el módulo Principal
con las opciones permitidas;
stop
""")

PROCESOS['act_02_usuarios'] = ("Proceso de mantenimiento de usuarios", """
|Administrador|
start
:Abrir el módulo de usuarios;
:Seleccionar la opción
de nuevo usuario;
:Capturar nombres, apellidos,
correo, teléfono y rol;
:Definir la pregunta secreta
y su respuesta;
|Sistema|
:Validar el formato
de los datos capturados;
if (¿El correo ya está registrado?) then (sí)
  |Administrador|
  :Corregir el correo electrónico;
  detach
else (no)
endif
if (¿La contraseña cumple
las reglas de seguridad?) then (no)
  |Administrador|
  :Corregir la contraseña;
  detach
else (sí)
endif
:Cifrar la contraseña
y la respuesta secreta;
:Guardar el usuario
con estado activo;
:Registrar la creación
en el historial de auditoría;
|Administrador|
:Visualizar la confirmación
del registro;
stop
""")

PROCESOS['act_03_recuperar'] = ("Proceso de recuperación de contraseña", """
|Usuario|
start
:Seleccionar la opción
de contraseña olvidada;
:Ingresar el correo electrónico;
|Sistema|
if (¿El correo está registrado
y activo?) then (no)
  |Usuario|
  :Visualizar el mensaje
  de correo no encontrado;
  stop
else (sí)
endif
:Recuperar la pregunta secreta
del usuario;
|Usuario|
:Responder la pregunta secreta;
|Sistema|
:Comparar la respuesta
con el valor cifrado;
if (¿La respuesta es correcta?) then (no)
  |Usuario|
  :Visualizar el mensaje
  de respuesta incorrecta;
  stop
else (sí)
endif
|Usuario|
:Capturar la contraseña nueva
y su confirmación;
|Sistema|
if (¿Las contraseñas coinciden
y cumplen las reglas?) then (no)
  |Usuario|
  :Corregir la contraseña;
  detach
else (sí)
endif
:Cifrar y actualizar
la contraseña;
:Registrar el cambio
en el historial;
|Usuario|
:Iniciar sesión con
la contraseña nueva;
stop
""")

# ──────────────────────────────── Pacientes ────────────────────────────────
PROCESOS['act_04_paciente'] = ("Proceso de registro de paciente y antecedentes médicos", """
|Recepcionista|
start
:Abrir el módulo de pacientes;
:Buscar al paciente
por código o nombre;
if (¿El paciente ya existe?) then (sí)
  :Abrir la ficha clínica
  existente;
  detach
else (no)
endif
:Capturar código, nombres,
apellidos, fecha de nacimiento,
sexo, teléfono y dirección;
|Sistema|
:Validar el formato
de los datos capturados;
if (¿El código ya está asignado?) then (sí)
  |Recepcionista|
  :Corregir el código
  del paciente;
  detach
else (no)
endif
:Guardar al paciente
con estado activo;
:Registrar la creación
en el historial de auditoría;
|Recepcionista|
:Abrir la ficha clínica
del paciente;
while (¿Registrar un antecedente médico?) is (sí)
  :Capturar el tipo
  y la descripción;
  |Sistema|
  :Asociar el antecedente
  a la ficha del paciente;
  |Recepcionista|
endwhile (no)
:Visualizar la ficha
clínica completa;
stop
""")

# ──────────────────────────────── Catálogo ────────────────────────────────
PROCESOS['act_05_catalogo'] = ("Proceso de mantenimiento del catálogo odontológico", """
|Administrador|
start
:Abrir el módulo de catálogos;
:Seleccionar la entidad a administrar
(especialidad, procedimiento,
odontólogo o unidad dental);
if (¿Qué operación se requiere?) then (alta)
  :Capturar los datos
  de la entidad;
  |Sistema|
  :Validar el código único
  y los campos obligatorios;
  if (¿Los datos son válidos?) then (no)
    |Administrador|
    :Corregir los datos;
    detach
  else (sí)
  endif
  :Guardar el registro
  con estado activo;
elseif (modificación) then
  |Administrador|
  :Seleccionar el registro
  y editar sus datos;
  |Sistema|
  :Validar que el código
  no duplique otro registro;
  :Actualizar el registro;
else (baja)
  |Administrador|
  :Seleccionar el registro
  a dar de baja;
  |Sistema|
  :Cambiar el estado a inactivo
  sin eliminar el registro;
  note right
    Borrado lógico: el registro
    deja de ofrecerse al programar,
    pero conserva su vínculo con
    las citas históricas.
  end note
endif
|Administrador|
:Visualizar el catálogo
actualizado;
stop
""")

PROCESOS['act_06_horarios'] = ("Proceso de configuración de horarios y ausencias", """
|Odontólogo|
start
:Abrir su ficha
de disponibilidad;
if (¿Qué se va a registrar?) then (horario semanal)
  :Seleccionar el día,
  la hora de inicio
  y la hora de fin;
  :Indicar si la franja
  se replica de lunes a viernes;
  |Sistema|
  :Verificar que la hora de fin
  sea posterior a la de inicio;
  if (¿Se traslapa con otra
  franja del mismo día?) then (sí)
    |Odontólogo|
    :Corregir el rango horario;
    detach
  else (no)
  endif
  :Crear la franja en el día
  elegido o en los cinco días;
else (ausencia puntual)
  |Odontólogo|
  :Seleccionar la fecha
  de la ausencia;
  :Indicar si cubre toda la jornada
  o solo un rango de horas;
  :Registrar el motivo;
  |Sistema|
  :Guardar la ausencia
  como excepción a la fecha;
  :Contar las citas ya programadas
  dentro de la ausencia;
  if (¿Hay citas afectadas?) then (sí)
    |Odontólogo|
    :Visualizar el aviso para
    reprogramarlas;
    note right
      La ausencia no cancela
      las citas existentes.
    end note
  else (no)
  endif
endif
|Sistema|
:Recalcular la disponibilidad
efectiva del odontólogo;
|Odontólogo|
:Visualizar su semana
de atención actualizada;
stop
""")

# ───────────────────── Agenda y Citas (módulo Principal) ─────────────────────
PROCESOS['act_07_agendar'] = ("Proceso de programación de cita con estimación predictiva", """
|Recepcionista|
start
:Abrir el formulario
de nueva cita;
:Seleccionar paciente, odontólogo,
procedimiento y número de piezas;
:Indicar la fecha
y la hora de inicio;
|Sistema|
:Solicitar la estimación
de duración al componente predictivo;
|Componente predictivo|
if (¿Existe un modelo entrenado
y activo?) then (sí)
  :Predecir la duración
  con el modelo;
elseif (¿Hay al menos tres
atenciones previas?) then (sí)
  :Promediar la duración real
  de las atenciones históricas;
else (no)
  :Tomar la duración
  de referencia del catálogo;
endif
:Calcular el bloque recomendado
y devolver el origen
de la estimación;
|Recepcionista|
:Visualizar la duración estimada
y confirmar o ajustar
la duración asignada;
:Enviar el formulario;
|Sistema|
if (¿La fecha es anterior a hoy?) then (sí)
  |Recepcionista|
  :Corregir la fecha;
  detach
else (no)
endif
:Calcular la disponibilidad efectiva
(patrón semanal menos ausencias);
if (¿La cita cabe completa
dentro de una franja?) then (no)
  |Recepcionista|
  :Visualizar las franjas en que
  sí atiende ese día;
  detach
else (sí)
endif
if (¿Se traslapa con otra cita
del mismo odontólogo?) then (sí)
  |Recepcionista|
  :Visualizar la cita
  con la que choca;
  detach
else (no)
endif
:Buscar una unidad dental libre
en ese intervalo;
if (¿Hay una unidad disponible?) then (no)
  |Recepcionista|
  :Visualizar que las unidades
  están ocupadas;
  detach
else (sí)
endif
:Asignar la primera unidad libre;
:Calcular la hora de finalización;
:Guardar la cita
con estado programada;
:Registrar la predicción
asociada a la cita;
:Registrar la creación
en el historial de la agenda;
|Recepcionista|
:Visualizar la cita
en el calendario;
stop
""")

PROCESOS['act_08_recomendacion'] = ("Proceso de recomendación de bloques de tiempo", """
|Recepcionista|
start
:Abrir el módulo Principal;
:Seleccionar el odontólogo
y el procedimiento a consultar;
:Indicar el número de piezas;
|Sistema|
:Estimar la duración
del procedimiento;
:Determinar el período visible
(semana o día);
repeat
:Tomar la siguiente fecha del período
y calcular las franjas efectivas
del odontólogo;
:Avanzar al siguiente inicio candidato
en pasos de quince minutos;
    if (¿La cita completa cabe
    dentro de la franja?) then (no)
      :Descartar el candidato;
    elseif (¿El horario ya pasó?) then (sí)
      :Descartar el candidato;
    elseif (¿Se traslapa con una
    cita vigente?) then (sí)
      :Descartar el candidato;
    elseif (¿Queda una unidad
    dental libre?) then (no)
      :Descartar el candidato;
    else (no)
      :Marcar el espacio
      como disponible;
    endif
repeat while (¿Quedan candidatos
en el período?) is (sí)
:Contar los espacios encontrados;
|Recepcionista|
:Visualizar la duración estimada,
el bloque recomendado y los
espacios marcados en el calendario;
:Seleccionar un espacio sugerido;
|Sistema|
:Abrir el formulario de cita
con la fecha, la hora y el
procedimiento precargados;
stop
""")

PROCESOS['act_09_atencion'] = ("Proceso de registro de la atención y realimentación del modelo", """
|Recepcionista|
start
:Abrir el detalle de la cita
desde el calendario;
if (¿La cita está vigente?) then (no)
  :Visualizar que la cita
  no admite cambios;
  stop
else (sí)
endif
:Seleccionar la opción
de registrar la atención;
:Capturar la hora real
de inicio y de finalización;
|Sistema|
if (¿La hora de fin es posterior
a la de inicio?) then (no)
  |Recepcionista|
  :Corregir las horas;
  detach
else (sí)
endif
:Calcular la duración real
en minutos;
:Cambiar el estado de la cita
a atendida;
:Registrar la atención
en el historial de la agenda;
|Componente predictivo|
:Incorporar la cita al conjunto
de entrenamiento con su
procedimiento, odontólogo, día,
hora y duración real;
|Sistema|
if (¿La cita atiende un renglón
de un plan de tratamiento?) then (sí)
  :Marcar el renglón
  como completado;
  :Recalcular el avance del plan;
  if (¿Se completaron todos
  los renglones?) then (sí)
    :Cerrar el plan
    como finalizado;
  else (no)
    :Mantener el plan
    en curso;
  endif
else (no)
endif
|Recepcionista|
:Visualizar la desviación entre
la duración estimada y la real;
|Odontólogo|
if (¿Tiene competencia para
registrar el expediente?) then (sí)
  :Redactar la nota clínica
  de la visita;
else (no)
endif
stop
""")

PROCESOS['act_10_reprogramar'] = ("Proceso de reprogramación y cancelación de citas", """
|Recepcionista|
start
:Abrir el detalle de la cita;
if (¿La cita está programada
o reprogramada?) then (no)
  :Visualizar que la cita
  ya está cerrada;
  stop
else (sí)
endif
if (¿Qué acción se requiere?) then (reprogramar)
  :Modificar la fecha,
  la hora o la duración;
  |Sistema|
  :Aplicar las mismas validaciones
  de horario, traslape y
  unidad dental;
  if (¿Las validaciones
  se cumplen?) then (no)
    |Recepcionista|
    :Corregir los datos;
    detach
  else (sí)
  endif
  :Guardar el estado anterior
  en el historial;
  :Actualizar la cita y marcarla
  como reprogramada;
  :Liberar la unidad anterior
  y asignar la que corresponda;
else (cancelar)
  |Recepcionista|
  :Confirmar la cancelación
  e indicar el motivo;
  |Sistema|
  :Guardar el estado anterior
  en el historial;
  :Cambiar el estado
  a cancelada;
  :Agregar el motivo
  a las observaciones;
  :Liberar la unidad dental
  y el espacio en la agenda;
  note right
    La cita no se elimina:
    conserva su registro para
    el análisis posterior.
  end note
endif
|Recepcionista|
:Visualizar el calendario
actualizado;
stop
""")

# ────────────────────────── Expediente clínico ──────────────────────────
PROCESOS['act_11_odontograma'] = ("Proceso de registro del odontograma", """
|Odontólogo|
start
:Abrir el expediente
clínico del paciente;
:Seleccionar la pestaña
del odontograma;
|Sistema|
:Recuperar el hallazgo vigente
de cada pieza y cara;
:Dibujar la arcada completa
con la nomenclatura FDI;
|Odontólogo|
:Seleccionar la pieza
a registrar;
|Sistema|
:Mostrar el estado vigente
y el historial de la pieza;
|Odontólogo|
:Seleccionar la cara,
el tipo de hallazgo,
la fecha y la observación;
|Sistema|
if (¿La pieza pertenece a la
nomenclatura FDI permanente?) then (no)
  |Odontólogo|
  :Corregir la pieza;
  detach
else (sí)
endif
if (¿La fecha es posterior
a hoy?) then (sí)
  |Odontólogo|
  :Corregir la fecha;
  detach
else (no)
endif
if (¿El hallazgo describe la
pieza completa registrado
sobre una cara?) then (sí)
  |Odontólogo|
  :Corregir la cara
  a toda la pieza;
  detach
else (no)
endif
:Agregar el hallazgo
sin modificar los anteriores;
note right
  La tabla es de solo agregado:
  la pieza conserva su historia
  y el odontograma muestra
  el registro más reciente.
end note
:Recalcular el hallazgo vigente
de esa pieza y cara;
|Odontólogo|
:Visualizar la arcada
con el estado actualizado;
stop
""")

PROCESOS['act_12_plan'] = ("Proceso de elaboración del plan de tratamiento", """
|Odontólogo|
start
:Abrir el expediente
del paciente;
:Revisar los hallazgos
por atender del odontograma;
:Crear un plan de tratamiento
y capturar el diagnóstico;
|Sistema|
:Generar el código del plan
y guardarlo como borrador;
:Registrar la creación
en el historial;
|Odontólogo|
repeat
:Agregar un renglón indicando
la fase, el procedimiento,
la pieza y el número de piezas;
  |Sistema|
  :Proponer el precio de lista
  del catálogo;
  |Componente predictivo|
  :Estimar la duración del renglón
  y devolver el origen
  de la estimación;
  |Sistema|
  :Guardar el renglón con su precio,
  su duración estimada
  y su orden dentro de la fase;
  :Recalcular el subtotal,
  el descuento y el total;
  :Repartir los renglones pendientes
  en sesiones, respetando el orden
  de las fases y un máximo de
  ciento veinte minutos por sesión;
  |Odontólogo|
repeat while (¿Falta algún renglón?) is (sí)
:Revisar el presupuesto
y las sesiones estimadas
con el paciente;
if (¿El paciente acepta
el tratamiento?) then (sí)
  :Marcar el plan
  como aprobado;
  |Sistema|
  if (¿El plan tiene al menos
  un renglón?) then (no)
    |Odontólogo|
    :Agregar los renglones
    faltantes;
    detach
  else (sí)
  endif
  :Registrar la fecha
  de aprobación;
  :Habilitar el agendado
  de sus renglones;
else (no)
  |Odontólogo|
  :Marcar el plan
  como rechazado;
  |Sistema|
  :Conservar el plan
  para consulta posterior;
endif
|Odontólogo|
:Visualizar el plan
con su estado definitivo;
stop
""")

PROCESOS['act_13_ejecucion'] = ("Proceso de ejecución del plan de tratamiento", """
|Recepcionista|
start
:Abrir el plan de tratamiento
aprobado;
|Sistema|
if (¿El plan está aprobado
o en curso?) then (no)
  |Recepcionista|
  :Visualizar que solo se agendan
  renglones de un plan vigente;
  stop
else (sí)
endif
|Recepcionista|
repeat
:Seleccionar un renglón pendiente
y solicitar su agendado;
  |Sistema|
  :Abrir el formulario de cita
  con el paciente, el odontólogo,
  el procedimiento y la duración
  estimada del renglón;
  |Recepcionista|
  :Elegir la fecha y la hora
  entre los espacios disponibles;
  |Sistema|
  :Aplicar las validaciones
  de la agenda;
  :Crear la cita y vincularla
  al renglón del plan;
  :Marcar el renglón
  como agendado;
  |Odontólogo|
  :Atender al paciente
  en la fecha programada;
  |Recepcionista|
  :Registrar los tiempos reales
  de la atención;
  |Sistema|
  :Marcar el renglón
  como completado;
  :Recalcular el avance y los
  minutos de sillón pendientes;
  |Recepcionista|
repeat while (¿Quedan renglones
pendientes?) is (sí)
|Sistema|
:Cerrar el plan
como finalizado;
if (¿El plan conserva saldo
pendiente?) then (sí)
  |Recepcionista|
  :Visualizar el aviso
  de saldo por cobrar;
else (no)
endif
stop
""")

PROCESOS['act_14_nota'] = ("Proceso de registro de la nota clínica de evolución", """
|Odontólogo|
start
:Abrir la cita atendida
desde el expediente
o desde el calendario;
|Sistema|
if (¿La cita ya tiene
nota clínica?) then (sí)
  |Odontólogo|
  :Consultar la nota
  existente;
  stop
else (no)
endif
:Precargar el odontólogo,
la fecha y el procedimiento
de la cita;
|Odontólogo|
:Capturar el motivo
de la consulta;
:Describir los hallazgos
clínicos observados;
:Describir el procedimiento
realizado;
:Enumerar las piezas tratadas
e indicar su número;
:Indicar si se aplicó anestesia;
:Indicar si hubo complicación;
:Registrar los materiales
y las indicaciones al paciente;
|Sistema|
if (¿Las piezas enumeradas
coinciden con el número
indicado?) then (no)
  |Odontólogo|
  :Corregir el número
  de piezas;
  detach
else (sí)
endif
if (¿Se marcó complicación
sin describirla?) then (sí)
  |Odontólogo|
  :Describir la complicación;
  detach
else (no)
endif
:Guardar la nota y vincularla
a la cita atendida;
|Componente predictivo|
:Incorporar el número de piezas,
el uso de anestesia y la
complicación como variables
explicativas de la duración;
note right
  Son las variables que el
  registro de tiempos no puede
  conocer por sí solo.
end note
|Odontólogo|
:Visualizar la evolución
del paciente actualizada;
stop
""")

# ─────────────────────────────── Cobros ───────────────────────────────
PROCESOS['act_15_cobros'] = ("Proceso de registro de abonos y control de saldo", """
|Recepcionista|
start
:Abrir el módulo de cobros;
|Sistema|
:Listar los planes aprobados
y en curso, ordenados por saldo;
:Calcular el total presupuestado,
lo abonado y el saldo de cada plan;
|Recepcionista|
:Seleccionar el plan a cobrar;
:Capturar la fecha, el monto,
la forma de pago y la referencia;
|Sistema|
if (¿El monto es mayor
que cero?) then (no)
  |Recepcionista|
  :Corregir el monto;
  detach
else (sí)
endif
if (¿El monto excede
el saldo pendiente?) then (sí)
  |Recepcionista|
  :Corregir el monto;
  detach
else (no)
endif
if (¿La fecha es posterior
a hoy?) then (sí)
  |Recepcionista|
  :Corregir la fecha;
  detach
else (no)
endif
:Guardar el abono
como vigente;
:Recalcular el saldo del plan;
:Registrar el abono
en el historial;
|Recepcionista|
if (¿El abono se capturó
con un error?) then (sí)
  :Solicitar la anulación
  del abono;
  |Sistema|
  :Marcar el abono como anulado
  sin eliminarlo;
  :Devolver el saldo
  a su valor anterior;
  note right
    Anulación lógica: el estado
    de cuenta conserva la traza
    de la operación.
  end note
else (no)
endif
|Recepcionista|
:Visualizar el estado
de cuenta actualizado;
stop
""")

# ────────────────────────────── Inteligencia ──────────────────────────────
PROCESOS['act_16_modelo'] = ("Proceso de entrenamiento y versionado del modelo predictivo", """
|Administrador|
start
:Solicitar el entrenamiento
de una versión nueva;
|Sistema|
:Reunir el conjunto de
entrenamiento acumulado;
if (¿Hay registros suficientes
para entrenar?) then (no)
  |Administrador|
  :Visualizar que se requieren
  más atenciones registradas;
  stop
else (sí)
endif
:Depurar los registros
atípicos e incompletos;
:Dividir los datos en
entrenamiento y prueba;
|Componente predictivo|
:Entrenar el algoritmo
de regresión;
:Calcular el error absoluto medio,
la raíz del error cuadrático medio
y el coeficiente de determinación;
|Sistema|
:Registrar la versión del modelo
con su algoritmo, su fecha
y sus métricas;
|Administrador|
:Comparar las métricas con las
de la versión en producción;
if (¿La versión nueva reduce
el error de forma apreciable?) then (sí)
  :Activar la versión nueva;
  |Sistema|
  :Desactivar la versión anterior
  conservando su registro;
  :Dirigir las estimaciones
  siguientes al modelo nuevo;
else (no)
  |Sistema|
  :Conservar la versión nueva
  como histórico sin activarla;
endif
|Administrador|
:Visualizar el comparativo
de versiones del modelo;
stop
""")


def main():
    destino = pathlib.Path('.')
    for nombre, (titulo, cuerpo) in PROCESOS.items():
        texto = (f'@startuml\ntitle {titulo}\n\n{ESTILO}\n'
                 f'{restaurar_calles(cuerpo.strip())}\n@enduml\n')
        (destino / f'{nombre}.puml').write_text(texto, encoding='utf-8')
    print(f'{len(PROCESOS)} diagramas de actividad generados')


if __name__ == '__main__':
    main()
