"""Convierte la sección 4.3.5 en registro de las sesiones realizadas.

Las dos primeras sesiones de prueba de implementación se ejecutaron el 16 de
octubre de 2026 sobre el entorno de producción. Este script actualiza el texto
que las anunciaba como previstas, incorpora el registro fotográfico y agrega la
precisión sobre el indicador de desviación media de la pantalla de inicio, que
no coincide con el error del modelo y podría leerse como contradicción.

Corrige además el pie de la Tabla 68, que decía 446 atenciones cuando el
conjunto con que se entrenó —y que el propio cuadro desglosa en 354 y 118— es
de 472.
"""
import sys
from pathlib import Path

from docx import Document
from docx.shared import Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402

RAIZ = Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs'
ARCHIVO = RAIZ / 'SmileeSync_Cuarta_Entrega.docx'
EVID = RAIZ / 'evidencias'


def escribir(parrafo, texto):
    """Sustituye el texto conservando el formato del documento.

    Los párrafos y las celdas heredados tienen un primer run vacío y sin
    formato; el que lleva la fuente es el siguiente. Escribir en el primero
    devolvería el texto a 12 pt dentro de una tabla de 9 pt.
    """
    runs = parrafo.runs
    destino = None
    for r in runs:
        if r._r.find(
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/'
                'main}rPr') is not None:
            destino = r
    if destino is None:
        destino = runs[0]
    destino.text = texto
    for r in runs:
        if r is not destino:
            r.text = ''


P_SESIONES = (
    'Con esa ficha se organizaron tres sesiones, una por cada perfil de '
    'usuario del sistema y en el orden en que la operación las requiere: '
    'primero el profesional que escribe el expediente, después la profesional '
    'que lo consulta y lo continúa, y por último la recepción, que es quien '
    'convierte todo eso en citas. La Tabla 79 las describe con su objetivo, '
    'las tareas que se ejercitan en cada una, lo que se observa y su estado '
    'de ejecución. Las dos primeras se realizaron el 16 de octubre de 2026 '
    'sobre el entorno de producción descrito en la sección 4.3.1, con el '
    'usuario y los permisos propios de cada profesional; la tercera, la de '
    'recepción, queda pendiente y se registrará con la misma ficha.')

P_EVIDENCIA = (
    'El registro fotográfico de las dos sesiones realizadas se presenta en '
    'las figuras siguientes. En todas ellas la dirección que muestra el '
    'navegador es la del servidor de producción y la información en pantalla '
    'pertenece al conjunto de datos de demostración de la Tabla 74: ninguna '
    'de las pruebas se ejecutó sobre datos de pacientes reales, por la razón '
    'que precisa la sección 4.3.7.')

FIGURAS = [
    ('ev1_lee.jpg', 300,
     'Sesión 1. El Dr. Hee Joon Lee opera el sistema con su propio usuario '
     'sobre el entorno de producción: la barra superior identifica su rol de '
     'odontólogo con permiso de solo consulta y la agenda aparece filtrada a '
     '«Mi agenda (Hee Joon Lee)»'),
    ('ev2_giron.jpg', 301,
     'Sesión 2. La Dra. Rachelle Girón trabaja sobre el módulo principal con '
     'la agenda semanal de la clínica y el buscador de espacios «¿Dónde cabe '
     'este procedimiento?»'),
    ('ev3_detalle_cita.jpg', 302,
     'Sesión 2. Consulta del detalle de una cita, donde el sistema conserva '
     'la duración estimada junto a la duración real registrada de la atención'),
    ('ev4_listado_citas.jpg', 303,
     'Listado de citas del 15 y del 16 de octubre de 2026 consultado durante '
     'las sesiones, con la duración asignada por el sistema, la duración real '
     'y el estado de cada atención'),
]

P_VERIFICADO = (
    'Las sesiones comprobaron sobre el entorno de producción, y no sobre el '
    'de desarrollo, tres comportamientos de los que depende el resto del '
    'sistema. El primero es el control de acceso por rol: cada profesional '
    'ingresó con su propio usuario y el sistema le presentó la agenda y los '
    'permisos que le corresponden, como muestra el distintivo de solo '
    'consulta de la Figura 300. El segundo es la construcción de la agenda y '
    'de los indicadores a partir de los datos cargados, que la Figura 301 '
    'recoge para la semana del 12 al 17 de octubre de 2026: siete citas en el '
    'día, 62 % de utilización de la agenda, veinticuatro pacientes activos y '
    'una desviación media de 0.9 minutos. El tercero es la conservación de la '
    'duración estimada junto a la real en cada cita, visible tanto en el '
    'detalle de la Figura 302 como en el listado de la Figura 303; es el dato '
    'del que se alimenta el reentrenamiento descrito en la sección 4.2.3.10 y '
    'el único que el sistema no puede obtener por sí mismo.')

P_INDICADOR = (
    'Conviene precisar el significado del indicador de desviación media, '
    'porque no coincide con el error del modelo y la diferencia podría leerse '
    'como una contradicción. El indicador de la pantalla de inicio es la '
    'diferencia entre el promedio de la duración real y el promedio de la '
    'duración asignada del conjunto de atenciones registradas, de modo que '
    'las desviaciones por exceso y por defecto se compensan entre sí; el '
    'error absoluto medio de la Tabla 68 se calcula atención por atención y '
    'no admite esa compensación, y por eso asciende a 4.67 minutos. El '
    'primero responde si la agenda, en conjunto, se queda corta o larga; el '
    'segundo, cuánto se equivoca el sistema en cada cita. Ambos son '
    'necesarios: una agenda puede estar equilibrada en promedio y, aun así, '
    'desplazar todas las citas de la tarde.')

P_PENDIENTE = (
    'Queda pendiente la tercera sesión, la de recepción, y con ella la etapa '
    'de uso autónomo de los tres perfiles, que por su naturaleza exige varios '
    'días de operación continua. Los siete hallazgos que presenta la sección '
    'siguiente se identificaron durante la construcción y la verificación de '
    'las pantallas, antes de estas sesiones; las observaciones que resulten '
    'de la sesión pendiente y del uso autónomo se incorporarán al mismo '
    'registro, con la ficha de la Tabla 78 como instrumento.')

P_RESULTADO = (
    ' Las sesiones de prueba de implementación con los dos odontólogos se '
    'realizaron el 16 de octubre de 2026 sobre ese entorno, conforme al '
    'registro de la sección 4.3.5.')


def main():
    doc = Document(str(ARCHIVO))
    s = doc.sections[0]
    ancho = s.page_width - s.left_margin - s.right_margin
    alto = (s.page_height - s.top_margin - s.bottom_margin
            - Emu(int(1.4 * 914400)))
    alto = min(int(alto), int(7.20 * 914400))

    def recorrer():
        items = []
        for h in doc.element.body.iterchildren():
            if h.tag.endswith('}p'):
                items.append(Paragraph(h, doc))
            elif h.tag.endswith('}tbl'):
                items.append(Table(h, doc))
        return items

    def buscar(inicio):
        for o in recorrer():
            if isinstance(o, Paragraph) and o.text.strip().startswith(inicio):
                return o
        raise SystemExit(f'No se encontró: {inicio!r}')

    def tabla_de(pie_texto):
        items = recorrer()
        for i, o in enumerate(items):
            if isinstance(o, Paragraph) and o.text.strip().startswith(pie_texto):
                return items[i - 1], o
        raise SystemExit(f'No se encontró el pie: {pie_texto!r}')

    # 1. El párrafo que anunciaba las sesiones como previstas.
    escribir(buscar('Con esa ficha se planificaron tres sesiones'), P_SESIONES)

    # 2. Estado de ejecución en la Tabla 79 y su pie.
    t79, pie79 = tabla_de('Tabla 79:')
    estados = ['Realizada el 16/10/2026.',
               'Realizada el 16/10/2026.',
               'Pendiente de ejecución.']
    for fila, estado in zip(t79.rows[1:], estados):
        escribir(fila.cells[1].paragraphs[2], estado)
    for r in pie79.runs:
        if r.text.startswith('Sesiones de prueba'):
            r.text = ('Sesiones de prueba de implementación, con su objetivo, '
                      'los aspectos por observar y su estado de ejecución')

    # 3. Registro fotográfico, después del párrafo sobre el orden.
    ancla = buscar('El orden de las sesiones no es arbitrario')
    ancla = F.parrafo(doc, P_EVIDENCIA, ancla)
    for archivo, numero, titulo in FIGURAS:
        ruta = EVID / archivo
        if not ruta.exists():
            raise SystemExit(f'Falta la imagen: {ruta}')
        p = F.imagen(doc, ruta, ancla, ancho, alto)
        ancla = F.pie(doc, f'Figura {numero}', titulo, p)
    for texto in (P_VERIFICADO, P_INDICADOR, P_PENDIENTE):
        ancla = F.parrafo(doc, texto, ancla)

    # 4. Cierre de la sección 4.3.7.
    p966 = buscar('El sistema completa los tres procesos del alcance')
    escribir(p966, p966.text + P_RESULTADO)

    # 5. Pie de la Tabla 68: el conjunto es de 472 atenciones, no de 446.
    _, pie68 = tabla_de('Tabla 68:')
    for r in pie68.runs:
        if '446 atenciones' in r.text:
            r.text = r.text.replace('446 atenciones', '472 atenciones')

    doc.save(str(ARCHIVO))
    print('Sección 4.3.5 actualizada con el registro de las sesiones.')


if __name__ == '__main__':
    main()
