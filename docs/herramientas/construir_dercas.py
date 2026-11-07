"""Reescribe la sección 3.1.1.2 (DERCAS) siguiendo la plantilla DERCAS Visión.

Reemplaza por completo el contenido comprendido entre el encabezado
«3.1.1.2 Delimitación (DERCAS)» y «3.1.2 Análisis de la solución».

Las tablas nuevas se numeran provisionalmente a partir de 100 para que ningún
rótulo se repita; una pasada posterior renumera todo el documento en orden de
aparición y corrige las referencias del texto.
"""
import sys

from docx import Document
from docx.shared import Emu, Pt

sys.path.insert(0, '.')
import formato as F                                                # noqa: E402
from requerimientos import MODULOS, REQUERIMIENTOS, por_modulo     # noqa: E402

ARCHIVO = '../mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx'
NUM = 100


def siguiente():
    global NUM
    NUM += 1
    return NUM - 1


def main():
    doc = Document(ARCHIVO)
    seccion = doc.sections[0]
    util = seccion.page_width - seccion.left_margin - seccion.right_margin

    inicio = fin = None
    for p in doc.paragraphs:
        t = p.text.strip()
        if t == '3.1.1.2 Delimitación (DERCAS)':
            inicio = p._p
        elif t == '3.1.2 Análisis de la solución':
            fin = p._p
            break
    if inicio is None or fin is None:
        raise SystemExit('No se localizaron los límites de la sección.')

    borrados = F.eliminar_rango(inicio, fin)
    print(f'Elementos reemplazados: {borrados}')

    a = inicio  # ancla: cada elemento nuevo se inserta después del anterior

    def p(texto, **kw):
        nonlocal a
        a = F.parrafo(doc, texto, a, **kw)
        return a

    def vinheta(texto):
        nonlocal a
        a = F.parrafo(doc, '•\t' + texto, a, sangria=False)
        a.paragraph_format.left_indent = Pt(36)
        a.paragraph_format.space_after = Pt(2)
        return a

    def tab(filas, titulo_pie, anchos, col_etiqueta=None):
        nonlocal a
        t = F.tabla(doc, filas, a, anchos=anchos, col_etiqueta=col_etiqueta)
        a = F.pie(doc, f'Tabla {siguiente()}', titulo_pie, t._tbl)
        return t

    def frac(*partes):
        total = sum(partes)
        return [Emu(int(util * x / total)) for x in partes]

    # ─────────────────────────────── introducción ───────────────────────────────
    p('El documento de especificación de requerimientos y criterios de aceptación '
      'de software (DERCAS) delimita qué construye el sistema, qué queda fuera de '
      'su alcance y bajo qué condiciones se considera aceptado. La presente '
      'sección sigue la estructura del DERCAS Visión adoptada por la carrera: '
      'antecedentes del problema con su impacto y sus beneficios, descripción de '
      'la problemática, alcance, funcionalidad requerida desglosada por módulo, '
      'limitantes, requerimientos no funcionales y de documentación, y cuadro de '
      'aceptación.')

    # ─────────────────────────────── antecedentes ───────────────────────────────
    p('Antecedentes. La Clínica Dental Smilee administra su agenda mediante un '
      'libro de citas en papel. La recepción asigna a cada tratamiento un bloque '
      'de tiempo estimado a partir de la experiencia del personal, sin distinguir '
      'el tipo de procedimiento, el número de piezas por tratar ni el ritmo de '
      'trabajo de cada profesional. La clínica no dispone de ningún sistema '
      'informático de gestión, de modo que la información de pacientes, '
      'procedimientos y atenciones se encuentra dispersa entre el libro de citas, '
      'las fichas individuales y el conocimiento no documentado del personal.')

    p('Impacto. La ausencia de una herramienta informática que apoye la '
      'planificación de la agenda produce los siguientes efectos sobre la '
      'operación de la clínica:')
    for texto in [
        'Retrasos acumulados a lo largo de la jornada, originados en bloques de '
        'tiempo asignados por debajo de la duración real del procedimiento.',
        'Tiempos muertos entre atenciones cuando el bloque asignado excede la '
        'duración real, con la consiguiente subutilización de los sillones.',
        'Reprogramación reactiva de citas, que traslada el retraso a los pacientes '
        'siguientes y ocupa al personal de recepción en tareas correctivas.',
        'Imposibilidad de verificar la disponibilidad real de un profesional sin '
        'consultar físicamente el libro de citas.',
        'Redundancia e inconsistencia de los datos del paciente, registrados en '
        'más de un lugar y sin un criterio común.',
        'Ausencia de registro histórico, que impide evaluar el desempeño de la '
        'operación o sustentar cualquier mejora en evidencia.',
    ]:
        vinheta(texto)

    p('Beneficio. La implantación del sistema aporta a la clínica un conjunto de '
      'beneficios directos:', espacio_antes=6)
    for texto in [
        'Centralización en un solo sistema de la información de usuarios, '
        'pacientes, catálogo, agenda y expediente clínico.',
        'Estimación de la duración de cada procedimiento a partir de las '
        'atenciones realmente registradas, y no de un promedio general.',
        'Recomendación automática del bloque de tiempo y de los espacios del '
        'calendario donde el procedimiento cabe completo.',
        'Control de la capacidad real de atención, derivada del número de '
        'unidades dentales activas y no solo de la disponibilidad del profesional.',
        'Trazabilidad de las operaciones mediante historiales de auditoría y '
        'borrado lógico en todas las entidades.',
        'Indicadores de desempeño que permiten evaluar la utilización de la '
        'agenda y la precisión del componente predictivo.',
        'Mejora progresiva de la estimación conforme la clínica acumula '
        'atenciones registradas.',
    ]:
        vinheta(texto)

    # ────────────────────────── descripción del problema ──────────────────────────
    p('Descripción del problema. La Tabla 100 sintetiza la problemática que da '
      'origen al proyecto, la población afectada, las consecuencias de no '
      'atenderla y las características que debe reunir una solución exitosa.',
      espacio_antes=6)
    tab([
        ['Aspecto', 'Descripción'],
        ['¿Cuál es el problema?',
         'La Clínica Dental Smilee asigna los tiempos de atención de su agenda '
         'utilizando promedios generales y criterios empíricos, sin considerar el '
         'tipo de tratamiento, el historial del paciente ni el odontólogo '
         'responsable. Ello ocasiona retrasos acumulados a lo largo de la jornada, '
         'tiempos muertos que reducen la productividad y una experiencia deficiente '
         'para el paciente. Adicionalmente, la información de la clínica se '
         'encuentra dispersa y no sistematizada, por lo que no existe registro '
         'histórico que permita analizar el comportamiento real de los tiempos de '
         'atención.'],
        ['¿A quiénes afecta?',
         'A los pacientes de la clínica, que experimentan esperas prolongadas; a '
         'los odontólogos, cuyo tiempo productivo se desaprovecha; al personal de '
         'recepción, que reprograma citas de forma reactiva; y al propietario, que '
         'carece de información objetiva sobre el desempeño de su operación.'],
        ['¿Cuál es el impacto de no resolverlo?',
         'Persistencia de retrasos frecuentes, baja utilización del tiempo '
         'disponible, pérdida de ingresos por espacios improductivos, '
         'insatisfacción del paciente con la consiguiente pérdida de fidelización, '
         'y ausencia de datos históricos que impide cualquier mejora sustentada en '
         'evidencia.'],
        ['¿Qué beneficios aporta la solución?',
         'Centralización de la información en un único sistema; estimación de la '
         'duración de los procedimientos a partir de datos históricos reales; '
         'recomendación automática de bloques de tiempo; trazabilidad completa de '
         'las operaciones mediante historiales de auditoría; e indicadores de '
         'desempeño que respaldan la toma de decisiones administrativas.'],
        ['¿Cómo debe ser una solución exitosa?',
         'Un sistema web centralizado, accesible desde los equipos con que ya '
         'cuenta la clínica, que administre usuarios, pacientes, catálogo, agenda y '
         'expediente clínico con control de acceso por rol, y que incorpore un '
         'modelo predictivo capaz de estimar la duración de cada procedimiento y '
         'sugerir el bloque de tiempo adecuado, mejorando su precisión conforme se '
         'acumulen datos.'],
    ], 'Descripción del problema', frac(1, 3), col_etiqueta=0)

    # ──────────────────────────────── alcance ────────────────────────────────
    p('Alcance del sistema. SmileeSync comprende ocho módulos funcionales: '
      'Seguridad y Usuarios, Pacientes, Catálogo Odontológico, Agenda y Citas, '
      'Expediente Clínico, Cobros, Inteligencia y Reportes e Indicadores. El '
      'módulo principal del proyecto es el de Agenda y Citas, sobre el cual opera '
      'el componente predictivo que constituye el aporte central del trabajo. '
      'El sistema se despliega como una aplicación web accesible desde los '
      'equipos con que la clínica ya cuenta, sin requerir instalación local.')

    p('Exclusiones. No forman parte del alcance de este proyecto la facturación '
      'electrónica en línea, que en Guatemala exige la certificación de un '
      'proveedor autorizado por la administración tributaria; la integración con '
      'equipos de radiología o con dispositivos de diagnóstico por imagen; el '
      'control de inventario de insumos odontológicos; el portal de '
      'autoagendamiento para pacientes; y la aplicación móvil nativa, puesto que '
      'la interfaz web es responsiva y opera desde cualquier navegador.')

    # ─────────────────────────── funcionalidad requerida ───────────────────────────
    total_req = len(REQUERIMIENTOS)
    total_func = sum(len(r[4]) for r in REQUERIMIENTOS)
    p(f'Funcionalidad requerida. El sistema comprende {total_req} requerimientos '
      f'funcionales, que en conjunto agrupan {total_func} funcionalidades. Cada '
      f'requerimiento se identifica con una nomenclatura que incorpora el módulo '
      f'al que pertenece, de la forma REQ-XXX-NN, donde XXX corresponde al '
      f'prefijo del módulo y NN al correlativo dentro de él. La clasificación por '
      f'prioridad responde a un criterio explícito: se califica como alta aquel '
      f'requerimiento sin el cual el sistema no puede operar, lo que comprende la '
      f'autenticación, el control de acceso y el ciclo completo de la cita; como '
      f'media, el que aporta valor operativo comprobable pero puede diferirse sin '
      f'detener la atención; y como baja, el que mejora la gestión sin '
      f'condicionar la operación diaria. La Tabla 101 presenta el resumen por '
      f'módulo y las tablas siguientes detallan cada requerimiento.',
      espacio_antes=6)

    filas = [['Módulo', 'ID', 'Nombre del requerimiento', 'Prioridad']]
    for prefijo, nombre, _, propios in por_modulo():
        for i, (rid, rnombre, prioridad, _ref, _f) in enumerate(propios):
            filas.append([nombre if i == 0 else '', rid, rnombre, prioridad])
    tab(filas, 'Resumen de requerimientos funcionales por módulo',
        frac(3, 2, 5, 1.6))

    for prefijo, nombre, descripcion, propios in por_modulo():
        altas = sum(1 for r in propios if r[2] == 'Alta')
        p(f'Módulo de {nombre}. {descripcion} Comprende {len(propios)} '
          f'requerimiento{"s" if len(propios) != 1 else ""}'
          + (f', de los cuales {altas} son de prioridad alta.' if altas else '.'),
          espacio_antes=10)

        for rid, rnombre, prioridad, referencia, funciones in propios:
            filas = [
                ['Id. Requerimiento', rid, 'Clasificación o prioridad', prioridad],
                ['Nombre Requerimiento', rnombre, 'Módulo', nombre],
                ['Referencia', referencia, 'Funcionalidades', str(len(funciones))],
                ['No. Func.', 'Funcionalidad', '', ''],
            ]
            for i, texto in enumerate(funciones, start=1):
                filas.append([f'{i:03d}', texto, '', ''])
            t = F.tabla(doc, filas, a, anchos=frac(2.2, 4.2, 2.4, 2.0),
                        encabezado=False, col_etiqueta=0)

            # Las tres primeras filas son la ficha del requerimiento: la tercera
            # columna también rotula, y la cuarta fila encabeza el desglose.
            from docx.oxml.ns import qn
            for i in range(3):
                F._escribir(t.cell(i, 2), filas[i][2], negrita=True)
                F._sombrear(t.cell(i, 2), 'F1F5F9')
            for j in range(4):
                F._escribir(t.cell(3, j), filas[3][j], negrita=True,
                            color='FFFFFF')
                F._sombrear(t.cell(3, j), F.AZUL)
            # El desglose ocupa el ancho completo a partir de la segunda columna.
            for i in range(3, len(filas)):
                t.cell(i, 1).merge(t.cell(i, 3))

            a = F.pie(doc, f'Tabla {siguiente()}',
                      f'Requerimiento {rid} — {rnombre}', t._tbl)

    # ──────────────────────── limitantes y restricciones ────────────────────────
    p('Limitantes y restricciones. El proyecto se encuentra condicionado por '
      'cinco factores. El primero, y de mayor peso sobre el componente '
      'predictivo, es que la clínica no dispone de un registro digital previo de '
      'duraciones, por lo que el modelo parte de la duración de referencia del '
      'catálogo y mejora conforme se acumulan atenciones reales. El segundo es la '
      'capacidad física instalada: la clínica cuenta con dos unidades dentales '
      'compartidas por los profesionales, lo que limita la atención simultánea con '
      'independencia del número de odontólogos disponibles. El tercero es el '
      'presupuesto de infraestructura, que restringe el despliegue a una '
      'instancia de cómputo de capacidad reducida. El cuarto es el calendario '
      'académico, cuyas fechas de entrega no admiten prórroga. El quinto es la '
      'disponibilidad del personal de la clínica para las actividades de '
      'validación y capacitación, que debe acomodarse a su jornada de atención.',
      espacio_antes=10)

    # ──────────────────────── requerimientos no funcionales ────────────────────────
    p('Requerimientos no funcionales. La Tabla 131 presenta las cualidades que '
      'debe exhibir el sistema, agrupadas por categoría.')
    tab([
        ['Categoría', 'ID', 'Descripción'],
        ['Seguridad', 'REQNF-01',
         'Las contraseñas y las respuestas secretas se almacenan cifradas mediante '
         'una función de derivación de claves, nunca en texto plano. El sistema '
         'implementa protección frente a inyección SQL, secuencias de comandos en '
         'sitios cruzados (XSS) y falsificación de peticiones (CSRF). Todas las '
         'vistas exigen autenticación previa.'],
        ['Integridad', 'REQNF-02',
         'Ningún registro se elimina físicamente de la base de datos: toda baja se '
         'ejecuta mediante borrado lógico. Las operaciones sobre la agenda se '
         'realizan dentro de transacciones que garantizan las propiedades ACID. '
         'Toda modificación relevante queda asentada en una tabla de auditoría.'],
        ['Rendimiento', 'REQNF-03',
         'Las operaciones de consulta responden en un máximo de tres segundos bajo '
         'condiciones normales de operación. La estimación de duración generada por '
         'el modelo predictivo se obtiene en línea, sin interrumpir el flujo de '
         'programación de la cita. El sistema soporta la operación concurrente del '
         'personal de la clínica.'],
        ['Usabilidad', 'REQNF-04',
         'La interfaz es responsiva y operable desde computadora, tableta o '
         'teléfono, sin requerir la instalación de software adicional. Todas las '
         'pantallas comparten la misma estructura de navegación. Los mensajes de '
         'error son específicos, se muestran junto al campo que los origina e '
         'indican la acción correctiva.'],
        ['Disponibilidad', 'REQNF-05',
         'El sistema se encuentra disponible durante el horario de atención de la '
         'clínica. El punto de acceso es estable mediante una dirección IP fija. '
         'Los respaldos de la base de datos se ejecutan de forma periódica y '
         'programada.'],
        ['Mantenibilidad', 'REQNF-06',
         'El código se organiza de forma modular, con una aplicación independiente '
         'por dominio funcional. El código fuente permanece versionado en un '
         'repositorio con integración continua, y el despliegue se ejecuta de forma '
         'automatizada tras superar las pruebas.'],
        ['Confidencialidad', 'REQNF-07',
         'El acceso a la información clínica se restringe mediante control por '
         'roles, y la escritura del expediente se reserva al personal con '
         'competencia profesional declarada. Los datos utilizados para el '
         'entrenamiento del modelo se tratan de forma anonimizada, empleando '
         'atributos del procedimiento y no la identidad del paciente.'],
        ['Portabilidad', 'REQNF-08',
         'El sistema opera indistintamente sobre PostgreSQL en producción y sobre '
         'SQLite en el entorno de desarrollo, sin modificar el código de la '
         'aplicación. El despliegue no depende del sistema operativo del equipo '
         'cliente.'],
    ], 'Requerimientos no funcionales del sistema', frac(1.8, 1.5, 7))

    # ───────────────────── documentación y otros requisitos ─────────────────────
    p('Requerimientos de documentación. El proyecto contempla la elaboración del '
      'presente documento de graduación conforme a las normas APA en su séptima '
      'edición, el DERCAS de visión y el DERCAS técnico, el diccionario de datos '
      'del modelo relacional, el manual de usuario por módulo y el manual de '
      'despliegue de la infraestructura. La documentación técnica del código se '
      'mantiene dentro del propio repositorio.', espacio_antes=6)

    p('Otros requisitos. Por tratarse de un sistema nuevo, no existen '
      'requerimientos de migración de datos desde una solución anterior ni de '
      'interoperabilidad con sistemas preexistentes de la clínica. La carga '
      'inicial del catálogo y del padrón de pacientes se realiza mediante las '
      'pantallas de mantenimiento del propio sistema. No se requiere la compra de '
      'licencias de software, puesto que la totalidad de las tecnologías '
      'empleadas son de código abierto.')

    # ────────────────────────────── referencias ──────────────────────────────
    p('Referencias. La Tabla 132 identifica las fuentes de información empleadas '
      'para la elaboración de los requerimientos.')
    tab([
        ['Tipo de referencia', 'Referencia', 'Descripción', 'Fecha'],
        ['Documento físico', 'Libro de citas de la clínica',
         'Agenda en papel donde la recepción registra las citas, el procedimiento '
         'y la hora de atención. Constituye la única fuente histórica de '
         'duraciones con que cuenta la clínica.', '2024–2026'],
        ['Entrevista', 'Propietario de la clínica',
         'Levantamiento de la problemática, del flujo de trabajo vigente y de las '
         'expectativas sobre el sistema.', 'Marzo de 2026'],
        ['Entrevista', 'Personal de recepción y odontólogos',
         'Identificación de los criterios con que se asignan los bloques de tiempo '
         'y de las causas habituales de retraso.', 'Marzo de 2026'],
        ['Observación directa', 'Jornada de atención',
         'Registro del tiempo real empleado en los procedimientos más frecuentes y '
         'de la ocupación de las unidades dentales.', 'Abril de 2026'],
        ['Documento normativo', 'Plantilla DERCAS Visión',
         'Estructura de especificación de requerimientos adoptada por la carrera '
         'de Ingeniería en Sistemas de Información.', '2024'],
    ], 'Referencias empleadas en el levantamiento de requerimientos',
        frac(2.2, 2.8, 5.5, 1.6))

    # ──────────────────────────── cuadro de aceptación ────────────────────────────
    p('Cuadro de aceptación. La Tabla 133 identifica a los responsables de la '
      'validación formal de cada entrega del proyecto y el ámbito sobre el cual '
      'recae su aprobación.', espacio_antes=6)
    tab([
        ['Responsable', 'Puesto', 'Ámbito de aprobación'],
        ['Hee Sung Lee', 'Analista y desarrollador del sistema',
         'Elaboración y entrega de los productos de análisis, diseño, desarrollo y '
         'documentación.'],
        ['Propietario de la Clínica Dental Smilee', 'Patrocinador del proyecto',
         'Validación de los requerimientos, de la funcionalidad entregada y de la '
         'puesta en producción del sistema.'],
        ['Ing. Carlos Eduardo Hernández Herrera', 'Asesor del trabajo de graduación',
         'Aprobación metodológica y académica de cada entrega del proyecto.'],
    ], 'Cuadro de aceptación del proyecto', frac(3, 3, 6))

    doc.save(ARCHIVO)
    print(f'Tablas insertadas: 100 a {NUM - 1}')
    print('Documento guardado.')


if __name__ == '__main__':
    main()
