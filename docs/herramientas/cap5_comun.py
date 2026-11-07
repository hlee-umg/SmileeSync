"""Utilidades y datos compartidos por los scripts del capítulo 5."""
import sys
from pathlib import Path

from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).parent))
import formato as F                                                # noqa: E402

SESIONES = [
    ('1', '02/10/2026', '09:00 a 09:30', 'Dr. Hee Joon Lee', 'Odontólogo',
     'Capacitación inicial y uso acompañado'),
    ('1', '02/10/2026', '09:00 a 09:50', 'Dra. Rachelle Girón', 'Odontólogo',
     'Capacitación inicial y uso acompañado'),
    ('1', '02/10/2026', '14:00 a 15:15', 'Maritza Aguilar', 'Recepcionista',
     'Capacitación inicial y uso acompañado'),
    ('2', '09/10/2026', '09:00 a 10:13', 'Dr. Hee Joon Lee', 'Odontólogo',
     'Uso acompañado y autónomo'),
    ('2', '09/10/2026', '09:30 a 10:30', 'Dra. Rachelle Girón', 'Odontólogo',
     'Uso acompañado y autónomo'),
    ('2', '09/10/2026', '14:35 a 15:40', 'Maritza Aguilar', 'Recepcionista',
     'Uso acompañado'),
    ('3', '16/10/2026', '12:16 a 13:02', 'Dr. Hee Joon Lee', 'Odontólogo y administrador',
     'Capacitación inicial en administración'),
    ('3', '16/10/2026', '14:45 a 15:30', 'Maritza Aguilar', 'Recepcionista',
     'Uso autónomo'),
    ('4', '17/10/2026', '13:30 a 14:45', 'Maritza Aguilar', 'Recepcionista',
     'Uso autónomo'),
    ('4', '17/10/2026', '15:04 a 16:00', 'Dr. Hee Joon Lee', 'Administrador',
     'Uso acompañado y autónomo'),
    ('5', '23/10/2026', '08:00 a 10:05', 'Dr. Hee Joon Lee', 'Administrador',
     'Uso autónomo'),
]


def titulo(doc, texto, nivel, despues_de):
    """Encabezado con el tamaño que usa el documento: 14 pt el de capítulo."""
    p = F.titulo(doc, texto, nivel, despues_de)
    if nivel == 1:
        for r in p.runs:
            r.font.size = Pt(14)
    return p


def pie_tabla(doc, numero, titulo_texto, despues_de):
    return F.pie(doc, f'Tabla {numero}', titulo_texto, despues_de)
