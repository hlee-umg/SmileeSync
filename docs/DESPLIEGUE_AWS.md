# Guía de despliegue en AWS — SmileeSync

Runbook paso a paso para desplegar la aplicación en una instancia EC2 de bajo
costo y activar el despliegue automático con GitHub Actions.

> Todo esto se ejecuta **en tu computadora** (con tu cuenta AWS). El servidor
> corre Django + Gunicorn + Nginx + PostgreSQL en una sola instancia `t3.small`.

---

## Parte 0 — Instalar prerrequisitos (en tu máquina)

- **AWS CLI**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- **Node.js** (para CDK): https://nodejs.org
- **AWS CDK**: `npm install -g aws-cdk`
- **Python 3.12+** y **git** (ya los tienes).

Verifica:

```bash
aws --version
cdk --version
python3 --version
```

---

## Parte 1 — Crear credenciales de acceso (IAM) y configurarlas

1. En la consola de AWS entra a **IAM → Users → Create user** (nómbralo `smileesync-admin`).
2. Marca **Provide user access to the AWS Management Console** solo si lo quieres; lo importante es el acceso programático.
3. En permisos, adjunta la política **AdministratorAccess** (para el proyecto está bien; en producción real se acota).
4. Crea el usuario, entra a la pestaña **Security credentials → Create access key → Command Line Interface (CLI)**.
5. Guarda el **Access key ID** y el **Secret access key**.

Configura la CLI:

```bash
aws configure
# AWS Access Key ID:     <tu access key>
# AWS Secret Access Key: <tu secret>
# Default region name:   us-east-1
# Default output format:  json
```

> Nunca subas estas llaves al repositorio.

---

## Parte 2 — Crear el key pair de EC2

Este par de llaves te deja entrar por SSH a la instancia.

```bash
aws ec2 create-key-pair --key-name smileesync-key \
  --query 'KeyMaterial' --output text > ~/smileesync-key.pem
chmod 400 ~/smileesync-key.pem
```

Guarda `~/smileesync-key.pem` en un lugar seguro: es tu llave para entrar al servidor.

---

## Parte 3 — Desplegar la infraestructura con CDK

```bash
cd "<ruta-del-repo>/smileesync/infra"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cdk bootstrap        # solo la primera vez en la cuenta/región
cdk synth            # opcional: revisa lo que se va a crear
cdk deploy           # crea la EC2, el security group y la IP elástica
```

Al terminar, CDK imprime la salida **`IPPublica`**. Anótala: es la IP de tu servidor.

---

## Parte 4 — Configuración inicial del servidor (una sola vez)

### 4.1 Entrar por SSH

```bash
ssh -i ~/smileesync-key.pem ubuntu@<IP_PUBLICA>
```

### 4.2 Dar acceso de solo lectura al repo privado (deploy key)

Como el repo es privado, el servidor necesita poder clonarlo. Usa una *deploy key*:

```bash
# En el servidor:
ssh-keygen -t ed25519 -C "smileesync-deploy" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Copia esa clave pública y agrégala en GitHub:
**Repo → Settings → Deploy keys → Add deploy key** (pégala, deja "Allow write access" desmarcado).

### 4.3 Clonar y preparar la aplicación

```bash
# En el servidor:
cd ~
git clone git@github.com:hlee-umg/SmileeSync.git smileesync
cd smileesync/app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env    # completa SECRET_KEY, ALLOWED_HOSTS=<IP_PUBLICA>, y los DB_*
```

### 4.4 Crear la base de datos PostgreSQL

```bash
sudo -u postgres psql -c "CREATE DATABASE smileesync;"
sudo -u postgres psql -c "CREATE USER smileesync WITH PASSWORD 'una-clave-segura';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smileesync TO smileesync;"
sudo -u postgres psql -c "ALTER DATABASE smileesync OWNER TO smileesync;"
```

Asegúrate de que el `.env` tenga `DB_ENGINE=postgres` y esas credenciales.

### 4.5 Migrar, sembrar y archivos estáticos

```bash
python manage.py migrate
python manage.py seed
python manage.py collectstatic --noinput
```

### 4.6 Servicios (Gunicorn + Nginx)

```bash
cd ~/smileesync
sudo cp infra/deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn

sudo cp infra/deploy/nginx-smileesync.conf /etc/nginx/sites-available/smileesync
sudo ln -sf /etc/nginx/sites-available/smileesync /etc/nginx/sites-enabled/smileesync
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

Abre `http://<IP_PUBLICA>/` en el navegador: deberías ver el login.

### 4.7 (Opcional) HTTPS con dominio

Si tienes un dominio apuntando a la IP:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

## Parte 5 — Activar el despliegue automático (GitHub Actions)

En GitHub: **Repo → Settings → Secrets and variables → Actions → New repository secret**. Crea:

| Secreto        | Valor                                             |
|----------------|---------------------------------------------------|
| `EC2_HOST`     | La `IP_PUBLICA` del servidor                       |
| `EC2_USER`     | `ubuntu`                                           |
| `EC2_SSH_KEY`  | El **contenido completo** de `~/smileesync-key.pem`|

Desde ahora, cada `git push` a `main` corre las pruebas y, si pasan, actualiza el
servidor automáticamente (git pull → migrate → collectstatic → reinicia gunicorn).

---

## Parte 6 — Probar el flujo completo

```bash
# en tu máquina, haz un cambio pequeño y:
git add -A && git commit -m "prueba de despliegue" && git push
```

Ve a la pestaña **Actions** del repo: verás el job de pruebas y luego el de deploy.
Cuando termine, recarga `http://<IP_PUBLICA>/`.

---

## Apagar todo (para no gastar créditos al terminar)

```bash
cd smileesync/infra && source .venv/bin/activate
cdk destroy      # elimina la instancia, el security group y la IP
```

> Antes de destruir, respalda la base de datos: `pg_dump` en el servidor.
