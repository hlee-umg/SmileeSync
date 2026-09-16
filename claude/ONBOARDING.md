# SmileeSync — Onboarding / Contexto del proyecto

> Documento de referencia para retomar el proyecto en otra computadora. Contiene credenciales
> en texto plano — **no lo subas a GitHub ni lo compartas**. Ya está agregado a `.gitignore`.
> Guárdalo también en un gestor de contraseñas o carpeta privada como respaldo.

Última actualización: 2026-09-16.

---

## 1. Qué es el proyecto

SmileeSync es un sistema web de gestión de citas para la Clínica Dental Smilee — Proyecto de
Graduación II, Universidad Mariano Gálvez de Guatemala. Incluye un módulo predictivo (duración
de procedimientos) y recomendación de bloques de tiempo para la agenda.

- **Repositorio:** `https://github.com/hlee-umg/SmileeSync.git`
- **Entrega actual:** Seguridad y Usuarios — login, CRUD de usuarios con borrado lógico e
  historial de auditoría, RBAC por rol (Administrador, Recepcionista, Odontólogo, Asistente).

## 2. Estructura del repo

```
app/     Django (backend + templates) — la app en sí
ml/      Entrenamiento offline del modelo predictivo (pandas, scikit-learn, XGBoost)
infra/   Infraestructura como código (AWS CDK, Python) — 1 sola instancia EC2
docs/    Documentación y entregas del curso
```

## 3. Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Django 5.0 (Python), Gunicorn (3 workers), Nginx como proxy inverso |
| Estáticos | WhiteNoise |
| Base de datos | PostgreSQL en producción (`psycopg2-binary`); SQLite por defecto en local |
| Frontend | Django Templates + Bootstrap 5.3.3 y Bootstrap Icons por CDN (sin build step, sin JS framework) |
| ML | pandas, scikit-learn, XGBoost, joblib — entrenamiento offline, modelo exportado a `.joblib` |
| Infraestructura | AWS CDK (Python) — 1 instancia EC2 t3.small, sin RDS, sin Load Balancer, sin NAT |
| CI/CD | GitHub Actions — tests + despliegue por SSH en cada push a `main` |

## 4. Arquitectura de producción

**Todo corre en una sola instancia EC2** (Ubuntu 24.04, t3.small): Django + Gunicorn + Nginx +
PostgreSQL en la misma máquina. No hay RDS — esto es importante: **si la instancia EC2 se
reemplaza o se recrea, se pierde la base de datos completa**, porque Postgres vive en el disco
de esa instancia. El AMI en el código CDK está fijado a propósito (`ami-052355af2a014bd2c`) para
evitar que un `cdk deploy` futuro reemplace la instancia sin querer (ver sección 8).

```
Internet → Nginx (:80/:443) → Gunicorn (127.0.0.1:8000) → Django → PostgreSQL (localhost:5432)
```

- Nginx sirve `/static/` directo desde `app/staticfiles/` y hace proxy del resto a Gunicorn.
- Gunicorn corre como servicio systemd (`gunicorn.service`), lee variables de `app/.env`.
- El despliegue automático hace `git pull` + `pip install` + `migrate` + `collectstatic` +
  `systemctl restart gunicorn` — no reinicia Nginx ni toca infraestructura.

## 5. Credenciales y accesos

### 5.1 Servidor EC2

| Dato | Valor |
|---|---|
| IP pública (Elastic IP) | `13.217.240.69` |
| Hostname interno | `ip-172-31-12-223` |
| Instance ID | `i-0d987fb6bc84d093d` |
| Región AWS | `us-east-1` |
| Usuario SSH | `ubuntu` |
| Key pair (nombre) | `smileesync-key` |
| Archivo de la llave privada | **no está en este documento** — localízalo/respáldalo aparte (normalmente algo como `~/.ssh/smileesync-key.pem`). Sin él no puedes entrar por SSH; habría que generar un key pair nuevo y asociarlo a la instancia si se pierde. |

### 5.2 Base de datos PostgreSQL

| Campo | Valor |
|---|---|
| Host (externo) | `13.217.240.69` |
| Host (desde la app, en el propio servidor) | `localhost` |
| Puerto | `5432` |
| Base de datos | `smileesync` |
| Usuario | `smileesync` |
| Contraseña | `SmileeSyncDb7Kq2Xp9Rt` |

Esta contraseña vive también en `app/.env` en el servidor — si alguna vez se desincroniza
(por ejemplo, si alguien corre `ALTER ROLE` directo en psql), la app deja de conectar con
`FATAL: password authentication failed`. Ambos lados deben coincidir siempre.

Acceso remoto (VS Code, pgAdmin, etc.) solo funciona si tu IP actual está permitida — ver
sección 6 (Security Group) y sección 8 (cómo actualizarla).

### 5.3 Variables de entorno (`app/.env` en el servidor)

```
DJANGO_SECRET_KEY=-9iCqKOvJ8GmeF-MS1UTpoz1mfG1Hm3f0IE5kfkITuUFE6H6xfS0_lMaJXBi3CYzZUw
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=13.217.240.69
DJANGO_CSRF_TRUSTED=http://13.217.240.69
DB_ENGINE=postgres
DB_NAME=smileesync
DB_USER=smileesync
DB_PASSWORD=SmileeSyncDb7Kq2Xp9Rt
DB_HOST=localhost
DB_PORT=5432
```

Este archivo **no está en git** (está en `.gitignore`). Si se pierde otra vez, entra por SSH
y revisa `cat ~/smileesync/app/.env` en el servidor — ahí sigue viviendo.

### 5.4 Usuarios de prueba (seed)

Definidos en `app/usuarios/management/commands/seed.py`. Se recrean/actualizan corriendo
`python manage.py seed` (es idempotente, no pisa contraseñas de usuarios que ya existen).

| Usuario | Email (login) | Contraseña | Rol | Pregunta secreta |
|---|---|---|---|---|
| Admin | `admin@smileesync.local` | `Admin123!` | Administrador | mascota → `firulais` |
| Recepción | `recepcion@smileesync.local` | `Recepcion123!` | Recepcionista | ciudad → `guatemala` |

El login del sistema es por **correo electrónico**, no por username.

### 5.5 AWS (cuenta y credenciales CLI)

| Campo | Valor |
|---|---|
| Account ID | `966499104816` |
| Usuario IAM | `smileesync-admin` |
| Región por defecto | `us-east-1` |
| Access Key ID | `AKIA6CB6V7AYA7IAE7NK` |
| Secret Access Key | `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` |

Estas son las credenciales que usa `aws configure` / la CDK CLI localmente. **No están
asociadas a nada del pipeline de GitHub Actions** (ese despliega por SSH, no usa AWS CLI).
Si algún día las vuelves a perder: consola AWS → IAM → Users → `smileesync-admin` →
Security credentials → crear un access key nuevo (y desactivar el viejo).

### 5.6 GitHub Actions Secrets

Configurados en el repo → Settings → Secrets and variables → Actions (los valores no se
documentan aquí por seguridad, solo los nombres que el workflow espera):

- `EC2_HOST` — IP pública del EC2 (`13.217.240.69`)
- `EC2_USER` — `ubuntu`
- `EC2_SSH_KEY` — contenido completo de la llave privada SSH (la misma de `smileesync-key`)

## 6. Seguridad de red (Security Group)

Nombre: `SmileeSyncStack-SmileeSGE5095E72-...` (gestionado por CDK, stack `SmileeSyncStack`).

| Puerto | Protocolo | Origen | Motivo |
|---|---|---|---|
| 22 | TCP | `0.0.0.0/0` | SSH |
| 80 | TCP | `0.0.0.0/0` | HTTP |
| 443 | TCP | `0.0.0.0/0` | HTTPS |
| 5432 | TCP | CIDR específico (contexto `dbAccessCidr`, ver sección 8) | Acceso remoto a Postgres para desarrollo (VS Code, etc.) |

El puerto 5432 **no está abierto a todo el mundo a propósito** — solo a la IP que se pase al
desplegar con `-c dbAccessCidr=TU_IP/32`. Si cambias de red (otra casa, café, VPN), tu IP
cambia y pierdes el acceso remoto a la base hasta que redepliegues con la IP nueva.

En el propio Postgres, además del Security Group, hace falta:
- `postgresql.conf`: `listen_addresses = '*'` (por defecto viene en `'localhost'`, hay que
  descomentar y cambiar).
- `pg_hba.conf`: una línea `host smileesync smileesync TU_IP/32 scram-sha-256` para que
  Postgres acepte autenticación desde esa IP.

Ambos cambios ya están aplicados en el servidor actual, pero si se reconstruye la instancia
desde cero, hay que volver a hacerlos manualmente (no están automatizados en el `UserData`
del CDK todavía).

## 7. Setup en una computadora nueva

```bash
# 1. Clonar
git clone https://github.com/hlee-umg/SmileeSync.git
cd SmileeSync

# 2. App Django (local, con SQLite — no necesita nada de AWS)
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver

# 3. AWS CLI (solo si vas a tocar infra/CDK)
aws configure
# Access Key ID / Secret Access Key: sección 5.5
# Region: us-east-1

# 4. CDK (solo si vas a tocar infra/)
cd ../infra
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk@latest   # ver nota de npm abajo
cdk --version   # debe ser razonablemente reciente, o "cdk diff" da error de schema
```

**Nota sobre npm:** si tienes configurado un registro privado de npm (por ejemplo uno
corporativo en `~/.npmrc`), instalar paquetes públicos como `aws-cdk` puede fallar con
errores raros de autenticación (401/404). Solución puntual sin tocar tu config global:

```bash
npm install -g aws-cdk@latest --registry=https://registry.npmjs.org/ --userconfig=/dev/null
```

## 8. Cómo desplegar cambios de infraestructura (CDK)

El stack (`infra/smileesync_infra/smileesync_stack.py`) acepta un parámetro de contexto para
la regla de firewall de Postgres:

```bash
cd infra
source .venv/bin/activate
curl -4 ifconfig.me                          # tu IP pública actual (IPv4, no IPv6)
cdk diff -c dbAccessCidr=TU_IP/32            # revisar el cambio antes de aplicar
cdk deploy -c dbAccessCidr=TU_IP/32          # aplicar
```

**Importante — antes de cualquier `cdk deploy`:** siempre correr `cdk diff` primero y
revisar que NO aparezca un `replace` sobre `AWS::EC2::Instance` ni `AWS::EC2::EIPAssociation`.
Eso significaría que la instancia se va a recrear — y como Postgres vive en su disco local,
**se perdería toda la base de datos**. Esto ya pasó una vez porque el código original usaba
`MachineImage.from_ssm_parameter(...)` (resuelve "el AMI más reciente de Ubuntu" en cada
deploy); se corrigió fijando el AMI exacto en el código. Si en el futuro se necesita cambiar
de AMI a propósito, hacerlo es una decisión consciente, no un efecto secundario de otro cambio.

## 9. Conectarse a la base de datos desde VS Code

Extensión: **PostgreSQL** (Microsoft / `ms-ossdata.vscode-pgsql`).

| Campo | Valor |
|---|---|
| Host | `13.217.240.69` |
| Puerto | `5432` |
| Base de datos | `smileesync` |
| Usuario | `smileesync` |
| Contraseña | ver sección 5.2 |
| SSL mode | `Prefer` (o `Require` si `Prefer` falla) |

Si da timeout: revisar que tu IP actual esté en el Security Group (sección 6/8) — es la causa
más común. Si da "password authentication failed": la contraseña en Postgres y en `app/.env`
están desincronizadas (sección 5.2).

## 10. Modelo de datos

El esquema completo (15 tablas en 6 apps: usuarios, catalogo, pacientes, agenda, inteligencia,
reportes) está documentado en un diagrama ER aparte, generado a partir de los `models.py` de
cada app. Regenerarlo si el modelo cambia — no vive versionado como imagen en el repo.

Puntos a recordar del modelo:
- Login por correo (`email`, único), no por `username`.
- Borrado lógico en casi todas las tablas principales (`estado: boolean`), no se usa `DELETE`.
- Las tablas de historial (`historial_usuario`, `historial_paciente`, `historial_cita`) guardan
  una copia plana del registro — su `*_ref` es un entero suelto, no una FK real. Es intencional:
  el historial sobrevive aunque el registro original cambie.
- PostgreSQL en producción no tiene RDS; recuerda la sección 4.

## 11. Pendientes / cosas a tener en cuenta

- La llave privada SSH (`smileesync-key.pem` o similar) no quedó respaldada en este documento
  — confirmar que exista una copia accesible antes de dar de baja la computadora actual.
- El `UserData` del CDK no automatiza los cambios de `postgresql.conf` / `pg_hba.conf` de la
  sección 6; si la instancia se reconstruye alguna vez, hay que rehacerlos a mano.
- Considerar mover la regla del Security Group de 5432 a algo más permanente (VPN, bastion) si
  el acceso remoto a la base se vuelve algo frecuente — depender de IPs fijas por persona es
  frágil.
- Por higiene general, si esta computadora se pierde o se comparte, vale la pena rotar el
  access key de AWS (sección 5.5) y la contraseña de Postgres (sección 5.2) en algún momento.
