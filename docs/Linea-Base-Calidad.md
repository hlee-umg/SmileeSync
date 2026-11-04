# Línea Base de Calidad — SmileeSync

Métricas del código **antes** de cualquier intervención de aseguramiento de la calidad.
Sirven como punto de comparación para el [Reporte de Mejora](Reporte-Mejora.md).

| Dato | Valor |
|------|-------|
| Fecha de medición | 2026-11-03 |
| Commit medido | `120f743` (rama `main`, "adding responsiveness") |
| Entorno | Windows 11, Python 3.12.10, Django 5.0.14, SQLite con datos de `manage.py seed` |
| Evidencias | [`docs/evidencias/01-linea-base/`](evidencias/01-linea-base/) |
| Reproducir | [`medir.sh`](evidencias/01-linea-base/medir.sh) |
| Capturas | [Reporte de cobertura (PDF)](evidencias/01-linea-base/reporte-cobertura.pdf) · [Ruff](evidencias/01-linea-base/captura-ruff.png) |

## 1. Resumen

| Métrica | Línea base | Observación |
|---------|-----------:|-------------|
| Pruebas automatizadas formales (pytest/unittest) | **0** | Solo existen 8 scripts manuales `prueba_*.py` |
| Verificaciones en scripts manuales | 307 ejecutadas: **295 OK, 12 fallidas** | `prueba_clinico.py` se interrumpe con una excepción |
| Los scripts reportan fallo al sistema (exit code ≠ 0) | **No** | Imprimen "fallidas" pero terminan con código 0: un CI no detectaría el fallo |
| Cobertura de líneas (ejecutando los scripts) | **79 %** (2 516 / 3 199) | No es medible en CI hoy: no hay herramienta de cobertura configurada |
| Hallazgos del linter (Ruff) | **170** | 15 corregibles automáticamente |
| Archivos con formato inconsistente (Black) | **67 de 81** | No hay formateador configurado |
| Complejidad ciclomática promedio | **A (3,36)** | 13 funciones con complejidad C o D |
| Índice de mantenibilidad | **A en 81 de 81 archivos** | |
| Problemas de seguridad (Bandit) | **4 bajos**, 0 medios, 0 altos | Contraseñas escritas en el código |
| Advertencias de despliegue (`check --deploy`) | **4** | Cookies y HTTPS no forzados desde la configuración |
| SonarCloud: seguridad / confiabilidad / mantenibilidad | **E (27) / C (61) / A (3)** | 89 issues; incluye un Open Redirect real |
| SonarCloud: duplicación | **0,9 %** | |
| Densidad de comentarios | 11 % (comentarios + docstrings / LOC) | |
| Tamaño | 8 179 LOC, 6 140 SLOC (sin migraciones) | |
| Linter / formateador / cobertura / SonarCloud en el pipeline | **No** | El workflow solo ejecuta `manage.py check` y `makemigrations --check` |
| Quality gate | **No existe** | |
| Rama `main` protegida | **No** | Push directo dispara despliegue a producción (EC2) |

## 2. Pruebas existentes

El README indica "336 verificaciones" en ocho scripts. No usan un framework de pruebas:
cada script llama a `django.setup()`, ejecuta verificaciones con una función `probar()`
propia e imprime `OK` / `FALLA`. **Operan sobre la base de datos de desarrollo real**, sin
aislamiento ni datos de prueba propios.

| Script | Correctas | Fallidas | Resultado |
|--------|----------:|---------:|-----------|
| `prueba_horarios.py` | 22 | 0 | ✅ |
| `prueba_permisos.py` | 33 | 0 | ✅ |
| `prueba_calendario.py` | 31 | 0 | ✅ |
| `prueba_recomendacion.py` | 20 | 0 | ✅ |
| `prueba_flujos.py` | 30 | 1 | ⚠️ |
| `prueba_capacidad.py` | 26 | 5 | ⚠️ |
| `prueba_clinico.py` | 47 | 6 | ❌ excepción `AttributeError` (línea 274) |
| `prueba_modelo.py` | 86 | 0 | ✅ |
| **Total** | **295** | **12** | 307 de las 336 declaradas en el README |

> `prueba_clinico.py` se detiene en la sección 11, por lo que no imprime su resumen y
> deja verificaciones sin ejecutar.

Verificaciones fallidas:

- **Capacidad de unidades dentales** (`prueba_capacidad.py`): la segunda cita simultánea
  usa la misma unidad (`SIL-01`), la tercera no se rechaza y el mensaje de "sin unidades
  libres" no aparece.
- **Expediente y plan de tratamiento** (`prueba_clinico.py`): la nota no queda ligada a la
  cita, no se guardan las variables del modelo, la cita del renglón del plan no se crea
  y el script termina con `'NoneType' object has no attribute 'pk'`.
- **Flujos** (`prueba_flujos.py`): 1 verificación.

**Causa probable (por confirmar en la Fase 2):** los scripts dependen del estado de la
base de datos y de la fecha actual; el `seed` llena la agenda de citas futuras, así que los
horarios que las pruebas intentan reservar pueden estar ocupados. Esto es justamente lo
que corrigen las pruebas aisladas con `pytest-django` (base de datos nueva por prueba).

## 3. Cobertura de código

Medida con `coverage.py` al ejecutar los ocho scripts. Se excluyen migraciones, los propios
scripts, `manage.py`, `asgi.py` y `wsgi.py`.

| Módulo | Sentencias | Cubiertas | Cobertura |
|--------|-----------:|----------:|----------:|
| agenda | 726 | 646 | 89,0 % |
| catalogo | 273 | 205 | 75,1 % |
| clinico | 709 | 612 | 86,3 % |
| config | 85 | 72 | 84,7 % |
| inteligencia | 448 | 383 | 85,5 % |
| pacientes | 226 | 158 | **69,9 %** |
| reportes | 118 | 117 | 99,2 % |
| usuarios | 614 | 323 | **52,6 %** |
| **Total** | **3 199** | **2 516** | **79 %** |

Archivos por debajo del 60 %:

| Archivo | Cobertura |
|---------|----------:|
| `usuarios/management/commands/seed.py` | 0 % |
| `inteligencia/management/commands/entrenar.py` | 0 % |
| `pacientes/views.py` | 51 % |

> La cifra es alta porque los scripts recorren flujos completos (pruebas de sistema), pero
> **no es una cobertura de pruebas unitarias** y no se puede reproducir en el pipeline: los
> scripts no están en ningún framework y fallan según el estado de los datos.

## 4. Análisis estático

### 4.1 Linter — Ruff

Reglas: `E`, `W` (pycodestyle), `F` (pyflakes), `B` (bugbear), `S` (seguridad), `C90`
(complejidad > 10), `DJ` (Django), `UP` (modernización) y `SIM` (simplificación).

| Regla | Cantidad | Descripción | Severidad |
|-------|---------:|-------------|-----------|
| E501 | 125 | Línea mayor a 88 caracteres | Menor |
| F401 | 14 | Import sin usar | Mayor |
| DJ008 | 8 | Modelo sin `__str__` | Menor |
| E741 | 4 | Nombre de variable ambiguo (`l`, `O`) | Menor |
| C901 | 4 | Función demasiado compleja | Mayor |
| E702 | 4 | Varias sentencias en una línea con `;` | Menor |
| E402 | 2 | Import fuera del inicio del módulo | Menor |
| B007 | 2 | Variable de ciclo sin usar | Menor |
| F811 | 1 | Nombre redefinido sin usarse | Mayor |
| B904 | 1 | `raise` sin `from` dentro de `except` | Mayor |
| B905 | 1 | `zip()` sin `strict=` | Menor |
| S106 | 1 | Contraseña escrita en el código | **Crítica** |
| S311 | 1 | `random` no criptográfico | Menor |
| SIM102 | 1 | `if` anidados que se pueden unir | Menor |
| SIM105 | 1 | `try/except/pass` reemplazable | Menor |
| **Total** | **170** | | |

### 4.2 Formato — Black

**67 de 81 archivos** no siguen un formato uniforme. El proyecto no tiene formateador
ni `pre-commit`.

### 4.3 Complejidad y mantenibilidad — Radon

- Complejidad ciclomática promedio: **A (3,36)**.
- Funciones con complejidad **C (11–20)** o **D (21–30)**:

| Función | Archivo | Complejidad |
|---------|---------|------------:|
| `principal` | `agenda/views.py:156` | **D (26)** |
| `Command.sembrar_agenda` | `usuarios/management/commands/seed.py:382` | **D (22)** |
| `sincronizar` | `inteligencia/entrenamiento.py:126` | C (17) |
| `capacidad_minutos` | `agenda/disponibilidad.py:123` | C (16) |
| `CitaForm.clean` | `agenda/forms.py:66` | C (15) |
| `panel` | `inteligencia/views.py:50` | C (15) |
| `Command.sembrar_expediente` | `usuarios/management/commands/seed.py:574` | C (15) |
| `_huecos_sugeridos` | `agenda/views.py:75` | C (14) |
| `crear` | `agenda/views.py:420` | C (13) |
| `ausencias` | `agenda/views.py:677` | C (12) |
| `odontograma` | `clinico/views.py:113` | C (12) |
| `horarios` | `agenda/views.py:527` | C (11) |
| `Command` | `usuarios/management/commands/seed.py:8` | C (11) |

- Índice de mantenibilidad: los **81 archivos** obtienen calificación **A**.

### 4.4 Seguridad

**Bandit:** 4 hallazgos de severidad baja.

| Prueba | Ubicación | Hallazgo |
|--------|-----------|----------|
| B106 / B105 | `prueba_flujos.py:41, 46, 67` | Contraseñas escritas en el script |
| B311 | `usuarios/management/commands/seed.py` | `random` usado para datos de demostración |

Además, `seed.py:113-115` crea el superusuario con una contraseña fija **y la imprime en
consola**.

**Configuración** (`config/settings.py`):

- `SECRET_KEY` tiene un valor por defecto inseguro si falta la variable de entorno.
- `DEBUG` es `True` por defecto.

**`manage.py check --deploy`** (con `DEBUG=False` y una clave segura): 4 advertencias.

| Código | Advertencia |
|--------|-------------|
| W004 | `SECURE_HSTS_SECONDS` sin definir |
| W008 | `SECURE_SSL_REDIRECT` no es `True` |
| W012 | `SESSION_COOKIE_SECURE` no es `True` |
| W016 | `CSRF_COOKIE_SECURE` no es `True` |

## 5. Proceso y pipeline

Workflow actual: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml).

| Etapa requerida | Estado actual |
|-----------------|---------------|
| build | Parcial: instala dependencias y ejecuta `manage.py check` |
| test | ❌ No ejecuta pruebas |
| analyze | ❌ Sin linter ni SonarCloud |
| report | ❌ Sin reportes de pruebas ni de cobertura |
| Quality gate | ❌ Ninguno |
| Protección de `main` | ❌ Push directo permitido; cada push despliega a la EC2 |
| deploy (CD) | ✅ SSH a la EC2 en push a `main` |

## 6. SonarCloud (SonarQube Cloud)

Proyecto `hlee-umg / SmileeSync`, plan Free (repositorio privado), **análisis automático**
de la rama `main` en el commit `120f7430`, antes de cualquier cambio.

Capturas: [resumen](evidencias/01-linea-base/sonarcloud/summary.png) ·
[issues](evidencias/01-linea-base/sonarcloud/issues.png) ·
[mantenibilidad](evidencias/01-linea-base/sonarcloud/measures.png)

| Métrica | Línea base | Calificación |
|---------|-----------:|:------------:|
| Quality gate (Sonar way) | **No calculado** (primer análisis, sin código nuevo) | — |
| Seguridad: issues abiertos | **27** | **E** |
| Esfuerzo para corregir seguridad | 1 d 2 h | |
| Confiabilidad: issues abiertos | **61** | **C** |
| Mantenibilidad: issues abiertos | **3** | A |
| Deuda técnica (mantenibilidad) | 2 h 50 min, ratio 0,0 % | A |
| Issues en total | **89**: 83 de severidad Blocker/High/Medium, con 1 d 7 h de esfuerzo | |
| Duplicación | **0,9 %** (sobre 18 k líneas) | |
| Cobertura | **No configurada**: el análisis automático no importa cobertura | — |
| Security hotspots | 0 | |
| Riesgos en dependencias | 0 en el análisis automático; **15 en el análisis desde CI** (ver nota) | **D** |
| Tamaño | 15 k líneas de código en 155 archivos (Python, HTML, YAML) | |

> SonarCloud mide 15 k líneas porque incluye plantillas HTML, la infraestructura (CDK)
> y el workflow; Radon (sección 4.3) mide solo Python.

> **Nota sobre las dependencias.** El análisis automático no revisa dependencias. El
> primer análisis desde el pipeline (commit `f2d5f9a`, con el código de la aplicación sin
> cambios respecto a `120f743`) detectó **15 riesgos en 54 dependencias**, todos en
> **Django 5.0.14**. Entre ellos hay inyección SQL (CVE-2025-64459, CVSS 9,1;
> CVE-2025-57833; CVE-2025-59681), control externo de rutas (CVE-2026-15307) y
> complejidad algorítmica (CVE-2025-64458). La rama 5.0 de Django ya no recibe parches de
> seguridad. Captura: [dependencias](evidencias/03-pipeline/sonar-dependencias-antes.png).

Issues **Blocker** más relevantes:

| Archivo | Línea | Issue | Verificación manual |
|---------|------:|-------|---------------------|
| `app/agenda/views.py` | 522 | Open Redirect en `cancelar()` | **Confirmado**: `redirect(request.POST.get('siguiente'))` sin validar que la URL sea del mismo sitio |
| `app/usuarios/management/commands/seed.py` | 124, 143 | Contraseña comprometida en el código | **Confirmado**: contraseñas de demostración escritas en el código |
| `infra/smileesync_infra/smileesync_stack.py` | 68 | Acceso público de red | A revisar: puede ser intencional (puertos HTTP/HTTPS de la EC2) |
| `.github/workflows/deploy.yml` | — | Issue en el workflow | A revisar |

**Interpretación:** SonarCloud detecta riesgos que el linter no reporta. La calificación
**E en seguridad** proviene de pocos problemas concretos y corregibles (open redirect y
contraseñas en el código), no de un diseño inseguro. La deuda de mantenibilidad es baja,
lo que coincide con Radon (índice A).

## 7. Conclusiones

1. **La debilidad principal es la falta de pruebas formales.** Los scripts manuales tienen
   buena cobertura funcional, pero no están aislados, no indican fallos al CI y hoy
   presentan 12 verificaciones fallidas.
2. **Hay deuda técnica de estilo** (170 hallazgos de linter, 67 archivos sin formato), pero
   la **mantenibilidad estructural es buena** (índice A en todos los archivos y complejidad
   promedio A).
3. **La seguridad es el área más débil según SonarCloud (calificación E):** hay un Open
   Redirect real en la cancelación de citas, contraseñas fijas en el código y valores por
   defecto inseguros en `settings.py`. Los 61 issues de confiabilidad (C) se revisan en la Fase 4.
4. **El pipeline despliega a producción sin ninguna verificación de calidad**, y `main` no
   está protegida.

Estas conclusiones definen las prioridades del [SQA Plan](SQA-Plan.md).
