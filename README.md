# SmileeSync

[![CI/CD SmileeSync](https://github.com/hlee-umg/SmileeSync/actions/workflows/ci.yml/badge.svg)](https://github.com/hlee-umg/SmileeSync/actions/workflows/ci.yml)
[![Quality Gate](https://img.shields.io/badge/SonarCloud-quality%20gate%20aprobado-brightgreen?logo=sonarcloud)](https://sonarcloud.io/project/overview?id=hlee-umg_SmileeSync)
[![Cobertura](https://img.shields.io/badge/cobertura-89%25-brightgreen)](docs/Matriz-Pruebas.md)
[![Pruebas](https://img.shields.io/badge/pruebas-177%20aprobadas-brightgreen?logo=pytest)](docs/Matriz-Pruebas.md)
[![Ruff](https://img.shields.io/badge/linter-ruff-261230?logo=ruff)](https://docs.astral.sh/ruff/)
[![Black](https://img.shields.io/badge/formato-black-000000)](https://black.readthedocs.io/)
![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/django-5.2%20LTS-092E20?logo=django)

Sistema web para la gestión inteligente de citas y agenda de la Clínica Dental Smilee.
Integra un módulo predictivo (duración de procedimientos) y un sistema de recomendación
de bloques de tiempo. Proyecto de Graduación II — Universidad Mariano Gálvez de Guatemala.

El proyecto incorpora además un **pipeline CI/CD con aseguramiento de calidad integrado**
(curso Aseguramiento de la Calidad de Software): cada cambio pasa por pruebas
automatizadas, análisis estático y quality gates antes de poder llegar a `main` y
desplegarse.

## Aseguramiento de la calidad

```
push / pull request ──► build ──► test ──► analyze ──► report
                                                 └──► deploy (solo main, si todo pasa)
```

| Gate | Herramienta | Umbral |
|------|-------------|--------|
| Build | Django `check` y migraciones | sin errores |
| Pruebas | pytest (unitarias, integración, regresión) sobre PostgreSQL | 100 % aprobadas |
| Cobertura | pytest-cov | ≥ 70 % |
| Linter | Ruff | 0 hallazgos |
| Formato | Black | 0 archivos |
| Seguridad | Bandit | 0 de severidad media o alta |
| Calidad global | SonarCloud (Sonar way) | gate aprobado |

| Documento | Contenido |
|-----------|-----------|
| [SQA Plan](docs/SQA-Plan.md) | Estándares, estrategia de pruebas, métricas, gates y riesgos |
| [Línea Base de Calidad](docs/Linea-Base-Calidad.md) | Métricas antes de la intervención |
| [Matriz de Pruebas](docs/Matriz-Pruebas.md) | Casos de prueba con resultado esperado y obtenido |
| [Reporte de Mejora](docs/Reporte-Mejora.md) | Comparativa antes / después |
| [Manual Técnico](docs/Manual-Tecnico.md) | Arquitectura del pipeline, decisiones y mantenimiento |

## Stack

| Capa | Tecnología |
|------|------------|
| Aplicación | Python 3.12, Django 5.2 LTS (vistas y plantillas del lado del servidor) |
| Base de datos | PostgreSQL (producción y CI), SQLite (desarrollo) |
| Modelo predictivo | scikit-learn, pandas |
| Pruebas | pytest, pytest-django, pytest-cov |
| Análisis estático | Ruff, Black, Bandit, SonarCloud |
| CI/CD | GitHub Actions → AWS EC2 (Nginx + Gunicorn) |
| Infraestructura | AWS CDK (Python) |

## Estructura

- `app/`   — Proyecto Django (backend + plantillas): los ocho módulos del sistema.
  - `app/tests/` — Pruebas unitarias, de integración y de regresión.
- `ml/`    — Entrenamiento offline del modelo y modelo exportado.
- `infra/` — Infraestructura como código con AWS CDK (Python).
- `docs/`  — Documentación, evidencias de calidad y herramientas para generar los entregables.
- `.github/` — Pipeline CI/CD y plantilla de pull request.

## Módulos implementados

| Módulo | Contenido |
|--------|-----------|
| Seguridad y Usuarios | Autenticación por correo, roles (RBAC), recuperación por pregunta secreta, auditoría. |
| Pacientes | Ficha, antecedentes médicos, historial de cambios. |
| Catálogo Odontológico | Especialidades, procedimientos y tarifas, odontólogos, unidades dentales. |
| Agenda y Citas (principal) | Calendario, estimación de duración, recomendación de espacios, horarios y ausencias, registro de tiempos reales. |
| Expediente Clínico | Odontograma (notación FDI), notas de evolución por visita. |
| Plan de Tratamiento y Cobros | Plan por fases, sesiones sugeridas, presupuesto, abonos y saldos. |
| Inteligencia | Entrenamiento y versionado del modelo; cadena de estimación de tres niveles. |
| Reportes e Indicadores | Utilización de la agenda, precisión de la estimación, carga por profesional. |

Todas las entidades aplican **borrado lógico** (campo `estado`) y las sensibles,
**historial de auditoría**.

## Verificación

```bash
cd app
pip install -r requirements-dev.txt
pytest                      # todas las pruebas, con base de datos aislada
pytest -m unit              # solo unitarias (también: integration, regression)
pytest --cov                # con reporte de cobertura
```

Los casos están documentados en [docs/Matriz-Pruebas.md](docs/Matriz-Pruebas.md).

## Modelo predictivo

```bash
python manage.py entrenar --algoritmo RF --activar      # entrena y pone en producción
python manage.py entrenar --algoritmo RF --solo-si-mejora
```

El entrenamiento se ejecuta fuera del proceso web: importar scikit-learn y pandas
añade ~140 MB al proceso, y el servidor de producción tiene 2 GB compartidos con
PostgreSQL. El proceso web solo carga el archivo serializado y lo conserva en memoria.

## Ejecutar en local

Requiere Python 3.10 o superior (se usa 3.12).

```bash
cd app
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed          # crea roles y usuarios de demostración
python manage.py runserver
```

Usuarios de demostración:

| Correo                        | Rol           |
|-------------------------------|---------------|
| `admin@smileesync.local`      | Administrador |
| `recepcion@smileesync.local`  | Recepcionista |
| `hjlee@smileesync.local`      | Odontólogo    |
| `rgiron@smileesync.local`     | Odontólogo    |

El inicio de sesión es por **correo**. La contraseña de las cuentas de demostración se
toma de la variable `SEED_PASSWORD`; si no está definida, `manage.py seed` genera una
aleatoria y la muestra al terminar.

## Configuración

Las variables de entorno se describen en [`app/.env.example`](app/.env.example) y en el
[Manual Técnico](docs/Manual-Tecnico.md#42-variables-de-entorno-de-la-aplicación). En
producción son obligatorias `DJANGO_DEBUG=False` y `DJANGO_SECRET_KEY`.

## Base de datos

- Desarrollo: SQLite (por defecto).
- Producción: PostgreSQL. Definir `DB_ENGINE=postgres` y las variables `DB_*`.
