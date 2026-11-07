"""Anexo C: las once fichas de registro firmadas de las sesiones."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402
import cap4_comun as C                                             # noqa: E402
from cap5_comun import titulo                                      # noqa: E402

PAG = C.RAIZ / 'evidencias' / 'paginas'

FICHAS = [
    ('dr_Hee_Joon_-_1_era_sesion_-_02102026', 'Dr. Hee Joon Lee', 1, '2 de octubre de 2026'),
    ('dra_Rachelle_-_1_era_sesion_-_02102026', 'Dra. Rachelle Girón', 1, '2 de octubre de 2026'),
    ('Maritza_-_1_era_sesion_-_02102026', 'Maritza Aguilar', 1, '2 de octubre de 2026'),
    ('dr_Hee_Joon_-_2_era_sesion_-_09102026', 'Dr. Hee Joon Lee', 2, '9 de octubre de 2026'),
    ('dra_Rachelle_-_2_era_sesion_-_09102026', 'Dra. Rachelle Girón', 2, '9 de octubre de 2026'),
    ('Maritza_-_2_era_sesion_-_09102026', 'Maritza Aguilar', 2, '9 de octubre de 2026'),
    ('dr_Hee_Joon_-_3_era_sesion_-_16102026', 'Dr. Hee Joon Lee', 3, '16 de octubre de 2026'),
    ('Maritza_-_3_era_sesion_-_16102026', 'Maritza Aguilar', 3, '16 de octubre de 2026'),
    ('Maritza_-_4_ta_sesion_-_17102026', 'Maritza Aguilar', 4, '17 de octubre de 2026'),
    ('dr_Hee_Joon_-_Admin_-_4_ta_sesion_-_17102026', 'Dr. Hee Joon Lee', 4,
     '17 de octubre de 2026'),
    ('dr_Hee_Joon_-_Admin_-_5_ta_sesion_-_23102026', 'Dr. Hee Joon Lee', 5,
     '23 de octubre de 2026'),
]

P_INTRO = (
    'Este anexo reproduce las once fichas de registro de las sesiones de prueba con '
    'usuarios finales documentadas en la sección 5.1.3. Cada ficha consta de dos '
    'hojas: la primera recoge los datos de la sesión, el rol con que el participante '
    'ingresó al sistema, la etapa del protocolo y los módulos ejercitados; la '
    'segunda, las observaciones —puntos de detención, preguntas formuladas, defectos '
    'observados, comentarios espontáneos y acciones derivadas— y la firma de quien '
    'participó. El instrumento es el de la Tabla 78 y se mantuvo invariable a lo '
    'largo del mes para que las observaciones resultaran comparables entre sí. Las '
    'fichas se presentan en orden cronológico.')


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)
    alto = min(int(alto), int(7.20 * C.PULGADA))
    a = C.buscar(doc, 'Anexo B. Diccionario de datos')
    # se inserta al final del documento, después del diccionario
    items = C.recorrer(doc)
    a = items[-1]

    a = titulo(doc, 'Anexo C. Fichas de registro de las sesiones de prueba', 2, a)
    a = F.parrafo(doc, P_INTRO, a)
    n = 600
    for archivo, quien, numero, fecha in FICHAS:
        for hoja in (2, 3):
            ruta = PAG / f'{archivo}-{hoja}.jpg'
            if not ruta.exists():
                raise SystemExit(f'Falta la imagen: {ruta}')
            a = F.imagen(doc, ruta, a, ancho, alto)
        a = F.pie(doc, f'Figura {n}', f'Ficha de registro de la sesión {numero} de '
                  f'{quien}, {fecha}', a)
        n += 1
    doc.save(str(C.ARCHIVO))
    print(f'Anexo C agregado con {len(FICHAS)} fichas.')


if __name__ == '__main__':
    main()
