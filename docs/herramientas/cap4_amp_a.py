"""Amplía 4.1.1 con los criterios y las alternativas de la plataforma."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

P_CRITERIOS = (
    'La plataforma no se eligió por familiaridad sino aplicando tres criterios '
    'declarados antes de resolver cada decisión. El primero es la sostenibilidad por '
    'un solo desarrollador: el proyecto lo construye y lo mantiene una persona, de '
    'modo que toda tecnología que exigiera administrar componentes separados quedaba '
    'descartada. El segundo es el costo de operación, que para una clínica de dos '
    'odontólogos debe ser nulo o marginal, lo que excluye los servicios gestionados '
    'de base de datos y las licencias por puesto. El tercero es la madurez '
    'documental: se privilegiaron componentes con documentación oficial extensa y '
    'comunidad activa, porque el tiempo que un desarrollador solo pierde resolviendo '
    'un problema sin documentación es el recurso más escaso del proyecto '
    '(Sommerville, 2011). La Tabla 420 resume las alternativas que se consideraron '
    'en cada decisión y el criterio que la resolvió.')

P_FRAMEWORK = (
    'La decisión del framework merece detallarse porque condiciona a todas las '
    'demás. Se compararon tres opciones. Flask, también de Python, ofrece un núcleo '
    'mínimo al que se incorporan las piezas necesarias; esa flexibilidad obliga a '
    'escoger e integrar por separado el mapeador objeto-relacional, el sistema de '
    'migraciones, el de autenticación y el de formularios, decisiones que en un '
    'proyecto de un solo desarrollador consumen tiempo sin agregar valor al problema '
    'de la clínica. Laravel, del ecosistema PHP, resuelve esos mismos componentes de '
    'forma integrada, pero habría impedido ejecutar el modelo predictivo dentro del '
    'mismo proceso de la aplicación, ya que las bibliotecas de aprendizaje automático '
    'maduras pertenecen al ecosistema de Python; la alternativa habría sido levantar '
    'un servicio aparte, lo que contradice el primer criterio. Django reúne en una '
    'sola instalación el mapeador, las migraciones, la autenticación, los formularios '
    'y el panel de administración, incorpora de manera predeterminada varias de las '
    'protecciones que la sección 4.1.3 describe, y pertenece al mismo ecosistema que '
    'scikit-learn, de modo que la estimación se resuelve con una llamada de función y '
    'no con una petición de red (Django Software Foundation, 2024).')

P_BD = (
    'En la base de datos se contrastaron PostgreSQL, MySQL y la permanencia de SQLite '
    'también en producción. SQLite quedó descartado para producción por su modelo de '
    'escritura: bloquea el archivo completo durante la escritura, lo que resulta '
    'aceptable mientras un solo usuario trabaja, pero no cuando la recepción programa '
    'una cita mientras un odontólogo registra una nota clínica. Entre los dos '
    'motores cliente-servidor, PostgreSQL se seleccionó por su tratamiento estricto '
    'de la integridad referencial y de las restricciones de verificación, que es '
    'justamente la propiedad de la que depende el modelo de datos de este sistema: '
    'una cita sin paciente o un abono sin plan de tratamiento no deben ser '
    'representables en la base, y no solo improbables en la aplicación (Elmasri y '
    'Navathe, 2016).')

P_INFRA = (
    'En la infraestructura se compararon los tres modelos de servicio que define el '
    'Instituto Nacional de Estándares y Tecnología: infraestructura, plataforma y '
    'software como servicio (Mell y Grance, 2011). El alojamiento compartido, '
    'asimilable al tercero, no permite instalar bibliotecas de cómputo ni programar '
    'tareas en el sistema operativo, dos requisitos de este proyecto: el modelo '
    'predictivo exige scikit-learn y el reentrenamiento exige una tarea periódica. '
    'Una plataforma como servicio habría resuelto el despliegue, pero su costo '
    'mensual supera el de una instancia pequeña y su modelo de archivos efímeros '
    'complica conservar el modelo entrenado entre reinicios. La infraestructura como '
    'servicio, materializada en una instancia EC2, concede control completo del '
    'sistema operativo al precio de administrarlo, que es el intercambio que este '
    'proyecto puede sostener.')

ALTERNATIVAS = [
    ['Decisión', 'Alternativas consideradas', 'Criterio que la resolvió', 'Elección'],
    ['Lenguaje y framework web', 'Django, Flask, Laravel',
     'Integración del componente predictivo en el mismo proceso y disponibilidad de '
     'mapeador, migraciones y autenticación sin ensamblaje manual.',
     'Python 3.12 con Django 5.0'],
    ['Base de datos en producción', 'PostgreSQL, MySQL, SQLite',
     'Escritura concurrente de varios usuarios y aplicación estricta de la '
     'integridad referencial.', 'PostgreSQL 16'],
    ['Base de datos en desarrollo', 'PostgreSQL local, SQLite, contenedor',
     'Reconstrucción inmediata de la base durante el desarrollo, sin administrar un '
     'servidor en el equipo personal.', 'SQLite'],
    ['Infraestructura', 'Instancia de cómputo, plataforma como servicio, alojamiento '
     'compartido',
     'Instalación de bibliotecas de cómputo, tareas programadas en el sistema '
     'operativo y persistencia del modelo entrenado.',
     'Amazon EC2 t3.small (infraestructura como servicio)'],
    ['Servidor web y de aplicaciones', 'Nginx con Gunicorn, Apache con mod_wsgi, el '
     'servidor de desarrollo de Django',
     'Atención de archivos estáticos sin ocupar procesos de la aplicación y aptitud '
     'declarada para producción.', 'Nginx como proxy inverso y Gunicorn'],
    ['Interfaz de usuario', 'Bootstrap, Tailwind, hojas de estilo propias',
     'Comportamiento adaptable a teléfono, tableta y escritorio sin construir el '
     'sistema de rejilla desde cero.', 'Bootstrap 5.3'],
    ['Algoritmo predictivo', 'Bosque aleatorio, regresión lineal múltiple, XGBoost',
     'Precisión medida sobre el mismo conjunto frente al peso de la dependencia que '
     'introduce.', 'Bosque aleatorio de scikit-learn'],
    ['Despliegue', 'Integración continua con GitHub Actions, carga manual por SSH, '
     'contenedores',
     'Reproducibilidad del despliegue y eliminación del paso manual propenso a '
     'error.', 'GitHub Actions sobre la rama principal'],
]


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'Tabla 56:', exacto=False)
    for texto in (P_CRITERIOS, P_FRAMEWORK, P_BD, P_INFRA):
        a = F.parrafo(doc, texto, a)
    t = F.tabla(doc, ALTERNATIVAS, a,
                anchos=[int(ancho * p) for p in (0.19, 0.25, 0.33, 0.23)])
    F.pie(doc, 'Tabla 420', 'Alternativas consideradas en cada decisión de plataforma '
          'y criterio que la resolvió', t)
    doc.save(str(C.ARCHIVO))
    print('Sección 4.1.1 ampliada.')


if __name__ == '__main__':
    main()
