"""Configuración de Django para el proyecto SmileeSync.

En desarrollo usa SQLite para no requerir un servidor de base de datos.
En producción (EC2) se usa PostgreSQL leyendo las variables de entorno.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga automática de variables desde app/.env si existe, para que los comandos
# de manage.py y el servidor (gunicorn) usen SIEMPRE la misma configuración.
# load_dotenv no sobrescribe variables ya presentes en el entorno (las de
# systemd tienen prioridad), así que es seguro en producción.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# --- Seguridad -------------------------------------------------------------
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    # Sin clave definida solo se admite el modo de desarrollo: se genera una
    # aleatoria y se guarda en un archivo local fuera del repositorio, para que
    # las sesiones sobrevivan a los reinicios del servidor de desarrollo. En
    # producción la ausencia de la variable es un error.
    if not DEBUG:
        raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY en el entorno de producción.')
    _archivo_clave = BASE_DIR / '.clave-desarrollo'
    if not _archivo_clave.exists():
        _archivo_clave.write_text(get_random_secret_key(), encoding='utf-8')
    SECRET_KEY = _archivo_clave.read_text(encoding='utf-8').strip()
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get('DJANGO_CSRF_TRUSTED', '').split(',') if o
]

# Endurecimiento para el sitio servido por HTTPS (Nginx + certificado). Se
# activa con DJANGO_HTTPS=True para no romper un despliegue que aún use HTTP.
if os.environ.get('DJANGO_HTTPS', 'False') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '3600'))

# --- Aplicaciones ----------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'catalogo',
    'pacientes',
    'agenda',
    'clinico',
    'inteligencia',
    'reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'usuarios.middleware.NoCacheMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.permisos',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Base de datos ---------------------------------------------------------
if os.environ.get('DB_ENGINE') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'smileesync'),
            'USER': os.environ.get('DB_USER', 'smileesync'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Autenticación ---------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

# Autenticación: primero por correo (EmailBackend); ModelBackend se mantiene
# para el sitio de administración (/admin/), que usa el username.
AUTHENTICATION_BACKENDS = [
    'usuarios.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'agenda:principal'
LOGOUT_REDIRECT_URL = 'login'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalización --------------------------------------------------
LANGUAGE_CODE = 'es-gt'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

# Django no trae configuración regional para es-GT y recae en la de España
# (1.750,00). Guatemala usa punto decimal y coma de millar, así que los
# separadores numéricos se redefinen en config/formats/es/formats.py.
FORMAT_MODULE_PATH = ['config.formats']
USE_THOUSAND_SEPARATOR = True

# --- Archivos estáticos ----------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
