"""Actualiza el inventario del módulo de Inteligencia y las cifras de 4.3."""
from docx import Document
from docx.shared import Emu

import cap4_comun as C
import cifras as X

P = C.PULGADA


def main():
    doc = Document(str(C.ARCHIVO))

    # ── Tabla 70: inventario del módulo de Inteligencia ──
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
         'Incorpora una cita atendida al conjunto de entrenamiento; actualiza '
         'la fila si la atención ya estaba registrada.'),
        ('entrenamiento.py', '_fila_de',
         'Arma, desde la cita y su nota clínica, los valores con que una '
         'atención entra al conjunto.'),
        ('entrenamiento.py', 'sincronizar',
         'Pone al día el conjunto de entrenamiento: da de alta las atenciones '
         'que faltan, corrige las que cambiaron y da de baja las que dejaron de '
         'ser válidas.'),
        ('entrenamiento.py', 'reunir_datos',
         'Devuelve el conjunto de entrenamiento, sincronizándolo antes de '
         'leerlo.'),
        ('entrenamiento.py', '_construir',
         'Arma la tubería de codificación y estimación del algoritmo '
         'solicitado.'),
        ('entrenamiento.py', 'entrenar',
         'Entrena, evalúa contra la línea base y contra la duración del '
         'catálogo, y serializa el modelo; devuelve sus métricas.'),
        ('entrenamiento.py', '_importancias',
         'Calcula el peso relativo de cada variable en el bosque aleatorio.'),
        ('entrenamiento.py', 'registrar_version, activar_version',
         'Registran la versión entrenada y la ponen en producción retirando la '
         'anterior.'),
        ('evaluacion.py', 'resumen_version',
         'Lectura retrospectiva de una versión: su error frente al del catálogo '
         'sobre el subconjunto de prueba, con el veredicto respecto de la meta '
         'del proyecto.'),
        ('evaluacion.py', 'contrastables',
         'Predicciones emitidas cuya cita ya fue atendida y medida.'),
        ('evaluacion.py', 'desempeno_en_operacion',
         'Lectura prospectiva: error del modelo y del catálogo sobre las citas '
         'realmente agendadas con él, y proporción de atenciones que cayeron '
         'dentro del bloque recomendado.'),
        ('evaluacion.py', 'desempeno_por_procedimiento',
         'Desglose de esa lectura por procedimiento.'),
        ('commands/entrenar.py', 'Command.handle',
         'Comando administrativo que sincroniza el conjunto y ejecuta el '
         'entrenamiento fuera del proceso web, con las opciones de algoritmo, '
         'activación y activación condicionada a la mejora.'),
        ('views.py', 'panel, activar, _desempeno_vigente',
         'Presentan la validación de la hipótesis, las versiones entrenadas con '
         'sus métricas, el desempeño en operación y el contraste entre la '
         'duración del catálogo y la real; permiten activar una versión.'),
    ]:
        filas.append([arch, fn, que])
    X.reemplazar_tabla(doc, 70, filas,
                       anchos=[Emu(int(1.3 * P)), Emu(int(1.9 * P)),
                               Emu(int(3.1 * P))])

    # ── 4.3.2: número de verificaciones ──
    X.texto(doc, 'Entregar a los usuarios un sistema que falla',
            'Entregar a los usuarios un sistema que falla en lo elemental '
            'convierte la prueba de implementación en una sesión de depuración '
            'y desperdicia la disposición del personal, que es un recurso '
            'escaso. Por esa razón se estableció como condición previa que el '
            'sistema superara un conjunto de verificaciones automatizadas, '
            'agrupadas en ocho conjuntos según el comportamiento que '
            'comprueban. Cada verificación formula una afirmación sobre el '
            'sistema y la comprueba contra la base de datos y contra las '
            'pantallas; en total son 336 y las 336 se cumplen. La Tabla 72 las '
            'relaciona.')

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
         'Sincronización del conjunto de entrenamiento, métricas contra la '
         'línea base y contra la duración del catálogo, versionado, caché del '
         'modelo, los tres niveles de la cadena de respaldo, el desempeño en '
         'operación y los paneles de inteligencia y de reportes.', '86'),
        ('Total', '', '336'),
    ]:
        filas.append([n, q, c])
    X.reemplazar_tabla(doc, 72, filas,
                       anchos=[Emu(int(1.5 * P)), Emu(int(3.9 * P)),
                               Emu(int(0.9 * P))])

    # ── Tabla 74: datos de demostración ──
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
        ('Citas', '663',
         '472 atendidas, 155 programadas y 36 canceladas.'),
        ('Notas de evolución', '472',
         'Una por cada atención, con piezas tratadas, anestesia y '
         'complicaciones.'),
        ('Registros de entrenamiento', '472',
         'Es el conjunto con que se entrenó el modelo que opera en el '
         'sistema; 118 se reservaron para evaluarlo.'),
    ]:
        filas.append([e, c, o])
    X.reemplazar_tabla(doc, 74, filas,
                       anchos=[Emu(int(1.7 * P)), Emu(int(1.4 * P)),
                               Emu(int(3.2 * P))])

    # ── 4.3.7 ──
    X.texto(doc, 'El sistema completa los tres procesos',
            'El sistema completa los tres procesos del alcance sobre el entorno '
            'de producción, con los usuarios de cada rol y con dos meses de '
            'datos de operación cargados: la programación de una cita con la '
            'duración estimada, el registro de la atención con los tiempos '
            'reales y la documentación de la visita en el expediente. Las 336 '
            'verificaciones automatizadas se cumplen, el modelo en producción '
            'reduce en 41.8 % el error del método de bloques fijos —frente a la '
            'meta de 25 % del proyecto— y los siete defectos derivados del uso '
            'fueron corregidos, cada uno con su verificación añadida al '
            'conjunto.')
    X.texto(doc, 'Quedan pendientes tres tareas',
            'Quedan pendientes tres tareas antes de considerar concluida la '
            'implantación, que se enuncian para que el alcance de lo verificado '
            'no se confunda con el de lo definitivo. La primera es la '
            'habilitación de HTTPS con un certificado y la activación de las '
            'marcas de seguridad correspondientes, condición para operar con '
            'datos de pacientes reales. La segunda es la configuración del '
            'respaldo periódico de la base de datos. La tercera es la '
            'sustitución de los datos de demostración por el historial real de '
            'la clínica, momento en que el modelo deberá reentrenarse sobre ese '
            'historial y en que las métricas reportadas en la Tabla 68 habrán '
            'de recalcularse: las cifras de este capítulo corresponden al '
            'conjunto de 472 atenciones con que se construyó y validó el '
            'sistema.')

    doc.save(str(C.ARCHIVO))
    print('inventario y cifras de 4.3 actualizados')


if __name__ == '__main__':
    main()
