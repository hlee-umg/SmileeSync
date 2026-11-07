"""Capítulo 4, sección 4.2: Codificación."""
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

    def fig(archivo, numero, titulo_pie, anclaje):
        p = F.imagen(doc, C.IMG / archivo, anclaje, ancho, alto)
        return F.pie(doc, f'Figura {numero}', titulo_pie, p)

    a = F.titulo(doc, '4.2 Codificación', 2, a)
    a = F.parrafo(
        doc,
        'La presente sección documenta el código fuente del sistema. Comienza '
        'por el inicio de sesión y la construcción del menú, que son los dos '
        'puntos por los que todo usuario pasa; continúa con el inventario de las '
        'funciones principales de cada módulo, con indicación de lo que hace '
        'cada una y con el fragmento de código de las más significativas; y '
        'concluye con un ejemplo completo de la generación de gráficas y '
        'reportes. Los fragmentos se reproducen tal como están en el '
        'repositorio, con la indicación del archivo al que pertenecen; donde el '
        'fragmento se abrevia, la omisión se señala con puntos suspensivos.', a)

    # ════════════════════════════ 4.2.1 inicio de sesión ═══════════════════════
    a = F.titulo(doc, '4.2.1 Inicio de sesión', 3, a)
    a = F.parrafo(
        doc,
        'El sistema no expone ninguna pantalla sin sesión abierta: toda vista '
        'lleva el decorador que exige autenticación y, al no haberla, redirige '
        'al formulario de ingreso (Figura 310). El formulario solicita el correo '
        'electrónico y la contraseña, y ante un fallo responde con un mensaje '
        'único —«Correo o contraseña incorrectos»— que deliberadamente no '
        'distingue cuál de los dos datos falló, para no confirmar a un tercero '
        'que un correo está registrado en el sistema.', a)
    a = fig('01_login.png', 310, 'Pantalla de inicio de sesión del sistema', a)
    a = F.parrafo(
        doc,
        'La Tabla 206 relaciona los archivos que intervienen en el proceso con '
        'la función que cumple cada uno.', a)

    filas = [['Archivo', 'Función o clase', 'Qué hace']]
    for arch, fn, que in [
        ('config/urls.py', 'ruta login/',
         'Publica la vista de autenticación de Django con la plantilla y el '
         'formulario propios del sistema.'),
        ('usuarios/forms.py', 'LoginCorreoForm',
         'Sustituye la etiqueta del campo de usuario por «Correo electrónico» y '
         'aplica los estilos del sistema.'),
        ('usuarios/backends.py', 'EmailBackend.authenticate',
         'Localiza al usuario por su correo sin distinguir mayúsculas, verifica '
         'la contraseña contra el resumen almacenado y comprueba que la cuenta '
         'esté activa.'),
        ('usuarios/models.py', 'Usuario',
         'Declara el correo como campo único e incorpora el rol, el estado y la '
         'pregunta secreta.'),
        ('usuarios/middleware.py', 'NoCacheMiddleware',
         'Impide que el navegador conserve en caché las páginas con sesión, de '
         'modo que el botón de retroceso no las muestre tras cerrar sesión.'),
        ('usuarios/views.py', 'recuperar_correo, recuperar_pregunta, '
                              'recuperar_nueva',
         'Resuelven en tres pasos la recuperación de la contraseña mediante la '
         'pregunta secreta.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 206,
              'Archivos y funciones que intervienen en el inicio de sesión', a,
              anchos=[Emu(int(1.5 * P)), Emu(int(1.7 * P)), Emu(int(3.1 * P))])

    a = F.parrafo(
        doc,
        'El enrutamiento reutiliza la vista de autenticación del framework y le '
        'entrega la plantilla y el formulario del sistema, con lo que el manejo '
        'de la sesión, del testigo contra falsificación de peticiones y de la '
        'redirección posterior queda a cargo de código ya probado.', a)
    a = F.codigo(doc, 'app/config/urls.py', r'''
urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginCorreoForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # El módulo Principal (calendario de la agenda) es la raíz del sitio.
    path('', include('agenda.urls')),
    path('usuarios/', include('usuarios.urls')),
    ...
]
'''.strip('\n'), a)

    a = F.parrafo(
        doc,
        'La verificación de las credenciales se implementó en un respaldo de '
        'autenticación propio. La línea que calcula y descarta un resumen cuando '
        'el correo no existe es la que iguala el tiempo de respuesta entre un '
        'correo inexistente y uno existente con contraseña equivocada, conforme '
        'se explicó en la sección 4.1.3.1.', a)
    a = F.codigo(doc, 'app/usuarios/backends.py', r'''
class EmailBackend(ModelBackend):
    """Permite iniciar sesión con el correo electrónico en lugar del username."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        email = kwargs.get('email') or username
        if not email or not password:
            return None
        try:
            user = UserModel.objects.get(email__iexact=email.strip())
        except UserModel.DoesNotExist:
            UserModel().set_password(password)  # iguala el tiempo de respuesta
            return None
        except UserModel.MultipleObjectsReturned:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
'''.strip('\n'), a)

    a = F.parrafo(
        doc,
        'El componente intermedio que acompaña al inicio de sesión no interviene '
        'en la autenticación, sino en lo que ocurre al terminarla. Añade a cada '
        'respuesta dinámica los encabezados que impiden al navegador conservarla '
        'en caché, y excluye los archivos estáticos, que sí deben almacenarse '
        'para no volver a descargarse en cada pantalla.', a)
    a = F.codigo(doc, 'app/usuarios/middleware.py', r'''
class NoCacheMiddleware:
    def __call__(self, request):
        response = self.get_response(request)
        # No aplicar a archivos estáticos (deben poder cachearse).
        if not request.path.startswith(settings.STATIC_URL):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
'''.strip('\n'), a)

    # ════════════════════════════ 4.2.2 menú principal ═════════════════════════
    a = F.titulo(doc, '4.2.2 Menú principal', 3, a)
    a = F.parrafo(
        doc,
        'Tras autenticarse, el usuario llega al módulo Principal (Figura 311), '
        'que ocupa la raíz del sitio. La pantalla se compone de tres partes: el '
        'menú lateral con los módulos a los que el usuario tiene acceso, la '
        'franja superior con su nombre, su rol y, cuando corresponde, el '
        'distintivo de solo consulta, y el área de trabajo con los indicadores '
        'del período y el calendario de la clínica.', a)
    a = fig('02_principal_semana.png', 311,
            'Menú principal del sistema con el calendario semanal de la clínica '
            '(datos de demostración)', a)
    a = F.parrafo(
        doc,
        'El menú no está escrito fijo en la plantilla: se construye a partir de '
        'los permisos del rol del usuario que tiene la sesión abierta. Cada '
        'entrada se condiciona al permiso del módulo correspondiente, de modo '
        'que la recepción no ve la entrada del módulo de inteligencia y el '
        'odontólogo no ve la de usuarios. El mismo archivo de plantilla sirve, '
        'así, a los cuatro roles del sistema.', a)
    a = F.codigo(doc, 'app/templates/base.html', r'''
<ul class="nav flex-column py-2">
  <li class="nav-item"><a class="nav-link {% if request.resolver_match.url_name == 'principal' %}active{% endif %}"
      href="{% url 'agenda:principal' %}"><i class="bi bi-speedometer2"></i> Inicio</a></li>

  {% if user.rol.puede_usuarios or user.es_admin %}
  <li class="nav-item"><a class="nav-link" href="{% url 'usuarios:lista' %}">
      <i class="bi bi-people"></i> Usuarios</a></li>
  {% endif %}

  {% if user.rol.puede_clinico or user.es_admin %}
  <li class="nav-item"><a class="nav-link" href="{% url 'clinico:lista' %}">
      <i class="bi bi-file-medical"></i> Expedientes</a></li>
  {% endif %}

  {% if user.rol.puede_inteligencia or user.es_admin %}
  <li class="nav-item"><a class="nav-link" href="{% url 'inteligencia:panel' %}">
      <i class="bi bi-cpu"></i> Inteligencia</a></li>
  {% endif %}
  ...
</ul>
'''.strip('\n'), a)

    a = F.parrafo(
        doc,
        'La decisión de qué puede hacer el usuario, y no solo qué puede ver, se '
        'concentra en dos métodos del modelo de usuario. El primero resuelve el '
        'acceso al módulo; el segundo, el permiso de escritura, con la excepción '
        'del expediente clínico, que se rige por la competencia profesional '
        'declarada en el rol y no por los privilegios administrativos.', a)
    a = F.codigo(doc, 'app/usuarios/models.py — clase Usuario', r'''
def puede(self, modulo):
    """Devuelve True si el usuario tiene acceso al módulo indicado."""
    if self.es_admin:
        return True
    return bool(self.rol and getattr(self.rol, f'puede_{modulo}', False))

def puede_escribir(self, modulo):
    """Acceso de escritura: exige el módulo y que el rol no sea de consulta.

    El módulo clínico es la excepción y se rige por `escritura_clinica`: el
    expediente lo escribe quien tiene competencia profesional declarada,
    con independencia de sus privilegios administrativos.
    """
    if self.es_admin:
        return True
    if not self.puede(modulo):
        return False
    if modulo == 'clinico':
        return bool(self.rol and self.rol.escritura_clinica)
    return not self.es_solo_consulta
'''.strip('\n'), a)

    a = F.parrafo(
        doc,
        'Para que la interfaz y la autorización no puedan contradecirse, un '
        'procesador de contexto expone a todas las plantillas el resultado de '
        'esos mismos métodos. Así, la condición con que la plantilla oculta un '
        'botón proviene del mismo cálculo con que el decorador rechaza la '
        'petición, y no de una regla escrita dos veces.', a)
    a = F.codigo(doc, 'app/usuarios/context_processors.py', r'''
MODULOS = ['usuarios', 'pacientes', 'catalogos', 'agenda', 'clinico',
           'finanzas', 'inteligencia', 'reportes']


def permisos(request):
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {'escritura': {}, 'solo_consulta': False}
    return {
        'escritura': {m: usuario.puede_escribir(m) for m in MODULOS},
        'solo_consulta': usuario.es_solo_consulta,
    }
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La Tabla 207 presenta la correspondencia entre los cuatro roles '
        'definidos y los módulos que cada uno alcanza, con indicación de si el '
        'acceso incluye escritura. Es la matriz que el sistema aplica y la que '
        'determina, en consecuencia, el menú que cada usuario encuentra al '
        'ingresar.', a)

    filas = [['Módulo', 'Administrador', 'Recepcionista', 'Odontólogo',
              'Asistente']]
    for m, ad, re, od, asi in [
        ('Usuarios', 'Escritura', 'Sin acceso', 'Sin acceso', 'Sin acceso'),
        ('Pacientes', 'Escritura', 'Escritura', 'Consulta', 'Sin acceso'),
        ('Catálogos', 'Escritura', 'Sin acceso', 'Sin acceso', 'Sin acceso'),
        ('Agenda y citas', 'Escritura', 'Escritura', 'Consulta', 'Consulta'),
        ('Expediente clínico', 'Escritura', 'Consulta', 'Escritura',
         'Consulta'),
        ('Cobros', 'Escritura', 'Escritura', 'Sin acceso', 'Sin acceso'),
        ('Inteligencia', 'Escritura', 'Sin acceso', 'Sin acceso', 'Sin acceso'),
        ('Reportes', 'Consulta', 'Consulta', 'Sin acceso', 'Sin acceso'),
    ]:
        filas.append([m, ad, re, od, asi])
    a = tabla(filas, 207,
              'Matriz de acceso por rol y por módulo implementada en el sistema',
              a, anchos=[Emu(int(1.6 * P)), Emu(int(1.1 * P)), Emu(int(1.1 * P)),
                         Emu(int(1.1 * P)), Emu(int(1.1 * P))])
    a = F.parrafo(
        doc,
        'El rol de odontólogo merece una precisión. Su acceso a la agenda es de '
        'consulta, porque la programación de citas es una función de la '
        'recepción; sin embargo, el profesional sí registra sus propias '
        'ausencias, que son información suya. Es el único caso del sistema en '
        'que un rol de consulta escribe, y está acotado a los registros del '
        'odontólogo vinculado a su propio usuario mediante una comprobación '
        'explícita en la vista.', a)

    # ═══════════════════════════ 4.2.3 funciones principales ═══════════════════
    a = F.titulo(doc, '4.2.3 Funciones principales', 3, a)
    a = F.parrafo(
        doc,
        'El módulo Principal es el que concentra el aporte del sistema y el que '
        'reúne, con sus dependencias, algo más de la mitad del código escrito. '
        'La presente sección documenta primero el inventario completo de sus '
        'funciones y a continuación sus cinco procesos, cada uno con el '
        'fragmento de código que lo resuelve; después inventaría las funciones '
        'de los demás módulos con el fragmento de la más representativa de cada '
        'uno. La Tabla 208 relaciona las funciones del módulo Principal con lo '
        'que hace cada una.', a)

    filas = [['Archivo', 'Función', 'Qué hace']]
    for arch, fn, que in [
        ('views.py', 'principal',
         'Construye la pantalla de inicio: resuelve el período solicitado, '
         'filtra las citas, calcula los indicadores, pide la estimación cuando '
         'hay una consulta en curso y arma la rejilla del calendario.'),
        ('views.py', '_rejilla',
         'Organiza las citas en una matriz de horas por días y determina el '
         'rango de horas visible, incluyendo las de los espacios '
         'recomendados.'),
        ('views.py', '_huecos_sugeridos',
         'Calcula el primer inicio viable de cada hora para una cita de la '
         'duración estimada, recorriendo la jornada en pasos de quince '
         'minutos.'),
        ('views.py', '_semana_solicitada, _fecha_solicitada, _lunes_de',
         'Interpretan el período pedido en la dirección y, ante un valor '
         'inválido, recaen en el día o la semana actuales.'),
        ('views.py', 'estimar',
         'Atiende la consulta de estimación en formato JSON que el formulario '
         'de cita realiza cada vez que cambia uno de sus campos.'),
        ('views.py', '_estimacion_para',
         'Obtiene la estimación con los datos que el formulario ya tiene, para '
         'mostrarla junto a los errores de validación sin perder lo capturado.'),
        ('views.py', 'crear',
         'Programa una cita nueva; registra la predicción, deja constancia en '
         'el historial y, cuando la cita proviene de un plan, liga el renglón '
         'correspondiente.'),
        ('views.py', 'editar, cancelar',
         'Reprograman y cancelan una cita conservando en el historial el estado '
         'anterior; la cancelación nunca elimina el registro.'),
        ('views.py', 'registrar_tiempos',
         'Registra los tiempos reales de la atención, incorpora el dato al '
         'conjunto de entrenamiento y cierra los renglones del plan que la cita '
         'atendió.'),
        ('views.py', '_cerrar_renglones',
         'Marca como completados los renglones del plan ejecutados por la cita '
         'y recalcula el avance del plan.'),
        ('views.py', 'lista, detalle',
         'Consultan las citas por rango de fechas, odontólogo y estado, y '
         'muestran el detalle de una cita con su desviación de tiempo.'),
        ('views.py', 'horarios, quitar_horario',
         'Administran el patrón semanal de disponibilidad de cada '
         'profesional.'),
        ('views.py', 'ausencias, quitar_ausencia',
         'Registran y retiran las ausencias de una fecha concreta.'),
        ('disponibilidad.py', 'franjas_efectivas',
         'Calcula los intervalos en que el profesional atiende una fecha: su '
         'patrón semanal menos las ausencias registradas para ese día.'),
        ('disponibilidad.py', '_restar',
         'Resta un intervalo de una lista de intervalos; un corte en medio '
         'parte el intervalo en dos y uno que lo cubre lo elimina.'),
        ('disponibilidad.py', 'hay_traslape',
         'Determina si dos intervalos se traslapan: cada uno empieza antes de '
         'que el otro termine.'),
        ('disponibilidad.py', 'cabe_en_franja',
         'Verifica que la cita completa quepa dentro de una sola franja '
         'efectiva.'),
        ('disponibilidad.py', 'unidades_libres, asignar_unidad',
         'Determinan qué unidades dentales están desocupadas en un intervalo y '
         'toman la primera disponible.'),
        ('disponibilidad.py', 'unidades_activas',
         'Lista las unidades dentales dadas de alta en el catálogo.'),
        ('disponibilidad.py', 'capacidad_minutos',
         'Calcula los minutos de atención posibles en un período como el menor '
         'entre profesionales disponibles y unidades activas en cada intervalo '
         'de quince minutos.'),
        ('forms.py', 'CitaForm.clean',
         'Valida las cuatro condiciones de una cita: duración positiva, cabida '
         'en la disponibilidad efectiva, ausencia de traslape y unidad dental '
         'libre.'),
        ('forms.py', 'CitaForm.clean_fecha',
         'Impide programar una cita nueva en una fecha pasada, sin bloquear la '
         'reprogramación de una cita antigua.'),
        ('forms.py', 'CitaForm.save',
         'Calcula la hora de fin y asigna automáticamente la unidad dental, que '
         'no se pide al usuario porque las unidades son intercambiables.'),
        ('forms.py', 'RegistrarTiemposForm',
         'Valida los tiempos reales y calcula la duración efectiva de la '
         'atención.'),
        ('forms.py', 'HorarioForm, AusenciaForm',
         'Validan que las franjas no se traslapen entre sí y que la hora de fin '
         'sea posterior a la de inicio.'),
        ('forms.py', 'sumar_minutos',
         'Suma minutos a una hora sin desbordar al día siguiente.'),
        ('models.py', 'Cita',
         'Entidad de la cita: paciente, profesional, procedimiento, fecha, '
         'horas programadas y reales, duración asignada y real, estado y unidad '
         'dental.'),
        ('models.py', 'HorarioDisponibilidad, AusenciaOdontologo',
         'Patrón semanal de atención y ausencias por fecha de cada '
         'profesional.'),
        ('models.py', 'HistorialCita',
         'Historial de auditoría de la cita: acción, estado anterior, '
         'responsable y fecha.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 208,
              'Inventario de funciones del módulo Principal y de la agenda', a,
              anchos=[Emu(int(1.1 * P)), Emu(int(1.9 * P)), Emu(int(3.3 * P))])

    a = F.titulo(doc, '4.2.3.1 Proceso 1: construcción del calendario', 4, a)
    a = F.parrafo(
        doc,
        'El calendario es la pantalla de trabajo habitual de la recepción y la '
        'que todo usuario encuentra al ingresar. La vista resuelve primero el '
        'período —semana o día, según el parámetro recibido—, consulta las citas '
        'de ese rango con sus relaciones precargadas en una sola consulta para '
        'no incurrir en una consulta por cita, y entrega a la plantilla una '
        'matriz de filas por hora y columnas por día.', a)
    a = F.parrafo(
        doc,
        'La función que arma esa matriz incorpora una decisión que no es '
        'evidente: el rango de horas visible no se calcula solo con las citas '
        'existentes, sino también con los espacios recomendados. Sin esa '
        'consideración, una recomendación situada a una hora en que no hay '
        'ninguna cita quedaría fuera de la rejilla y el usuario no la vería, que '
        'es precisamente el caso en que la recomendación resulta más útil.', a)
    a = F.codigo(doc, 'app/agenda/views.py — función _rejilla', r'''
def _rejilla(citas, inicio, dias_visibles, sugeridos=None):
    """Organiza las citas en una rejilla de horas por días para la plantilla."""
    rejilla = {}
    for cita in citas:
        indice_dia = (cita.fecha - inicio).days
        if 0 <= indice_dia < dias_visibles:
            hora = cita.hora_inicio_programada.hour
            rejilla.setdefault(hora, {}).setdefault(indice_dia, []).append(cita)

    # El rango de horas visible abarca tanto las citas existentes como los
    # espacios sugeridos: de lo contrario una recomendación podría quedar
    # fuera de la rejilla y el usuario no la vería.
    horas = sorted(rejilla.keys()) + [h for _, h in (sugeridos or {})]
    if horas:
        desde = max(HORA_APERTURA, min(horas) - 1)
        hasta = min(HORA_CIERRE, max(horas) + 2)
    else:
        desde, hasta = 8, 18

    filas = []
    for hora in range(desde, hasta):
        celdas = []
        for d in range(dias_visibles):
            fecha = inicio + timedelta(days=d)
            celdas.append({
                'indice': d, 'citas': rejilla.get(hora, {}).get(d, []),
                'fecha': fecha.isoformat(), 'hora': f'{hora:02d}:00',
                'sugerida': (sugeridos or {}).get((d, hora)),
            })
        filas.append({'hora': f'{hora:02d}:00', 'celdas': celdas})
    return filas
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'Cada casilla lleva su fecha y su hora, de modo que la plantilla pueda '
        'enlazar directamente a la programación de una cita en ese espacio. Esa '
        'es la razón por la que la casilla libre del calendario es un enlace y '
        'no un simple espacio en blanco: al pulsarla, el formulario de cita '
        'llega con la fecha, la hora y el profesional ya definidos, con lo que '
        'el usuario solo captura el paciente y el procedimiento.', a)
    a = F.parrafo(
        doc,
        'La misma vista calcula los cuatro indicadores de la franja superior. El '
        'más relevante de ellos es la utilización de la agenda, que no se mide '
        'contra las horas declaradas por los profesionales sino contra la '
        'capacidad real de la clínica, calculada como el menor entre '
        'profesionales disponibles y unidades dentales activas en cada intervalo '
        'de quince minutos. Medirla contra las horas declaradas sobrestimaría la '
        'capacidad y reportaría una utilización inferior a la real, que es '
        'justamente el dato que la clínica necesita para decidir si le hace '
        'falta otro sillón.', a)

    a = F.titulo(doc, '4.2.3.2 Proceso 2: estimación de la duración del '
                      'procedimiento', 4, a)
    a = F.parrafo(
        doc,
        'La estimación de duraciones es el objeto de la investigación y, en el '
        'código, un servicio con una sola puerta de entrada. Todo el sistema '
        '—el calendario, el formulario de cita, el plan de tratamiento— solicita '
        'la estimación a la misma función, que aplica una cadena de respaldo de '
        'tres niveles: el modelo entrenado, si existe una versión en producción; '
        'el promedio histórico real de la clínica, si hay al menos tres '
        'atenciones del mismo procedimiento; y la duración de referencia del '
        'catálogo, como último respaldo.', a)
    a = F.parrafo(
        doc,
        'La cadena no es una redundancia defensiva sino un requisito de la '
        'implantación. Una clínica que estrena el sistema no tiene historial, de '
        'modo que un sistema que solo supiera estimar con el modelo entrenado '
        'sería inservible durante sus primeros meses, que son precisamente '
        'aquellos en que la clínica debe adoptarlo. Cada estimación declara, '
        'además, de qué nivel proviene, de manera que quien agenda sepa qué tan '
        'fundado es el número que está viendo.', a)
    a = F.codigo(doc, 'app/inteligencia/servicio.py — función estimar_duracion', r'''
def estimar_duracion(procedimiento, odontologo, fecha, hora, num_piezas=1):
    """Estima la duración de un procedimiento y el bloque de tiempo sugerido."""
    # --- Nivel 1: modelo predictivo entrenado ---
    modelo = _modelo_activo()
    if modelo:
        prediccion = _estimar_con_modelo(modelo, procedimiento, odontologo,
                                         fecha, hora, num_piezas)
        if prediccion:
            duracion = _redondear(prediccion)
            minimo, maximo = _bloque_recomendado(duracion)
            est = Estimacion(duracion, minimo, maximo, 'modelo',
                             f'Estimado por {modelo.nombre} '
                             f'({modelo.get_algoritmo_display()}).')
            est.modelo = modelo
            return est

    # --- Nivel 2: promedio histórico real de la clínica ---
    promedio, total, es_del_odontologo = _estimar_con_historico(
        procedimiento, odontologo)
    if promedio:
        duracion = _redondear(promedio)
        minimo, maximo = _bloque_recomendado(duracion)
        alcance = ('de este odontólogo' if es_del_odontologo
                   else 'de todos los odontólogos')
        return Estimacion(duracion, minimo, maximo, 'historico',
                          f'Promedio de {total} atenciones previas {alcance}. '
                          f'La precisión aumentará al acumularse más registros.')

    # --- Nivel 3: duración de referencia del catálogo ---
    duracion = _redondear(procedimiento.duracion_promedio_min)
    minimo, maximo = _bloque_recomendado(duracion)
    return Estimacion(duracion, minimo, maximo, 'catalogo',
                      'Aún no hay suficientes atenciones registradas de este '
                      'procedimiento; se usa la duración de referencia del catálogo.')
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'El servicio no devuelve un número suelto sino un objeto con la '
        'duración estimada, el bloque recomendado —un rango del 85 % al 120 % de '
        'la estimación, para no quedarse corto ni bloquear agenda de más—, el '
        'origen de la estimación y el texto con que la pantalla lo explica. '
        'Devolver también la explicación es deliberado: es lo que permite que la '
        'interfaz declare la procedencia del número sin que cada pantalla tenga '
        'que redactarla por su cuenta.', a)
    a = F.parrafo(
        doc,
        'La lectura del modelo desde el disco requirió una corrección durante el '
        'desarrollo. En la primera versión, la función que predice invocaba la '
        'carga del archivo serializado en cada estimación, lo que significaba '
        'deserializar medio megabyte por cada cita que se consultaba. Se agregó '
        'una caché en memoria del módulo, de modo que el archivo se lea una sola '
        'vez por versión y se descarte únicamente cuando se activa otra. La '
        'verificación automatizada mide esa diferencia: la primera estimación '
        'tras limpiar la caché resulta sensiblemente más costosa que las '
        'siguientes, y estas se mantienen por debajo de cien milisegundos.', a)
    a = F.codigo(doc, 'app/inteligencia/servicio.py — caché del modelo', r'''
# El archivo del modelo puede pesar varios megabytes. Deserializarlo en cada
# estimación significaría releerlo en cada cita que se agenda, de modo que se
# conserva en memoria y solo se recarga cuando cambia la versión activa.
_CACHE = {'version': None, 'estimador': None, 'anestesia': {}}


def _cargar(modelo):
    """Devuelve el estimador de la versión indicada, cargándolo una sola vez."""
    if _CACHE['version'] == modelo.pk and _CACHE['estimador'] is not None:
        return _CACHE['estimador']
    try:
        import joblib
    except ImportError:
        return None
    if not modelo.ruta_archivo or not os.path.exists(modelo.ruta_archivo):
        return None
    try:
        estimador = joblib.load(modelo.ruta_archivo)
    except Exception:
        # Un archivo dañado o entrenado con otra versión de la biblioteca no
        # debe impedir que se agende: la cadena de respaldo continúa.
        return None
    _CACHE['version'] = modelo.pk
    _CACHE['estimador'] = estimador
    return estimador
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'Al predecir, dos de las siete variables del modelo plantean un problema '
        'que el diseño tuvo que resolver: en el momento de agendar no se sabe '
        'todavía si se aplicará anestesia ni si surgirá una complicación, porque '
        'ambas se conocen al atender. La anestesia se resuelve con el '
        'comportamiento histórico del procedimiento —si más de la mitad de sus '
        'atenciones la usaron, se asume que la usará—; la complicación se asume '
        'ausente, porque por definición es imprevista y el sistema estima el '
        'caso nominal. Omitir ambas variables del entrenamiento habría sido la '
        'alternativa, pero son dos de las tres que más explican la duración, de '
        'modo que la precisión habría caído.', a)
    a = F.codigo(doc, 'app/inteligencia/servicio.py — función _estimar_con_modelo',
                 r'''
estimador = _cargar(modelo)
if estimador is None:
    return None
try:
    import pandas as pd
except ImportError:
    return None

try:
    # Los nombres de las columnas deben coincidir con los del entrenamiento.
    entrada = pd.DataFrame([{
        'procedimiento': procedimiento.nombre,
        'odontologo': f'{odontologo.nombres} {odontologo.apellidos}',
        'dia_semana': DIAS[fecha.weekday()],
        'hora_inicio': hora.hour,
        'num_piezas': num_piezas,
        'anestesia': _anestesia_habitual(procedimiento),
        'complicacion': 0,
    }])
    return float(estimador.predict(entrada)[0])
except Exception:
    # Un fallo del modelo no debe impedir agendar una cita.
    return None
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'El manejo de excepciones de ese fragmento responde a un criterio '
        'explícito: ninguna falla del componente predictivo puede impedir que la '
        'clínica agende una cita. Si las bibliotecas no están instaladas, si el '
        'archivo del modelo desapareció o si fue entrenado con una versión '
        'incompatible de la biblioteca, la función devuelve un valor nulo y la '
        'cadena de respaldo continúa con el promedio histórico. Una de las '
        'verificaciones automatizadas comprueba exactamente ese escenario: '
        'apunta la versión activa a una ruta inexistente y confirma que la '
        'estimación sigue estando disponible, con el origen declarado en otro '
        'nivel de la cadena.', a)
    a = F.parrafo(
        doc,
        'La estimación se consulta desde el navegador sin recargar la página. '
        'Cada vez que el usuario cambia el procedimiento, el profesional, la '
        'fecha, la hora o el número de piezas, el formulario solicita la '
        'estimación a una vista que responde en formato JSON y actualiza el '
        'panel de recomendación.', a)
    a = F.codigo(doc, 'app/agenda/views.py — función estimar', r'''
@login_required
@modulo_requerido('agenda')
def estimar(request):
    """Devuelve la estimación de duración en formato JSON."""
    id_proc = (request.GET.get('procedimiento') or '').strip()
    id_odo = (request.GET.get('odontologo') or '').strip()
    if not (id_proc.isdigit() and id_odo.isdigit()):
        return JsonResponse({'disponible': False})

    procedimiento = Proc.objects.filter(pk=int(id_proc), estado=True).first()
    odontologo = Odo.objects.filter(pk=int(id_odo), estado=True).first()
    if not (procedimiento and odontologo):
        return JsonResponse({'disponible': False})
    ...
    est = estimar_duracion(procedimiento, odontologo, fecha, hora, piezas)
    return JsonResponse({
        'disponible': True, 'duracion': est.duracion_min,
        'bloque_min': est.bloque_min, 'bloque_max': est.bloque_max,
        'origen': est.origen, 'etiqueta_origen': est.etiqueta_origen,
        'detalle': est.detalle,
    })
'''.strip('\n'), a)

    a = F.titulo(doc, '4.2.3.3 Proceso 3: recomendación de espacios en la '
                      'agenda', 4, a)
    a = F.parrafo(
        doc,
        'La estimación por sí sola no resuelve el problema de la recepción. '
        'Saber que un tratamiento de conducto tomará noventa minutos no dice '
        'dónde caben noventa minutos en la semana. El sistema recorre, '
        'entonces, la disponibilidad de la semana en pasos de quince minutos y '
        'devuelve el primer inicio viable de cada hora, que la plantilla resalta '
        'sobre la rejilla del calendario.', a)
    a = F.parrafo(
        doc,
        'Un inicio es viable cuando cumple cuatro condiciones a la vez: la cita '
        'completa cabe dentro de una franja efectiva del profesional, no se '
        'traslapa con ninguna de sus citas vigentes, no corresponde a un momento '
        'ya pasado y queda al menos una unidad dental libre. La última condición '
        'es la que distingue la recomendación de un simple cálculo de huecos en '
        'la agenda del profesional: la clínica tiene menos sillones que '
        'odontólogos, de modo que dos profesionales libres a la misma hora no '
        'significan dos citas simultáneas posibles.', a)
    a = F.codigo(doc, 'app/agenda/views.py — función _huecos_sugeridos', r'''
PASO_SUGERENCIA_MIN = 15


def _huecos_sugeridos(odontologo, fechas, duracion, hoy, ahora):
    """Primer inicio viable de cada hora para una cita de `duracion` minutos."""
    if not (odontologo and duracion):
        return {}

    ocupadas = {}
    for c in (Cita.objects
              .filter(odontologo=odontologo, fecha__in=fechas, estado=True)
              .exclude(estado_cita='CANCELADA')):
        ocupadas.setdefault(c.fecha, []).append((c.hora_inicio_programada,
                                                 c.hora_fin_programada))

    sugeridos = {}
    for indice, fecha in enumerate(fechas):
        # Disponibilidad efectiva: el patrón semanal menos las ausencias.
        for f_ini, f_fin in franjas_efectivas(odontologo, fecha):
            candidato = datetime.combine(fecha, f_ini)
            limite = datetime.combine(fecha, f_fin)
            while candidato + timedelta(minutes=duracion) <= limite:
                inicio_h = candidato.time()
                fin_h = (candidato + timedelta(minutes=duracion)).time()
                clave = (indice, inicio_h.hour)
                ya_paso = fecha < hoy or (fecha == hoy and inicio_h < ahora)
                choca = any(hay_traslape(inicio_h, fin_h, oi, of)
                            for oi, of in ocupadas.get(fecha, []))
                # Un espacio solo sirve si además queda un sillón libre.
                if not ya_paso and not choca and clave not in sugeridos:
                    if unidades_libres(fecha, inicio_h, fin_h):
                        sugeridos[clave] = inicio_h.strftime('%H:%M')
                candidato += timedelta(minutes=PASO_SUGERENCIA_MIN)
    return sugeridos
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La disponibilidad del profesional no se lee directamente de su patrón '
        'semanal, porque ese patrón describe cómo atiende habitualmente y no si '
        'estará ese día concreto. La disponibilidad efectiva es el patrón menos '
        'las ausencias registradas para la fecha, y se calcula restando '
        'intervalos: una ausencia a media jornada parte la franja en dos y una '
        'que la cubre por completo la elimina. Esa resta es la única operación '
        'del módulo que no resulta evidente, y es también la que permite que una '
        'ausencia de dos horas no cancele el resto del día.', a)
    a = F.codigo(doc, 'app/agenda/disponibilidad.py', r'''
def _restar(intervalos, quitar):
    """Resta un intervalo de una lista de intervalos, en minutos."""
    inicio_q, fin_q = quitar
    resultado = []
    for inicio, fin in intervalos:
        if fin_q <= inicio or inicio_q >= fin:      # no se tocan
            resultado.append((inicio, fin))
            continue
        if inicio_q > inicio:                        # queda un tramo antes
            resultado.append((inicio, inicio_q))
        if fin_q < fin:                              # queda un tramo después
            resultado.append((fin_q, fin))
    return resultado


def franjas_efectivas(odontologo, fecha):
    """Intervalos (hora_inicio, hora_fin) en que el odontólogo atiende."""
    intervalos = [
        (_a_minutos(f.hora_inicio), _a_minutos(f.hora_fin))
        for f in HorarioDisponibilidad.objects.filter(
            odontologo=odontologo, dia_semana=DIAS[fecha.weekday()], estado=True)
        if f.hora_fin > f.hora_inicio
    ]
    if not intervalos:
        return []

    for ausencia in AusenciaOdontologo.objects.filter(
            odontologo=odontologo, fecha=fecha, estado=True):
        intervalos = _restar(intervalos, (_a_minutos(ausencia.hora_inicio),
                                          _a_minutos(ausencia.hora_fin)))
        if not intervalos:
            break

    return [(_a_hora(i), _a_hora(f)) for i, f in sorted(intervalos)]
'''.strip('\n'), a)

    a = F.titulo(doc, '4.2.3.4 Proceso 4: programación de la cita y validación '
                      'de la disponibilidad', 4, a)
    a = F.parrafo(
        doc,
        'La recomendación orienta, pero no obliga: el usuario puede programar '
        'una cita en cualquier espacio. Por eso la validación no se delega a la '
        'pantalla sino que reside en el formulario, que verifica cuatro '
        'condiciones antes de permitir el guardado y, cuando alguna falla, '
        'devuelve un mensaje que indica qué hacer en lugar de limitarse a '
        'rechazar.', a)
    a = F.codigo(doc, 'app/agenda/forms.py — método CitaForm.clean', r'''
fin = sumar_minutos(inicio, duracion)
if fin <= inicio:
    self.add_error('duracion_asignada_min',
                   'La duración debe hacer que la cita termine después de '
                   'haber empezado.')
    return limpio
limpio['hora_fin_programada'] = fin

# --- la cita debe caber en la disponibilidad efectiva del odontólogo ---
dia = DIAS[fecha.weekday()]
tiene_patron = HorarioDisponibilidad.objects.filter(
    odontologo=odontologo, dia_semana=dia, estado=True).exists()
franjas = franjas_efectivas(odontologo, fecha)

if not tiene_patron:
    self.add_error('fecha', f'{odontologo} no tiene horario de atención '
                            f'configurado para ese día de la semana.')
elif not franjas:
    self.add_error('fecha', f'{odontologo} tiene registrada una ausencia que '
                            f'cubre toda su jornada del '
                            f'{fecha.strftime("%d/%m/%Y")}.')
elif not any(f_ini <= inicio and fin <= f_fin for f_ini, f_fin in franjas):
    disponibles = ', '.join(f'{i.strftime("%H:%M")} a {t.strftime("%H:%M")}'
                            for i, t in franjas)
    self.add_error('hora_inicio_programada',
                   f'La cita queda fuera del horario de atención. '
                   f'{odontologo} atiende ese día de {disponibles}.')
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'Las dos validaciones restantes verifican el traslape con otras citas '
        'del mismo profesional y la disponibilidad de una unidad dental. La '
        'segunda incorpora un detalle de redacción que surgió de las pruebas de '
        'implementación: el mensaje distingue el caso de una sola unidad activa '
        'del de varias, porque con un único sillón dado de alta el mensaje '
        'genérico producía la frase «Las 1 unidades dentales están ocupadas».', a)
    a = F.codigo(doc, 'app/agenda/forms.py — método CitaForm.clean (continuación)',
                 r'''
# --- no puede traslaparse con otra cita del mismo odontólogo ---
otras = Cita.objects.filter(odontologo=odontologo, fecha=fecha, estado=True
                            ).exclude(estado_cita='CANCELADA')
if self.instance.pk:
    otras = otras.exclude(pk=self.instance.pk)
for otra in otras:
    if hay_traslape(inicio, fin, otra.hora_inicio_programada,
                    otra.hora_fin_programada):
        self.add_error('hora_inicio_programada',
                       f'Se traslapa con la cita de {otra.paciente} '
                       f'({otra.hora_inicio_programada.strftime("%H:%M")} a '
                       f'{otra.hora_fin_programada.strftime("%H:%M")}).')
        break

# --- debe quedar una unidad dental libre ---
unidades = unidades_activas()
if not unidades:
    self.add_error(None, 'No hay unidades dentales activas en el catálogo, '
                         'por lo que no es posible programar citas.')
else:
    libre = asignar_unidad(fecha, inicio, fin, excluir_cita=self.instance.pk)
    if libre is None:
        cuantas = ('La única unidad dental está ocupada' if len(unidades) == 1
                   else f'Las {len(unidades)} unidades dentales están ocupadas')
        self.add_error('hora_inicio_programada',
                       f'{cuantas} en ese horario. Elija otro espacio o '
                       f'consulte la recomendación del calendario.')
    else:
        limpio['unidad'] = libre
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La unidad dental no se le pide al usuario. Las unidades son '
        'intercambiables entre sí, de modo que preguntar en qué sillón se '
        'atenderá añadiría un campo al formulario sin aportar información: el '
        'sistema asigna la primera libre al guardar. La asignación automática '
        'tiene además la ventaja de que la validación y la asignación usan el '
        'mismo cálculo, con lo que no puede ocurrir que el formulario acepte una '
        'cita para la que luego no haya sillón.', a)

    a = F.titulo(doc, '4.2.3.5 Proceso 5: registro de la atención y '
                      'realimentación del modelo', 4, a)
    a = F.parrafo(
        doc,
        'El quinto proceso es el que cierra el ciclo y el que hace que el '
        'sistema mejore con su propio uso. Al concluir la atención se registran '
        'la hora real de inicio y la de finalización; el formulario calcula la '
        'duración efectiva, el sistema deja constancia en el historial de la '
        'cita, incorpora el registro al conjunto de entrenamiento del modelo y '
        'cierra los renglones del plan de tratamiento que esa cita ejecutó.', a)
    a = F.codigo(doc, 'app/agenda/views.py — función registrar_tiempos', r'''
@login_required
@escritura_requerida('agenda')
def registrar_tiempos(request, pk):
    """Registro de los tiempos reales de atención al cerrar la cita."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == 'POST':
        form = RegistrarTiemposForm(request.POST, instance=cita)
        if form.is_valid():
            HistorialCita.objects.create(
                cita_ref=cita.pk, paciente=str(cita.paciente),
                odontologo=str(cita.odontologo), fecha_cita=cita.fecha,
                estado_cita_anterior=cita.estado_cita, accion='ATENCION',
                realizado_por=request.user.username)
            cita = form.save()
            registrar_dato_entrenamiento(cita)
            messages.success(
                request,
                f'Atención registrada: {cita.duracion_real_min} minutos reales '
                f'frente a {cita.duracion_asignada_min} asignados. '
                f'El dato se incorporó al entrenamiento del modelo.')
            _cerrar_renglones(request, cita)
            # El expediente del paciente queda incompleto sin la nota de la
            # visita, así que se ofrece escribirla en el momento a quien tiene
            # competencia para hacerlo.
            if request.user.puede_escribir('clinico') and not _tiene_nota(cita):
                return redirect(f'{reverse("clinico:nota_nueva", args=[cita.paciente_id])}'
                                f'?cita={cita.pk}')
            return redirect('agenda:lista')
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La redirección final no es un detalle de comodidad. La duración real '
        'sin la nota clínica de la visita es un dato incompleto para el modelo: '
        'el número de piezas tratadas, el uso de anestesia y la aparición de '
        'complicaciones son tres de sus siete variables y solo se conocen al '
        'documentar la atención. Por eso, cuando quien cierra la cita tiene '
        'competencia para escribir el expediente, el sistema lo lleva '
        'directamente al formulario de la nota con la cita ya vinculada. Cuando '
        'no la tiene —el caso de la recepción—, la cita queda cerrada y la nota '
        'pendiente para el profesional.', a)
    a = F.parrafo(
        doc,
        'El cierre de los renglones del plan responde al mismo criterio de no '
        'pedir al usuario lo que el sistema puede deducir: si la cita que '
        'ejecutaba un renglón presupuestado fue atendida, el renglón está '
        'ejecutado, y el avance del plan se recalcula sin que nadie lo marque a '
        'mano. Cuando el plan queda finalizado con saldo pendiente, el sistema '
        'lo advierte, porque es el momento en que la clínica debe gestionar el '
        'cobro.', a)

    # ═════════════════ 4.2.3.6 a 4.2.3.11: los demás módulos ══════════════════
    a = F.titulo(doc, '4.2.3.6 Funciones del módulo de Seguridad y Usuarios', 4, a)
    a = F.parrafo(
        doc,
        'Las funciones de este módulo se inventarían en la Tabla 209. La más '
        'significativa no es una vista sino los dos decoradores que protegen a '
        'todas las demás, porque son el punto único en que se aplica la '
        'autorización del sistema.', a)

    filas = [['Archivo', 'Función o clase', 'Qué hace']]
    for arch, fn, que in [
        ('views.py', 'lista, crear, editar, cambiar_estado',
         'Mantenimiento de usuarios con borrado lógico; cada operación deja '
         'constancia en el historial de auditoría.'),
        ('views.py', 'historial',
         'Consulta del historial de cambios de los usuarios.'),
        ('views.py', 'recuperar_correo, recuperar_pregunta, recuperar_nueva',
         'Recuperación de contraseña en tres pasos mediante la pregunta '
         'secreta, con verificación de la etapa anterior en cada paso.'),
        ('decorators.py', 'modulo_requerido',
         'Restringe una vista a los usuarios cuyo rol tiene acceso al módulo.'),
        ('decorators.py', 'escritura_requerida',
         'Exige acceso al módulo y además que el rol no sea de solo consulta.'),
        ('decorators.py', 'puede_gestionar_odontologo',
         'Permite al profesional administrar la disponibilidad de su propia '
         'ficha, único caso en que un rol de consulta escribe.'),
        ('backends.py', 'EmailBackend.authenticate',
         'Autenticación por correo electrónico con tiempo de respuesta '
         'uniforme.'),
        ('middleware.py', 'NoCacheMiddleware',
         'Impide el almacenamiento en caché de las páginas con sesión.'),
        ('context_processors.py', 'permisos',
         'Expone a todas las plantillas los permisos de escritura del usuario.'),
        ('models.py', 'Rol',
         'Declara el acceso por módulo, la condición de solo consulta y el '
         'permiso de escritura clínica.'),
        ('models.py', 'Usuario.puede, puede_escribir, es_solo_consulta, '
                      'es_admin',
         'Resuelven el acceso y la escritura por módulo para un usuario.'),
        ('models.py', 'Usuario.set_respuesta_secreta, '
                      'check_respuesta_secreta',
         'Guardan y verifican la respuesta de la pregunta secreta cifrada.'),
        ('models.py', 'HistorialUsuario.registrar',
         'Inserta una copia del estado previo del usuario antes de '
         'modificarlo.'),
        ('forms.py', 'UsuarioCrearForm, UsuarioEditarForm',
         'Validan nombres, correo único y contraseña, y aplican los '
         'validadores compartidos del sistema.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 209,
              'Inventario de funciones del módulo de Seguridad y Usuarios', a,
              anchos=[Emu(int(1.3 * P)), Emu(int(1.9 * P)), Emu(int(3.1 * P))])

    a = F.codigo(doc, 'app/usuarios/decorators.py', r'''
def modulo_requerido(modulo):
    """Restringe una vista a los usuarios cuyo rol tiene acceso al módulo."""
    def decorador(vista):
        @wraps(vista)
        def _envuelta(request, *args, **kwargs):
            u = request.user
            if not u.is_authenticated:
                return redirect('login')
            if u.puede(modulo):
                return vista(request, *args, **kwargs)
            raise PermissionDenied('No tiene acceso a este módulo.')
        return _envuelta
    return decorador


def escritura_requerida(modulo):
    """Restringe una vista que modifica información.

    Exige acceso al módulo y, además, que el rol no sea de solo consulta. Se
    aplica a las vistas de alta, edición, cambio de estado y registro de
    tiempos, de modo que la restricción no dependa de ocultar el botón en la
    plantilla: el acceso directo a la dirección también queda denegado.
    """
    def decorador(vista):
        @wraps(vista)
        def _envuelta(request, *args, **kwargs):
            u = request.user
            if not u.puede(modulo):
                raise PermissionDenied('No tiene acceso a este módulo.')
            if u.es_solo_consulta:
                raise PermissionDenied(
                    'Su rol es de solo consulta: no puede modificar información.')
            return vista(request, *args, **kwargs)
        return _envuelta
    return decorador
'''.strip('\n'), a)

    a = F.titulo(doc, '4.2.3.7 Funciones de los módulos de Pacientes y de '
                      'Catálogo', 4, a)
    a = F.parrafo(
        doc,
        'Los dos módulos comparten una característica: su comportamiento es el '
        'mismo para varias entidades. El catálogo administra cuatro '
        '—especialidades, procedimientos, odontólogos y unidades dentales— y '
        'todas se listan, se crean, se editan y se dan de baja igual. En lugar '
        'de escribir cuatro veces el mismo código, las cuatro se resuelven con '
        'vistas genéricas parametrizadas por un diccionario de configuración, '
        'con lo que agregar una quinta entidad al catálogo requiere declararla y '
        'no programarla.', a)
    a = F.codigo(doc, 'app/catalogo/views.py', r'''
# Configuración de cada entidad del catálogo: modelo, formulario y etiquetas.
ENTIDADES = {
    'procedimientos': {
        'modelo': Procedimiento, 'form': ProcedimientoForm,
        'singular': 'procedimiento', 'plural': 'Procedimientos',
        'orden': ['nombre'],
        'busqueda': lambda q: Q(codigo__icontains=q) | Q(nombre__icontains=q),
    },
    'unidades': {
        'modelo': UnidadDental, 'form': UnidadDentalForm,
        'singular': 'unidad dental', 'plural': 'Unidades dentales',
        'orden': ['codigo'],
        'busqueda': lambda q: (Q(codigo__icontains=q) | Q(nombre__icontains=q) |
                               Q(ubicacion__icontains=q)),
    },
    ...
}


@login_required
@modulo_requerido('catalogos')
def lista(request, entidad='procedimientos'):
    cfg = _config(entidad)
    ...
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'Los validadores de los datos de entrada están centralizados en un '
        'módulo compartido por los dos módulos y por el resto del sistema. La '
        'expresión regular de los nombres admite tildes, la letra eñe, '
        'apóstrofos y guiones, de modo que acepte nombres compuestos y '
        'apellidos con guion, y rechace números y caracteres especiales.', a)
    a = F.codigo(doc, 'app/config/validadores.py', r'''
# Letras (con tildes y ñ), espacios, apóstrofos y guiones, para admitir nombres
# compuestos como "María José" o apellidos como "López-García".
NOMBRE_REGEX = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[\s'-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")

# Un código alfanumérico con guiones, por ejemplo PAC-0001 o PROC-014.
CODIGO_REGEX = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]$')


def validar_nombre(valor, etiqueta='nombre'):
    """Rechaza números y caracteres especiales en nombres y apellidos."""
    valor = (valor or '').strip()
    if not valor:
        raise ValidationError(f'El campo {etiqueta} es obligatorio.')
    if not NOMBRE_REGEX.match(valor):
        raise ValidationError(
            f'El {etiqueta} solo puede contener letras y espacios '
            '(no se permiten números ni caracteres especiales).')
    return valor
'''.strip('\n'), a)

    filas = [['Módulo', 'Función', 'Qué hace']]
    for mod, fn, que in [
        ('pacientes', 'lista',
         'Localiza pacientes por código, nombre o teléfono.'),
        ('pacientes', 'crear, editar',
         'Registran y actualizan al paciente con sus datos de identificación y '
         'de contacto.'),
        ('pacientes', 'ficha',
         'Consolida en una vista los datos personales, los antecedentes '
         'médicos y el historial de citas del paciente.'),
        ('pacientes', 'cambiar_estado, quitar_antecedente',
         'Aplican el borrado lógico al paciente y a sus antecedentes.'),
        ('pacientes', '_auditar',
         'Inserta en el historial una copia del estado previo del paciente.'),
        ('pacientes', 'siguiente_codigo',
         'Genera el siguiente código correlativo de paciente.'),
        ('catalogo', 'lista, crear, editar, cambiar_estado',
         'Vistas genéricas que atienden las cuatro entidades del catálogo.'),
        ('catalogo', '_config',
         'Resuelve la configuración de la entidad solicitada y responde con '
         'error cuando no existe.'),
        ('catalogo', 'ProcedimientoForm',
         'Valida el código, el nombre, el precio y la duración de referencia '
         'del procedimiento.'),
        ('catalogo', 'OdontologoForm',
         'Valida los datos del profesional, su número de colegiado y su '
         'vínculo con un usuario del sistema.'),
    ]:
        filas.append([mod, fn, que])
    a = tabla(filas, 210,
              'Inventario de funciones de los módulos de Pacientes y de '
              'Catálogo', a,
              anchos=[Emu(int(1.0 * P)), Emu(int(2.0 * P)), Emu(int(3.3 * P))])

    a = F.titulo(doc, '4.2.3.8 Funciones del módulo de Expediente Clínico', 4, a)
    a = F.parrafo(
        doc,
        'La función más característica del módulo es la que reconstruye el '
        'odontograma vigente. La tabla de hallazgos es de solo agregado: cada '
        'observación se registra con su fecha y no se modifica, de modo que el '
        'expediente conserva la evolución de cada pieza. El estado actual de la '
        'boca es, entonces, el último hallazgo activo de cada combinación de '
        'pieza y cara, y se obtiene recorriendo los registros del más antiguo al '
        'más reciente: cada escritura sobre la misma clave sustituye a la '
        'anterior y, al terminar el recorrido, queda la observación vigente.', a)
    a = F.codigo(doc, 'app/clinico/models.py', r'''
def odontograma_vigente(paciente):
    """Último hallazgo activo de cada pieza y cara del paciente.

    Devuelve {numero_de_pieza: {cara: Hallazgo}}. Al recorrer los registros de
    más antiguo a más reciente, cada escritura sobre la misma clave sustituye a
    la anterior, de modo que al terminar queda la observación vigente.
    """
    vigente = {}
    consulta = (Hallazgo.objects
                .filter(paciente=paciente, estado=True)
                .order_by('fecha', 'creado'))
    for h in consulta:
        vigente.setdefault(h.pieza, {})[h.cara] = h
    return vigente
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La nota clínica de cada visita se vincula con la cita en una relación '
        'uno a uno, lo que impide documentar dos veces la misma atención. Tres '
        'de sus campos —número de piezas tratadas, uso de anestesia y aparición '
        'de complicaciones— cumplen la doble función ya señalada: documentan el '
        'acto clínico y constituyen variables del modelo predictivo. El '
        'inventario del módulo se presenta en la Tabla 211.', a)

    filas = [['Archivo', 'Función o clase', 'Qué hace']]
    for arch, fn, que in [
        ('views.py', 'lista, expediente',
         'Localizan al paciente y presentan su expediente con el odontograma '
         'vigente, los hallazgos pendientes y la última nota.'),
        ('views.py', 'odontograma, quitar_hallazgo',
         'Registran un hallazgo sobre una pieza y una cara, y aplican el '
         'borrado lógico al hallazgo registrado por error.'),
        ('views.py', 'notas, nota_nueva',
         'Presentan la hoja de evolución y registran la nota de una visita '
         'atendida.'),
        ('views.py', '_exigir_escritura_clinica',
         'Verifica el permiso de escritura clínica antes de modificar el '
         'expediente.'),
        ('views.py', '_resumen_odontograma',
         'Cuenta las piezas por tipo de hallazgo para el encabezado del '
         'expediente.'),
        ('models.py', 'Hallazgo',
         'Observación fechada del estado de una pieza; tabla de solo '
         'agregado.'),
        ('models.py', 'Hallazgo.simbolo, clase_css, es_patologico',
         'Traducen el tipo de hallazgo al símbolo y al color con que la pieza '
         'se dibuja, y distinguen los hallazgos por atender.'),
        ('models.py', 'odontograma_vigente',
         'Reconstruye el estado actual de la boca a partir del historial de '
         'hallazgos.'),
        ('models.py', 'NotaClinica',
         'Nota de evolución de una visita, vinculada uno a uno con la cita '
         'atendida.'),
        ('models.py', 'NotaClinica.lista_piezas',
         'Convierte el campo de piezas tratadas en la lista de números de '
         'pieza.'),
        ('piezas.py', 'es_valida, nombre, filas_arcada',
         'Validan el número de pieza según la notación FDI, devuelven su '
         'nombre anatómico y organizan las piezas en los cuatro cuadrantes.'),
        ('forms.py', 'HallazgoForm, NotaClinicaForm',
         'Validan la pieza, la fecha y la coherencia entre el hallazgo y la '
         'visita que lo registra.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 211,
              'Inventario de funciones del módulo de Expediente Clínico', a,
              anchos=[Emu(int(1.0 * P)), Emu(int(2.1 * P)), Emu(int(3.2 * P))])

    a = F.titulo(doc, '4.2.3.9 Funciones de los módulos de Plan de Tratamiento '
                      'y de Cobros', 4, a)
    a = F.parrafo(
        doc,
        'El plan de tratamiento es el punto en que el componente predictivo deja '
        'de resolver una cita aislada. Cada renglón del plan conserva la '
        'duración que el modelo estimó al presupuestarlo, y con esas duraciones '
        'el sistema reparte el trabajo pendiente en sesiones de sillón: agrupa '
        'los renglones respetando el orden de las fases —una fase posterior no '
        'se adelanta— y sin que ninguna sesión exceda las dos horas, que es el '
        'tope razonable en jornadas de cuatro. El resultado es una previsión del '
        'número de visitas que el tratamiento requerirá, disponible antes de '
        'agendar la primera.', a)
    a = F.codigo(doc, 'app/clinico/models.py — método PlanTratamiento.sesiones_sugeridas',
                 r'''
def sesiones_sugeridas(self):
    """Reparte los renglones pendientes en sesiones de sillón.

    Los renglones se agrupan respetando su fase (una fase posterior no se
    adelanta) y sin que ninguna sesión pase de `MINUTOS_SESION_MAX`. Es una
    estimación de planificación, no una reserva: agendar cada sesión sigue
    siendo una decisión de la recepción.
    """
    sesiones = []
    actual, minutos, fase_actual = [], 0, None
    for d in self.renglones.order_by('fase', 'orden', 'id'):
        if d.estado_detalle == 'COMPLETADO':
            continue
        cambia_fase = fase_actual is not None and d.fase != fase_actual
        no_cabe = minutos + d.duracion_estimada_min > MINUTOS_SESION_MAX
        if actual and (cambia_fase or no_cabe):
            sesiones.append({'fase': fase_actual, 'renglones': actual,
                             'minutos': minutos})
            actual, minutos = [], 0
        actual.append(d)
        minutos += d.duracion_estimada_min
        fase_actual = d.fase
    if actual:
        sesiones.append({'fase': fase_actual, 'renglones': actual,
                         'minutos': minutos})
    return sesiones
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'El estado financiero del plan no se almacena: se deriva. El subtotal es '
        'la suma de los importes de los renglones, el total descuenta la '
        'rebaja acordada, lo pagado es la suma de los abonos vigentes y el saldo '
        'es la diferencia. Mantener esas cifras como campos obligaría a '
        'recalcularlas en cada operación que las afecte, y bastaría que una '
        'ruta omitiera el recálculo para que el saldo de un paciente quedara '
        'equivocado. Derivarlas en el momento de leerlas hace imposible esa '
        'inconsistencia; la anulación de un abono, además, no borra el registro, '
        'sino que lo marca como inactivo, con lo que el saldo se corrige y la '
        'trazabilidad del cobro se conserva.', a)
    a = F.codigo(doc, 'app/clinico/models.py — clase PlanTratamiento', r'''
@property
def subtotal(self):
    return sum((d.importe for d in self.renglones), Decimal('0.00'))

@property
def total(self):
    return max(Decimal('0.00'),
               self.subtotal - (self.descuento or Decimal('0.00')))

@property
def pagado(self):
    return sum((p.monto for p in self.pagos.filter(estado=True)),
               Decimal('0.00'))

@property
def saldo(self):
    return self.total - self.pagado
'''.strip('\n'), a)

    filas = [['Archivo', 'Función o clase', 'Qué hace']]
    for arch, fn, que in [
        ('views.py', 'planes, plan_nuevo, plan_detalle',
         'Listan los planes, crean uno nuevo y presentan su detalle con fases, '
         'renglones, sesiones sugeridas y estado financiero.'),
        ('views.py', 'plan_estado',
         'Mueve el plan entre propuesto, aprobado, en curso, finalizado y '
         'anulado, registrando el cambio en el historial.'),
        ('views.py', 'plan_quitar_detalle',
         'Aplica el borrado lógico a un renglón del plan.'),
        ('views.py', 'agendar_renglon',
         'Lleva al formulario de cita con el paciente, el procedimiento y la '
         'duración estimada del renglón ya definidos.'),
        ('views.py', 'cobros, anular_pago',
         'Presentan el estado de cobro de los planes aprobados y anulan un '
         'abono sin eliminar su registro.'),
        ('models.py', 'PlanTratamiento.sesiones_sugeridas',
         'Reparte los renglones pendientes en sesiones que no exceden las dos '
         'horas, respetando las fases.'),
        ('models.py', 'PlanTratamiento.subtotal, total, pagado, saldo',
         'Derivan el estado financiero del plan a partir de sus renglones y '
         'abonos vigentes.'),
        ('models.py', 'PlanTratamiento.actualizar_avance',
         'Mueve el plan a en curso o finalizado según sus renglones '
         'completados.'),
        ('models.py', 'PlanTratamiento.minutos_estimados, minutos_pendientes',
         'Suman los minutos de sillón del plan completo y de lo que resta.'),
        ('models.py', 'PlanTratamiento.siguiente_codigo',
         'Genera el código correlativo del plan.'),
        ('models.py', 'DetallePlan.importe, etiqueta_origen',
         'Calculan el importe del renglón y declaran de qué fuente proviene su '
         'duración estimada.'),
        ('models.py', 'Pago, HistorialPlan.registrar',
         'Registran los abonos aplicados al plan y el historial de cambios de '
         'estado.'),
        ('forms.py', 'DetallePlanForm',
         'Propone la tarifa del catálogo y la duración estimada por el modelo '
         'al agregar un renglón.'),
        ('forms.py', 'PagoForm',
         'Valida que el abono sea positivo y no exceda el saldo del plan.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 212,
              'Inventario de funciones de los módulos de Plan de Tratamiento y '
              'de Cobros', a,
              anchos=[Emu(int(1.0 * P)), Emu(int(2.2 * P)), Emu(int(3.1 * P))])

    a = F.titulo(doc, '4.2.3.10 Funciones del módulo de Inteligencia', 4, a)
    a = F.parrafo(
        doc,
        'El módulo de inteligencia se divide en dos partes que no comparten '
        'proceso. El servicio de estimación, documentado en la sección 4.2.3.2, '
        'opera dentro del proceso web y solo lee el modelo. El entrenamiento '
        'opera fuera de él, como un comando administrativo, por la razón de '
        'memoria expuesta en la sección 4.1.2.2.', a)
    a = F.parrafo(
        doc,
        'El entrenamiento construye una tubería de procesamiento que serializa '
        'en un solo objeto la codificación de las variables categóricas y el '
        'estimador. Las tres variables categóricas —procedimiento, odontólogo y '
        'día de la semana— se codifican como variables indicadoras, con la '
        'instrucción de ignorar las categorías no vistas en el entrenamiento, de '
        'modo que un procedimiento nuevo no provoque un error al estimar. Las '
        'cuatro numéricas pasan sin transformación.', a)
    a = F.codigo(doc, 'app/inteligencia/entrenamiento.py', r'''
CATEGORICAS = ['procedimiento', 'odontologo', 'dia_semana']
NUMERICAS = ['hora_inicio', 'num_piezas', 'anestesia', 'complicacion']


def _construir(algoritmo):
    preparacion = ColumnTransformer([
        ('categoricas', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS),
        ('numericas', 'passthrough', NUMERICAS),
    ])
    if algoritmo == 'RF':
        estimador = RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1)
    else:
        estimador = LinearRegression()
    return Pipeline([('preparacion', preparacion), ('estimador', estimador)])
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'El entrenamiento reserva la cuarta parte del conjunto para evaluar y no '
        'entrena con ella. Además de las tres métricas habituales, calcula el '
        'error de una línea base —estimar siempre el promedio global— porque es '
        'contra ella y no contra cero como se juzga si el modelo aporta algo. Un '
        'modelo con error de cinco minutos es excelente si la línea base se '
        'equivoca en diecisiete y mediocre si se equivoca en seis.', a)
    a = F.codigo(doc, 'app/inteligencia/entrenamiento.py — función entrenar', r'''
df = pd.DataFrame(filas)
X = df.drop(columns=['duracion_real_min'])
y = df['duracion_real_min']
X_ent, X_pru, y_ent, y_pru = train_test_split(
    X, y, test_size=PROPORCION_PRUEBA, random_state=42)

pipe = _construir(algoritmo)
inicio = time.perf_counter()
pipe.fit(X_ent, y_ent)
segundos = time.perf_counter() - inicio

prediccion = pipe.predict(X_pru)
# Línea base: estimar siempre el promedio global. Es contra lo que se mide
# si el modelo aporta algo.
base = [y_ent.mean()] * len(y_pru)

resultado = Resultado(
    algoritmo=algoritmo,
    mae=round(float(mean_absolute_error(y_pru, prediccion)), 2),
    rmse=round(float(mean_squared_error(y_pru, prediccion) ** 0.5), 2),
    r2=round(float(r2_score(y_pru, prediccion)), 3),
    registros=len(df), registros_prueba=len(y_pru),
    mae_base=round(float(mean_absolute_error(y_pru, base)), 2),
    segundos=round(segundos, 3))
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La Tabla 213 presenta el resultado del entrenamiento de los dos '
        'algoritmos implementados sobre el conjunto de 446 atenciones '
        'registradas en el sistema, de las cuales 112 se reservaron para '
        'evaluar. Las dos reducen el error de la línea base en más de setenta '
        'por ciento, de modo que la hipótesis de trabajo se cumple con '
        'cualquiera de ellas; el bosque aleatorio lo reduce más, a costa de un '
        'archivo unas doscientas setenta veces mayor y de un entrenamiento treinta '
        'veces más largo. Ninguno de los dos costos resulta limitante en esta '
        'escala, por lo que el bosque aleatorio es el que opera en producción.', a)

    filas = [['Métrica', 'Regresión lineal múltiple', 'Bosque aleatorio']]
    for m, lin, rf in [
        ('Error absoluto medio (MAE)', '4.81 minutos', '3.58 minutos'),
        ('Raíz del error cuadrático medio (RMSE)', '6.11 minutos',
         '4.73 minutos'),
        ('Coeficiente de determinación (R²)', '0.908', '0.945'),
        ('MAE de la línea base (promedio global)', '16.55 minutos',
         '16.55 minutos'),
        ('Reducción del error frente a la línea base', '70.9 %', '78.4 %'),
        ('Tiempo de entrenamiento', '0.007 segundos', '0.230 segundos'),
        ('Tamaño del archivo serializado', '1.9 KB', '510.2 KB'),
        ('Registros de entrenamiento / de prueba', '334 / 112', '334 / 112'),
    ]:
        filas.append([m, lin, rf])
    a = tabla(filas, 213,
              'Resultado del entrenamiento de los dos algoritmos implementados '
              'sobre 446 atenciones registradas', a,
              anchos=[Emu(int(2.6 * P)), Emu(int(1.9 * P)), Emu(int(1.8 * P))])

    a = F.parrafo(
        doc,
        'El bosque aleatorio permite, además, examinar el peso de cada variable '
        'en la predicción, que la Tabla 214 presenta. El resultado tiene una '
        'consecuencia metodológica directa: las tres variables de mayor peso son '
        'el número de piezas tratadas, el tipo de procedimiento y el uso de '
        'anestesia, y dos de ellas provienen de la nota clínica de la visita y '
        'no de la cita. Es la justificación empírica de haber incorporado el '
        'módulo de expediente clínico al sistema: las variables que aporta la nota '
        'de evolución reúnen el 60.7 % del peso del modelo, de modo que sin ella '
        'la estimación tendría que renunciar a la mayor parte de lo que hoy le '
        'permite acertar.', a)

    filas = [['Variable', 'Peso en el modelo', 'Procedencia del dato']]
    for v, peso, orig in [
        ('Número de piezas tratadas', '43.6 %', 'Nota clínica de la visita'),
        ('Procedimiento: tratamiento de conducto', '21.1 %', 'Cita'),
        ('Uso de anestesia', '15.2 %', 'Nota clínica de la visita'),
        ('Procedimiento: colocación de brackets', '7.8 %', 'Cita'),
        ('Procedimiento: retiro de brackets', '3.7 %', 'Cita'),
        ('Aparición de complicaciones', '1.9 %', 'Nota clínica de la visita'),
        ('Hora de inicio de la cita', '1.2 %', 'Cita'),
        ('Odontólogo que atiende', '0.9 %', 'Cita'),
    ]:
        filas.append([v, peso, orig])
    a = tabla(filas, 214,
              'Peso de cada variable en el modelo de bosque aleatorio y '
              'procedencia del dato', a,
              anchos=[Emu(int(2.8 * P)), Emu(int(1.4 * P)), Emu(int(2.1 * P))])

    a = F.parrafo(
        doc,
        'El versionado conserva el histórico completo de los entrenamientos. '
        'Cada versión registra su algoritmo, sus métricas y la ruta de su '
        'archivo, y una sola está activa a la vez; las demás se conservan para '
        'poder comparar y, en caso necesario, volver a una anterior. El comando '
        'admite una opción que condiciona la activación a que la versión nueva '
        'reduzca el error de la vigente, de modo que un reentrenamiento con '
        'datos de mala calidad no degrade la estimación en producción.', a)
    a = F.codigo(doc, 'Comando de entrenamiento', r'''
python manage.py entrenar --algoritmo RF --activar
python manage.py entrenar --algoritmo RF --solo-si-mejora
python manage.py entrenar --algoritmo LINEAL
'''.strip('\n'), a)
    a = F.codigo(doc, 'app/inteligencia/entrenamiento.py — función activar_version',
                 r'''
def activar_version(version):
    """Pone una versión en producción y retira la anterior.

    Solo una versión está activa a la vez; las demás se conservan para poder
    comparar y, en caso necesario, volver atrás.
    """
    ModeloVersion.objects.filter(activo=True).exclude(
        pk=version.pk).update(activo=False)
    version.activo = True
    version.save(update_fields=['activo'])
    limpiar_cache()
    return version
'''.strip('\n'), a)

    filas = [['Archivo', 'Función', 'Qué hace']]
    for arch, fn, que in [
        ('servicio.py', 'estimar_duracion',
         'Punto único de entrada de la estimación; aplica la cadena de respaldo '
         'de tres niveles.'),
        ('servicio.py', '_estimar_con_modelo',
         'Arma el registro de entrada y solicita la predicción al modelo '
         'entrenado.'),
        ('servicio.py', '_estimar_con_historico',
         'Promedia la duración real de las atenciones previas, prefiriendo las '
         'del mismo profesional cuando hay al menos tres.'),
        ('servicio.py', '_cargar, limpiar_cache',
         'Conservan el modelo en memoria entre peticiones y lo descartan al '
         'activarse otra versión.'),
        ('servicio.py', '_anestesia_habitual',
         'Deduce el uso habitual de anestesia del procedimiento, que al agendar '
         'todavía no se conoce.'),
        ('servicio.py', '_redondear, _bloque_recomendado',
         'Redondean la estimación a múltiplos de cinco minutos y calculan el '
         'rango recomendado del 85 % al 120 %.'),
        ('servicio.py', 'registrar_prediccion',
         'Guarda la predicción emitida para contrastarla después con la '
         'duración real.'),
        ('servicio.py', 'registrar_dato_entrenamiento',
         'Incorpora una cita atendida al conjunto de entrenamiento.'),
        ('entrenamiento.py', 'reunir_datos',
         'Construye el conjunto de entrenamiento a partir de las citas '
         'atendidas y de sus notas clínicas.'),
        ('entrenamiento.py', '_construir',
         'Arma la tubería de codificación y estimación del algoritmo '
         'solicitado.'),
        ('entrenamiento.py', 'entrenar',
         'Entrena, evalúa contra la línea base y serializa el modelo; devuelve '
         'sus métricas.'),
        ('entrenamiento.py', '_importancias',
         'Calcula el peso relativo de cada variable en el bosque aleatorio.'),
        ('entrenamiento.py', 'registrar_version, activar_version',
         'Registran la versión entrenada y la ponen en producción retirando la '
         'anterior.'),
        ('commands/entrenar.py', 'Command.handle',
         'Comando administrativo que ejecuta el entrenamiento fuera del proceso '
         'web, con las opciones de algoritmo, activación y activación '
         'condicionada a la mejora.'),
        ('views.py', 'panel, activar, _desempeno_vigente',
         'Presentan las versiones entrenadas con sus métricas, el contraste '
         'entre la duración del catálogo y la real, y permiten activar una '
         'versión.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 215,
              'Inventario de funciones del módulo de Inteligencia', a,
              anchos=[Emu(int(1.3 * P)), Emu(int(1.9 * P)), Emu(int(3.1 * P))])

    a = F.titulo(doc, '4.2.3.11 Funciones del módulo de Reportes', 4, a)
    a = F.parrafo(
        doc,
        'El módulo de reportes separa el cálculo de la presentación: un módulo '
        'de servicio produce las cifras y la vista únicamente las entrega a la '
        'plantilla. Esa separación permite que las mismas cifras se consuman '
        'desde la pantalla y desde las verificaciones automatizadas sin '
        'duplicar la consulta. El inventario se presenta en la Tabla 216.', a)

    filas = [['Archivo', 'Función', 'Qué hace']]
    for arch, fn, que in [
        ('servicio.py', 'rango, _dias_habiles',
         'Resuelven el período solicitado y la lista de días hábiles que '
         'contiene.'),
        ('servicio.py', 'resumen',
         'Calcula las cifras globales del período: citas, atenciones, '
         'cancelaciones, horas de sillón, utilización y error medio entre lo '
         'asignado y lo real.'),
        ('servicio.py', 'atenciones_por_semana',
         'Serie de atenciones y cancelaciones por semana.'),
        ('servicio.py', 'carga_por_odontologo',
         'Horas atendidas y utilización por profesional.'),
        ('servicio.py', 'procedimientos_frecuentes',
         'Procedimientos más realizados en el período.'),
        ('servicio.py', 'precision_por_procedimiento',
         'Contrasta la duración del catálogo, la asignada y la real por '
         'procedimiento, y ordena por la magnitud de la desviación.'),
        ('servicio.py', 'ocupacion_por_hora',
         'Distribución de las atenciones por hora de la jornada.'),
        ('views.py', 'panel',
         'Reúne los siete cálculos, serializa las series para las gráficas y '
         'entrega el conjunto a la plantilla.'),
    ]:
        filas.append([arch, fn, que])
    a = tabla(filas, 216, 'Inventario de funciones del módulo de Reportes', a,
              anchos=[Emu(int(1.1 * P)), Emu(int(2.0 * P)), Emu(int(3.3 * P))])

    a = F.parrafo(
        doc,
        'La función más importante del módulo es la que contrasta la duración de '
        'referencia del catálogo con la que la clínica tarda realmente. Es la '
        'cifra que sustenta el componente predictivo, porque identifica los '
        'procedimientos en que la duración de referencia se aleja de la '
        'realidad, que son aquellos donde la estimación aporta más. La función '
        'excluye los procedimientos con menos de tres atenciones medidas, para '
        'no reportar como desviación lo que es ruido de una muestra pequeña, y '
        'ordena el resultado por la magnitud de la desviación relativa, de modo '
        'que lo que más se aparta aparezca primero.', a)
    a = F.codigo(doc, 'app/reportes/servicio.py — función precision_por_procedimiento',
                 r'''
def precision_por_procedimiento(desde, hasta):
    """Contraste entre la duración del catálogo, la asignada y la real."""
    filas = []
    for proc in Procedimiento.objects.filter(estado=True).order_by('nombre'):
        base = Cita.objects.filter(
            procedimiento=proc, fecha__range=(desde, hasta), estado=True,
            estado_cita='ATENDIDA', duracion_real_min__isnull=False)
        n = base.count()
        if n < MINIMO_PARA_PROMEDIO:
            continue
        agregado = base.aggregate(real=Avg('duracion_real_min'),
                                  asignado=Avg('duracion_asignada_min'))
        real = round(agregado['real'], 1)
        catalogo = proc.duracion_promedio_min
        filas.append({
            'nombre': proc.nombre, 'catalogo': catalogo,
            'asignado': round(agregado['asignado'], 1), 'real': real,
            'desvio': round(real - catalogo, 1),
            'desvio_pct': round((real - catalogo) / catalogo * 100, 1)
                          if catalogo else 0,
            'atenciones': n,
        })
    return sorted(filas, key=lambda f: abs(f['desvio_pct']), reverse=True)
'''.strip('\n'), a)

    # ══════════════════ 4.2.4 ejemplo de gráficas y reportes ═══════════════════
    a = F.titulo(doc, '4.2.4 Ejemplo de gráficas y reportes', 3, a)
    a = F.parrafo(
        doc,
        'El panel de reportes (Figura 312) reúne en una sola pantalla los '
        'indicadores del período, tres gráficas y dos tablas. El período es '
        'filtrable entre cuatro, ocho, doce y veintiséis semanas, y el conjunto '
        'completo se recalcula con la selección.', a)
    a = fig('25_reportes.png', 312,
            'Panel de reportes e indicadores del sistema (datos de '
            'demostración)', a)
    a = F.parrafo(
        doc,
        'La gráfica central del panel es la que contrasta la duración de '
        'referencia del catálogo con la duración real promedio de cada '
        'procedimiento. Su lectura es directa: donde ambas barras coinciden, la '
        'duración del catálogo basta; donde se separan, el bloque reservado se '
        'queda corto o sobra, y es ahí donde la estimación del modelo aporta. '
        'Sobre los datos de demostración, la resina compuesta excede en 24.0 % '
        'su duración de referencia, la limpieza profunda por cuadrante en 23.4 % '
        'y el sellante en 20.4 %, lo que confirma el problema que el proyecto '
        'plantea: la duración declarada en el catálogo subestima '
        'sistemáticamente el tiempo real de varios procedimientos.', a)
    a = F.parrafo(
        doc,
        'La implementación de las gráficas sigue un principio: el servidor '
        'produce datos y el navegador los dibuja. La vista serializa cada serie '
        'a JSON y la plantilla la deposita en la página mediante la etiqueta '
        'json_script del framework, que escapa el contenido de modo que un dato '
        'con caracteres especiales no pueda cerrar la etiqueta e inyectar '
        'código.', a)
    a = F.codigo(doc, 'app/reportes/views.py — función panel', r'''
@login_required
@modulo_requerido('reportes')
def panel(request):
    semanas = request.GET.get('semanas', '8')
    semanas = int(semanas) if semanas.isdigit() and int(semanas) in SEMANAS else 8
    desde, hasta = servicio.rango(semanas)

    precision = servicio.precision_por_procedimiento(desde, hasta)
    contexto = {
        'semanas': semanas, 'opciones': SEMANAS,
        'desde': desde, 'hasta': hasta,
        'resumen': servicio.resumen(desde, hasta),
        'carga': servicio.carga_por_odontologo(desde, hasta),
        'frecuentes': servicio.procedimientos_frecuentes(desde, hasta),
        'precision': precision,
        'serie_semanal': json.dumps(servicio.atenciones_por_semana(desde, hasta)),
        'serie_horas': json.dumps(servicio.ocupacion_por_hora(desde, hasta)),
        'serie_precision': json.dumps({
            'etiquetas': [f['nombre'] for f in precision],
            'catalogo': [f['catalogo'] for f in precision],
            'real': [f['real'] for f in precision],
        }),
        'generado': timezone.localtime(),
    }
    return render(request, 'reportes/panel.html', contexto)
'''.strip('\n'), a)
    a = F.codigo(doc, 'app/templates/reportes/panel.html', r'''
{{ serie_semanal|json_script:"d-semanal" }}
{{ serie_precision|json_script:"d-precision" }}
{{ serie_horas|json_script:"d-horas" }}

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
(function () {
  if (typeof Chart === 'undefined') return;

  const SERIE_1 = '#2a78d6';
  const SERIE_2 = '#eb6834';
  const leer = (id) => JSON.parse(JSON.parse(
      document.getElementById(id).textContent));

  const precision = leer('d-precision');
  new Chart(document.getElementById('g-precision'), {
    type: 'bar',
    data: {
      labels: precision.etiquetas,
      datasets: [
        { label: 'Duración del catálogo', data: precision.catalogo,
          backgroundColor: SERIE_1, borderRadius: 4, maxBarThickness: 14 },
        { label: 'Duración real promedio', data: precision.real,
          backgroundColor: SERIE_2, borderRadius: 4, maxBarThickness: 14 },
      ],
    },
    options: Object.assign({}, comunes, { indexAxis: 'y', ... }),
  });
})();
</script>
'''.strip('\n'), a)
    a = F.parrafo(
        doc,
        'La primera línea del bloque de script comprueba que la biblioteca de '
        'gráficas se haya cargado antes de usarla. Sin esa comprobación, un '
        'servidor sin salida a internet —o una red de distribución de contenido '
        'momentáneamente inaccesible— produciría un error de JavaScript que '
        'detendría la ejecución del resto del script de la página. Con ella, la '
        'pantalla pierde las gráficas pero conserva los indicadores y las '
        'tablas, que es la degradación aceptable.', a)
    a = F.parrafo(
        doc,
        'Esa consideración se extiende al diseño de todo el panel: cada gráfica '
        'tiene junto a sí la tabla con los mismos datos. La decisión atiende tres '
        'situaciones distintas con una sola medida. La primera es la señalada: '
        'si la biblioteca no carga, la información sigue disponible. La segunda '
        'es la lectura precisa, porque de una barra se estima una magnitud pero '
        'no se lee un valor exacto. La tercera es la accesibilidad: las dos '
        'series de las gráficas se distinguen por color, y la tabla garantiza '
        'que la información no dependa únicamente de esa distinción. Los dos '
        'colores empleados —un azul y un naranja— se seleccionaron verificando '
        'que conserven contraste suficiente entre sí bajo las formas más '
        'frecuentes de visión cromática deficiente.', a)
    a = F.parrafo(
        doc,
        'El panel del módulo de inteligencia (Figura 313) aplica el mismo '
        'patrón a la información del modelo: presenta el error del modelo frente '
        'al error del catálogo, el coeficiente de determinación, el número de '
        'registros de entrenamiento, el histórico de versiones entrenadas con '
        'sus métricas y la documentación de la cadena de estimación. Es la '
        'pantalla desde la que se activa una versión del modelo y la única '
        'reservada al rol de administrador.', a)
    a = fig('26_inteligencia.png', 313,
            'Panel del módulo de Inteligencia con las métricas del modelo y el '
            'histórico de versiones (datos de demostración)', a)

    doc.save(str(C.ARCHIVO))
    print('4.2 agregada.')


if __name__ == '__main__':
    main()
