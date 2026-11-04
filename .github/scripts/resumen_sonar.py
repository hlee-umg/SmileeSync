"""Publica el estado del quality gate de SonarCloud y sus issues pendientes.

Consulta la API web de SonarCloud con el token del pipeline y escribe en la
salida estándar (Markdown) las condiciones del gate y los issues abiertos del
código nuevo de la rama o del pull request analizado.
"""

import json
import os
import urllib.parse
import urllib.request

API = "https://sonarcloud.io/api"
PROYECTO = "hlee-umg_SmileeSync"


def consultar(ruta, **parametros):
    url = f"{API}/{ruta}?{urllib.parse.urlencode(parametros)}"
    peticion = urllib.request.Request(  # noqa: S310 - URL fija de SonarCloud
        url, headers={"Authorization": f"Bearer {os.environ['SONAR_TOKEN']}"}
    )
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:  # noqa: S310
        return json.load(respuesta)


def alcance():
    """Rama o pull request que se analizó en esta ejecución."""
    pr = os.environ.get("PR_NUMERO")
    if pr:
        return {"pullRequest": pr}
    return {"branch": os.environ.get("RAMA", "main")}


def main():
    filtro = alcance()
    estado = consultar("qualitygates/project_status", projectKey=PROYECTO, **filtro)[
        "projectStatus"
    ]
    salida = [
        f"## Quality gate de SonarCloud: {estado['status']}",
        "",
        "| Métrica | Valor | Umbral | Resultado |",
        "|---------|------:|-------:|-----------|",
    ]
    for c in estado.get("conditions", []):
        icono = "✅" if c["status"] == "OK" else "❌"
        salida.append(
            f"| {c['metricKey']} | {c.get('actualValue', '-')} "
            f"| {c.get('comparator', '')} {c.get('errorThreshold', '')} "
            f"| {icono} {c['status']} |"
        )

    issues = consultar(
        "issues/search",
        componentKeys=PROYECTO,
        resolved="false",
        inNewCodePeriod="true",
        ps=100,
        **filtro,
    )
    salida += ["", f"### Issues abiertos en código nuevo: {issues['total']}", ""]
    if issues["issues"]:
        salida += [
            "| Severidad | Regla | Archivo | Línea | Mensaje |",
            "|---|---|---|---:|---|",
        ]
    for i in issues["issues"]:
        archivo = i["component"].split(":", 1)[-1]
        mensaje = i["message"].replace("|", "\\|")
        salida.append(
            f"| {i.get('severity', '')} | {i['rule']} | {archivo} "
            f"| {i.get('line', '')} | {mensaje} |"
        )
    print("\n".join(salida))


if __name__ == "__main__":
    main()
