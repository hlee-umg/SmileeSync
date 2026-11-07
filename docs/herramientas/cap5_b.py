"""Capítulo 5, sección 5.1.3: las once sesiones con usuarios finales."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import SESIONES, titulo                            # noqa: E402

P_INTRO = (
    'Entre el 2 y el 23 de octubre de 2026 se ejecutaron once sesiones de prueba con '
    'el personal de la clínica, que suman once horas y cuarenta minutos de operación '
    'observada. Participaron tres personas sobre cuatro perfiles: el ortodoncista, '
    'que intervino cinco veces —tres como odontólogo y dos como administrador—; la '
    'odontóloga general, en dos sesiones; y la recepcionista, en cuatro. La Tabla 401 '
    'las relaciona en orden cronológico.')

P_NOTA_CONJUNTA = (
    'Las sesiones del 2 y del 9 de octubre con los dos odontólogos se condujeron de '
    'forma conjunta, en el mismo horario y frente al mismo equipo, por una razón '
    'práctica: ambos profesionales comparten las unidades dentales y la agenda, de '
    'modo que varias de las preguntas de uno resultaban pertinentes para el otro. La '
    'ficha se llenó por separado para cada uno, de manera que las observaciones '
    'quedaran atribuidas individualmente.')

P_LEE = (
    'El ortodoncista acumuló cinco sesiones y cinco horas y media de uso observado, '
    'el recorrido más extenso por ser además el administrador del sistema. En la '
    'primera, de media hora, se detuvo en todos los módulos por tratarse del primer '
    'contacto, y sus preguntas se concentraron en la pantalla principal: quiénes '
    'pueden ver las citas, quiénes pueden programarlas y cómo se modifican. Comentó '
    'que el flujo le parecía enredado y, al terminar, atribuyó esa impresión a la '
    'falta de familiaridad antes que al diseño. En la segunda sesión informó que '
    'había seguido usando el sistema por su cuenta y planteó tres puntos de mejora, '
    'de los cuales uno resultó un defecto real: la carga en teléfonos móviles no era '
    'utilizable. Las sesiones cuarta y quinta se dedicaron a los módulos de '
    'administración y fueron progresivamente autónomas; la última, de dos horas, '
    'transcurrió sin detenciones, sin preguntas y sin defectos observados, que es el '
    'indicador de que la capacitación concluyó.')

P_GIRON = (
    'La odontóloga general participó en dos sesiones que suman una hora y cincuenta '
    'minutos, concentradas en los dos módulos que constituyen su trabajo: la agenda y '
    'el expediente clínico. De sus observaciones, dos resultaron determinantes para '
    'el proyecto. La primera es de orden jurídico: advirtió que en Guatemala el '
    'expediente clínico electrónico no sustituye por sí solo al expediente en papel, '
    'lo que fijó la estrategia de implantación paralela descrita en la sección 5.1.2 '
    'y explica por qué el sistema no reemplaza todavía el registro físico. La segunda '
    'es técnica y coincidió con la del ortodoncista el mismo día: el menú no se '
    'comportaba correctamente en su teléfono. Preguntó, además, si era posible '
    'imprimir el expediente del paciente, solicitud que no está resuelta y que se '
    'recoge entre las recomendaciones.')

P_MARITZA = (
    'La recepcionista registró cuatro sesiones y cuatro horas y veinte minutos, y es '
    'el perfil cuya evolución resulta más ilustrativa. En la primera sesión manifestó '
    'que el uso le resultaba complejo y que se sentía cómoda con la hoja de cálculo '
    'que venía empleando; preguntó para qué le servían los reportes y solicitó acceso '
    'al plan de tratamiento. En la segunda, la navegación por agenda, expediente y '
    'pacientes ya fue autónoma y sus preguntas se desplazaron hacia los módulos que '
    'aún no dominaba, plan de tratamiento y cobros, con dos observaciones de fondo '
    'sobre la forma en que la clínica cobra: que los abonos se aplican al tratamiento '
    'completo y no a una pieza concreta, y que conviene registrar la referencia del '
    'pago. Las sesiones tercera y cuarta fueron autónomas; la última no registró '
    'detenciones, preguntas ni defectos. El desplazamiento de «esto es complejo» a una '
    'sesión sin preguntas, en quince días, es el resultado más relevante de la '
    'implantación, porque la recepción es el usuario principal del sistema y el que '
    'más resistencia oponía al cambio.')


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)
    a = C.buscar(doc, 'La capacitación se condujo con el guion', exacto=False)

    a = titulo(doc, '5.1.3 Descripción de las pruebas realizadas con usuarios finales', 3, a)
    a = F.parrafo(doc, P_INTRO, a)
    filas = [['N.°', 'Fecha', 'Horario', 'Participante', 'Rol', 'Etapa']]
    filas += [list(s) for s in SESIONES]
    t = F.tabla(doc, filas, a,
                anchos=[int(ancho * p) for p in (0.05, 0.12, 0.14, 0.22, 0.19, 0.28)])
    a = F.pie(doc, 'Tabla 401', 'Sesiones de prueba con usuarios finales ejecutadas '
              'entre el 2 y el 23 de octubre de 2026', t)
    for texto in (P_NOTA_CONJUNTA, P_LEE, P_GIRON, P_MARITZA):
        a = F.parrafo(doc, texto, a)
    doc.save(str(C.ARCHIVO))
    print('Sección 5.1.3 agregada.')


if __name__ == '__main__':
    main()
