# Reporte de Mejora — SmileeSync

Comparativa de las métricas de calidad **antes** ([Línea Base](Linea-Base-Calidad.md),
commit `120f743`) y **después** de la intervención de aseguramiento de la calidad (rama
`qa/pipeline-sqa`, pull request #1).

| Dato | Valor |
|------|-------|
| Línea base | 2026-11-03, commit `120f743` de `main` |
| Medición final | 2026-11-04, rama `qa/pipeline-sqa` |
| Evidencias | [`docs/evidencias/04-mejora/`](evidencias/04-mejora/) · reproducir con [`medir.sh`](evidencias/04-mejora/medir.sh) |
| Estado | Versión final de entrega. Medición sobre la rama `qa/pipeline-sqa` y el pull request #1 (ver sección 6.2) |

## 1. Resumen ejecutivo

La aplicación tenía buena estructura (mantenibilidad A), pero **no tenía ningún control de
calidad automatizado**: no había pruebas formales, linter, formateador, cobertura ni quality
gates, y cada push a `main` se desplegaba directamente a producción. Además, SonarCloud
calificaba la **seguridad con E**.

Después de la intervención:

- **177 pruebas automatizadas** (antes 0) con **89 % de cobertura**, ejecutadas sobre
  PostgreSQL en cada push.
- **Pipeline con 7 quality gates**: un cambio que no los cumple no puede desplegarse.
- **Se corrigieron 2 bugs reales** (uno de seguridad Blocker), **15 vulnerabilidades de
  dependencias** y todas las contraseñas escritas en el código.
- Los hallazgos del linter bajaron de **185 a 0** y los archivos sin formato de **67 a 0**.

## 2. Comparativa general

| Métrica | Antes | Después | Meta (SQA Plan) | Cumple |
|---------|------:|--------:|----------------:|:------:|
| Pruebas automatizadas formales | 0 | **177** | ≥ 120 | ✅ |
| Pruebas que fallan | 12 (scripts manuales) | **0** | 0 | ✅ |
| El CI detecta una prueba fallida | No | **Sí** | Sí | ✅ |
| Cobertura (líneas y ramas) | 79 %\* | **89 %** | ≥ 70 % (meta 80 %) | ✅ |
| Cobertura del código nuevo (SonarCloud) | — | **89,7 %** | ≥ 80 % | ✅ |
| Hallazgos del linter (Ruff) | 170 (185 con las reglas finales) | **0** | 0 | ✅ |
| Archivos sin formato (Black) | 67 | **0** | 0 | ✅ |
| Bandit, severidad media o alta | 0 | **0** | 0 | ✅ |
| Bandit, severidad baja | 4 | **1** (justificado) | — | ✅ |
| Credenciales de producción en el repositorio | `ONBOARDING.md` con llaves de AWS, Django y PostgreSQL | **0** (archivo retirado, credenciales rotadas) | 0 | ✅ |
| Contraseñas de cuentas en el código | 3 (`seed.py`) y una usada para iniciar sesión en los scripts | **0**† | 0 | ✅ |
| Advertencias de `check --deploy` | 4 | **0 de esas 4**\*\* | 0 | ✅ |
| Riesgos en dependencias (SonarCloud) | 15 (D) | **0 en Django 5.2**\*\*\* | — | ✅ |
| Gate de SonarCloud | No calculado | **Aprobado** en la rama y en el PR | Aprobado | ✅ |
| Seguridad (SonarCloud, código nuevo) | E (27 issues, global) | **A** (0 issues) | A | ✅ |
| Funciones con complejidad > 15 | 4 | **3** | ≤ 3 | ✅ |
| Complejidad ciclomática promedio | A (3,36) | **A (3,34)** | A | ✅ |
| Índice de mantenibilidad | A en todos | A en 72 de 73; **B en 1** | A | ⚠️ |
| Etapas del pipeline | 2 (test parcial, deploy) | **5** (build, test, analyze, report, deploy) | ≥ 4 | ✅ |
| Quality gates | 0 | **7** | 7 | ✅ |
| `main` protegida | No | **Sí**: PR obligatorio y `build`, `test`, `analyze` requeridos | Sí | ✅ |

\* Medida ejecutando a mano los scripts sobre la base de desarrollo; no era reproducible en CI.<br>
\*\* Con `DJANGO_HTTPS=True`. Quedan W005 y W021 (HSTS para subdominios y *preload*), que se
dejan apagados a propósito porque son difíciles de revertir.<br>
\*\*\* Django 5.2.19 corrige los CVE reportados para 5.0.14. Se confirma en el análisis de `main`.<br>
† Las pruebas siguen usando claves ficticias propias (por ejemplo, para probar el cambio de
contraseña). Están permitidas en `tests/` según el SQA Plan y no corresponden a ninguna cuenta.

## 3. Pruebas y cobertura

### 3.1 Suite de pruebas

| Tipo | Antes | Después |
|------|------:|--------:|
| Unitarias | 0 | 108 casos (52 funciones) |
| Integración | 0 | 56 casos (42 funciones) |
| Regresión | 8 scripts manuales, 12 verificaciones fallidas | 13 casos: los 8 flujos aislados (0 fallos) y 5 de bugs corregidos |
| **Total** | **0 formales** | **177 casos, 100 % aprobados** |

**Hallazgo:** los 12 fallos de la línea base **no eran defectos**. Los scripts se ejecutaban
sobre la base de desarrollo y se contaminaban con datos de ejecuciones previas. Al correrlos
sobre una base nueva por prueba, los 8 pasan al 100 %. El aislamiento de las pruebas era el
problema de calidad.

### 3.2 Cobertura por módulo

| Módulo | Antes | Después | Cambio |
|--------|------:|--------:|-------:|
| agenda | 89,0 % | 91,9 % | +2,9 |
| catalogo | 75,1 % | 75,1 % | 0,0 |
| clinico | 86,3 % | 95,8 % | +9,5 |
| config | 84,7 % | 90,0 % | +5,3 |
| inteligencia | 85,5 % | 85,8 % | +0,3 |
| pacientes | **69,9 %** | **99,6 %** | **+29,7** |
| reportes | 99,2 % | 99,2 % | 0,0 |
| usuarios | **52,6 %** | **95,9 %** | **+43,3** |
| **Total (líneas)** | **78,7 %** | **92,0 %** | **+13,3** |

Los dos módulos con menor cobertura en la línea base (usuarios y pacientes) son los que más
mejoraron, porque concentran la seguridad (login, permisos por rol, auditoría) y los datos
personales. El catálogo queda como el módulo menos cubierto.

## 4. Análisis estático

### 4.1 Linter (Ruff)

| Regla | Antes | Después | Cómo se resolvió |
|-------|------:|--------:|------------------|
| E501 Línea larga | 125 | 0 | Black + división manual de cadenas largas |
| F401 Import sin usar | 14 | 0 | `ruff --fix` |
| DJ008 Modelo sin `__str__` | 8 | 0 | `__str__` en 8 modelos, con pruebas (UNI-STR) |
| E741 Nombre ambiguo (`l`) | 4 | 0 | Renombrado a `linea` |
| C901 Complejidad excesiva | 4 | 0 | Refactor de `seed.sembrar_agenda` (22 → 12) |
| E702 Varias sentencias por línea | 4 | 0 | Black |
| E402 Import fuera del inicio | 2 | 0 | Import movido; excepción documentada en los scripts de regresión |
| B007 Variable de ciclo sin usar | 2 | 0 | Iterar sobre `values()` |
| B904 `raise` sin `from` | 1 | 0 | `raise ... from None` |
| B905 `zip` sin `strict` | 1 | 0 | `strict=True` |
| F811 Nombre redefinido | 1 | 0 | `ruff --fix` |
| SIM102 / SIM105 | 2 | 0 | `if` combinado / `contextlib.suppress` |
| S106 Contraseña en el código | 1 | 0 | Variable de entorno `SEED_PASSWORD` |
| S311 `random` no criptográfico | 1 | 0 | Justificado: datos de demostración con semilla fija |
| **Total** | **170** | **0** | |

### 4.2 Formato (Black)

De **67 archivos sin formato a 0**. El formateo se hizo en un commit aparte (`063416d`),
sin cambios funcionales, registrado en `.git-blame-ignore-revs`.

### 4.3 Complejidad y mantenibilidad (Radon)

| Función | Antes | Después |
|---------|------:|--------:|
| `seed.Command.sembrar_agenda` | **D (22)** | **C (12)** |
| `agenda.views.principal` | D (26) | D (26) |
| `inteligencia.entrenamiento.sincronizar` | C (17) | C (17) |
| `agenda.disponibilidad.capacidad_minutos` | C (16) | C (16) |

El refactor de `sembrar_agenda` se verificó con una huella (hash SHA-256) de las 675 citas que
genera: idéntica antes y después, así que la reducción de complejidad no cambió los datos.

**Regresión detectada:** el índice de mantenibilidad de `agenda/views.py` bajó de A a
**B (18,3)**. La causa es el aumento de líneas por el formato de Black (el índice penaliza el
tamaño). El archivo concentra 11 vistas y la función más compleja del sistema (`principal`,
26); dividirlo es la siguiente acción de deuda técnica.

## 5. Seguridad

### 5.1 Defectos corregidos

| ID | Problema | Severidad | Detectado por | Corrección | Prueba |
|----|----------|-----------|---------------|------------|--------|
| BUG-01 | **Open Redirect** al cancelar una cita | Blocker | SonarCloud + prueba | Validar la URL con `url_has_allowed_host_and_scheme` | INT-CIT-06 (3 variantes) |
| BUG-02 | La **auditoría de edición** guardaba los datos nuevos en vez del estado previo | Mayor | **Prueba de integración** (ninguna herramienta estática lo detectó) | Auditar una copia del registro tomada antes de `is_valid()` | REG-AUD-01, REG-AUD-02 |
| SEC-01 | **Django 5.0.14** con 15 CVE, entre ellos inyección SQL (CVE-2025-64459, CVSS 9,1) | Crítica | SonarCloud (dependencias) | Actualización a Django 5.2.19 LTS | Suite completa: 177 pruebas sin cambios de código |
| SEC-02 | Contraseñas de demostración en el código, impresas en consola | Blocker | SonarCloud, Bandit | `SEED_PASSWORD` o contraseña aleatoria | REG-FLU-01 a 08 |
| SEC-03 | `SECRET_KEY` con valor inseguro por defecto | Mayor | `check --deploy`, revisión | Sin la variable, la aplicación no arranca en producción | `manage.py check` |
| SEC-04 | Cookies y HTTPS no forzados | Mayor | `check --deploy` | Ajustes activables con `DJANGO_HTTPS` | `check --deploy` |
| SEC-05 | Ambigüedad entre la constante `SEXO` y el campo `sexo` | Blocker (SonarCloud) | Gate del código nuevo | Renombrada a `OPCIONES_SEXO` | Suite completa |
| SEC-06 | **Credenciales de producción versionadas** en `claude/ONBOARDING.md` (llave de acceso de AWS, `SECRET_KEY`, contraseña de PostgreSQL) e ID de la cuenta de AWS en `infra/cdk.context.json` | **Crítica** | **Revisión manual** antes de hacer público el repositorio (ni Bandit ni SonarCloud analizan archivos `.md`) | Llave de AWS desactivada; `SECRET_KEY` y contraseña de la base cambiadas en el servidor; archivos retirados del repositorio y agregados al `.gitignore` | Verificación manual del sitio en producción |

### 5.2 Valor de las pruebas en la actualización de Django

Pasar de Django 5.0 a 5.2 cambia dos versiones menores del framework. Con la suite de 177
pruebas, la actualización se validó en unos 3 minutos y sin advertencias de funciones
obsoletas. Sin pruebas, ese cambio habría requerido revisar a mano los 8 módulos.

## 6. SonarCloud

### 6.1 Quality gate del código nuevo (rama y pull request)

| Condición (Sonar way) | Ejecución #4 | Ejecución #5 y PR #1 |
|-----------------------|-------------:|---------------------:|
| Calificación de confiabilidad | A | A |
| Calificación de seguridad | **C** ❌ | **A** ✅ |
| Calificación de mantenibilidad | A | A |
| Cobertura | 89,7 % | 89,7 % |
| Duplicación | 0,3 % | 0,3 % |
| Security hotspots revisados | 100 % | 100 % |
| Issues abiertos | 2 | **0** |
| **Gate** | **ERROR** | **OK** |

Capturas: [gate fallido](evidencias/04-mejora/run-anterior-sonar-gate.png) ·
[gate aprobado](evidencias/04-mejora/run-verde-sonar-gate.png).

### 6.2 Alcance de la medición de SonarCloud

En las ramas y los pull requests, SonarCloud evalúa el **código nuevo**: todo lo que cambió
respecto de `main`. Como la intervención reformateó y corrigió prácticamente todo el código
de la aplicación (67 archivos), ese "código nuevo" abarca casi todo el proyecto, y sobre él
el resultado es **0 issues abiertos, calificación A en seguridad, confiabilidad y
mantenibilidad, 89,7 % de cobertura y 0,3 % de duplicación**.

El análisis global de la rama `main` se actualiza cuando el pull request #1 se integra. Al
cierre del proyecto el PR quedó abierto, con todos los checks aprobados, porque el merge
despliega automáticamente a la instancia de producción y antes debe verificarse en el
servidor la variable `DJANGO_SECRET_KEY`, que ahora es obligatoria (Manual Técnico,
sección 6.5).

Captura del pull request: [gate aprobado en el PR #1](evidencias/04-mejora/pr1-sonarcloud-gate.png).

## 7. Proceso: evolución del pipeline

| Ejecución | Commit | Resultado | Qué la detuvo |
|----------:|--------|-----------|---------------|
| #1 | Pipeline con quality gates | ❌ | Ruff (código original), Black (67 archivos) y SonarCloud (sin token) |
| #2 | Evidencias del primer pipeline | ❌ | Ruff y Black (el código seguía sin corregir) |
| #3 | Corrección de Ruff y complejidad | ❌ | **Gate de SonarCloud**: 2 issues en el código nuevo |
| #4 | Detalle del gate en el resumen | ❌ | Mismo gate, ahora con el detalle visible |
| #5 | Corrección de los 2 issues | ✅ | — |
| #8 (PR #1) | Pull request a `main` | ✅ | — |

El pipeline **rechazó cuatro veces** código que no cumplía los umbrales y solo aprobó
cuando todos los gates pasaron. La ejecución #3 es el ejemplo más claro: Ruff, Black, Bandit
y las 177 pruebas ya estaban en verde, pero SonarCloud detectó dos problemas que ninguna otra
herramienta había marcado.

Capturas: [historial](evidencias/04-mejora/historial-ejecuciones.png) ·
[primer rechazo](evidencias/03-pipeline/run1-general.png) ·
[pipeline en verde](evidencias/04-mejora/run-verde-general.png).

## 8. Deuda técnica restante

| Elemento | Severidad | Acción propuesta |
|----------|-----------|------------------|
| `agenda.views.principal` con complejidad 26 | Mayor | Extraer el cálculo de indicadores y del calendario a funciones o servicios |
| `agenda/views.py` con mantenibilidad B | Menor | Dividir en módulos por pantalla |
| Catálogo con 75 % de cobertura | Menor | Pruebas de integración del CRUD del catálogo |
| `sincronizar` y `capacidad_minutos` con complejidad 16–17 | Menor | Refactor con la misma técnica de verificación por huella |
| Credenciales antiguas en el historial de git | Menor (ya rotadas) | Purgar el historial con `git filter-repo` si se requiere un historial limpio |

## 9. Conclusiones

1. **La falta de pruebas aisladas era el problema de calidad más grave**, más que el código
   en sí. Al aislarlas desaparecieron los "fallos" de la línea base y se hicieron visibles
   los bugs reales.
2. **Cada herramienta encontró algo que las otras no**: Ruff, el estilo y los errores
   lógicos; SonarCloud, el Open Redirect, las dependencias vulnerables y la ambigüedad de
   nombres; las pruebas de integración, el bug de auditoría; y la **revisión manual**, las
   credenciales de producción guardadas en un archivo de notas, que ninguna herramienta
   automática analizaba.
3. **Las pruebas hicieron segura la actualización de Django**, que corrigió las
   vulnerabilidades más graves del proyecto.
4. **El pipeline cambia el proceso, no solo el código**: antes, cualquier push llegaba a
   producción; ahora, un cambio solo se despliega si pasa los 7 gates.
