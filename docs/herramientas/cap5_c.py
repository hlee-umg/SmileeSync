"""Capítulo 5: observaciones recogidas y eventualidades de la implementación."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_SOLICITUDES = (
    'Las once fichas recogen quince observaciones distintas entre preguntas no '
    'previstas, solicitudes de cambio y defectos. Cada una se contrastó con el '
    'estado real del sistema y con el historial del repositorio, de modo que la '
    'columna de resultado no reproduce lo que se ofreció en la sesión sino lo que '
    'puede comprobarse hoy. La Tabla 402 las presenta.')

P_ANALISIS = (
    'La distribución de esas quince observaciones dice más que su número. Solo una '
    'constituyó un defecto del sistema, y fue el de la interfaz en teléfonos; cinco '
    'correspondían a funcionalidad que el sistema ya ofrecía y que el usuario no '
    'había encontrado o suponía ausente. Esta segunda categoría no es un defecto de '
    'programación sino de visibilidad o de capacitación, y tiene una lectura '
    'favorable sobre el análisis de requerimientos: lo que el personal pidió al '
    'operar el sistema coincidía con lo que el análisis había previsto meses antes. '
    'Cuatro observaciones quedaron pendientes y se trasladan a las recomendaciones, '
    'una se declaró fuera del alcance en la sesión misma, otra corresponde a una '
    'restricción jurídica ajena al sistema y la última no procede por decisión de '
    'diseño.')

P_DISENO = (
    'Esa última merece explicación porque toca el núcleo del proyecto. El '
    'ortodoncista preguntó si era posible modificar manualmente las duraciones que '
    'el algoritmo estima, agregando o quitando minutos a su criterio. La respuesta '
    'fue negativa y la razón es metodológica: un modelo que se corrige a mano deja '
    'de aprender del historial y pasa a reproducir la estimación de quien lo '
    'corrige, que es exactamente el método de bloques fijos que el proyecto busca '
    'mejorar. La vía correcta para ajustar una estimación que el profesional '
    'considera errada es registrar la duración real de la atención, que es el dato '
    'con que el modelo se reentrena, o corregir la duración de referencia del '
    'catálogo cuando el desvío es sistemático. Ambas rutas están disponibles en el '
    'sistema y se explicaron en la sesión.')

P_EVENT = (
    'La implantación no transcurrió sin contratiempos. La Tabla 403 los enumera con '
    'la fecha en que se presentaron, el efecto que tuvieron sobre el trabajo y la '
    'forma en que se resolvieron. Se incluyen tanto los de origen técnico como los '
    'de orden operativo y jurídico, porque unos y otros condicionaron por igual el '
    'desarrollo de las sesiones.')

P_EVENT_CIERRE = (
    'De las seis eventualidades, cuatro quedaron resueltas dentro del período de '
    'implantación y dos permanecen abiertas: la habilitación del cifrado en tránsito, '
    'que depende de adquirir un nombre de dominio, y la sustitución de los datos de '
    'demostración por el historial real, que depende de la primera y de la '
    'depuración previa de los registros de la clínica. Ninguna de las dos impidió '
    'ejecutar las pruebas; ambas impiden, en cambio, declarar concluida la '
    'implantación, y por eso se enuncian también entre las recomendaciones.')

SOLICITUDES = [
    ['Observación o solicitud', 'Sesión', 'Resultado verificado'],
    ['Ampliar el acceso de la recepción al plan de tratamiento.',
     'Recepción, 02/10',
     'Ya disponible. El rol de recepcionista tiene acceso de consulta al módulo '
     'clínico desde el 26 de septiembre. La sesión confirmó una decisión de diseño '
     'que el equipo había puesto en duda al suponer que el plan no formaba parte de '
     'sus responsabilidades.'],
    ['Para qué sirven los reportes al perfil de recepción.',
     'Recepción, 02/10', 'Atendido en la capacitación.'],
    ['Impresión del expediente del paciente.', 'Odontóloga general, 02/10',
     'Pendiente. Se traslada a las recomendaciones.'],
    ['El expediente electrónico no sustituye legalmente al expediente en papel.',
     'Odontóloga general, 02/10',
     'Restricción jurídica ajena al sistema. Determinó la estrategia de implantación '
     'paralela de la sección 5.1.2.'],
    ['Restringir a los odontólogos la programación de citas, que corresponde a la '
     'recepción.', 'Ortodoncista, 09/10',
     'Ya disponible. El rol de odontólogo es de solo consulta sobre la agenda desde '
     'el 26 de septiembre; la observación confirmó la regla vigente.'],
    ['Integración con el sistema de cobros que la clínica ya emplea.',
     'Ortodoncista, 09/10',
     'Fuera del alcance del proyecto; así se respondió en la sesión.'],
    ['La interfaz no resulta utilizable en teléfonos: el menú ocupa la pantalla '
     'completa.', 'Ortodoncista y odontóloga general, 09/10',
     'Corregido. El menú se rediseñó como panel lateral retráctil el 15 de octubre y '
     'se verificó en teléfono, tableta y escritorio antes de la sesión del 16.'],
    ['Aplicar los abonos al tratamiento completo y no a una pieza concreta.',
     'Recepción, 09/10',
     'Ya disponible. El abono se registra contra el plan de tratamiento, no contra '
     'sus renglones.'],
    ['Registrar el comprobante del pago.', 'Recepción, 09/10',
     'Parcialmente disponible. El formulario de abono incluye el campo de referencia '
     'o número de recibo. La solicitud contemplaba adjuntar una imagen del '
     'comprobante; se resolvió conservar el campo de texto y la carga de archivos se '
     'traslada a las recomendaciones.'],
    ['Importar desde una hoja de cálculo las citas y los expedientes anteriores.',
     'Recepción, 16/10', 'Pendiente. Se traslada a las recomendaciones.'],
    ['Lanzar un reentrenamiento del modelo cuando el administrador lo decida.',
     'Administrador, 16/10',
     'Pendiente. El reentrenamiento se ejecuta por tarea programada o por línea de '
     'comandos; no existe una acción equivalente en la interfaz.'],
    ['Volver a una versión anterior del modelo si resultaba mejor.',
     'Administrador, 16/10',
     'Ya disponible. El panel de inteligencia permite activar cualquier versión del '
     'histórico, que pasa a ser la vigente.'],
    ['Reportes personalizados.', 'Administrador, 16/10',
     'Pendiente. Se traslada a las recomendaciones.'],
    ['Modificar manualmente las duraciones que estima el algoritmo.',
     'Administrador, 17/10',
     'No procede por diseño. Se explica en el párrafo siguiente a esta tabla.'],
    ['Configurar la periodicidad del reentrenamiento.', 'Administrador, 17/10',
     'Parcialmente resuelto. El reentrenamiento automático se ejecuta el primer día '
     'de cada mes; elegir otra periodicidad desde la interfaz queda pendiente.'],
]

EVENTUALIDADES = [
    ['Eventualidad', 'Fecha', 'Efecto', 'Resolución'],
    ['El entrenamiento del modelo falló en el servidor por datos insuficientes.',
     '16/10/2026',
     'La base de producción contenía trece atenciones registradas y el procedimiento '
     'exige un mínimo de sesenta, de modo que el sistema quedó estimando con la '
     'duración del catálogo.',
     'Se cargó el conjunto de datos de demostración y el entrenamiento concluyó con '
     'un error absoluto medio de 3.87 minutos sobre el servidor.'],
    ['La interfaz resultaba inservible en teléfonos móviles.', '09/10/2026',
     'El menú lateral se desplegaba completo sobre la pantalla y obligaba a '
     'desplazarse hasta el final para alcanzar el contenido. La odontóloga general '
     'reportó que en su teléfono no cargaba correctamente.',
     'Se rediseñó como panel retráctil el 15 de octubre y se verificó en los tres '
     'tamaños de pantalla.'],
    ['El navegador advierte que la conexión no es segura.', 'Desde el 16/10/2026',
     'El sistema se publica sobre una dirección IP y sin cifrado en tránsito, de modo '
     'que el navegador interpone una advertencia antes de mostrar la aplicación.',
     'Pendiente. La emisión de un certificado exige un nombre de dominio, que la '
     'clínica no ha adquirido.'],
    ['El expediente electrónico carece de validez legal por sí solo.', '02/10/2026',
     'Impide sustituir el expediente en papel y obliga a sostener ambos registros.',
     'Se adoptó la estrategia de implantación paralela y se documenta como '
     'restricción del alcance.'],
    ['Las cifras del conjunto de demostración varían según el día de ejecución.',
     'Octubre de 2026',
     'El generador construye la agenda en relación con la fecha actual, de modo que '
     'el número de atenciones y las métricas del modelo cambian de un día a otro.',
     'Se fijaron las cifras del documento en el conjunto de 472 atenciones del 15 de '
     'octubre y se declara expresamente esa fecha de corte.'],
    ['No se dispuso del historial real de la clínica.', 'Todo el período',
     'El modelo se entrenó sobre datos de demostración construidos con el volumen y '
     'la variabilidad reales, pero no con los registros efectivos de los pacientes.',
     'Pendiente. Queda condicionado a la habilitación del cifrado y a la depuración '
     'previa de los registros existentes.'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'La recepcionista registró cuatro sesiones', exacto=False)

    a = F.parrafo(doc, P_SOLICITUDES, a)
    t = F.tabla(doc, SOLICITUDES, a,
                anchos=[int(ancho * p) for p in (0.34, 0.17, 0.49)])
    a = F.pie(doc, 'Tabla 402', 'Observaciones y solicitudes recogidas en las sesiones, '
              'con su resultado verificado', t)
    a = F.parrafo(doc, P_ANALISIS, a)
    a = F.parrafo(doc, P_DISENO, a)

    a = titulo(doc, '5.1.4 Eventualidades ocurridas durante la implementación', 3, a)
    a = F.parrafo(doc, P_EVENT, a)
    t = F.tabla(doc, EVENTUALIDADES, a,
                anchos=[int(ancho * p) for p in (0.24, 0.13, 0.32, 0.31)])
    a = F.pie(doc, 'Tabla 403', 'Eventualidades presentadas durante la implementación '
              'y su resolución', t)
    a = F.parrafo(doc, P_EVENT_CIERRE, a)
    doc.save(str(C.ARCHIVO))
    print('Secciones 5.1.3 (cierre) y 5.1.4 agregadas.')


if __name__ == '__main__':
    main()
