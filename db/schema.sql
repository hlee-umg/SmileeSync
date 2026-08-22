-- =============================================================================
-- SmileeSync — Script de creación de la base de datos (PostgreSQL 16)
-- Modelo relacional completo del sistema de gestión de citas odontológicas.
--
-- Ejecutar sobre una base vacía:
--     createdb smileesync
--     psql -d smileesync -f schema.sql
--
-- Convenciones:
--   * Clave primaria: id (BIGSERIAL).
--   * Borrado lógico: columna "estado" (TRUE = activo, FALSE = inactivo).
--   * Historial/auditoría: tablas historial_* que guardan copia antes de cambios.
--   * Django administra además sus tablas estándar (auth_permission,
--     django_session, etc.); aquí se define el modelo de dominio del sistema.
-- =============================================================================

-- =====================  MÓDULO: SEGURIDAD Y USUARIOS  ========================

CREATE TABLE rol (
    id                  BIGSERIAL PRIMARY KEY,
    nombre              VARCHAR(50)  NOT NULL UNIQUE,
    descripcion         VARCHAR(200) NOT NULL DEFAULT '',
    puede_usuarios      BOOLEAN      NOT NULL DEFAULT FALSE,
    puede_pacientes     BOOLEAN      NOT NULL DEFAULT FALSE,
    puede_catalogos     BOOLEAN      NOT NULL DEFAULT FALSE,
    puede_agenda        BOOLEAN      NOT NULL DEFAULT FALSE,
    puede_inteligencia  BOOLEAN      NOT NULL DEFAULT FALSE,
    puede_reportes      BOOLEAN      NOT NULL DEFAULT FALSE,
    estado              BOOLEAN      NOT NULL DEFAULT TRUE,
    creado              TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE usuario (
    id            BIGSERIAL PRIMARY KEY,
    password      VARCHAR(128) NOT NULL,
    last_login    TIMESTAMP    NULL,
    is_superuser  BOOLEAN      NOT NULL DEFAULT FALSE,
    username      VARCHAR(150) NOT NULL UNIQUE,
    first_name    VARCHAR(150) NOT NULL DEFAULT '',
    last_name     VARCHAR(150) NOT NULL DEFAULT '',
    email         VARCHAR(254) NOT NULL DEFAULT '',
    is_staff      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    date_joined   TIMESTAMP    NOT NULL DEFAULT NOW(),
    rol_id        BIGINT       NULL REFERENCES rol(id) ON DELETE RESTRICT,
    telefono      VARCHAR(20)  NOT NULL DEFAULT '',
    estado        BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE historial_usuario (
    id               BIGSERIAL PRIMARY KEY,
    usuario_ref      INTEGER      NOT NULL,
    username         VARCHAR(150) NOT NULL,
    nombre_completo  VARCHAR(200) NOT NULL DEFAULT '',
    email            VARCHAR(254) NOT NULL DEFAULT '',
    rol              VARCHAR(50)  NOT NULL DEFAULT '',
    estado_anterior  BOOLEAN      NOT NULL,
    accion           VARCHAR(20)  NOT NULL,   -- CREACION | ACTUALIZACION | DESACTIVACION | ACTIVACION
    realizado_por    VARCHAR(150) NOT NULL,
    fecha            TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- =====================  MÓDULO: CATÁLOGO ODONTOLÓGICO  =======================

CREATE TABLE especialidad (
    id           BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(80)  NOT NULL UNIQUE,
    descripcion  VARCHAR(200) NOT NULL DEFAULT '',
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE procedimiento (
    id                     BIGSERIAL PRIMARY KEY,
    codigo                 VARCHAR(20)  NOT NULL UNIQUE,
    nombre                 VARCHAR(120) NOT NULL,
    especialidad_id        BIGINT       NOT NULL REFERENCES especialidad(id) ON DELETE RESTRICT,
    nivel_complejidad      VARCHAR(5)   NOT NULL DEFAULT 'MEDIA',  -- BAJA | MEDIA | ALTA
    duracion_promedio_min  INTEGER      NOT NULL DEFAULT 30 CHECK (duracion_promedio_min >= 0),
    descripcion            TEXT         NOT NULL DEFAULT '',
    estado                 BOOLEAN      NOT NULL DEFAULT TRUE,
    creado                 TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE odontologo (
    id               BIGSERIAL PRIMARY KEY,
    usuario_id       BIGINT      NULL REFERENCES usuario(id) ON DELETE SET NULL,
    nombres          VARCHAR(80) NOT NULL,
    apellidos        VARCHAR(80) NOT NULL,
    colegiado        VARCHAR(30) NOT NULL DEFAULT '',
    especialidad_id  BIGINT      NOT NULL REFERENCES especialidad(id) ON DELETE RESTRICT,
    telefono         VARCHAR(20) NOT NULL DEFAULT '',
    estado           BOOLEAN     NOT NULL DEFAULT TRUE,
    creado           TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =====================  MÓDULO: PACIENTES  ===================================

CREATE TABLE paciente (
    id                BIGSERIAL PRIMARY KEY,
    codigo            VARCHAR(20)  NOT NULL UNIQUE,
    nombres           VARCHAR(80)  NOT NULL,
    apellidos         VARCHAR(80)  NOT NULL,
    fecha_nacimiento  DATE         NULL,
    sexo              VARCHAR(1)   NOT NULL DEFAULT '',   -- M | F
    telefono          VARCHAR(20)  NOT NULL DEFAULT '',
    email             VARCHAR(254) NOT NULL DEFAULT '',
    direccion         VARCHAR(200) NOT NULL DEFAULT '',
    estado            BOOLEAN      NOT NULL DEFAULT TRUE,
    creado            TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE antecedente_medico (
    id           BIGSERIAL PRIMARY KEY,
    paciente_id  BIGINT      NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    tipo         VARCHAR(60) NOT NULL,
    descripcion  TEXT        NOT NULL,
    estado       BOOLEAN     NOT NULL DEFAULT TRUE,
    creado       TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE TABLE historial_paciente (
    id               BIGSERIAL PRIMARY KEY,
    paciente_ref     INTEGER      NOT NULL,
    codigo           VARCHAR(20)  NOT NULL,
    nombre_completo  VARCHAR(200) NOT NULL,
    estado_anterior  BOOLEAN      NOT NULL,
    accion           VARCHAR(20)  NOT NULL,
    realizado_por    VARCHAR(150) NOT NULL,
    fecha            TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- =====================  MÓDULO: AGENDA Y CITAS  ==============================

CREATE TABLE horario_disponibilidad (
    id            BIGSERIAL PRIMARY KEY,
    odontologo_id BIGINT     NOT NULL REFERENCES odontologo(id) ON DELETE CASCADE,
    dia_semana    VARCHAR(3) NOT NULL,   -- LUN | MAR | MIE | JUE | VIE | SAB
    hora_inicio   TIME       NOT NULL,
    hora_fin      TIME       NOT NULL,
    estado        BOOLEAN    NOT NULL DEFAULT TRUE,
    creado        TIMESTAMP  NOT NULL DEFAULT NOW()
);

CREATE TABLE cita (
    id                      BIGSERIAL PRIMARY KEY,
    paciente_id             BIGINT   NOT NULL REFERENCES paciente(id)      ON DELETE RESTRICT,
    odontologo_id           BIGINT   NOT NULL REFERENCES odontologo(id)    ON DELETE RESTRICT,
    procedimiento_id        BIGINT   NOT NULL REFERENCES procedimiento(id) ON DELETE RESTRICT,
    fecha                   DATE     NOT NULL,
    hora_inicio_programada  TIME     NOT NULL,
    hora_fin_programada     TIME     NOT NULL,
    hora_inicio_real        TIME     NULL,
    hora_fin_real           TIME     NULL,
    duracion_asignada_min   INTEGER  NOT NULL CHECK (duracion_asignada_min >= 0),
    duracion_real_min       INTEGER  NULL     CHECK (duracion_real_min IS NULL OR duracion_real_min >= 0),
    estado_cita             VARCHAR(12) NOT NULL DEFAULT 'PROGRAMADA', -- PROGRAMADA|ATENDIDA|CANCELADA|REPROGRAMADA
    observaciones           TEXT     NOT NULL DEFAULT '',
    estado                  BOOLEAN  NOT NULL DEFAULT TRUE,
    creado                  TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_cita_fecha        ON cita(fecha);
CREATE INDEX idx_cita_odontologo   ON cita(odontologo_id);

CREATE TABLE historial_cita (
    id                    BIGSERIAL PRIMARY KEY,
    cita_ref              INTEGER      NOT NULL,
    paciente              VARCHAR(200) NOT NULL,
    odontologo            VARCHAR(200) NOT NULL,
    fecha_cita            DATE         NOT NULL,
    estado_cita_anterior  VARCHAR(12)  NOT NULL,
    accion                VARCHAR(20)  NOT NULL,
    realizado_por         VARCHAR(150) NOT NULL,
    fecha                 TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- =====================  MÓDULO: INTELIGENCIA (PREDICCIÓN / RECOMENDACIÓN)  ===

CREATE TABLE modelo_version (
    id                   BIGSERIAL PRIMARY KEY,
    nombre               VARCHAR(80)  NOT NULL,
    algoritmo            VARCHAR(10)  NOT NULL,   -- LINEAL | RF | XGB
    mae                  DOUBLE PRECISION NULL,
    rmse                 DOUBLE PRECISION NULL,
    r2                   DOUBLE PRECISION NULL,
    fecha_entrenamiento  TIMESTAMP    NULL,
    ruta_archivo         VARCHAR(255) NOT NULL DEFAULT '',
    activo               BOOLEAN      NOT NULL DEFAULT FALSE,   -- modelo en producción
    estado               BOOLEAN      NOT NULL DEFAULT TRUE,
    creado               TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE dato_entrenamiento (
    id                  BIGSERIAL PRIMARY KEY,
    cita_id             BIGINT       NULL REFERENCES cita(id) ON DELETE SET NULL,
    tipo_procedimiento  VARCHAR(120) NOT NULL,
    odontologo          VARCHAR(200) NOT NULL,
    dia_semana          VARCHAR(3)   NOT NULL,
    hora_inicio         INTEGER      NOT NULL CHECK (hora_inicio BETWEEN 0 AND 23),
    num_piezas          INTEGER      NOT NULL DEFAULT 1,
    duracion_real_min   INTEGER      NOT NULL CHECK (duracion_real_min >= 0),
    creado              TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE prediccion (
    id                     BIGSERIAL PRIMARY KEY,
    cita_id                BIGINT   NOT NULL REFERENCES cita(id)           ON DELETE CASCADE,
    modelo_id              BIGINT   NOT NULL REFERENCES modelo_version(id) ON DELETE RESTRICT,
    duracion_estimada_min  INTEGER  NOT NULL,
    bloque_min_recomendado INTEGER  NOT NULL,
    bloque_max_recomendado INTEGER  NOT NULL,
    fecha                  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================  MÓDULO: REPORTES E INDICADORES  ======================

CREATE TABLE indicador_desempeno (
    id                     BIGSERIAL PRIMARY KEY,
    fecha                  DATE     NOT NULL,
    citas_atendidas        INTEGER  NOT NULL DEFAULT 0,
    utilizacion_pct        DOUBLE PRECISION NULL,
    tiempo_espera_prom_min DOUBLE PRECISION NULL,
    mae_actual             DOUBLE PRECISION NULL,
    rmse_actual            DOUBLE PRECISION NULL,
    r2_actual              DOUBLE PRECISION NULL,
    creado                 TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Fin del script.
-- =============================================================================
