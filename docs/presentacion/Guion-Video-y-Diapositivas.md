# Guion del video y esquema de diapositivas

Material de apoyo para los entregables 7.3 (video) y 7.4 (presentación) del enunciado.
No forma parte de la documentación técnica.

---

## 1. Preparación (antes de grabar)

### 1.1 Situación al grabar

- `main` ya está **protegida** (el repositorio es público): en el pull request de demostración
  se verá **"Merging is blocked"** mientras un check falle.
- El PR #1 queda abierto: no hace falta integrarlo para grabar. Las métricas de SonarCloud que
  se muestran son las del análisis de la rama y del PR (código nuevo).

### 1.2 Pull request de demostración

Se prepara un cambio mínimo que **viola un gate a propósito** y luego se corrige. Los
pasos 1 a 3 se hacen **en cámara**; las esperas se cortan en la edición.

```bash
git switch main
git pull
git switch -c demo/quality-gate
```

**Commit 1 (debe fallar).** En `app/pacientes/views.py`, agregar un import que no se usa:

```python
import json  # cambio de demostración
```

```bash
git commit -am "Demo: cambio que no cumple el quality gate"
git push -u origin demo/quality-gate
gh pr create --base main --title "Demo: quality gate" --body "Pull request de demostración para el video."
```

Resultado esperado: **analyze ❌** (Ruff: `F401 'json' imported but unused`), deploy omitido y,
con la protección activa, el botón de merge bloqueado.

**Commit 2 (debe pasar).** Quitar el import:

```bash
git commit -am "Demo: corregir el hallazgo del linter"
git push
```

Resultado esperado: build ✅ test ✅ analyze ✅ report ✅, el comentario de SonarCloud dice
*Quality Gate passed* y el merge queda habilitado.

Al terminar, **cerrar el PR sin hacer merge** y borrar la rama:

```bash
gh pr close --delete-branch
```

> Alternativa si no hay tiempo de esperar el pipeline: grabar la demo con el PR #1 y las
> ejecuciones ya registradas (#3 rechazada por SonarCloud y #5 aprobada), y mostrar la regla
> de `main` en **Settings → Branches**.

### 1.3 Pestañas abiertas antes de grabar

| # | Pestaña | Para la sección |
|--:|---------|-----------------|
| 1 | Terminal en la carpeta del repositorio | Demo |
| 2 | GitHub → pull request de demostración | Demo |
| 3 | GitHub → Actions → la ejecución del PR | Demo |
| 4 | SonarCloud → proyecto, rama `main` (Summary) | Dashboard |
| 5 | SonarCloud → Issues y Measures | Dashboard |
| 6 | `docs/entregables/Reporte-Mejora.pdf`, tabla de la sección 2 | Comparativa |
| 7 | Diapositivas | Intro y conclusiones |

### 1.4 Requisitos técnicos

- **Duración: 4 a 5 minutos (máximo estricto).** El guion suma unos 4:30.
- Formato **.mp4**, mínimo **720p** (recomendado 1080p).
- OBS Studio: *Ajustes → Salida → Formato de grabación: mp4*; *Vídeo → Resolución: 1920x1080*.
- Zoom del navegador al 125 % para que el texto se lea en el video.
- Ocultar marcadores, pestañas personales y notificaciones. **No mostrar** el `.env`, los
  secrets ni la IP del servidor.

---

## 2. Guion

Los tiempos son de referencia. El texto entre comillas es la narración; lo demás indica qué
mostrar.

### 2.1 Introducción (0:00 – 0:40)

**Pantalla:** diapositiva de portada.

> "Buen día. Mi nombre es Hee Sung Lee, carné 3190-11-342, del curso Aseguramiento de la
> Calidad de Software. Mi proyecto es SmileeSync, el sistema de citas de una clínica dental
> que desarrollé en Proyecto de Graduación y que ya está en producción en AWS.
>
> El problema era que no tenía ningún control de calidad: cero pruebas automatizadas y cada
> cambio se desplegaba directo a producción. El objetivo fue construir un pipeline CI/CD
> donde todo cambio pase por pruebas, análisis estático y quality gates antes de llegar a
> la rama principal."

**Pantalla:** diapositiva del pipeline (build → test → analyze → report → deploy).

> "El pipeline tiene cinco etapas en GitHub Actions y siete quality gates. Lo muestro en
> funcionamiento."

### 2.2 Demostración del pipeline (0:40 – 2:40)

**Pantalla:** terminal.

> "Creo una rama y hago un cambio que, a propósito, no cumple los estándares: agrego un
> import que no se usa."

Mostrar `git switch -c`, la línea agregada, `git commit` y `git push`.

**Pantalla:** GitHub, abrir el pull request hacia `main`.

> "Abro un pull request hacia main. La plantilla trae la lista de verificación del SQA Plan,
> y el pipeline arranca solo."

**Pantalla:** Actions → la ejecución (cortar la espera en la edición).

> "Build compila y revisa migraciones. Test levanta un PostgreSQL igual al de producción y
> corre 177 pruebas unitarias, de integración y de regresión, exigiendo al menos 70 % de
> cobertura. Pasa. Pero analyze falla."

**Pantalla:** el job *analyze* abierto, en el paso de Ruff, con la anotación.

> "Ruff detectó el import sin usar y el quality gate rechaza el cambio. Como analyze falló,
> deploy no se ejecuta: este código nunca llegaría a producción."

**Pantalla:** el pull request, con los checks en rojo y el merge bloqueado.

> "Y como main está protegida, GitHub no permite hacer merge mientras un check obligatorio
> falle."

**Pantalla:** terminal, quitar el import y hacer push.

> "Corrijo el problema y vuelvo a subir el cambio."

**Pantalla:** el pull request con todos los checks en verde y el comentario de SonarCloud.

> "Ahora pasan las cuatro etapas. SonarCloud también analiza el pull request y comenta que
> su quality gate está aprobado. Además, la etapa report publica un resumen con las pruebas,
> la cobertura y el detalle del gate de SonarCloud."

**Pantalla:** Summary de la ejecución (tablas *Resumen de calidad* y *Quality gate*).

### 2.3 Dashboard de calidad (2:40 – 3:35)

**Pantalla:** SonarCloud, Summary de `main` (pestañas *New Code* y *Overall Code*).

> "Este es el panel de SonarCloud. En la línea base, la seguridad tenía nota E y la
> confiabilidad C. Hoy, el código intervenido tiene A en seguridad, confiabilidad y
> mantenibilidad, cero issues abiertos, 89 % de cobertura medida desde el pipeline y 0,3 %
> de duplicación. En el código global los issues bajaron de 89 a 75, aunque la seguridad
> sigue en E por archivos que no intervine: eso queda documentado como deuda técnica."

**Pantalla:** Issues, filtrados por severidad.

> "SonarCloud encontró un Open Redirect real en la cancelación de citas, contraseñas en el
> código y 15 vulnerabilidades en Django 5.0, entre ellas una inyección SQL crítica.
> Corregí el redirect, saqué las contraseñas a variables de entorno y actualicé a Django 5.2
> LTS. Las 177 pruebas me permitieron hacer esa actualización con confianza."

**Pantalla:** Measures → Maintainability, o la pestaña de dependencias.

### 2.4 Comparativa de métricas (3:35 – 4:10)

**Pantalla:** diapositiva o tabla del Reporte de Mejora.

> "En resumen: de 0 a 177 pruebas automatizadas; cobertura de 89 %; los hallazgos del
> linter, de 185 a 0; los archivos sin formato, de 67 a 0; dos bugs reales corregidos, y de
> no tener quality gates a tener siete.
>
> Un dato interesante: los 12 fallos que mostraban los scripts originales no eran bugs. Se
> debían a que las pruebas compartían la base de datos. Al aislarlas, desaparecieron, y una
> prueba de integración encontró un bug de auditoría que ninguna herramienta estática
> detectó."

### 2.5 Conclusiones (4:10 – 4:40)

**Pantalla:** diapositiva de conclusiones.

> "Aprendí que cada herramienta encuentra cosas distintas: el linter, el estilo; SonarCloud,
> la seguridad; y las pruebas, los errores de lógica. Las dificultades fueron que el
> proyecto usa Django y no el stack sugerido, lo que resolví usando herramientas
> equivalentes de Python, y que GitHub no permite proteger ramas privadas en el plan
> gratuito, así que hice público el repositorio. Al revisarlo antes de publicarlo encontré
> credenciales de producción en un archivo de notas que ninguna herramienta había detectado:
> las cambié y saqué el archivo del repositorio. El resultado es que hoy ningún cambio
> llega a producción sin pasar por los siete gates. Muchas gracias."

---

## 3. Esquema de diapositivas (10)

Formato: exportar a **PDF**. Sugerencia de diseño: fondo blanco, títulos en el azul de la
UMG, una idea por diapositiva y capturas grandes.

| # | Título | Contenido | Evidencia a usar |
|--:|--------|-----------|------------------|
| 1 | **Portada** | Universidad, curso, "SmileeSync: Pipeline CI/CD con Aseguramiento de Calidad Integrado", Hee Sung Lee, carné 3190-11-342, Ing. Edgar Jehomias Matul García, Guatemala, noviembre 2026 | Escudo de la UMG (`docs/herramientas/escudo-umg.png`) |
| 2 | **Objetivo y alcance** | Problema: sin pruebas y despliegue directo a producción. Objetivo: pipeline con quality gates. Alcance: pruebas, análisis estático, cobertura, gates, protección de `main`, documentación. Excluye pruebas de carga | — |
| 3 | **Stack tecnológico** | Tabla "sugerido → usado": Jest → pytest, Supertest → Django test client, Istanbul → coverage.py, ESLint → Ruff, Prettier → Black, MySQL → PostgreSQL, SonarCloud, GitHub Actions, AWS EC2. Una línea de justificación | SQA Plan, sección 2.2 |
| 4 | **Arquitectura del pipeline** | Diagrama build → test → analyze → report → deploy, con los gates de cada etapa (QG-1 a QG-7) | Manual Técnico, sección 2.1; `03-pipeline/run1-general.png` |
| 5 | **Línea base (antes)** | 0 pruebas · cobertura no medible en CI · Ruff 170 · Black 67 · SonarCloud: seguridad **E**, confiabilidad **C**, 89 issues · Django 5.0 con 15 CVE · `main` sin protección | `01-linea-base/sonarcloud/summary.png` |
| 6 | **Métricas finales (después)** | 177 pruebas · 89 % · Ruff 0 · Black 0 · gate aprobado · Django 5.2 LTS · métricas globales de `main` | Tabla de la sección 2 del Reporte de Mejora; panel final de SonarCloud |
| 7 | **El pipeline funcionando** | Rechazo (analyze ❌) y aprobación (todo ✅); historial con 4 rechazos y luego verde | `03-pipeline/run1-general.png`, `04-mejora/run-verde-general.png`, `04-mejora/historial-ejecuciones.png` |
| 8 | **Dashboard de calidad** | SonarCloud: gate aprobado, cobertura 89 %, dependencias; detalle del gate en el resumen del pipeline | `03-pipeline/sonar-rama-cobertura.png`, `04-mejora/run-verde-sonar-gate.png` |
| 9 | **Conclusiones y lecciones** | 1) El aislamiento de pruebas era el problema. 2) Cada herramienta encuentra algo distinto. 3) Las pruebas hicieron segura la actualización de Django. 4) El pipeline cambia el proceso. Dificultades y cómo se resolvieron | Reporte de Mejora, sección 9 |
| 10 | **Referencias** | IEEE Std 730-2014; ISO/IEC 25010:2011; OWASP Top 10 (2021); documentación de GitHub Actions, SonarCloud, pytest, pytest-django, Ruff, Black, Bandit y Django | — |
