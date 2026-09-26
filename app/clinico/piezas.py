"""Nomenclatura de las piezas dentales (sistema FDI de dos dígitos).

El primer dígito identifica el cuadrante y el segundo la posición de la pieza
contada desde la línea media. Se usa la dentición permanente, que es la que
atiende la clínica en la mayoría de sus procedimientos; la dentición temporal
(cuadrantes 5 a 8) queda fuera del alcance de esta entrega.
"""

CUADRANTES = [
    (1, 'Superior derecho', [18, 17, 16, 15, 14, 13, 12, 11]),
    (2, 'Superior izquierdo', [21, 22, 23, 24, 25, 26, 27, 28]),
    (4, 'Inferior derecho', [48, 47, 46, 45, 44, 43, 42, 41]),
    (3, 'Inferior izquierdo', [31, 32, 33, 34, 35, 36, 37, 38]),
]

PIEZAS = [p for _, _, piezas in CUADRANTES for p in piezas]

NOMBRES_POSICION = {
    1: 'Incisivo central', 2: 'Incisivo lateral', 3: 'Canino',
    4: 'Primer premolar', 5: 'Segundo premolar', 6: 'Primer molar',
    7: 'Segundo molar', 8: 'Tercer molar',
}


def es_valida(pieza):
    """Si el número corresponde a una pieza permanente del sistema FDI."""
    try:
        return int(pieza) in PIEZAS
    except (TypeError, ValueError):
        return False


def nombre(pieza):
    """Descripción legible de una pieza, p. ej. 'Primer molar superior derecho'."""
    if not es_valida(pieza):
        return str(pieza)
    pieza = int(pieza)
    cuadrante, posicion = divmod(pieza, 10)
    etiqueta = next((n for c, n, _ in CUADRANTES if c == cuadrante), '')
    return f'{NOMBRES_POSICION.get(posicion, "")} {etiqueta.lower()}'.strip()


def filas_arcada():
    """Los cuatro cuadrantes en el orden en que se dibujan en la pantalla."""
    return [{'cuadrante': c, 'nombre': n, 'piezas': piezas}
            for c, n, piezas in CUADRANTES]
