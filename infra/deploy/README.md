# Despliegue en el servidor (EC2)

## Configuración inicial (una vez)
1. Copiar el repo a `/home/ubuntu/smileesync`.
2. Crear el entorno: `cd app && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
3. Crear `app/.env` a partir de `.env.example`.
4. `python manage.py migrate && python manage.py seed && python manage.py collectstatic --noinput`.
5. Instalar servicios:
   - `sudo cp infra/deploy/gunicorn.service /etc/systemd/system/ && sudo systemctl enable --now gunicorn`
   - `sudo cp infra/deploy/nginx-smileesync.conf /etc/nginx/sites-available/smileesync`
   - `sudo ln -s /etc/nginx/sites-available/smileesync /etc/nginx/sites-enabled/ && sudo systemctl restart nginx`
6. SSL: `sudo certbot --nginx`.

## Despliegue automático (GitHub Actions)
Cada push a `main` ejecuta pruebas y, si pasan, actualiza el servidor por SSH.
Configurar en GitHub → Settings → Secrets and variables → Actions:
- `EC2_HOST` — IP pública o dominio de la instancia.
- `EC2_USER` — usuario SSH (ej. `ubuntu`).
- `EC2_SSH_KEY` — clave privada SSH (contenido completo) con acceso a la instancia.
