"""Manual de usuario: preguntas frecuentes y resolución de problemas."""
import json
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import SALIDA, faq, h, nota, p, pasos            # noqa: E402

PROBLEMAS = [
    ('El navegador dice que la conexión no es segura.',
     'Es una advertencia esperada mientras la clínica no instale el certificado de '
     'seguridad. Puede continuar, pero no registre datos reales de pacientes hasta '
     'que esa advertencia desaparezca.'),
    ('No recuerdo mi contraseña.',
     'Use «¿Olvidó su contraseña?» en la pantalla de ingreso y responda su pregunta '
     'secreta. Si tampoco recuerda la respuesta, el administrador puede restablecer '
     'su acceso.'),
    ('El sistema no me deja guardar una cita.',
     'El mensaje indica cuál condición no se cumple. Lo más frecuente es que la '
     'atención terminaría después del cierre de la franja del odontólogo, o que las '
     'dos unidades dentales ya están ocupadas en ese horario.'),
    ('No encuentro un botón que otra persona sí ve.',
     'Cada rol ve únicamente lo que le corresponde. Si necesita una función que no '
     'aparece, consúltelo con el administrador: puede ser un permiso y no una falla.'),
    ('La estimación de duración me parece equivocada.',
     'Escriba la duración a mano: el sistema la acepta. Y registre después el tiempo '
     'real de la atención, porque es así como la estimación se corrige para la '
     'próxima vez.'),
    ('El sistema no está disponible.',
     'La agenda del día puede imprimirse por anticipado desde la vista por día. Las '
     'atenciones se registran después; lo que importa es que las horas anotadas sean '
     'las reales, no el momento en que se capturaron.'),
    ('En el teléfono el menú ocupa toda la pantalla.',
     'Pulse el botón de menú de la esquina superior izquierda para plegarlo. Si el '
     'comportamiento persiste, actualice la página para que el navegador cargue la '
     'versión vigente.'),
]


def main():
    doc = Document(str(SALIDA))
    datos = json.load(open('faq.json', encoding='utf-8'))
    titulos = {'recepción': '8.1 Preguntas de la recepción',
               'odontólogos': '8.2 Preguntas del personal odontológico',
               'administrador': '8.3 Preguntas del administrador'}

    h(doc, '8. Preguntas frecuentes', salto=True)
    p(doc, 'Estas son las preguntas que el personal formuló durante las sesiones de '
      'capacitación, con la respuesta que se dio en cada caso.')
    for clave in ('recepción', 'odontólogos', 'administrador'):
        filas = datos.get(clave)
        if not filas:
            continue
        h(doc, titulos[clave], 2)
        faq(doc, [(f[0], f[1]) for f in filas[1:]])

    h(doc, '9. Si algo no funciona')
    faq(doc, PROBLEMAS)
    p(doc, '')
    nota(doc, 'Si el problema no está en esta lista, anote qué estaba haciendo, qué '
         'esperaba que ocurriera y qué ocurrió en su lugar, y repórtelo al '
         'administrador del sistema. Esos tres datos son los que permiten reproducir '
         'el problema y corregirlo.', 'Cómo reportar un problema')
    doc.save(str(SALIDA))
    print('Manual: preguntas frecuentes y resolución de problemas.')


if __name__ == '__main__':
    main()
