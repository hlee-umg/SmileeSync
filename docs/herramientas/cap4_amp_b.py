"""Agrega los diagramas de componentes y de despliegue a la sección 4.1.2.1."""
import sys
from pathlib import Path

from docx import Document
from docx.shared import Emu

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402

DIAG = C.RAIZ / 'diagramas'

P_INTRO = (
    'La arquitectura descrita se materializa en ocho componentes de software, uno '
    'por cada aplicación del proyecto Django más el paquete de configuración. La '
    'Figura 500 los presenta con sus dependencias. El diagrama no es un diseño '
    'previo sino una lectura del sistema construido: se obtuvo analizando las '
    'importaciones declaradas en los sesenta y siete archivos de código del '
    'proyecto, excluidas las migraciones y los comandos de mantenimiento, de modo '
    'que cada flecha corresponde a una dependencia que existe efectivamente en el '
    'código y no a una que se haya previsto en el papel.')

P_LECTURA = (
    'El diagrama revela tres niveles de dependencia. En la base están configuración '
    'y usuarios: el primero concentra las rutas y los parámetros del proyecto y el '
    'segundo, la autenticación, los roles y la auditoría, de los que dependen todos '
    'los demás y que no dependen de ninguno. En el nivel intermedio están pacientes '
    'y catálogo, que registran las entidades sobre las que opera la clínica y solo '
    'dependen de la base. En el nivel superior están los tres componentes que '
    'resuelven la operación —agenda, expediente clínico e inteligencia— que dependen '
    'de todos los anteriores y, además, entre sí. Reportes ocupa una posición '
    'particular: depende de agenda y de catálogo para leer sus datos, pero ningún '
    'componente depende de él, que es la forma del consumidor final de información.')

P_CICLO = (
    'La dependencia mutua entre agenda, expediente clínico e inteligencia no es un '
    'descuido sino la traducción fiel de un hecho del dominio: la cita produce la '
    'atención, la atención se documenta en el expediente, el expediente alimenta al '
    'modelo y el modelo estima la duración de la siguiente cita. El ciclo existe en '
    'la clínica antes de existir en el código. Para que esa reciprocidad no impida '
    'cargar los módulos, las importaciones que cerrarían el ciclo se declaran dentro '
    'de la función que las necesita y no en el encabezado del archivo, técnica '
    'habitual en Django para dependencias circulares legítimas; únicamente la '
    'importación del servicio de estimación desde la agenda se declara en el '
    'encabezado, por ser la que interviene en cada programación de cita.')

P_DESPLIEGUE = (
    'La Figura 501 presenta el despliegue efectivo del sistema con sus nodos, sus '
    'procesos y sus puertos. Una petición del navegador llega por el puerto 80 al '
    'servidor Nginx, que cumple dos funciones: entrega directamente los archivos '
    'estáticos y traslada el resto al servidor de aplicaciones Gunicorn por una '
    'dirección interna, de modo que los tres procesos de la aplicación no se ocupan '
    'de servir hojas de estilo ni imágenes. Gunicorn ejecuta la aplicación Django, '
    'que consulta la base de datos PostgreSQL por el puerto local 5432 y, cuando la '
    'operación lo requiere, invoca al motor predictivo, que carga el modelo '
    'serializado desde el disco. Una unidad temporizada del sistema operativo '
    'dispara el reentrenamiento el primer día de cada mes, al margen del tránsito '
    'web. El despliegue se actualiza desde el repositorio: un cambio incorporado a '
    'la rama principal dispara la revisión automática y, superada esta, la '
    'actualización del servidor por conexión segura.')

P_RIESGO = (
    'El diagrama hace visible la principal debilidad de la arquitectura de '
    'despliegue: todos los componentes residen en una sola instancia. La aplicación, '
    'el servidor web, la base de datos y el modelo comparten los dos gigabytes de '
    'memoria y el mismo disco, de modo que la instancia constituye un punto único de '
    'falla y el respaldo de la base de datos deja de ser una buena práctica para '
    'convertirse en la única protección contra la pérdida total de la información. '
    'La decisión responde al criterio de costo expuesto en la sección 4.1.1 y es '
    'adecuada para el volumen de una clínica de dos unidades dentales, pero debe '
    'enunciarse con precisión y no suponerse resuelta.')


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)
    alto = min(int(alto), int(7.20 * C.PULGADA))
    a = C.buscar(doc, 'La decisión de diseño con mayor consecuencia práctica', exacto=False)

    a = F.parrafo(doc, P_INTRO, a)
    p = F.imagen(doc, DIAG / 'componentes_app.png', a, ancho, alto)
    a = F.pie(doc, 'Figura 500', 'Componentes de la aplicación y sus dependencias, '
              'obtenidas del análisis de las importaciones del código fuente', p)
    a = F.parrafo(doc, P_LECTURA, a)
    a = F.parrafo(doc, P_CICLO, a)
    a = F.parrafo(doc, P_DESPLIEGUE, a)
    p = F.imagen(doc, DIAG / 'despliegue.png', a, ancho, alto)
    a = F.pie(doc, 'Figura 501', 'Despliegue en producción: nodos, procesos y puertos', p)
    a = F.parrafo(doc, P_RIESGO, a)
    doc.save(str(C.ARCHIVO))
    print('Sección 4.1.2.1 ampliada con los dos diagramas.')


if __name__ == '__main__':
    main()
