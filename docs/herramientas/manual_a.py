"""Manual de usuario: portada, acceso, pantalla principal y recepción."""
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import (AZUL, GRIS, SALIDA, captura, faq, fuente, h, nota, p,
                          pasos)                                   # noqa: E402


def portada(doc):
    p(doc, '', despues=90)
    par = p(doc, 'SmileeSync', 36, True, AZUL, despues=0, centrado=True)
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p(doc, 'Manual de usuario', 20, False, GRIS, despues=4, centrado=True)
    p(doc, 'Sistema de gestión de citas y agenda', 12, False, GRIS, despues=120,
      centrado=True)
    p(doc, 'Clínica Dental Smilee', 12, True, None, despues=2, centrado=True)
    p(doc, 'Versión 1.0 · Octubre de 2026', 10.5, False, GRIS, centrado=True)
    doc.add_page_break()


def main():
    doc = Document()
    s = doc.sections[0]
    s.left_margin = s.right_margin = Inches(1.0)
    s.top_margin = s.bottom_margin = Inches(0.9)
    portada(doc)

    h(doc, '1. Sobre este manual')
    p(doc, 'SmileeSync es el sistema con que la Clínica Dental Smilee programa sus '
      'citas, registra las atenciones y documenta el expediente clínico de sus '
      'pacientes. Este manual explica cómo usarlo, y está organizado por el trabajo '
      'de cada quien: hay un capítulo para la recepción, uno para el personal '
      'odontológico y uno para quien administra el sistema. No hace falta leerlo '
      'completo: basta con el capítulo que corresponde al puesto, más los dos '
      'primeros, que son comunes a todos.')
    p(doc, 'Cada procedimiento se explica en pasos numerados y se acompaña de la '
      'pantalla tal como aparece en el sistema. Al final hay un apartado de preguntas '
      'frecuentes por puesto y otro sobre qué hacer cuando algo no funciona.')

    h(doc, '2. Antes de empezar')
    p(doc, 'El sistema es un sitio web: no se instala nada. Se abre desde cualquier '
      'navegador moderno —Chrome, Edge o Firefox— escribiendo la dirección que la '
      'clínica le proporcionó. Funciona en computadora, tableta y teléfono; para el '
      'calendario semanal conviene la computadora, porque muestra seis días a la vez.')
    nota(doc, 'Al abrir el sistema el navegador puede advertir que la conexión no es '
         'segura. Es una advertencia esperada mientras la clínica no instale el '
         'certificado de seguridad, y no significa que el sistema esté dañado. Por esa '
         'misma razón, mientras esa advertencia aparezca no deben registrarse datos '
         'reales de pacientes.', 'Sobre el aviso de seguridad')
    p(doc, 'Cada persona entra con su propio usuario. No se comparten cuentas, y no es '
      'una formalidad: el sistema deja constancia de quién registró cada cita, cada '
      'cobro y cada nota clínica, de modo que una cuenta compartida impide saber quién '
      'hizo qué.')

    h(doc, '3. Ingresar al sistema')
    pasos(doc, [
        'Abra el navegador y escriba la dirección del sistema.',
        'Escriba su correo electrónico y su contraseña.',
        'Pulse «Ingresar».',
    ])
    captura(doc, '01_login.png', 'Pantalla de ingreso')
    p(doc, 'Si olvidó su contraseña, pulse «¿Olvidó su contraseña?» en esa misma '
      'pantalla. El sistema le pedirá su correo y después la respuesta a la pregunta '
      'secreta que eligió al crear su cuenta; si la respuesta es correcta, podrá '
      'definir una contraseña nueva. La respuesta no distingue mayúsculas de '
      'minúsculas.')

    h(doc, '4. La pantalla principal')
    p(doc, 'Al entrar, el sistema muestra la agenda de la semana. En la parte superior '
      'hay cuatro indicadores: las citas del día, el porcentaje de ocupación de la '
      'agenda, los pacientes activos y la desviación media, que es la diferencia '
      'promedio entre el tiempo que se reservó para las atenciones y el que realmente '
      'tomaron.')
    captura(doc, '02_principal_semana.png', 'Pantalla principal con la agenda semanal')
    p(doc, 'Debajo de los indicadores está el buscador de espacios, rotulado «¿Dónde '
      'cabe este procedimiento?». Se elige el procedimiento, el odontólogo y el número '
      'de piezas, y el sistema calcula cuánto durará la atención y resalta en el '
      'calendario los espacios donde cabe. Es el punto de partida para programar una '
      'cita sin tener que revisar el calendario a ojo.')
    captura(doc, '03_principal_recomendacion.png',
            'Buscador de espacios con los huecos disponibles resaltados')
    p(doc, 'El selector de la derecha cambia entre la vista por semana y la vista por '
      'día. La vista por día muestra las citas de una jornada con su hora, su '
      'duración y la unidad dental asignada, y es la que conviene imprimir cada '
      'mañana.')
    doc.save(str(SALIDA))
    print('Manual: secciones 1 a 4.')


if __name__ == '__main__':
    main()
