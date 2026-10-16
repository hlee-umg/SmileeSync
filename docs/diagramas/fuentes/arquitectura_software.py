"""Diagrama de arquitectura de software de SmileeSync (vista por capas)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

TINTA = '#0F172A'
BORDE_CAPA = '#64748B'
FONDO_CAPA = '#F8FAFC'
CAJA = '#EEF2FF'
BORDE_CAJA = '#4F46E5'
TEXTO_CAJA = '#1E1B4B'
FLECHA = '#334155'
VERDE = '#ECFDF5'
BORDE_VERDE = '#059669'

ANCHO, ALTO = 15.0, 9.6
fig, ax = plt.subplots(figsize=(ANCHO, ALTO))
ax.set_xlim(0, 100)
ax.set_ylim(14.5, 99)
ax.axis('off')

X0, X1 = 4, 68          # banda principal de capas
ALTO_CAPA = 12.0
SEP = 3.4


def capa(y, titulo, cajas, x0=X0, x1=X1, alto=ALTO_CAPA):
    """Dibuja una banda de capa con sus componentes repartidos a lo ancho."""
    ax.add_patch(FancyBboxPatch(
        (x0, y), x1 - x0, alto, boxstyle='round,pad=0,rounding_size=0.8',
        linewidth=1.3, edgecolor=BORDE_CAPA, facecolor=FONDO_CAPA, zorder=1))
    ax.text(x0 + 1.4, y + alto - 2.3, titulo, fontsize=11.5, weight='bold',
            color=TINTA, va='center', ha='left', zorder=3)

    n = len(cajas)
    margen = 1.8
    util = (x1 - x0) - margen * 2
    hueco = 1.6
    ancho = (util - hueco * (n - 1)) / n
    alto_caja = alto - 5.2
    for i, texto in enumerate(cajas):
        cx = x0 + margen + i * (ancho + hueco)
        ax.add_patch(FancyBboxPatch(
            (cx, y + 1.1), ancho, alto_caja,
            boxstyle='round,pad=0,rounding_size=0.6',
            linewidth=1.2, edgecolor=BORDE_CAJA, facecolor=CAJA, zorder=2))
        ax.text(cx + ancho / 2, y + 1.1 + alto_caja / 2, texto, fontsize=9.6,
                color=TEXTO_CAJA, va='center', ha='center', zorder=3,
                linespacing=1.45)
    return y


def flecha(x, y_desde, y_hasta, etiqueta='', dx=0, lado='der', estilo='-|>'):
    ax.add_patch(FancyArrowPatch(
        (x, y_desde), (x + dx, y_hasta), arrowstyle=estilo, mutation_scale=15,
        linewidth=1.4, color=FLECHA, zorder=4,
        connectionstyle='arc3,rad=0'))
    if etiqueta:
        ax.text(x + dx / 2 + (1.2 if lado == 'der' else -1.2),
                (y_desde + y_hasta) / 2, etiqueta, fontsize=8.8, color=FLECHA,
                va='center', ha='left' if lado == 'der' else 'right', zorder=5)


# ------------------------------------------------------------------ capas
y = 86.5
capa(y, 'CLIENTE', ['Navegador del usuario\nHTML 5 + Bootstrap 5'], alto=9.5)
y_cliente = y

y -= ALTO_CAPA + SEP
capa(y, 'CAPA DE PRESENTACIÓN',
     ['Plantillas Django\n(herencia de base.html)',
      'Procesador de contexto\nde permisos'])
y_pres = y

y -= ALTO_CAPA + SEP
capa(y, 'CAPA DE APLICACIÓN',
     ['Enrutador\nURL', 'Vistas\n(controladores)',
      'Formularios y\nvalidaciones', 'Decoradores de\ncontrol de acceso'])
y_apl = y

y -= ALTO_CAPA + SEP
capa(y, 'CAPA DE DOMINIO',
     ['Disponibilidad\nhorarios, ausencias,\nunidades y capacidad',
      'Servicio de estimación\ncascada de tres niveles',
      'Reglas del plan\nde tratamiento'])
y_dom = y

y -= ALTO_CAPA + SEP
capa(y, 'CAPA DE PERSISTENCIA',
     ['Modelos ORM de Django\n(24 entidades)'])
y_per = y

# Base de datos, bajo la capa de persistencia
y_bd = y_per - 9.0
ax.add_patch(FancyBboxPatch(
    (X0 + 22, y_bd), 22, 6.4, boxstyle='round,pad=0,rounding_size=0.8',
    linewidth=1.3, edgecolor=BORDE_VERDE, facecolor=VERDE, zorder=2))
ax.text(X0 + 33, y_bd + 3.2, 'PostgreSQL 16', fontsize=10.2, weight='bold',
        color='#064E3B', va='center', ha='center', zorder=3)

# --------------------------------------------------- componente predictivo
PX0, PX1 = 73, 96
ax.add_patch(FancyBboxPatch(
    (PX0, y_dom - 14.5), PX1 - PX0, ALTO_CAPA + 14.5,
    boxstyle='round,pad=0,rounding_size=0.8',
    linewidth=1.3, edgecolor=BORDE_CAPA, facecolor=FONDO_CAPA, zorder=1))
ax.text((PX0 + PX1) / 2, y_dom + ALTO_CAPA - 2.3, 'COMPONENTE PREDICTIVO',
        fontsize=11.5, weight='bold', color=TINTA, va='center', ha='center',
        zorder=3)
for i, (texto, dy) in enumerate([('Modelo entrenado\n(.joblib)', 0),
                                 ('Conjunto de entrenamiento\n(citas atendidas)', -11.5)]):
    ax.add_patch(FancyBboxPatch(
        (PX0 + 2, y_dom + 1.6 + dy), PX1 - PX0 - 4, 7.0,
        boxstyle='round,pad=0,rounding_size=0.6',
        linewidth=1.2, edgecolor=BORDE_CAJA, facecolor=CAJA, zorder=2))
    ax.text((PX0 + PX1) / 2, y_dom + 1.6 + dy + 3.5, texto, fontsize=9.6,
            color=TEXTO_CAJA, va='center', ha='center', zorder=3,
            linespacing=1.45)

# ---------------------------------------------------------------- flechas
EJE = 20
flecha(EJE, y_cliente, y_pres + ALTO_CAPA)
ax.text(EJE + 1.2, (y_cliente + y_pres + ALTO_CAPA) / 2, 'solicitud HTTPS',
        fontsize=8.8, color=FLECHA, va='center', ha='left', zorder=6,
        )
flecha(EJE, y_pres, y_apl + ALTO_CAPA, 'petición enrutada')
flecha(EJE, y_apl, y_dom + ALTO_CAPA, 'reglas de negocio')
flecha(EJE, y_dom, y_per + ALTO_CAPA, 'consultas y escrituras')
flecha(EJE + 13, y_per, y_bd + 6.4, 'SQL')

# Respuesta que sube por la derecha de la banda principal
ax.add_patch(FancyArrowPatch(
    (X1 - 6, y_apl + ALTO_CAPA), (X1 - 6, y_pres), arrowstyle='-|>',
    mutation_scale=15, linewidth=1.3, color=FLECHA, linestyle=(0, (5, 3)),
    zorder=4))
ax.text(X1 - 4.6, (y_apl + ALTO_CAPA + y_pres) / 2, 'respuesta\nrenderizada',
        fontsize=8.8, color=FLECHA, va='center', ha='left', linespacing=1.4)

# Dominio <-> componente predictivo
ax.add_patch(FancyArrowPatch(
    (X1, y_dom + 7.5), (PX0, y_dom + 7.5), arrowstyle='-|>',
    mutation_scale=15, linewidth=1.4, color=FLECHA, zorder=4))
ax.text((X1 + PX0) / 2, y_dom + 8.4, 'solicita la\nestimación', fontsize=8.6,
        color=FLECHA, va='bottom', ha='center', linespacing=1.4)
ax.add_patch(FancyArrowPatch(
    (PX0, y_dom + 4.2), (X1, y_dom + 4.2), arrowstyle='-|>',
    mutation_scale=15, linewidth=1.4, color=FLECHA, zorder=4))
ax.text((X1 + PX0) / 2, y_dom + 3.4, 'duración estimada', fontsize=8.6,
        color=FLECHA, va='top', ha='center')

# Persistencia -> conjunto de entrenamiento
ax.add_patch(FancyArrowPatch(
    (X1, y_per + 6), (PX0 + 1, y_dom - 6.4), arrowstyle='-|>',
    mutation_scale=15, linewidth=1.3, color=FLECHA, zorder=4,
    connectionstyle='arc3,rad=-0.18'))
ax.text(X1 + 1.0, y_per + 1.0, 'citas atendidas\n(realimentación)',
        fontsize=8.6, color=FLECHA, va='top', ha='left', linespacing=1.4,
        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none'), zorder=6)

# Entrenamiento -> modelo
ax.add_patch(FancyArrowPatch(
    ((PX0 + PX1) / 2, y_dom - 9.9 + 7.0), ((PX0 + PX1) / 2, y_dom + 1.6),
    arrowstyle='-|>', mutation_scale=14, linewidth=1.3, color=FLECHA,
    linestyle=(0, (4, 2.5)), zorder=4))
ax.text((PX0 + PX1) / 2 + 1.0, y_dom - 1.2, 'entrena', fontsize=8.6,
        color=FLECHA, va='center', ha='left')

plt.tight_layout(pad=0.4)
plt.savefig('arquitectura_software.png', dpi=200, facecolor='white',
            bbox_inches='tight')
print('listo')
