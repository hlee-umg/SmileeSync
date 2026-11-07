"""Agrega la correspondencia con el OWASP Top 10:2025 a la sección 4.1.3."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_MARCO = (
    'Las medidas descritas en los cinco apartados anteriores se adoptaron a partir '
    'del análisis de los riesgos propios del sistema. Para verificar que ese '
    'análisis no dejara zonas sin examinar, se contrastó con un marco externo y '
    'reconocido: el Top 10 del Open Worldwide Application Security Project, que '
    'clasifica las diez categorías de riesgo más extendidas en aplicaciones web a '
    'partir del análisis de datos aportados por la industria. Se emplea la edición '
    'de 2025, construida sobre más de dos millones ochocientas mil aplicaciones y '
    'cerca de doscientos veinte mil registros de vulnerabilidades publicadas (OWASP '
    'Foundation, 2025). Esa edición introduce dos cambios pertinentes para este '
    'proyecto: eleva las fallas de la cadena de suministro de software al tercer '
    'lugar, ampliando la categoría que antes se limitaba a los componentes '
    'desactualizados, e incorpora como categoría nueva el manejo inadecuado de '
    'condiciones excepcionales.')

P_METODO = (
    'El contraste se realizó categoría por categoría, declarando en cada una el '
    'mecanismo implementado, el lugar del sistema donde reside y, cuando '
    'corresponde, lo que queda pendiente. Se optó por documentar también lo '
    'pendiente porque un inventario de seguridad que solo enumera lo resuelto no '
    'permite dimensionar el riesgo residual, que es la información que la clínica '
    'necesita antes de operar con datos de pacientes reales. La Tabla 421 presenta '
    'esa correspondencia.')

P_RESIDUAL = (
    'De las diez categorías, siete se consideran cubiertas por mecanismos '
    'implementados y verificados, y tres presentan riesgo residual. El más '
    'significativo es el de las fallas criptográficas: mientras el servidor atienda '
    'por un protocolo sin cifrar, las credenciales y la información clínica viajan '
    'legibles por la red, lo que basta para desaconsejar la carga de datos de '
    'pacientes reales y es la razón por la que esa tarea encabeza las '
    'recomendaciones. Los otros dos corresponden a las fallas de autenticación '
    '—falta un límite de intentos fallidos y un segundo factor— y al registro y '
    'monitoreo, donde el sistema conserva el historial de cambios sobre los datos '
    'pero no un registro centralizado de los eventos de seguridad ni un mecanismo de '
    'alerta. Ninguno de los tres compromete la operación con datos de demostración; '
    'los tres deben resolverse antes de la operación real.')

OWASP = [
    ['Categoría del Top 10:2025', 'Mecanismo implementado en SmileeSync',
     'Dónde reside'],
    ['A01. Pérdida de control de acceso',
     'Control de acceso basado en roles aplicado en el servidor mediante '
     'decoradores de vista, no en la plantilla: ocultar el botón no basta y el '
     'acceso directo a la dirección queda igualmente denegado. Treinta y tres '
     'verificaciones automatizadas comprueban el acceso de cada rol a cada vista.',
     'usuarios/decorators.py; conjunto de verificación de permisos'],
    ['A02. Configuración de seguridad incorrecta',
     'Indicador de depuración desactivado en producción, lista explícita de dominios '
     'autorizados, secretos fuera del código y archivo de exclusión del control de '
     'versiones que descarta entornos, llaves y certificados.',
     'config/settings.py; archivo de entorno del servicio'],
    ['A03. Fallas en la cadena de suministro de software',
     'Ocho dependencias declaradas con su versión mínima en un único archivo de '
     'requerimientos, instaladas por la integración continua y no de forma manual. '
     'Se descartó una biblioteca adicional por el peso que agregaba. Pendiente: '
     'fijar versiones exactas y revisar periódicamente los avisos de seguridad.',
     'app/requirements.txt; flujo de integración continua'],
    ['A04. Fallas criptográficas',
     'Las contraseñas y la respuesta a la pregunta secreta se almacenan como resumen '
     'PBKDF2 con SHA-256 y 720 000 iteraciones. Pendiente: cifrado en tránsito, hoy '
     'ausente.',
     'usuarios/models.py; sección 4.1.3.5'],
    ['A05. Inyección',
     'Todo acceso a la base de datos pasa por el mapeador objeto-relacional con '
     'parámetros enlazados; no hay concatenación de datos del usuario en sentencias '
     'SQL. Las plantillas escapan la salida de forma predeterminada, lo que contiene '
     'la inyección de guiones en el navegador.',
     'Capa de modelos; plantillas del sistema'],
    ['A06. Diseño inseguro',
     'Borrado lógico e historial de auditoría en lugar de eliminación física; '
     'separación de los criterios de negocio en módulos propios; la estimación del '
     'modelo se presenta como sugerencia revisable y no como valor impuesto.',
     'Secciones 4.1.2.1 y 4.2.3.2'],
    ['A07. Fallas de autenticación',
     'Identificación por correo único con respaldo de autenticación propio que '
     'calcula el resumen incluso cuando el correo no existe, para que el tiempo de '
     'respuesta no revele qué cuentas existen. Pendiente: límite de intentos '
     'fallidos y segundo factor.',
     'usuarios/backends.py'],
    ['A08. Fallas en la integridad del software o de los datos',
     'El servidor solo se actualiza desde la rama principal del repositorio mediante '
     'integración continua; las migraciones están versionadas y el historial de '
     'auditoría conserva el estado anterior de cada cambio.',
     'Flujo de integración continua; tablas de historial'],
    ['A09. Fallas en el registro, alerta y monitoreo',
     'Historial por entidad con usuario, fecha y estado anterior, y registro de cada '
     'versión del modelo con sus métricas. Pendiente: registro centralizado de '
     'eventos de seguridad y alertas ante intentos de acceso no autorizado.',
     'Tablas de historial; inteligencia/models.py'],
    ['A10. Manejo inadecuado de condiciones excepcionales',
     'El componente predictivo captura sus propias fallas y degrada en cascada al '
     'promedio histórico y a la duración del catálogo: si las bibliotecas faltan, el '
     'archivo del modelo desapareció o la versión es incompatible, la cita se agenda '
     'igual. Ninguna falla del componente predictivo impide operar la agenda.',
     'inteligencia/servicio.py; sección 4.2.3.2'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'Queda pendiente una medida de endurecimiento', exacto=False)

    a = titulo(doc, '4.1.3.6 Correspondencia con el OWASP Top 10:2025', 4, a)
    a = F.parrafo(doc, P_MARCO, a)
    a = F.parrafo(doc, P_METODO, a)
    t = F.tabla(doc, OWASP, a, anchos=[int(ancho * p) for p in (0.22, 0.52, 0.26)])
    a = F.pie(doc, 'Tabla 421', 'Correspondencia entre las categorías del OWASP Top '
              '10:2025 y los mecanismos de seguridad implementados', t)
    a = F.parrafo(doc, P_RESIDUAL, a)
    doc.save(str(C.ARCHIVO))
    print('Sección 4.1.3.6 agregada.')


if __name__ == '__main__':
    main()
