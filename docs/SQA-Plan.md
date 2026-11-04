# Plan de Aseguramiento de la Calidad del Software (SQA Plan) — SmileeSync

| Dato | Valor |
|------|-------|
| Proyecto | SmileeSync: gestión de citas y agenda de la Clínica Dental Smilee |
| Curso | Aseguramiento de la Calidad del Software (SQA), Universidad Mariano Gálvez |
| Responsable | Hee Sung Lee, carné 3190-11-342 |
| Versión del plan | 1.0, 2026-11-03 |
| Repositorio | `hlee-umg/SmileeSync`, rama de trabajo `qa/pipeline-sqa` |
| Estructura de referencia | IEEE Std 730-2014 (SQA Processes), adaptada al alcance del curso |

---

## 1. Propósito

Este plan define **cómo se asegura la calidad** de SmileeSync a partir de ahora: qué
estándares sigue el código, qué pruebas se ejecutan, qué métricas se miden, qué umbrales
debe cumplir cada cambio y qué herramientas lo verifican automáticamente.

Su objetivo es que **ningún cambio llegue a la rama `main` (y por tanto a producción)
sin pasar por un conjunto de verificaciones de calidad automatizadas** y que la mejora
sea medible frente a la [Línea Base de Calidad](Linea-Base-Calidad.md).

## 2. Alcance

### 2.1 Producto

SmileeSync es una aplicación web **Django 5 (Python 3.12)** con plantillas HTML del
lado del servidor y **PostgreSQL** en producción, desplegada en una instancia **AWS EC2**.
Tiene ocho módulos: Usuarios y Seguridad, Pacientes, Catálogo, Agenda y Citas, Expediente
Clínico, Plan de Tratamiento y Cobros, Inteligencia (modelo predictivo) y Reportes.

| Incluido | Excluido |
|----------|----------|
| Código Python de `app/` (los 8 módulos y `config/`) | Migraciones generadas por Django |
| Plantillas HTML de `app/templates/` (análisis estático en SonarCloud) | Entrenamiento offline de `ml/` (fuera del proceso web) |
| Workflow de GitHub Actions | Infraestructura `infra/` (CDK): solo análisis estático, sin pruebas |
| Configuración de seguridad de Django | Pruebas de carga, estrés y rendimiento (excluidas por el enunciado) |

### 2.2 Variante de stack (justificación)

El enunciado sugiere React + Express + MySQL y permite variantes justificadas. SmileeSync
es un proyecto real de Proyecto de Graduación II, ya en producción, por lo que se mantiene
su stack y se usan las herramientas equivalentes de Python. **Los conceptos de SQA
evaluados no cambian:**

| Concepto | Sugerido | Usado en SmileeSync |
|----------|----------|---------------------|
| Pruebas unitarias | Jest | **pytest + pytest-django** |
| Pruebas de API / integración | Supertest | **Django test client** (peticiones HTTP reales contra las vistas) |
| Pruebas de frontend | React Testing Library | Django test client sobre el HTML renderizado (no hay SPA) |
| Cobertura | Istanbul / nyc | **coverage.py (pytest-cov)** |
| Linter | ESLint | **Ruff** |
| Formateador | Prettier | **Black** |
| Análisis estático | SonarCloud | **SonarCloud** + **Bandit** (seguridad) |
| Base de datos | MySQL | **PostgreSQL** (servicio del pipeline, igual que producción) |
| CI/CD | GitHub Actions | **GitHub Actions** |

## 3. Documentos de referencia

| Documento | Uso |
|-----------|-----|
| [Linea-Base-Calidad.md](Linea-Base-Calidad.md) | Estado inicial de las métricas |
| [Matriz-Pruebas.md](Matriz-Pruebas.md) | Casos de prueba diseñados |
| [Reporte-Mejora.md](Reporte-Mejora.md) | Comparativa antes / después |
| [Manual-Tecnico.md](Manual-Tecnico.md) | Arquitectura del pipeline y mantenimiento |
| IEEE Std 730-2014 | Estructura del plan |
| ISO/IEC 25010 | Características de calidad del producto |
| PEP 8 | Estilo de código Python |
| OWASP Top 10 (2021) | Riesgos de seguridad web |

## 4. Organización y responsabilidades

| Rol | Responsabilidad |
|-----|-----------------|
| Desarrollador / responsable SQA | Escribe el código y las pruebas, mantiene el pipeline, corrige issues y actualiza la documentación |
| Pipeline (GitHub Actions) | Revisor automático: compila, prueba, analiza y bloquea el merge si falla un quality gate |
| SonarCloud | Revisor automático de calidad y seguridad; comenta en cada pull request |
| Revisor manual | Revisa el pull request con la lista de verificación de la sección 8.2 antes del merge |
| Docente | Evalúa los entregables y puede revisar el repositorio en vivo |

## 5. Características de calidad (ISO/IEC 25010)

| Característica | Por qué importa en SmileeSync | Cómo se verifica |
|----------------|------------------------------|------------------|
| **Adecuación funcional** | Agenda de citas sin choques de horario ni de unidades dentales | Pruebas unitarias, de integración y de regresión |
| **Seguridad** | Datos clínicos y personales de pacientes; roles con permisos distintos | Pruebas de permisos (RBAC), Bandit, SonarCloud, `check --deploy` |
| **Fiabilidad** | Un error en producción afecta la operación diaria de la clínica | Quality gates antes del despliegue; regresión automatizada |
| **Mantenibilidad** | Proyecto que seguirá creciendo | Ruff, Black, complejidad ciclomática, deuda técnica de SonarCloud |

## 6. Estándares y convenciones

| Ámbito | Estándar | Herramienta que lo hace cumplir |
|--------|----------|---------------------------------|
| Estilo Python | PEP 8, longitud de línea 88 | Ruff (`E`, `W`) |
| Errores lógicos | Imports sin usar, nombres redefinidos, malas prácticas | Ruff (`F`, `B`, `SIM`, `UP`) |
| Formato | Formato uniforme y automático | Black |
| Convenciones Django | Modelos con `__str__`, etc. | Ruff (`DJ`) |
| Complejidad | Complejidad ciclomática ≤ 15 por función en código nuevo | Ruff (`C90`), Radon |
| Seguridad | OWASP Top 10, sin secretos en el código | Bandit, Ruff (`S`), SonarCloud |
| Pruebas | Archivos `test_*.py` por módulo; una prueba verifica un comportamiento; nombres en español que describen el comportamiento | pytest |
| Commits | Mensaje en imperativo que describe el cambio | Revisión manual |
| Ramas | `main` protegida; trabajo en ramas `tipo/descripcion` (`feat/`, `fix/`, `test/`, `qa/`) | Protección de rama en GitHub |

## 7. Estrategia de pruebas

### 7.1 Niveles de prueba

| Nivel | Qué cubre | Ejemplos en SmileeSync | Marca pytest |
|-------|-----------|------------------------|--------------|
| **Unitarias** | Funciones, modelos, formularios y validadores aislados, sin peticiones HTTP | `agenda/disponibilidad.py`, `CitaForm.clean`, `clinico/piezas.py` (notación FDI), `config/validadores.py`, `inteligencia/evaluacion.py` | `unit` |
| **Integración** | Vista + formulario + modelo + base de datos + permisos, mediante peticiones HTTP con el test client | CRUD de pacientes, crear o cancelar una cita, acceso por rol, login por correo | `integration` |
| **Regresión** | Flujos completos ya validados que no deben romperse, y una prueba por cada bug corregido | Los 8 scripts `prueba_*.py` migrados a pytest; Open Redirect en `cancelar()` | `regression` |
| **E2E** (opcional) | Navegador real | No incluido en esta versión | — |

Reglas:

- **Cada prueba crea sus propios datos** (fixtures de pytest) en una base de datos aislada
  que se reinicia en cada prueba. Ninguna prueba depende de `manage.py seed` ni de la fecha
  actual, que es la causa probable de los 12 fallos de la línea base.
- **Las fechas se fijan** en las pruebas que dependen del calendario.
- **Cada bug corregido lleva una prueba de regresión** que falla antes de la corrección y
  pasa después.
- Los casos se documentan en la [Matriz de Pruebas](Matriz-Pruebas.md) con ID, tipo,
  entrada, resultado esperado y resultado obtenido.

### 7.2 Entornos

| Entorno | Base de datos | Uso |
|---------|---------------|-----|
| Local | SQLite | Desarrollo y ejecución rápida de pruebas |
| CI (GitHub Actions) | **PostgreSQL 16** (contenedor de servicio) | Pruebas con el mismo motor que producción |
| Producción (EC2) | PostgreSQL | Solo recibe código que pasó todos los quality gates |

## 8. Revisiones

### 8.1 Revisión automática (en cada push y pull request)

El pipeline ejecuta todas las verificaciones de la sección 10 y SonarCloud publica su
resultado en el pull request. **Si cualquiera falla, GitHub bloquea el merge.**

### 8.2 Revisión manual (lista de verificación del pull request)

- [ ] El cambio tiene pruebas y aparecen en la matriz de pruebas.
- [ ] El pipeline está en verde y el quality gate de SonarCloud aprobado.
- [ ] No se agregan secretos, contraseñas ni datos reales de pacientes.
- [ ] Los issues nuevos de SonarCloud están corregidos o justificados.
- [ ] La documentación afectada está actualizada.

La lista vive en la plantilla del pull request (`.github/pull_request_template.md`).

## 9. Métricas

| Métrica | Herramienta | Línea base | Meta |
|---------|-------------|-----------:|-----:|
| Pruebas automatizadas formales | pytest | 0 | ≥ 120 |
| Pruebas que fallan en `main` | pytest | 12 fallos en scripts | **0** |
| Cobertura de líneas global | coverage.py | 79 %* | **≥ 70 % (gate) · meta 80 %** |
| Cobertura del código nuevo | SonarCloud | — | ≥ 80 % |
| Hallazgos del linter | Ruff | 170 | **0** |
| Archivos sin formato | Black | 67 | **0** |
| Issues de seguridad Bandit (medio/alto) | Bandit | 0 | **0** |
| Calificación de seguridad | SonarCloud | **E** (27) | **A** |
| Calificación de confiabilidad | SonarCloud | **C** (61) | ≤ B |
| Calificación de mantenibilidad | SonarCloud | A (3) | A |
| Issues Blocker | SonarCloud | ≥ 4 | **0** |
| Duplicación | SonarCloud | 0,9 % | ≤ 3 % |
| Funciones con complejidad > 15 | Radon | 6 | ≤ 4 |
| Advertencias de `check --deploy` | Django | 4 | 0 en configuración de producción |

\* Obtenida con scripts manuales no reproducibles en CI. La cobertura de pytest se mide
desde cero.

Las métricas finales se registran en el [Reporte de Mejora](Reporte-Mejora.md).

## 10. Quality gates

Un cambio **solo puede llegar a `main`** si cumple **todas** estas condiciones. Cada una
hace fallar el pipeline cuando no se cumple.

| # | Gate | Umbral | Etapa del pipeline | Implementación |
|---|------|--------|--------------------|----------------|
| QG-1 | Build | Dependencias instaladas, `manage.py check` sin errores y sin migraciones pendientes | build | `check`, `makemigrations --check` |
| QG-2 | Pruebas | **100 % de las pruebas pasan** | test | `pytest` |
| QG-3 | Cobertura | **≥ 70 % de líneas** | test | `pytest --cov --cov-fail-under=70` |
| QG-4 | Linter | **0 hallazgos** | analyze | `ruff check` |
| QG-5 | Formato | **0 archivos** por formatear | analyze | `black --check` |
| QG-6 | Seguridad | **0 issues de severidad media o alta** | analyze | `bandit -ll` |
| QG-7 | SonarCloud | Quality gate **"Sonar way" aprobado** | analyze | `sonarqube-scan-action` con espera del resultado |

El quality gate **"Sonar way"** evalúa el **código nuevo** de cada cambio:

- 0 issues nuevos.
- Cobertura del código nuevo ≥ 80 %.
- Duplicación del código nuevo ≤ 3 %.
- Todos los security hotspots revisados.

> El plan Free de SonarCloud no permite crear quality gates personalizados. Por eso los
> umbrales propios del proyecto (QG-1 a QG-6) se aplican en GitHub Actions y SonarCloud
> aporta su gate estándar (QG-7).

## 11. Pipeline CI/CD

Archivo: `.github/workflows/ci.yml`. Se ejecuta en cada **push** y **pull request** hacia
`main`.

```
build ──► test ──► analyze ──► report ──► deploy (solo push a main)
```

| Etapa | Acciones | Gates |
|-------|----------|-------|
| **build** | Instalar Python 3.12 y dependencias; `manage.py check`; verificar migraciones | QG-1 |
| **test** | PostgreSQL de servicio; pytest (unitarias, integración, regresión) con cobertura | QG-2, QG-3 |
| **analyze** | Ruff, Black, Bandit; SonarCloud con la cobertura generada en *test* | QG-4 a QG-7 |
| **report** | Publicar los resultados de pruebas (JUnit), el reporte HTML de cobertura y el resumen en la página de la ejecución | — |
| **deploy** | SSH a la EC2: `git pull`, migraciones, `collectstatic` y reinicio de Gunicorn | Solo si todas las etapas anteriores pasaron |

### 11.1 Protección de la rama `main`

- Pull request obligatorio: no se permite push directo.
- Checks obligatorios: *build*, *test*, *analyze* y el quality gate de SonarCloud.
- La rama debe estar actualizada con `main` antes del merge.
- Las conversaciones del pull request deben estar resueltas.
- Las reglas se aplican también a los administradores.

### 11.2 Manejo de secretos

| Secreto | Dónde vive |
|---------|------------|
| `SONAR_TOKEN` | GitHub Secrets |
| `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` | GitHub Secrets (ya existentes) |
| Credenciales de la base de datos de CI | Variables del workflow (base efímera, no son secretos de producción) |
| `DJANGO_SECRET_KEY` de producción | Archivo `.env` en la EC2, fuera del repositorio |

## 12. Gestión de deuda técnica

1. **Identificación:** SonarCloud (issues y deuda en tiempo), Ruff y Radon.
2. **Clasificación por severidad:**

   | Severidad | Ejemplos | Tratamiento |
   |-----------|----------|-------------|
   | Blocker / crítica | Open Redirect, contraseñas en el código | Corregir en esta intervención |
   | Mayor | Imports sin usar, `raise` sin `from`, complejidad > 15 | Corregir en esta intervención |
   | Menor | Líneas largas, nombres de variable | Corrección automática (Black / Ruff `--fix`) |
   | Falso positivo o intencional | Subred pública de la EC2 (servidor web) | Marcar en SonarCloud como *Accepted* con justificación |

3. **Prevención:** el quality gate impide agregar deuda nueva porque exige 0 issues nuevos
   en el código modificado.
4. **Seguimiento:** cada corrección relevante se registra en el
   [Reporte de Mejora](Reporte-Mejora.md).

## 13. Plan de actividades

| Fase | Actividades | Entregable |
|------|-------------|------------|
| 1. Planeación | Línea base de calidad (local + SonarCloud); SQA Plan | `Linea-Base-Calidad.md`, `SQA-Plan.md` |
| 2. Pruebas | Configurar pytest; matriz de pruebas; pruebas unitarias, de integración y de regresión; cobertura ≥ 70 % | `Matriz-Pruebas.md`, `app/*/tests/` |
| 3. Pipeline | `ci.yml` con 4 etapas + deploy; Ruff, Black, Bandit; SonarCloud desde CI; protección de `main` | `.github/workflows/ci.yml`, `pyproject.toml`, `sonar-project.properties` |
| 4. Mejora | Corregir issues Blocker y mayores; formatear; medición final | `Reporte-Mejora.md` |
| 5. Cierre | Manual técnico; README con badges; video; presentación | `Manual-Tecnico.md`, video `.mp4`, presentación PDF |

## 14. Riesgos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|:------------:|:-------:|------------|
| R1 | Un merge a `main` despliega a producción un cambio defectuoso | Media | **Alto** | `main` protegida; el deploy depende de todos los gates; merges solo después de revisar |
| R2 | Pruebas inestables por depender de la fecha o de datos compartidos | **Alta** | Medio | Base aislada por prueba y fechas fijas |
| R3 | Diferencias entre SQLite (local) y PostgreSQL (producción) | Media | Medio | El pipeline prueba sobre PostgreSQL |
| R4 | No alcanzar la cobertura mínima | Baja | Alto | La migración de los scripts ya cubre cerca del 79 %; se priorizan `usuarios` y `pacientes` |
| R5 | Las dependencias de ML (scikit-learn, pandas) hacen lento el pipeline | Media | Bajo | Caché de pip en GitHub Actions |
| R6 | Límites del plan Free de SonarCloud (gate no personalizable, proyecto privado ≤ 50 k LOC) | Baja | Medio | Gates propios en GitHub Actions; el proyecto tiene unas 15 k líneas |
| R7 | Fuga de secretos en el repositorio o en los logs | Baja | **Alto** | GitHub Secrets; Bandit y SonarCloud detectan secretos; se eliminan las contraseñas del código |
| R8 | Formatear todo el código de una vez dificulta revisar los diffs | Media | Bajo | El formateo masivo va en un commit separado y sin cambios funcionales |

## 15. Registros y evidencias

| Registro | Ubicación |
|----------|-----------|
| Salidas de herramientas y capturas por fase | `docs/evidencias/` |
| Ejecuciones del pipeline | GitHub → Actions (90 días de retención) |
| Reportes de cobertura y pruebas | Artefactos de cada ejecución del pipeline |
| Historial de métricas | SonarCloud → Activity |
| Pull requests y revisiones | GitHub → Pull requests |
