"""Capítulo 5: apertura, cronograma y descripción de la implementación."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_APERTURA = (
    'El capítulo anterior describió la construcción del sistema y su verificación '
    'técnica. Este documenta su puesta en operación en la Clínica Dental Smilee: el '
    'orden en que se ejecutaron las actividades, la manera en que el sistema se '
    'incorporó al trabajo diario, las once sesiones de prueba realizadas con el '
    'personal que habrá de operarlo y las eventualidades que surgieron en el camino. '
    'La distinción con el capítulo precedente es deliberada: allí se comprobó que el '
    'sistema hace lo que la especificación exige; aquí se comprueba que el personal '
    'de la clínica puede hacer su trabajo con él, que es una afirmación distinta y '
    'que no se demuestra con pruebas automatizadas.')

P_ESTRATEGIA = (
    'La literatura de sistemas de información distingue cuatro estrategias de '
    'conversión: la directa, en que el sistema anterior se abandona el día en que '
    'entra el nuevo; la paralela, en que ambos operan simultáneamente durante un '
    'período; la piloto, en que el nuevo se implanta primero en una parte de la '
    'organización; y la gradual o por fases, en que se incorpora un módulo a la vez '
    '(Laudon y Laudon, 2016). La implantación de SmileeSync se condujo con una '
    'estrategia paralela: la clínica conservó su agenda en papel y sus hojas de '
    'cálculo mientras el personal operaba el sistema sobre el conjunto de datos de '
    'demostración descrito en la Tabla 74.')

P_PARALELA = (
    'Esa decisión no obedece a precaución genérica sino a dos restricciones '
    'concretas. La primera es jurídica y la señaló la odontóloga general durante la '
    'primera sesión: en Guatemala el expediente clínico electrónico no sustituye por '
    'sí solo al expediente en papel, de modo que la clínica no puede prescindir del '
    'segundo mientras no exista un respaldo normativo que lo autorice. La segunda es '
    'técnica: la migración del historial real exige una depuración previa de los '
    'registros existentes y la habilitación del cifrado en tránsito, dos tareas que '
    'la sección 5.1.4 enumera entre las pendientes. Operar en paralelo permitió '
    'ejercitar los tres procesos del alcance con el personal real sin exponer '
    'información de pacientes y sin comprometer la operación de la clínica si algo '
    'fallaba, que es precisamente la ventaja que la estrategia paralela ofrece a '
    'cambio del costo de sostener dos registros a la vez.')

P_CRONO = (
    'El cronograma no se organizó por semanas calendario sino por condición de '
    'avance: cada etapa exigía que la anterior hubiera producido un resultado '
    'verificable, de modo que una sesión de uso no se programaba mientras no '
    'estuviera corregido lo que la anterior había revelado. La Tabla 400 presenta '
    'las siete etapas con su fecha, la actividad ejecutada y el resultado que la dio '
    'por concluida.')

P_CRONO_CIERRE = (
    'Dos rasgos del cronograma merecen señalarse. El primero es que la corrección '
    'del defecto de la interfaz móvil, detectado el 9 de octubre, se desplegó el 15 '
    'y se verificó con los usuarios el 16: el ciclo completo de observación, '
    'corrección y comprobación tomó seis días y queda documentado en el repositorio '
    'con la marca de tiempo de cada cambio. El segundo es que la etapa de uso '
    'autónomo no es posterior a las demás sino simultánea: a partir de la segunda '
    'sesión los profesionales emplearon el sistema por su cuenta entre una sesión y '
    'la siguiente, y cinco de las once fichas registran esa modalidad.')

P_ENTORNO = (
    'La implantación se ejecutó sobre el entorno de producción descrito en la '
    'sección 4.3.1 y no sobre una copia de ensayo. Todas las sesiones se realizaron '
    'contra el servidor alojado en Amazon Web Services, con la base de datos '
    'PostgreSQL de producción, el servidor web Nginx, el servidor de aplicaciones '
    'Gunicorn y el despliegue automatizado por integración continua. Esa decisión '
    'tiene una consecuencia metodológica: lo que el personal observó es el '
    'comportamiento real del sistema bajo las condiciones de red, latencia y '
    'configuración en que habrá de operar, y no el de un entorno de desarrollo que '
    'suele ser más rápido y más permisivo.')

P_USUARIOS = (
    'Se habilitó un usuario por persona y no un usuario por puesto, de modo que cada '
    'acción quedara atribuida a quien la ejecutó. Participaron tres personas sobre '
    'cuatro perfiles distintos: el ortodoncista, que opera además como administrador '
    'del sistema; la odontóloga general; y la recepcionista, que concentra la '
    'operación diaria de la agenda. El cuarto perfil, el de asistente, no se ejercitó '
    'por no existir hoy esa figura en la clínica. Conviene subrayar que estas tres '
    'personas no constituyen una muestra sino la totalidad del personal que operará '
    'el sistema, de manera que la cobertura de la prueba es censal y no estadística.')

P_CAPACITACION = (
    'La capacitación se condujo con el guion de acompañamiento de la sección 4.3.4 y '
    'con el protocolo de tres etapas de la sección 4.3.5. Cada sesión se registró en '
    'la ficha de la Tabla 78, impresa y llenada durante la sesión misma y firmada por '
    'quien participó en ella; las once fichas se incorporan en el Anexo C. El '
    'instrumento se mantuvo invariable a lo largo del mes para que las observaciones '
    'de sesiones distintas resultaran comparables entre sí.')

CRONOGRAMA = [
    ['Etapa', 'Fecha', 'Actividad', 'Resultado que la concluye'],
    ['1. Preparación del entorno', 'Hasta el 01/10/2026',
     'Despliegue de la aplicación en el servidor de producción, creación de los '
     'usuarios de cada rol y carga del conjunto de datos de demostración.',
     'Entorno accesible desde la dirección pública, con los cuatro roles operativos.'],
    ['2. Capacitación inicial', '02/10/2026',
     'Recorrido guiado del sistema con los tres perfiles y ejecución acompañada de '
     'los procesos que corresponden a cada uno.',
     'Tres fichas de registro y dos solicitudes de ajuste al alcance de la recepción.'],
    ['3. Uso acompañado', '09/10/2026',
     'Operación por cuenta propia bajo observación silenciosa, sobre los módulos de '
     'agenda, expediente clínico, pacientes, plan de tratamiento y cobros.',
     'Tres fichas y la detección del defecto de la interfaz en teléfonos móviles.'],
    ['4. Corrección y nueva versión', '15/10/2026',
     'Rediseño del menú para teléfonos y tabletas, incorporación del reentrenamiento '
     'programado y de la validación automática de la hipótesis.',
     'Versión desplegada en producción y verificada en teléfono, tableta y escritorio.'],
    ['5. Verificación en producción', '16/10/2026',
     'Entrenamiento del modelo sobre el servidor de producción y tercera ronda de '
     'sesiones con los tres perfiles.',
     'Modelo activo en producción y registro fotográfico de las sesiones.'],
    ['6. Administración del sistema', '17 y 23/10/2026',
     'Sesiones centradas en los módulos de seguridad, inteligencia y reportes con el '
     'perfil de administrador.',
     'Dos fichas y las solicitudes sobre la periodicidad del reentrenamiento.'],
    ['7. Uso autónomo', 'Del 09/10/2026 en adelante',
     'Operación sin acompañamiento entre una sesión y la siguiente, con reporte de lo '
     'que el personal encuentra por su cuenta.',
     'Cinco de las once fichas registran esta modalidad.'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.antes_de_referencias(doc)

    a = titulo(doc, 'Capítulo 5. Marco Metodológico: Implementación', 1, a)
    a.alignment = 1
    a = F.parrafo(doc, P_APERTURA, a)
    a = titulo(doc, '5.1 Implementación', 2, a)
    a = F.parrafo(doc, P_ESTRATEGIA, a)
    a = F.parrafo(doc, P_PARALELA, a)

    a = titulo(doc, '5.1.1 Cronograma de implementación', 3, a)
    a = F.parrafo(doc, P_CRONO, a)
    t = F.tabla(doc, CRONOGRAMA, a,
                anchos=[int(ancho * p) for p in (0.17, 0.14, 0.38, 0.31)])
    a = F.pie(doc, 'Tabla 400', 'Cronograma de la implementación de SmileeSync en la '
              'Clínica Dental Smilee', t)
    a = F.parrafo(doc, P_CRONO_CIERRE, a)

    a = titulo(doc, '5.1.2 Descripción de la implementación', 3, a)
    for texto in (P_ENTORNO, P_USUARIOS, P_CAPACITACION):
        a = F.parrafo(doc, texto, a)

    doc.save(str(C.ARCHIVO))
    print('Capítulo 5: apertura, cronograma y descripción agregados.')


if __name__ == '__main__':
    main()
