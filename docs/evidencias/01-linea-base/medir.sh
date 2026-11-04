#!/usr/bin/env bash
# Reproduce la medición de la línea base de calidad.
# Ejecutar desde app/ con el entorno virtual creado (Python 3.12):
#   pip install -r requirements.txt coverage ruff black radon bandit
#   python manage.py migrate && python manage.py seed
#   bash ../docs/evidencias/01-linea-base/medir.sh
set -u
E=../docs/evidencias/01-linea-base
P=.venv/Scripts/python
[ -x "$P" ] || P=.venv/bin/python
export PYTHONIOENCODING=utf-8
OMIT="*/migrations/*,prueba_*,.venv/*,manage.py,config/asgi.py,config/wsgi.py"

# 1. Pruebas existentes bajo cobertura
rm -f .coverage*
for s in horarios permisos calendario recomendacion flujos capacidad clinico modelo; do
    $P -m coverage run -p --source=. --omit="$OMIT" prueba_$s.py > $E/prueba_$s.txt 2>&1
done
$P -m coverage combine -q
$P -m coverage report > $E/cobertura.txt
$P -m coverage html -q -d $E/cobertura-html
$P -m coverage json -q -o $E/cobertura.json

# 2. Linter (Ruff) y formato (Black)
REGLAS=E,F,W,B,S,C90,DJ,UP,SIM
$P -m ruff check . --exclude .venv,migrations --select $REGLAS --statistics > $E/ruff-estadisticas.txt 2>&1
$P -m ruff check . --exclude .venv,migrations --select $REGLAS --output-format concise > $E/ruff-detalle.txt 2>&1
$P -m black --check . --extend-exclude "migrations|\.venv" > $E/black.txt 2>&1

# 3. Complejidad, mantenibilidad y tamaño (Radon)
$P -m radon cc . -e ".venv/*,*/migrations/*" -a -s -n C > $E/radon-complejidad.txt
$P -m radon mi . -e ".venv/*,*/migrations/*" -s > $E/radon-mantenibilidad.txt
$P -m radon raw . -e ".venv/*,*/migrations/*" -s | tail -12 > $E/radon-loc.txt

# 4. Seguridad (Bandit y chequeo de despliegue de Django)
$P -m bandit -r . -x ./.venv,./*/migrations -q -f txt -o $E/bandit.txt
K=$($P -c "import secrets;print(secrets.token_urlsafe(60))")
DJANGO_DEBUG=False DJANGO_SECRET_KEY=$K $P manage.py check --deploy > $E/django-check-deploy.txt 2>&1
