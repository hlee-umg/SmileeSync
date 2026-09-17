#!/usr/bin/env python3
"""Cronograma de desarrollo (Gantt) de SmileeSync — Proyecto de Graduación II."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import date

# --- Paleta validada (dataviz: slots 1-3, all-pairs PASS sobre fondo blanco) ---
AZUL = '#2a78d6'     # Análisis y diseño
NARANJA = '#eb6834'  # Desarrollo de módulos
AQUA = '#1baf7a'     # Modelo predictivo y cierre

TINTA = '#0b0b0b'
TINTA_2 = '#52514e'
MUDO = '#898781'
REJILLA = '#e1e0d9'
EJE = '#c3c2b7'

# (etiqueta, inicio, fin, grupo)
TAREAS = [
    ('Levantamiento de requerimientos',            date(2026, 8, 3),  date(2026, 8, 21), AZUL),
    ('Análisis de la solución y factibilidades',   date(2026, 8, 17), date(2026, 9, 5),  AZUL),
    ('Diseño de la base de datos (modelo relacional)', date(2026, 8, 24), date(2026, 9, 12), AZUL),
    ('Diseño UML y de interfaces',                 date(2026, 8, 31), date(2026, 9, 19), AZUL),

    ('Configuración del entorno e infraestructura AWS', date(2026, 8, 24), date(2026, 9, 5), NARANJA),
    ('Sprint 1 — Seguridad y Usuarios',            date(2026, 9, 1),  date(2026, 9, 19), NARANJA),
    ('Sprint 2 — Módulo Principal y Agenda',       date(2026, 9, 22), date(2026, 10, 10), NARANJA),
    ('Sprint 3 — Pacientes y Catálogo Odontológico', date(2026, 10, 6), date(2026, 10, 24), NARANJA),
    ('Sprint 4 — Reportes e Indicadores',          date(2026, 10, 20), date(2026, 11, 7), NARANJA),

    ('Recolección y preparación de datos (CRISP-DM)', date(2026, 9, 22), date(2026, 10, 24), AQUA),
    ('Entrenamiento y comparación de algoritmos',  date(2026, 10, 19), date(2026, 11, 14), AQUA),
    ('Integración del módulo de Inteligencia',     date(2026, 11, 2),  date(2026, 11, 21), AQUA),
    ('Pruebas integrales y evaluación del modelo', date(2026, 11, 16), date(2026, 11, 28), AQUA),
    ('Despliegue final y documentación',           date(2026, 11, 23), date(2026, 12, 5),  AQUA),
]

HITOS = [
    ('Primera entrega',  date(2026, 8, 22)),
    ('Segunda entrega',  date(2026, 9, 19)),
    ('Tercera entrega',  date(2026, 10, 17)),
    ('Entrega final',    date(2026, 11, 28)),
]

fig, ax = plt.subplots(figsize=(12.5, 7.6), dpi=200)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

n = len(TAREAS)
ALTO = 0.58   # deja separación visible entre filas

for i, (etiqueta, inicio, fin, color) in enumerate(TAREAS):
    y = n - 1 - i
    x0 = mdates.date2num(inicio)
    ancho = mdates.date2num(fin) - x0
    ax.barh(y, ancho, left=x0, height=ALTO, color=color, linewidth=0, zorder=3)
    dias = (fin - inicio).days
    ax.text(x0 + ancho + 1.5, y, f'{dias} d', va='center', ha='left',
            fontsize=7.5, color=MUDO, zorder=4)

# --- Hitos de entrega: líneas verticales punteadas + rombo etiquetado ---
for etiqueta, f in HITOS:
    x = mdates.date2num(f)
    ax.axvline(x, color=TINTA_2, linestyle=(0, (3, 3)), linewidth=1.1, zorder=2, alpha=.75)
    ax.plot(x, n - 0.15, marker='D', markersize=7, color=TINTA,
            zorder=6, clip_on=False)
    ax.text(x, n + 0.12, f'{etiqueta}\n{f.strftime("%d/%m/%Y")}',
            ha='center', va='bottom', fontsize=8.5, color=TINTA,
            fontweight='bold', linespacing=1.5, clip_on=False)

ax.set_yticks(range(n))
ax.set_yticklabels([t[0] for t in reversed(TAREAS)], fontsize=9.5, color=TINTA)
ax.set_ylim(-0.7, n + 0.1)

MESES_ES = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}


def formato_mes_es(x, pos=None):
    d = mdates.num2date(x)
    return f'{MESES_ES[d.month]} {d.year}'


ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(plt.FuncFormatter(formato_mes_es))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.set_xlim(mdates.date2num(date(2026, 7, 29)), mdates.date2num(date(2026, 12, 12)))
ax.tick_params(axis='x', colors=TINTA_2, labelsize=9, length=0, pad=6)
ax.tick_params(axis='y', length=0, pad=6)

ax.grid(axis='x', which='major', color=EJE, linewidth=0.9, zorder=1)
ax.grid(axis='x', which='minor', color=REJILLA, linewidth=0.6, zorder=1)
ax.set_axisbelow(True)

for lado in ('top', 'right', 'left'):
    ax.spines[lado].set_visible(False)
ax.spines['bottom'].set_color(EJE)

leyenda = [
    Patch(facecolor=AZUL, label='Análisis y diseño'),
    Patch(facecolor=NARANJA, label='Desarrollo de módulos'),
    Patch(facecolor=AQUA, label='Modelo predictivo y cierre'),
]
ax.legend(handles=leyenda, loc='lower right', frameon=False, fontsize=9,
          ncol=3, bbox_to_anchor=(1.0, -0.14), labelcolor=TINTA_2)

ax.set_title('Cronograma de desarrollo del sistema SmileeSync',
             fontsize=13, color=TINTA, fontweight='bold', pad=44, loc='left')

plt.tight_layout()
plt.savefig('/tmp/diagramas/cronograma_gantt.png', dpi=200,
            bbox_inches='tight', facecolor='white')
print('Cronograma generado con', len(TAREAS), 'actividades y', len(HITOS), 'hitos.')
