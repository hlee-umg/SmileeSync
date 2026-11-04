"""Genera el resumen de calidad (Markdown) de una ejecución del pipeline.

Lee los resultados de pytest (JUnit) y de cobertura (Cobertura XML) que deja la
etapa test, y el resultado de cada etapa que recibe por variables de entorno.
Se ejecuta desde app/ y escribe en la salida estándar.
"""

import os
import xml.etree.ElementTree as ET  # noqa: S405 - archivos generados por el propio pipeline
from pathlib import Path

ICONOS = {"success": "✅", "failure": "❌", "cancelled": "⏹️", "skipped": "⏭️"}
MINIMA = float(os.environ.get("COBERTURA_MINIMA", "70"))


def etapa(nombre):
    resultado = os.environ.get(f"RESULTADO_{nombre.upper()}", "desconocido")
    return f"| {nombre} | {ICONOS.get(resultado, '❔')} {resultado} |"


def pruebas():
    archivo = Path("junit.xml")
    if not archivo.exists():
        return ["No se generaron resultados de pruebas."]
    raiz = ET.parse(archivo).getroot()  # noqa: S314
    suite = raiz if raiz.tag == "testsuite" else raiz.find("testsuite")
    total = int(suite.get("tests", 0))
    fallidas = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    omitidas = int(suite.get("skipped", 0))
    aprobadas = total - fallidas - omitidas
    tiempo = float(suite.get("time", 0))
    return [
        "| Total | Aprobadas | Fallidas | Fallo esperado / omitidas | Tiempo |",
        "|------:|----------:|---------:|--------------------------:|-------:|",
        f"| {total} | {aprobadas} | {fallidas} | {omitidas} | {tiempo:.0f} s |",
    ]


def cobertura():
    archivo = Path("coverage.xml")
    if not archivo.exists():
        return ["No se generó el reporte de cobertura."]
    raiz = ET.parse(archivo).getroot()  # noqa: S314
    lineas = float(raiz.get("line-rate", 0)) * 100
    ramas = float(raiz.get("branch-rate", 0)) * 100
    estado = "✅" if lineas >= MINIMA else "❌"
    return [
        "| Líneas | Ramas | Umbral (QG-3) |",
        "|-------:|------:|--------------:|",
        f"| {lineas:.1f} % | {ramas:.1f} % | {estado} ≥ {MINIMA:.0f} % |",
    ]


def main():
    salida = [
        "## Resumen de calidad — SmileeSync",
        "",
        "### Etapas",
        "| Etapa | Resultado |",
        "|-------|-----------|",
        etapa("build"),
        etapa("test"),
        etapa("analyze"),
        "",
        "### Pruebas",
        *pruebas(),
        "",
        "### Cobertura",
        *cobertura(),
        "",
        "El detalle de Ruff, Black y Bandit está en el log de la etapa *analyze*; "
        "el de SonarCloud, en su panel y en el comentario del pull request.",
    ]
    print("\n".join(salida))


if __name__ == "__main__":
    main()
