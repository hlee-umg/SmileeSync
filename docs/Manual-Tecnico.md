# Manual Técnico — Pipeline CI/CD con Aseguramiento de Calidad de SmileeSync

| Dato | Valor |
|------|-------|
| Versión | 1.0, 2026-11-04 |
| Workflow | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| Configuración de calidad | [`app/pyproject.toml`](../app/pyproject.toml), [`sonar-project.properties`](../sonar-project.properties) |
| Documentos relacionados | [SQA Plan](SQA-Plan.md) · [Matriz de Pruebas](Matriz-Pruebas.md) · [Línea Base](Linea-Base-Calidad.md) · [Reporte de Mejora](Reporte-Mejora.md) |

Este manual describe cómo está construido el pipeline de integración y entrega continua de
SmileeSync, por qué se tomaron sus decisiones técnicas y cómo se mantiene. Está dirigido a
quien tenga que modificar el pipeline, agregar pruebas o diagnosticar un fallo.

## 1. Arquitectura general

```
  Desarrollador                GitHub                          Servicios externos
 ┌─────────────┐  push / PR  ┌──────────────────────────┐
 │ rama de     │────────────►│ Repositorio SmileeSync   │
 │ trabajo     │             │  main (protegida)        │
 └─────────────┘             └────────────┬─────────────┘
                                          │ dispara
                                          ▼
                             ┌──────────────────────────┐  análisis + cobertura  ┌────────────┐
                             │ GitHub Actions (ci.yml)  │───────────────────────►│ SonarCloud │
                             │ build·test·analyze·report│◄───────────────────────│ quality    │
                             └────────────┬─────────────┘  estado del gate       │ gate       │
                                          │ solo push a main y gates en verde    └────────────┘
                                          ▼
                             ┌──────────────────────────┐
                             │ AWS EC2 (producción)     │
                             │ Nginx · Gunicorn · Django│
                             │ PostgreSQL               │
                             └──────────────────────────┘
```

| Componente | Tecnología | Función |
|------------|------------|---------|
| Aplicación | Django 5.2 LTS, Python 3.12 | Sistema web de la clínica (8 módulos) |
| Base de datos | PostgreSQL (producción y CI), SQLite (desarrollo) | Persistencia |
| Repositorio | GitHub (`hlee-umg/SmileeSync`, público) | Código, pull requests, protección de `main` |
| CI/CD | GitHub Actions | Ejecuta el pipeline en cada push y pull request |
| Análisis estático | Ruff, Black, Bandit, SonarCloud | Quality gates QG-4 a QG-7 |
| Pruebas | pytest, pytest-django, pytest-cov | Quality gates QG-2 y QG-3 |
| Producción | AWS EC2 (Nginx + Gunicorn) | Recibe el despliegue automático |

## 2. Arquitectura del pipeline

### 2.1 Flujo

```
 push (cualquier rama) ─┐
 pull request → main ───┼──►  build ──► test ──► analyze ──► report
 ejecución manual ──────┘       │        │         │           │
                              QG-1    QG-2,3    QG-4,5,6,7   resumen
                                                   │
                                                   └──► deploy ──► EC2
                                          (solo push a main y si build,
                                           test y analyze pasaron)
```

- Las etapas son **jobs encadenados con `needs`**: si una falla, las siguientes no corren y
  el commit queda marcado en rojo.
- **report** corre siempre (`if: always()`), también cuando algo falló, para publicar el
  resultado.
- **deploy** solo corre en `push` a `main`. En una rama o en un pull request aparece como
  *skipped*.
- `concurrency` cancela la ejecución anterior de la misma rama cuando llega un push nuevo.

### 2.2 Etapas

| Etapa | Qué hace | Gates | Duración aprox. |
|-------|----------|-------|----------------:|
| **build** | Instala Python 3.12 y dependencias (con caché de pip); `manage.py check`; `makemigrations --check` | QG-1 | 45 s |
| **test** | Levanta PostgreSQL 16 como contenedor de servicio; ejecuta pytest con cobertura; guarda `junit.xml`, `coverage.xml` y `htmlcov/` como artefacto | QG-2, QG-3 | 2–3 min |
| **analyze** | Ruff, Black y Bandit; descarga la cobertura de *test* y ejecuta SonarCloud esperando el resultado del gate; publica el detalle del gate | QG-4 a QG-7 | 3–4 min |
| **report** | Genera el *Resumen de calidad* (etapas, pruebas y cobertura) en la página de la ejecución | — | 10 s |
| **deploy** | Entra por SSH a la EC2: `git pull`, dependencias, migraciones, `collectstatic` y reinicio de Gunicorn | — | 1 min |

### 2.3 Quality gates

| Gate | Condición para pasar | Dónde se configura | Cómo cambiar el umbral |
|------|----------------------|--------------------|------------------------|
| QG-1 Build | `check` sin errores y sin migraciones pendientes | `ci.yml`, job *build* | — |
| QG-2 Pruebas | 100 % de las pruebas aprobadas | `ci.yml`, job *test* | — |
| QG-3 Cobertura | ≥ 70 % (líneas y ramas) | `ci.yml`, variable `COBERTURA_MINIMA` | Editar la variable en `env:` |
| QG-4 Linter | 0 hallazgos de Ruff | `app/pyproject.toml`, `[tool.ruff]` | Reglas en `select`, complejidad en `max-complexity` |
| QG-5 Formato | 0 archivos por formatear | `app/pyproject.toml`, `[tool.black]` | `line-length` |
| QG-6 Seguridad | 0 issues de Bandit de severidad media o alta | `ci.yml` (`-ll`), `[tool.bandit]` | `-l` (bajo) o `-lll` (solo alto) |
| QG-7 SonarCloud | Gate "Sonar way" aprobado en el código nuevo | SonarCloud (plan Free) | No editable en el plan Free |

El gate **Sonar way** exige sobre el código nuevo: calificaciones A de confiabilidad,
seguridad y mantenibilidad; cobertura ≥ 80 %; duplicación ≤ 3 %, y todos los *security
hotspots* revisados.

### 2.4 Artefactos y reportes

| Dónde | Qué se encuentra |
|-------|------------------|
| Página de la ejecución → **Summary** | *Resumen de calidad* (etapas, pruebas y cobertura) y *Quality gate de SonarCloud* (condiciones e issues del código nuevo) |
| Página de la ejecución → **Annotations** | Cada hallazgo de Ruff marcado en su archivo y línea |
| Artefacto **resultados-pruebas** (30 días) | `junit.xml`, `coverage.xml` y reporte HTML de cobertura (`htmlcov/index.html`) |
| Pull request | Comentario de SonarCloud con el estado del gate y la lista de checks |
| SonarCloud → proyecto `hlee-umg_SmileeSync` | Panel con métricas, historial (*Activity*) e issues |

## 3. Decisiones técnicas

| # | Decisión | Alternativas consideradas | Motivo |
|---|----------|---------------------------|--------|
| D1 | Mantener el stack **Django + PostgreSQL** | Migrar a React + Express + MySQL | El enunciado permite variantes justificadas y la aplicación ya está en producción; reescribirla está fuera de alcance. Ver la equivalencia de herramientas en el SQA Plan, sección 2.2 |
| D2 | **pytest + pytest-django** | `unittest` / `manage.py test` | Fixtures reutilizables, parametrización (un caso por conjunto de datos), marcas `unit` / `integration` / `regression` y reporte JUnit nativo |
| D3 | **PostgreSQL 16 en CI**, SQLite en local | SQLite en todos lados | El pipeline prueba con el mismo motor que producción (riesgo R3); en local se mantiene la simplicidad |
| D4 | Los 8 scripts originales corren como **regresión sobre una base nueva y sembrada** (`runpy` + `manage.py seed`) | Reescribirlos como pruebas pytest | Conservan sus 300+ verificaciones de flujos completos sin reescribirlas; el aislamiento eliminó los 12 fallos de la línea base |
| D5 | Bugs conocidos documentados con **`xfail(strict=True)`** | Dejar la prueba en rojo o no escribirla | El bug queda probado y visible sin bloquear el pipeline; al corregirlo, `strict` obliga a quitar la marca |
| D6 | **Ruff** como linter | flake8 + plugins, pylint | Una sola herramienta con reglas de pycodestyle, pyflakes, bugbear, seguridad, complejidad y Django; anota los hallazgos en GitHub |
| D7 | **Black en un commit aparte** registrado en `.git-blame-ignore-revs` | Formatear junto con las correcciones | El diff de las correcciones sigue siendo legible (riesgo R8) y `git blame` ignora el cambio de formato |
| D8 | **Bandit con `-ll`** | Bloquear también los hallazgos bajos | Los hallazgos bajos que quedan son falsos positivos documentados (generador aleatorio de datos de demostración) |
| D9 | SonarCloud por **análisis desde CI** | Análisis automático | El automático no recibe la cobertura de pytest ni revisa dependencias; desde CI se obtienen ambas y el gate bloquea el pipeline (`sonar.qualitygate.wait=true`) |
| D10 | Umbrales propios (QG-1 a QG-6) en **GitHub Actions** | Gate personalizado en SonarCloud | El plan Free de SonarCloud no permite gates personalizados |
| D11 | Detalle del gate de SonarCloud **en el resumen de la ejecución** (`resumen_sonar.py`) | Revisar el panel de SonarCloud | Quien ve el fallo en GitHub sabe de inmediato qué condición y qué issue lo causó |
| D12 | **Deploy condicionado** a build, test y analyze | Despliegue independiente (como el `deploy.yml` original) | Producción solo recibe código que pasó todos los gates |
| D13 | **Django 5.0 → 5.2 LTS** | Mantener 5.0 o saltar a 6.x | 5.0 ya no recibe parches (15 CVE); 5.2 es LTS hasta abril de 2028 y no requirió cambios de código |
| D14 | Endurecimiento HTTPS activable con **`DJANGO_HTTPS`** | Activarlo siempre | El servidor puede estar sirviendo por HTTP; activarlo sin certificado dejaría el sitio inaccesible |
| D15 | Contraseñas de demostración desde **`SEED_PASSWORD`** o aleatorias | Contraseñas fijas en el código | SonarCloud las marcaba como Blocker; ninguna credencial queda en el repositorio |

## 4. Configuración

### 4.1 Secretos del repositorio (GitHub → Settings → Secrets and variables → Actions)

| Secreto | Uso | Etapa |
|---------|-----|-------|
| `SONAR_TOKEN` | Autenticación con SonarCloud (análisis y consulta del gate) | analyze |
| `EC2_HOST` | IP o dominio del servidor | deploy |
| `EC2_USER` | Usuario SSH del servidor | deploy |
| `EC2_SSH_KEY` | Llave privada SSH | deploy |

Las credenciales de PostgreSQL del job *test* no son secretos: pertenecen a una base
efímera que se destruye al terminar la ejecución.

### 4.2 Variables de entorno de la aplicación

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `DJANGO_DEBUG` | `True` | En producción debe ser `False` |
| `DJANGO_SECRET_KEY` | — | **Obligatoria con `DEBUG=False`**: sin ella la aplicación no arranca. En desarrollo se genera una clave local en `app/.clave-desarrollo` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Dominios permitidos |
| `DJANGO_CSRF_TRUSTED` | vacío | Orígenes de confianza para CSRF |
| `DJANGO_HTTPS` | `False` | `True` activa cookies seguras, redirección a HTTPS y HSTS |
| `DJANGO_HSTS_SECONDS` | `3600` | Duración de HSTS cuando `DJANGO_HTTPS=True` |
| `DB_ENGINE` y `DB_*` | SQLite | `DB_ENGINE=postgres` usa PostgreSQL con `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` |
| `SEED_PASSWORD` | aleatoria | Contraseña de las cuentas que crea `manage.py seed` |

Plantilla: [`app/.env.example`](../app/.env.example).

### 4.3 Archivos del pipeline

| Archivo | Contenido |
|---------|-----------|
| `.github/workflows/ci.yml` | Definición del pipeline |
| `.github/scripts/resumen_calidad.py` | Resumen de pruebas y cobertura (etapa report) |
| `.github/scripts/resumen_sonar.py` | Detalle del gate de SonarCloud (etapa analyze) |
| `.github/pull_request_template.md` | Lista de verificación de la revisión manual |
| `app/pyproject.toml` | Configuración de pytest, coverage, Ruff, Black y Bandit |
| `app/requirements.txt` / `app/requirements-dev.txt` | Dependencias de la aplicación / del pipeline |
| `sonar-project.properties` | Fuentes, pruebas, exclusiones y ruta de la cobertura para SonarCloud |
| `.git-blame-ignore-revs` | Commits de solo formato que `git blame` debe omitir |

### 4.4 Protección de la rama `main`

Reglas definidas en el SQA Plan (sección 11.1):

| Regla | Valor |
|-------|-------|
| Pull request obligatorio | Sí; aprobaciones requeridas: 0 (proyecto individual; la revisión manual se hace con la lista de la plantilla) |
| Checks obligatorios | `build`, `test`, `analyze` |
| Rama actualizada antes del merge | Sí |
| Conversaciones resueltas | Sí |
| Aplica a administradores | Sí |
| Force push y borrado de la rama | No permitidos |

> **Estado: aplicada el 2026-11-05.** GitHub solo permite proteger ramas de repositorios
> privados con GitHub Pro, así que el repositorio se hizo **público**. Antes se retiraron
> del repositorio las notas con credenciales (`claude/ONBOARDING.md`) y se rotaron las
> credenciales expuestas (Reporte de Mejora, SEC-06).

Se puede configurar desde **Settings → Rules → Rulesets → New branch ruleset** (destino: la
rama por defecto; reglas: *Restrict deletions*, *Block force pushes*, *Require a pull
request* con 0 aprobaciones y conversaciones resueltas, y *Require status checks* con
`build`, `test` y `analyze` y la rama actualizada) o por API.

Comando para aplicarlas (requiere permisos de administrador del repositorio):

```bash
gh api -X PUT repos/hlee-umg/SmileeSync/branches/main/protection --input proteccion.json
```

con `proteccion.json`:

```json
{
  "required_status_checks": { "strict": true, "contexts": ["build", "test", "analyze"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

## 5. Uso en el entorno local

```bash
cd app
python -m venv .venv
.venv\Scripts\activate                  # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
python manage.py migrate
```

| Tarea | Comando (desde `app/`) |
|-------|------------------------|
| Todas las pruebas | `pytest` |
| Por tipo | `pytest -m unit` · `pytest -m integration` · `pytest -m regression` |
| Con cobertura y umbral | `pytest --cov --cov-fail-under=70` |
| Linter | `ruff check .` (con `--fix` corrige lo automático) |
| Formato | `black .` (verificar: `black --check .`) |
| Seguridad | `bandit -c pyproject.toml -r . -ll` |
| Chequeo de producción | `DJANGO_DEBUG=False DJANGO_SECRET_KEY=<clave> python manage.py check --deploy` |
| Medición completa | `bash ../docs/evidencias/04-mejora/medir.sh` |

Antes de hacer push conviene ejecutar `ruff check .`, `black --check .` y `pytest`: son los
mismos gates que aplica el pipeline.

## 6. Guía de mantenimiento

### 6.1 Diagnóstico de un pipeline en rojo

| Etapa / paso que falla | Causa habitual | Qué hacer |
|------------------------|----------------|-----------|
| build → *Revisar la configuración* | Error de configuración de Django o import roto | Ejecutar `python manage.py check` en local |
| build → *Migraciones pendientes* | Cambio en un modelo sin migración | `python manage.py makemigrations` y agregar el archivo |
| test → pytest | Prueba fallida o diferencia SQLite/PostgreSQL | Leer el log; reproducir con `pytest -x -k <nombre>`. Si solo falla en CI, sospechar del motor de base de datos |
| test → cobertura | Cobertura < 70 % | Agregar pruebas del código nuevo (el log muestra las líneas sin cubrir) |
| analyze → Ruff | Hallazgo del linter | Ver **Annotations**; `ruff check . --fix` resuelve parte |
| analyze → Black | Archivo sin formato | `black .` y volver a hacer commit |
| analyze → Bandit | Riesgo de seguridad medio/alto | Corregir. Solo si es falso positivo: `# nosec <regla>` con justificación |
| analyze → SonarCloud | Gate no aprobado | El **Summary** muestra la condición que falló y los issues; corregirlos. Si `SONAR_TOKEN` falta o venció, regenerarlo en SonarCloud (*My Account → Security*) |
| deploy | Fallo de SSH o del servidor | Verificar los secretos `EC2_*`, que la instancia esté encendida y el log de Gunicorn |

### 6.2 Agregar una prueba

1. Crear `test_<tema>.py` en `app/tests/unit/` o `app/tests/integration/` según el nivel
   (SQA Plan, sección 7.1).
2. Marcar el módulo: `pytestmark = pytest.mark.unit` (o `integration`, o `regression`).
3. Usar las fixtures de `app/tests/conftest.py` (`admin`, `recepcionista`, `paciente`,
   `cita`, `cliente_recepcion`, etc.) en lugar de datos reales.
4. Registrar el caso en la [Matriz de Pruebas](Matriz-Pruebas.md) con un ID nuevo.
5. Si documenta un bug todavía sin corregir: `@pytest.mark.xfail(strict=True, reason="BUG-NN: ...")`.

### 6.3 Falsos positivos

| Herramienta | Cómo se marca | Regla |
|-------------|---------------|-------|
| Ruff | `# noqa: <REGLA>` en la línea, o `per-file-ignores` en `pyproject.toml` | Siempre con un comentario que explique por qué |
| Bandit | `# nosec <REGLA>` | Igual |
| SonarCloud | `# NOSONAR` en la línea, o *Accept* / *Safe* en la interfaz | Igual; queda registrado en el historial del issue |

Excepciones vigentes: `S311`/`S2245` (generador aleatorio con semilla del seed), `E402` en
los scripts de regresión (configuran Django antes de importar) y `S101`/`S105`/`S106` en las
pruebas (assert y claves de prueba).

### 6.4 Actualizar dependencias

1. Cambiar la versión en `requirements.txt` en una rama.
2. Ejecutar la suite completa: es la red de seguridad que permitió pasar de Django 5.0 a 5.2.
3. Revisar en SonarCloud → *Dependency risks* que no aparezcan vulnerabilidades nuevas.
4. **Precaución:** actualizar scikit-learn puede invalidar los modelos ya entrenados en
   producción (`app/modelos/`); después de actualizarlo hay que reentrenar
   (`python manage.py entrenar --algoritmo RF --activar`).

### 6.5 Antes del primer despliegue con esta versión

- El `.env` del servidor debe definir `DJANGO_SECRET_KEY` y `DJANGO_DEBUG=False`.
- El servidor debe tener Python ≥ 3.10 (requisito de Django 5.2).
- Si Nginx ya sirve por HTTPS (certbot), agregar `DJANGO_HTTPS=True`.

### 6.6 Regenerar los entregables .docx / .pdf

```bash
pip install -r docs/herramientas/requirements.txt
python docs/herramientas/generar_docx.py
```

Convierte los Markdown de `docs/` a Word con la portada institucional y los exporta a PDF
con Microsoft Word en `docs/entregables/`.

## 7. Limitaciones conocidas

| Limitación | Impacto | Seguimiento |
|------------|---------|-------------|
| En ramas de corta duración, SonarCloud solo evalúa el **código nuevo** | Las métricas globales se ven sobre `main` | Comparativa final en el Reporte de Mejora |
| GitHub avisa que las acciones con Node.js 20 están en desuso | Solo advertencia | Actualizar `actions/*` a sus versiones mayores nuevas cuando se publiquen |
| `ubuntu-latest` pasará a Ubuntu 26 | Posibles cambios en el entorno | Fijar `ubuntu-24.04` si aparece una incompatibilidad |
| HSTS sin `includeSubDomains` ni `preload` (`check --deploy` W005, W021) | Advertencias informativas | Decisión intencional: el preload es difícil de revertir |
| Catálogo con 75 % de cobertura | Módulo menos probado | Próximas pruebas de integración |
