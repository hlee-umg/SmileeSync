# Matriz de Pruebas — SmileeSync

Casos de prueba automatizados definidos según la estrategia del [SQA Plan](SQA-Plan.md#7-estrategia-de-pruebas).

| Dato | Valor |
|------|-------|
| Framework | pytest 8 + pytest-django + pytest-cov |
| Ubicación | `app/tests/unit/`, `app/tests/integration/`, `app/tests/regresion/` |
| Fecha de ejecución | 2026-11-03 |
| Evidencias | [`docs/evidencias/02-pruebas/`](evidencias/02-pruebas/): salida de pytest, JUnit XML y reporte HTML de cobertura |
| Ejecutar | `cd app && pytest` (todas) · `pytest -m unit` · `pytest -m integration` · `pytest -m regression` |

## 1. Resumen de resultados

| Tipo | Funciones de prueba | Casos ejecutados* | Aprobados | Fallo esperado (bug conocido) | Fallidos |
|------|--------------------:|------------------:|----------:|------------------------------:|---------:|
| Unitarias | 49 | 99 | 99 | 0 | 0 |
| Integración | 42 | 56 | 56 | 0 | 0 |
| Regresión | 4 | 11 | 8 | 3 | 0 |
| **Total** | **95** | **166** | **163** | **3** | **0** |

\* Un caso es una ejecución; las funciones parametrizadas se ejecutan una vez por cada
conjunto de datos de entrada.

| Cobertura | Valor | Umbral (QG-3) |
|-----------|------:|--------------:|
| Líneas y ramas (`--cov-branch`) | **89 %** | ≥ 70 % ✅ |

**Fallo esperado (`xfail`):** son pruebas que documentan un bug real todavía sin corregir.
Se ejecutan en cada corrida y deben fallar. La marca es `strict`: si el bug se corrige y la
prueba empieza a pasar, pytest lo reporta y hay que quitar la marca. Esto obliga a mantener
la matriz actualizada.

## 2. Bugs detectados por las pruebas

| ID | Descripción | Severidad | Detectado por | Prueba asociada | Estado |
|----|-------------|-----------|---------------|-----------------|--------|
| BUG-01 | **Open Redirect** en la cancelación de citas: `redirect(request.POST.get('siguiente'))` acepta cualquier URL, incluso de otro sitio | Blocker (seguridad) | SonarCloud + prueba | INT-CIT-06 | Pendiente (Fase 4) |
| BUG-02 | La **auditoría de edición** de usuarios y pacientes guarda los datos *nuevos* en lugar del estado previo, porque `form.is_valid()` ya modificó la instancia antes de registrar el historial | Mayor (integridad de auditoría) | Prueba de integración | REG-AUD-01, REG-AUD-02 | Pendiente (Fase 4) |
| — | Los 12 fallos de la línea base **no eran bugs**: los scripts se contaminaban con los datos de ejecuciones previas. Con una base aislada por prueba, los 8 flujos pasan al 100 % (REG-FLU-01 a 08) | — | Migración a pytest | REG-FLU-* | Resuelto |

## 3. Casos de prueba

**Columnas:** el resultado obtenido corresponde a la ejecución del 2026-11-03. ✅ aprobado ·
⚠️ fallo esperado (bug conocido) · ❌ fallido.

### 3.1 Pruebas unitarias

#### Validadores compartidos — `tests/unit/test_validadores.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| UNI-VAL-01 | Nombre con tildes, compuesto o con guion | `María José`, `López-García`, `O'Connor`, `Ñuñez` | Se acepta y se recortan los espacios | ✅ (4) |
| UNI-VAL-02 | Nombre con números o símbolos | `Juan2`, `Ana@`, `-Luis`, `José--María`, `Ana  María` | `ValidationError`: "solo puede contener letras" | ✅ (5) |
| UNI-VAL-03 | Nombre vacío | `''`, `'   '`, `None` | `ValidationError`: "obligatorio" | ✅ (3) |
| UNI-VAL-04 | Correo con mayúsculas y espacios | `  Ana.Lopez@Correo.GT ` | `ana.lopez@correo.gt` | ✅ |
| UNI-VAL-05 | Correo con formato inválido | `ana`, `ana@`, `@correo.gt`, `ana@correo` | Mensaje único "usuario@dominio.com" | ✅ (4) |
| UNI-VAL-06 | Correo opcional vacío | `''`, `obligatorio=False` | Se acepta `''` | ✅ |
| UNI-VAL-07 | Correo obligatorio vacío | `''` | `ValidationError`: "obligatorio" | ✅ |
| UNI-VAL-08 | Código válido | `pac-0001`, ` proc-14 `, `A1` | Se normaliza a mayúsculas | ✅ (3) |
| UNI-VAL-09 | Código inválido | `PAC_01`, `-PAC`, `PAC-`, `P`, `PAC 01` | `ValidationError`: "letras, números y guiones" | ✅ (5) |
| UNI-VAL-10 | Código vacío | `''` | `ValidationError`: "obligatorio" | ✅ |
| UNI-VAL-11 | Teléfono válido | `5555-1234`, `+502 5555 1234`, `(502) 2222-3333` | Se acepta | ✅ (3) |
| UNI-VAL-12 | Teléfono inválido | `12345`, `cinco55551234`, `5555/1234` | `ValidationError` | ✅ (3) |
| UNI-VAL-13 | Teléfono vacío | `'  '` | Se acepta `''` (es opcional) | ✅ |

#### Piezas dentales FDI — `tests/unit/test_piezas.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| UNI-FDI-01 | Total de piezas permanentes | Catálogo `PIEZAS` | 32 piezas, sin repetidas | ✅ |
| UNI-FDI-02 | Piezas válidas | 11, 18, 21, 28, 31, 38, 41, 48, `'36'` | `es_valida` = `True` | ✅ (9) |
| UNI-FDI-03 | Piezas inválidas o temporales | 10, 19, 51, 85, 0, `None`, `'abc'` | `es_valida` = `False` | ✅ (7) |
| UNI-FDI-04 | Nombre legible | 11, 23, 36, 48 | p. ej. 36 → "Primer molar inferior izquierdo" | ✅ (4) |
| UNI-FDI-05 | Nombre de pieza inválida | 99 | `'99'` | ✅ |
| UNI-FDI-06 | Orden de dibujo de la arcada | — | Cuadrantes 1, 2, 4, 3 con 8 piezas cada uno | ✅ |

#### Permisos por rol y autenticación — `tests/unit/test_usuarios_modelo.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| UNI-USR-01 | Administrador | Rol con todos los módulos | Accede y escribe en todo; no es de solo consulta | ✅ |
| UNI-USR-02 | Superusuario sin rol | `is_superuser=True` | Se considera administrador | ✅ |
| UNI-USR-03 | Usuario sin rol | `rol=None` | No accede ni escribe en ningún módulo | ✅ |
| UNI-USR-04 | Recepcionista | Módulos pacientes, agenda y finanzas | Accede y escribe solo en sus módulos | ✅ |
| UNI-USR-05 | Rol de solo consulta | `solo_lectura=True` | Ve el módulo pero no escribe | ✅ |
| UNI-USR-06 | Odontólogo con escritura clínica | `escritura_clinica=True`, `solo_lectura=True` | Escribe en el expediente, no en la agenda | ✅ |
| UNI-USR-07 | Acceso clínico sin escritura clínica | Módulo clínico sin `escritura_clinica` | Lectura del expediente, sin escritura | ✅ |
| UNI-USR-08 | Respuesta secreta | `'  Firulais '` y luego `'FIRULAIS'` | Se guarda cifrada y valida sin importar mayúsculas | ✅ |
| UNI-USR-09 | Sin respuesta secreta configurada | Cualquier texto | No valida | ✅ |
| UNI-USR-10 | Historial de usuario | `registrar(usuario, 'DESACTIVACION')` | Copia id, rol, estado previo y autor | ✅ |
| UNI-USR-11 | Login por correo | `ADMIN@prueba.gt` + clave correcta | Autentica al usuario | ✅ |
| UNI-USR-12 | Login con clave incorrecta | Clave errónea | `None` | ✅ |
| UNI-USR-13 | Login con correo inexistente | `nadie@prueba.gt` | `None` | ✅ |
| UNI-USR-14 | Login sin datos | Correo y clave vacíos | `None` | ✅ |
| UNI-USR-15 | Login de usuario inactivo | `is_active=False` | `None` | ✅ |

#### Disponibilidad de la agenda — `tests/unit/test_disponibilidad.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| UNI-DIS-01 | Traslape de intervalos | Idénticos, parcial, contenido, contiguos, separados | `True`, `True`, `True`, `False`, `False` | ✅ (5) |
| UNI-DIS-02 | Restar intervalos | Corte al inicio, al final, en medio, total y sin contacto | Tramos restantes correctos | ✅ (5) |
| UNI-DIS-03 | Conversión de minutos a hora | −10, 1445, 570 | 00:00, 23:59, 09:30 | ✅ |
| UNI-DIS-04 | Franja efectiva | Horario lunes 8:00–12:00 | `[(08:00, 12:00)]` | ✅ |
| UNI-DIS-05 | Día sin horario | Martes | `[]` | ✅ |
| UNI-DIS-06 | Ausencia parcial | Ausencia 9:00–10:00 | `[(08:00, 09:00), (10:00, 12:00)]` | ✅ |
| UNI-DIS-07 | Ausencia de todo el día | Ausencia 00:00–23:59 | Sin franjas; la cita no cabe | ✅ |
| UNI-DIS-08 | Ausencia inactiva | `estado=False` | No reduce la disponibilidad | ✅ |
| UNI-DIS-09 | Cita dentro o fuera de la franja | 8–12, 11:30–12, 11:30–12:30, 7:30–8:30 | Cabe, cabe, no cabe, no cabe | ✅ (4) |
| UNI-DIS-10 | Unidad ocupada | Cita 9:00–9:30 en SIL-01; consulta 9:15–9:45 | Libre solo SIL-02 y se asigna SIL-02 | ✅ |
| UNI-DIS-11 | Cita cancelada | La cita anterior cancelada | Ambas unidades libres | ✅ |
| UNI-DIS-12 | Reprogramar la propia cita | `excluir_cita` = la cita | Ambas unidades libres | ✅ |
| UNI-DIS-13 | Todas las unidades ocupadas | Dos citas simultáneas | `asignar_unidad` = `None` | ✅ |
| UNI-DIS-14 | Capacidad en minutos | 1 odontólogo de 8:00 a 12:00 y 2 sillones | 240 minutos | ✅ |
| UNI-DIS-15 | Sin unidades activas | 0 sillones | Capacidad 0 | ✅ |

### 3.2 Pruebas de integración

Peticiones HTTP reales con el *test client* de Django: vista + formulario + modelo + base
de datos + permisos.

#### Autenticación y recuperación de contraseña — `tests/integration/test_autenticacion.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| INT-AUT-01 | Página protegida sin sesión | `GET /pacientes/` | 302 al login | ✅ |
| INT-AUT-02 | Login por correo | `POST /login/` con correo y clave | 302 a la agenda | ✅ |
| INT-AUT-03 | Login con clave incorrecta | Clave errónea | 200, sin sesión iniciada | ✅ |
| INT-AUT-04 | Cierre de sesión | `POST /logout/` | Las páginas protegidas vuelven a pedir login | ✅ |
| INT-AUT-05 | Páginas sin caché | `GET` autenticado | `Cache-Control: no-store`, `Pragma: no-cache` | ✅ |
| INT-AUT-06 | Recuperación completa | Correo → respuesta correcta → nueva clave | La clave cambia; 302 al login | ✅ |
| INT-AUT-07 | Recuperación con correo desconocido | `nadie@prueba.gt` | "No se encontró una cuenta" | ✅ |
| INT-AUT-08 | Respuesta secreta incorrecta | `michi` | "La respuesta no es correcta" | ✅ |
| INT-AUT-09 | Saltarse la pregunta secreta | `GET` directo al paso 3 | 302 al paso 1 | ✅ |
| INT-AUT-10 | Pregunta sin correo previo | `GET` directo al paso 2 | 302 al paso 1 | ✅ |
| INT-AUT-11 | Nueva clave inválida | Claves distintas; clave de 5 caracteres | "no coinciden"; "al menos 8" | ✅ (2) |

#### Pacientes — `tests/integration/test_pacientes.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| INT-PAC-01 | Crear paciente | Datos válidos | 302 a la ficha; auditoría `CREACION` con el autor | ✅ |
| INT-PAC-02 | Código correlativo | `GET /pacientes/nuevo/` | Propone `PAC-000n` siguiente | ✅ |
| INT-PAC-03 | Datos inválidos | Nombre con número, correo, teléfono, fecha futura, fecha de hace más de 120 años, código repetido | 200 con el mensaje de error; no se crea | ✅ (6) |
| INT-PAC-04 | Editar paciente | Nuevo nombre | Se actualiza; 1 registro `ACTUALIZACION` | ✅ |
| INT-PAC-05 | Formulario de edición | `GET` | Muestra los datos actuales | ✅ |
| INT-PAC-06 | Borrado lógico | `POST` de cambio de estado (dos veces) | Se desactiva sin borrarse, se audita y se reactiva | ✅ |
| INT-PAC-07 | Cambio de estado por GET | `GET` | No modifica | ✅ |
| INT-PAC-08 | Lista con inactivos | Con y sin `?inactivos=1` | Se ocultan o se muestran | ✅ |
| INT-PAC-09 | Búsqueda | Apellido, código, teléfono | Encuentra al paciente | ✅ (3) |
| INT-PAC-10 | Búsqueda sin resultados | `zzz` | Lista vacía | ✅ |
| INT-PAC-11 | Antecedente médico | Agregar "Alergia a la penicilina" y quitarlo | Aparece en la ficha; al quitarlo, borrado lógico | ✅ |
| INT-PAC-12 | Antecedente corto | `x` | "al menos cinco caracteres" | ✅ |
| INT-PAC-13 | Ficha inexistente | `/pacientes/999/` | 404 | ✅ |

#### Control de acceso (RBAC) — `tests/integration/test_permisos.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| INT-RBAC-01 | Recepción en el módulo de usuarios | Lista, crear, historial | 403 | ✅ (3) |
| INT-RBAC-02 | Recepción en el catálogo | `/catalogo/unidades/` | 403 | ✅ |
| INT-RBAC-03 | Consulta en pacientes | Lista y formulario de alta | 200 y 403 | ✅ |
| INT-RBAC-04 | Consulta desactiva por URL directa | `POST` de cambio de estado | 403; el paciente sigue activo | ✅ |
| INT-RBAC-05 | Consulta cancela una cita | `POST` de cancelación | 403; la cita sigue programada | ✅ |
| INT-RBAC-06 | Escritura sin sesión | `POST` sin login | 302 al login; sin cambios | ✅ |
| INT-RBAC-07 | Usuario sin rol | `GET /pacientes/` | 403 | ✅ |

#### Usuarios — `tests/integration/test_usuarios.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| INT-USR-01 | Crear usuario | Datos válidos, correo con mayúsculas | `username` = correo en minúsculas; clave y respuesta cifradas; auditoría | ✅ |
| INT-USR-02 | Datos inválidos | Claves distintas, correo repetido, nombre con número | 200 con el mensaje de error | ✅ (3) |
| INT-USR-03 | Editar usuario | Cambio de rol | Se actualiza; 1 registro `ACTUALIZACION` | ✅ |
| INT-USR-04 | Desactivar usuario | `POST` de cambio de estado | `estado` e `is_active` en `False` | ✅ |
| INT-USR-05 | Desactivar la propia cuenta | El admin sobre sí mismo | Se rechaza; sigue activo | ✅ |
| INT-USR-06 | Pantallas del módulo | Búsqueda, historial, editar, crear | 200 y resultados correctos | ✅ |

#### Citas — `tests/integration/test_citas.py`

| ID | Caso | Entrada | Resultado esperado | Obtenido |
|----|------|---------|--------------------|:--------:|
| INT-CIT-01 | Programar cita | Lunes 10:00, 30 min | Se crea con fin 10:30 y unidad SIL-01 | ✅ |
| INT-CIT-02 | Fuera de disponibilidad | 11:45 (se pasa de las 12:00); martes sin horario; fecha pasada | 200 con el mensaje; no se crea | ✅ (3) |
| INT-CIT-03 | Traslape con el mismo odontólogo | 9:15, con una cita existente 9:00–9:30 | Se rechaza | ✅ |
| INT-CIT-04 | Cancelar cita | Motivo "no asistirá" | Estado `CANCELADA`, registro conservado, motivo en observaciones, historial | ✅ |
| INT-CIT-05 | Redirección interna después de cancelar | `siguiente=/citas/<id>/` | 302 a esa página | ✅ |
| INT-CIT-06 | **Redirección externa después de cancelar** | `siguiente=https://sitio-malicioso.example` | No debe redirigir fuera del sitio | ⚠️ **BUG-01** |

### 3.3 Pruebas de regresión

#### Flujos completos — `tests/regresion/test_flujos_completos.py`

Cada caso ejecuta uno de los scripts originales del proyecto sobre una base de datos
nueva, sembrada con `manage.py seed`. Falla si alguna verificación interna falla o si el
script se interrumpe.

| ID | Script | Verificaciones internas | Qué protege | Obtenido |
|----|--------|------------------------:|-------------|:--------:|
| REG-FLU-01 | `prueba_horarios.py` | 22 | Alta de horarios, franjas, rechazo fuera de horario | ✅ |
| REG-FLU-02 | `prueba_permisos.py` | 33 | Acceso de cada rol a cada pantalla | ✅ |
| REG-FLU-03 | `prueba_calendario.py` | 31 | Calendario de la agenda y vista de solo consulta | ✅ |
| REG-FLU-04 | `prueba_recomendacion.py` | 20 | Recomendación de bloques libres | ✅ |
| REG-FLU-05 | `prueba_flujos.py` | 31 | Flujos de la presentación: login, CRUD, 22 pantallas | ✅ |
| REG-FLU-06 | `prueba_capacidad.py` | 31 | Restricción por unidades dentales y ausencias | ✅ |
| REG-FLU-07 | `prueba_clinico.py` | 60+ | Odontograma, notas, plan de tratamiento, cobros | ✅ |
| REG-FLU-08 | `prueba_modelo.py` | 86 | Entrenamiento, versionado y estimación del modelo | ✅ |

#### Bugs conocidos — pruebas de regresión con fallo esperado

| ID | Bug | Entrada | Resultado esperado | Obtenido |
|----|-----|---------|--------------------|:--------:|
| INT-CIT-06 | BUG-01 | Ver la sección 3.2 | No redirige fuera del sitio | ⚠️ |
| REG-AUD-01 | BUG-02 | Editar el rol de un usuario de Recepcionista a Consulta | El historial guarda `Recepcionista` (estado previo) | ⚠️ guarda `Consulta` |
| REG-AUD-02 | BUG-02 | Editar el nombre de un paciente | El historial guarda "María José López García" (nombre previo) | ⚠️ guarda el nuevo |

## 4. Trazabilidad con los módulos

| Módulo | Unitarias | Integración | Regresión | Cobertura |
|--------|:---------:|:-----------:|:---------:|----------:|
| Seguridad y Usuarios | UNI-USR | INT-AUT, INT-USR, INT-RBAC | REG-FLU-02, REG-AUD-01 | ver reporte |
| Pacientes | UNI-VAL | INT-PAC | REG-FLU-05, REG-AUD-02 | ver reporte |
| Catálogo | UNI-VAL | INT-RBAC-02 | REG-FLU-01, 05, 06 | ver reporte |
| Agenda y Citas | UNI-DIS | INT-CIT | REG-FLU-01, 03, 04, 06 | ver reporte |
| Expediente Clínico y Cobros | UNI-FDI | — | REG-FLU-07 | ver reporte |
| Inteligencia | — | — | REG-FLU-08 | ver reporte |
| Reportes | — | — | REG-FLU-03, 05 | ver reporte |

La cobertura por archivo está en
[`evidencias/02-pruebas/cobertura-html/index.html`](evidencias/02-pruebas/cobertura-html/index.html).
