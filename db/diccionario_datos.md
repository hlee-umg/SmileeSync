# SmileeSync — Diccionario de datos

Descripción de cada tabla del modelo de datos y sus campos.

## Módulo: Seguridad y Usuarios

### Tabla: `rol`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| nombre | VARCHAR(50) | No | nombre |
| descripcion | VARCHAR(200) | No | descripción |
| puede_usuarios | BOOLEAN | No | módulo usuarios |
| puede_pacientes | BOOLEAN | No | módulo pacientes |
| puede_catalogos | BOOLEAN | No | módulo catálogos |
| puede_agenda | BOOLEAN | No | módulo agenda |
| puede_inteligencia | BOOLEAN | No | módulo inteligencia |
| puede_reportes | BOOLEAN | No | módulo reportes |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `usuario`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| password | VARCHAR(128) | No | contraseña |
| last_login | TIMESTAMP | Sí | último inicio de sesión |
| is_superuser | BOOLEAN | No | estado de superusuario |
| username | VARCHAR(150) | No | nombre de usuario |
| first_name | VARCHAR(150) | No | nombre |
| last_name | VARCHAR(150) | No | apellidos |
| email | VARCHAR(254) | No | dirección de correo electrónico |
| is_staff | BOOLEAN | No | es staff |
| is_active | BOOLEAN | No | activo |
| date_joined | TIMESTAMP | No | fecha de alta |
| rol_id | BIGINT (FK) | Sí | FK → rol |
| telefono | VARCHAR(20) | No | teléfono |
| estado | BOOLEAN | No | activo |

### Tabla: `historial_usuario`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| usuario_ref | INTEGER | No | id de usuario |
| username | VARCHAR(150) | No | username |
| nombre_completo | VARCHAR(200) | No | nombre completo |
| email | VARCHAR(254) | No | email |
| rol | VARCHAR(50) | No | rol |
| estado_anterior | BOOLEAN | No | estado anterior |
| accion | VARCHAR(20) | No | accion |
| realizado_por | VARCHAR(150) | No | realizado por |
| fecha | TIMESTAMP | No | fecha |

## Módulo: Catálogo Odontológico

### Tabla: `especialidad`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| nombre | VARCHAR(80) | No | nombre |
| descripcion | VARCHAR(200) | No | descripción |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `procedimiento`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| codigo | VARCHAR(20) | No | código |
| nombre | VARCHAR(120) | No | nombre |
| especialidad_id | BIGINT (FK) | No | FK → especialidad |
| nivel_complejidad | VARCHAR(5) | No | nivel de complejidad |
| duracion_promedio_min | INTEGER | No | duración promedio (min) |
| descripcion | TEXT | No | descripción |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `odontologo`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| usuario_id | BIGINT (FK) | Sí | FK → usuario |
| nombres | VARCHAR(80) | No | nombres |
| apellidos | VARCHAR(80) | No | apellidos |
| colegiado | VARCHAR(30) | No | número de colegiado |
| especialidad_id | BIGINT (FK) | No | FK → especialidad |
| telefono | VARCHAR(20) | No | teléfono |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

## Módulo: Pacientes

### Tabla: `paciente`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| codigo | VARCHAR(20) | No | código |
| nombres | VARCHAR(80) | No | nombres |
| apellidos | VARCHAR(80) | No | apellidos |
| fecha_nacimiento | DATE | Sí | fecha de nacimiento |
| sexo | VARCHAR(1) | No | sexo |
| telefono | VARCHAR(20) | No | teléfono |
| email | VARCHAR(254) | No | correo |
| direccion | VARCHAR(200) | No | dirección |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `antecedente_medico`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| paciente_id | BIGINT (FK) | No | FK → paciente |
| tipo | VARCHAR(60) | No | tipo |
| descripcion | TEXT | No | descripción |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `historial_paciente`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| paciente_ref | INTEGER | No | id de paciente |
| codigo | VARCHAR(20) | No | codigo |
| nombre_completo | VARCHAR(200) | No | nombre completo |
| estado_anterior | BOOLEAN | No | estado anterior |
| accion | VARCHAR(20) | No | accion |
| realizado_por | VARCHAR(150) | No | realizado por |
| fecha | TIMESTAMP | No | fecha |

## Módulo: Agenda y Citas

### Tabla: `horario_disponibilidad`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| odontologo_id | BIGINT (FK) | No | FK → odontologo |
| dia_semana | VARCHAR(3) | No | día de la semana |
| hora_inicio | TIME | No | hora de inicio |
| hora_fin | TIME | No | hora de fin |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `cita`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| paciente_id | BIGINT (FK) | No | FK → paciente |
| odontologo_id | BIGINT (FK) | No | FK → odontologo |
| procedimiento_id | BIGINT (FK) | No | FK → procedimiento |
| fecha | DATE | No | fecha |
| hora_inicio_programada | TIME | No | hora inicio programada |
| hora_fin_programada | TIME | No | hora fin programada |
| hora_inicio_real | TIME | Sí | hora inicio real |
| hora_fin_real | TIME | Sí | hora fin real |
| duracion_asignada_min | INTEGER | No | duración asignada (min) |
| duracion_real_min | INTEGER | Sí | duración real (min) |
| estado_cita | VARCHAR(12) | No | estado de la cita |
| observaciones | TEXT | No | observaciones |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `historial_cita`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| cita_ref | INTEGER | No | id de cita |
| paciente | VARCHAR(200) | No | paciente |
| odontologo | VARCHAR(200) | No | odontologo |
| fecha_cita | DATE | No | fecha cita |
| estado_cita_anterior | VARCHAR(12) | No | estado cita anterior |
| accion | VARCHAR(20) | No | accion |
| realizado_por | VARCHAR(150) | No | realizado por |
| fecha | TIMESTAMP | No | fecha |

## Módulo: Inteligencia

### Tabla: `modelo_version`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| nombre | VARCHAR(80) | No | nombre |
| algoritmo | VARCHAR(10) | No | algoritmo |
| mae | DOUBLE PRECISION | Sí | MAE |
| rmse | DOUBLE PRECISION | Sí | RMSE |
| r2 | DOUBLE PRECISION | Sí | R² |
| fecha_entrenamiento | TIMESTAMP | Sí | fecha de entrenamiento |
| ruta_archivo | VARCHAR(255) | No | ruta del modelo (.joblib) |
| activo | BOOLEAN | No | en producción |
| estado | BOOLEAN | No | activo |
| creado | TIMESTAMP | No | creado |

### Tabla: `dato_entrenamiento`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| cita_id | BIGINT (FK) | Sí | FK → cita |
| tipo_procedimiento | VARCHAR(120) | No | tipo de procedimiento |
| odontologo | VARCHAR(200) | No | odontólogo |
| dia_semana | VARCHAR(3) | No | día de la semana |
| hora_inicio | INTEGER | No | hora de inicio (0-23) |
| num_piezas | INTEGER | No | número de piezas |
| duracion_real_min | INTEGER | No | duración real (min) |
| creado | TIMESTAMP | No | creado |

### Tabla: `prediccion`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| cita_id | BIGINT (FK) | No | FK → cita |
| modelo_id | BIGINT (FK) | No | FK → modelo_version |
| duracion_estimada_min | INTEGER | No | duración estimada (min) |
| bloque_min_recomendado | INTEGER | No | bloque mínimo (min) |
| bloque_max_recomendado | INTEGER | No | bloque máximo (min) |
| fecha | TIMESTAMP | No | fecha de la predicción |

## Módulo: Reportes e Indicadores

### Tabla: `indicador_desempeno`

| Campo | Tipo | Nulo | Descripción |
|---|---|---|---|
| id | BIGSERIAL | No | ID |
| fecha | DATE | No | fecha |
| citas_atendidas | INTEGER | No | citas atendidas |
| utilizacion_pct | DOUBLE PRECISION | Sí | utilización de agenda (%) |
| tiempo_espera_prom_min | DOUBLE PRECISION | Sí | tiempo de espera promedio (min) |
| mae_actual | DOUBLE PRECISION | Sí | MAE del modelo |
| rmse_actual | DOUBLE PRECISION | Sí | RMSE del modelo |
| r2_actual | DOUBLE PRECISION | Sí | R² del modelo |
| creado | TIMESTAMP | No | creado |
