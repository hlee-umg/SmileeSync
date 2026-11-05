#!/usr/bin/env bash
# Medición final de calidad, con las mismas herramientas de la línea base.
# Ejecutar desde app/ con el entorno virtual y requirements-dev.txt instalados.
set -u
E=../docs/evidencias/04-mejora
P=.venv/Scripts/python
[ -x "$P" ] || P=.venv/bin/python
export PYTHONIOENCODING=utf-8

# 1. Pruebas con cobertura (pytest)
$P -m pytest -p no:cacheprovider -q -rxX --cov --cov-report=term \
    --cov-report=json:$E/cobertura.json --junitxml=$E/resultados-junit.xml \
    > $E/pytest-salida.txt 2>&1

# 2. Linter y formato con la configuración del proyecto
$P -m ruff check . --statistics > $E/ruff.txt 2>&1
# Mismas reglas que la línea base, para una comparación directa
$P -m ruff check . --exclude .venv,migrations --select E,F,W,B,S,C90,DJ,UP,SIM \
    --line-length 88 --statistics > $E/ruff-reglas-linea-base.txt 2>&1
$P -m black --check . > $E/black.txt 2>&1

# 3. Complejidad, mantenibilidad y tamaño
$P -m radon cc . -e ".venv/*,*/migrations/*,tests/*" -a -s -n C > $E/radon-complejidad.txt
$P -m radon cc . -e ".venv/*,*/migrations/*,tests/*" -a -s | tail -1 >> $E/radon-complejidad.txt
$P -m radon mi . -e ".venv/*,*/migrations/*,tests/*" -s > $E/radon-mantenibilidad.txt
$P -m radon raw . -e ".venv/*,*/migrations/*,tests/*" -s | tail -12 > $E/radon-loc.txt

# 4. Seguridad
$P -m bandit -c pyproject.toml -r . -f txt -o $E/bandit.txt -q
K=$($P -c "import secrets;print(secrets.token_urlsafe(60))")
DJANGO_DEBUG=False DJANGO_SECRET_KEY=$K DJANGO_HTTPS=True \
    $P manage.py check --deploy > $E/django-check-deploy.txt 2>&1
