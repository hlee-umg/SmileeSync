"""Fija todas las cifras del documento en el conjunto congelado del 27/10/2026.

El generador de datos de demostración construye la agenda en relación con la
fecha de ejecución, de modo que el número de atenciones y las métricas del
modelo cambian de un día a otro. Para que todas las cifras del documento
provengan del mismo conjunto, este se congeló el 27 de octubre de 2026 y se
conserva en el repositorio.
"""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import cap4_comun as C                                             # noqa: E402
import cifras as CI                                                # noqa: E402

TABLA_68 = [
    ['Métrica', 'Regresión lineal múltiple', 'Bosque aleatorio'],
    ['Registros de entrenamiento / de prueba', '334 / 112', '334 / 112'],
    ['Error absoluto medio (MAE)', '4.92 minutos', '3.53 minutos'],
    ['Raíz del error cuadrático medio (RMSE)', '6.20 minutos', '4.72 minutos'],
    ['Coeficiente de determinación (R²)', '0.905', '0.945'],
    ['MAE de la línea base (promedio global)', '16.79 minutos', '16.79 minutos'],
    ['Reducción frente a la línea base', '70.7 %', '79.0 %'],
    ['MAE de los bloques del catálogo', '6.46 minutos', '6.46 minutos'],
    ['Reducción frente al catálogo (hipótesis)', '23.8 %', '45.4 %'],
    ['Meta del proyecto', '25 %', '25 %'],
    ['Tiempo de entrenamiento', '0.005 segundos', '0.249 segundos'],
    ['Tamaño del archivo serializado', '1.9 KB', '509.0 KB'],
]

TABLA_69 = [
    ['Variable', 'Peso en el modelo', 'Procedencia del dato'],
    ['Número de piezas tratadas', '42.6 %', 'Nota clínica de la visita'],
    ['Procedimiento: tratamiento de conducto', '21.9 %', 'Cita'],
    ['Uso de anestesia', '15.5 %', 'Nota clínica de la visita'],
    ['Procedimiento: colocación de brackets', '8.0 %', 'Cita'],
    ['Procedimiento: retiro de brackets', '3.7 %', 'Cita'],
    ['Aparición de complicaciones', '1.9 %', 'Nota clínica de la visita'],
    ['Hora de inicio de la cita', '1.1 %', 'Cita'],
    ['Odontólogo responsable', '0.8 %', 'Cita'],
]

CAMBIOS_TABLA_74 = {
    '31/08/2026 al 30/10/2026': '14/09/2026 al 13/11/2026',
    'Seis semanas de historial y dos de agenda futura.':
        'Ocho semanas de historial y cuatro de agenda futura.',
    '663': '676',
    '472 atendidas, 155 programadas y 36 canceladas.':
        '446 atendidas, 195 programadas y 35 canceladas.',
}

PARRAFOS = [
    ('Se consideró además la biblioteca XGBoost',
     [('de 0.939 y redujo en 41.8 %', 'de 0.945 y redujo en 45.4 %')]),
    ('La Tabla 68 presenta el resultado del entrenamiento',
     [('conjunto de 472 atenciones registradas en el sistema, de las cuales 118 se reservaron',
       'conjunto congelado de 446 atenciones registradas en el sistema, de las cuales 112 se '
       'reservaron')]),
    ('Las dos comparaciones de la Tabla 68',
     [('las mismas 118 atenciones', 'las mismas 112 atenciones')]),
    ('El resultado es el que resuelve la hipótesis',
     [('Sobre esas 118 atenciones', 'Sobre esas 112 atenciones'),
      ('un error absoluto medio de 8.03 minutos y el modelo uno de 4.67, lo que representa '
       'una reducción de 41.8 %',
       'un error absoluto medio de 6.46 minutos y el modelo uno de 3.53, lo que representa '
       'una reducción de 45.4 %')]),
    ('Conviene precisar el significado del indicador de desviación media',
     [('y por eso asciende a 4.67 minutos', 'y por eso asciende a 3.53 minutos')]),
    ('El sistema completa los tres procesos del alcance',
     [('el modelo en producción reduce en 41.8 %', 'el modelo en producción reduce en 45.4 %')]),
    ('Quedan pendientes tres tareas',
     [('las cifras de este capítulo corresponden al conjunto de 472 atenciones con que se '
       'construyó y validó el sistema',
       'las cifras de este capítulo corresponden al conjunto de 446 atenciones congelado el 27 '
       'de octubre de 2026, con que se construyó y validó el sistema')]),
]


def sustituir(doc, prefijo, cambios):
    p = C.buscar(doc, prefijo, exacto=False)
    hechos = 0
    for viejo, nuevo in cambios:
        for r in p.runs:
            if viejo in r.text:
                r.text = r.text.replace(viejo, nuevo)
                hechos += 1
                break
        else:
            raise SystemExit(f'No se encontró «{viejo[:50]}…» en «{prefijo[:40]}…»')
    return hechos


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, _ = C.medidas(doc)

    CI.reemplazar_tabla(doc, 68, TABLA_68,
                        anchos=[int(ancho * p) for p in (0.44, 0.28, 0.28)])
    CI.reemplazar_tabla(doc, 69, TABLA_69,
                        anchos=[int(ancho * p) for p in (0.42, 0.20, 0.38)])
    print('Tablas 68 y 69 actualizadas.')

    for pie, viejo, nuevo in (('Tabla 68', '472 atenciones', '446 atenciones'),):
        p = CI.pie_de(doc, 'Tabla', 68)
        for r in p.runs:
            if viejo in r.text:
                r.text = r.text.replace(viejo, nuevo)
    print('Pie de la Tabla 68 actualizado.')

    tabla74 = None
    for o in C.recorrer(doc):
        if hasattr(o, 'rows'):
            tabla74 = o
        elif o.text.strip().startswith('Tabla 74:'):
            break
    n = 0
    for fila in tabla74.rows:
        for celda in fila.cells:
            for p in celda.paragraphs:
                for r in p.runs:
                    for viejo, nuevo in CAMBIOS_TABLA_74.items():
                        if r.text.strip() == viejo or viejo in r.text:
                            r.text = r.text.replace(viejo, nuevo)
                            n += 1
    print(f'Tabla 74: {n} celdas actualizadas.')

    for celda_vieja, celda_nueva in (('472', '446'),):
        for fila in tabla74.rows:
            for celda in fila.cells:
                for p in celda.paragraphs:
                    for r in p.runs:
                        if r.text.strip() == celda_vieja:
                            r.text = celda_nueva
    total = sum(sustituir(doc, prefijo, cambios) for prefijo, cambios in PARRAFOS)
    print(f'{total} sustituciones en el texto corrido.')
    doc.save(str(C.ARCHIVO))


if __name__ == '__main__':
    main()
