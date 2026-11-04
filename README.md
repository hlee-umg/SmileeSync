# SmileeSync

Sistema web para la gestión inteligente de citas y agenda de la Clínica Dental Smilee.
Integra un módulo predictivo (duración de procedimientos) y un sistema de recomendación
de bloques de tiempo. Proyecto de Graduación II — Universidad Mariano Gálvez de Guatemala.

## Estructura

- `app/`   — Proyecto Django (backend + plantillas): los ocho módulos del sistema.
- `ml/`    — Entrenamiento offline del modelo y modelo exportado.
- `infra/` — Infraestructura como código con AWS CDK (Python).
- `docs/`  — Documentación y entregas.

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

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
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

El inicio de sesión es por **correo**. Las contraseñas de demostración las imprime
`manage.py seed` al terminar.

## Base de datos

- Desarrollo: SQLite (por defecto).
- Producción: PostgreSQL. Definir `DB_ENGINE=postgres` y las variables `DB_*`.
