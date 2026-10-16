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
7. Entrenar el modelo por primera vez:
   `python manage.py entrenar --algoritmo RF --activar`.
8. Programar el reentrenamiento mensual:
   - `sudo cp infra/deploy/smileesync-entrenar.service /etc/systemd/system/`
   - `sudo cp infra/deploy/smileesync-entrenar.timer /etc/systemd/system/`
   - `sudo systemctl daemon-reload && sudo systemctl enable --now smileesync-entrenar.timer`

## Reentrenamiento del modelo

El entrenamiento NO corre dentro del servidor web. Importar scikit-learn y
pandas añade alrededor de 140 MB al proceso que lo haga, y la instancia tiene
2 GB compartidos entre PostgreSQL y los tres procesos de Gunicorn; por eso vive
en un comando aparte que el temporizador ejecuta una vez al mes.

- Ver cuándo corre la próxima vez: `systemctl list-timers smileesync-entrenar*`
- Ejecutarlo ahora: `sudo systemctl start smileesync-entrenar.service`
- Ver el resultado del último: `journalctl -u smileesync-entrenar -n 40`

El comando usa `--solo-si-mejora`: entrena, compara contra la versión en
producción y la sustituye únicamente si reduce el error. Las versiones
anteriores se conservan y desde `/inteligencia/` se puede volver a cualquiera
de ellas.

Los archivos `.joblib` de los modelos entrenados viven en `app/modelos/` y están
excluidos del control de versiones: se regeneran en el servidor y pesan varios
cientos de kilobytes cada uno.

## Despliegue automático (GitHub Actions)
Cada push a `main` ejecuta pruebas y, si pasan, actualiza el servidor por SSH.
Configurar en GitHub → Settings → Secrets and variables → Actions:
- `EC2_HOST` — IP pública o dominio de la instancia.
- `EC2_USER` — usuario SSH (ej. `ubuntu`).
- `EC2_SSH_KEY` — clave privada SSH (contenido completo) con acceso a la instancia.
