# SmileeSync

Sistema web para la gestión inteligente de citas y agenda de la Clínica Dental Smilee.
Integra un módulo predictivo (duración de procedimientos) y un sistema de recomendación
de bloques de tiempo. Proyecto de Graduación II — Universidad Mariano Gálvez de Guatemala.

## Estructura

- `app/`   — Proyecto Django (backend + plantillas). Entrega actual: **login + módulo de usuarios**.
- `ml/`    — Entrenamiento offline del modelo y modelo exportado.
- `infra/` — Infraestructura como código con AWS CDK (Python).
- `docs/`  — Documentación y entregas.

## Entrega actual: Seguridad y Usuarios

- Autenticación (login / logout).
- Módulo de usuarios con CRUD, **borrado lógico** (estado Activo/Inactivo) e **historial de auditoría**.
- Control de acceso por rol (RBAC): el menú y el acceso a cada módulo dependen del rol.
  Roles base: Administrador, Recepcionista, Odontólogo, Asistente.

## Ejecutar en local

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # crea roles y usuarios de demostración
python manage.py runserver
```

Usuarios de demostración:

| Usuario     | Contraseña      | Rol           |
|-------------|-----------------|---------------|
| `admin`     | `***REMOVED***`     | Administrador |
| `recepcion` | `***REMOVED***` | Recepcionista |

## Base de datos

- Desarrollo: SQLite (por defecto).
- Producción: PostgreSQL. Definir `DB_ENGINE=postgres` y las variables `DB_*`.
