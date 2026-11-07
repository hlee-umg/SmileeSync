"""Manual técnico: portada, arquitectura, requisitos e instalación."""
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import (AZUL, GRIS, RAIZ, SALIDA_TECNICO, codigo, h, imagen,
                          nota, p, tabla)                          # noqa: E402

ENTORNO = [
    ['Variable', 'Qué define', 'Valor en producción'],
    ['DJANGO_SECRET_KEY', 'Clave con que Django firma sesiones y formularios.',
     'Cadena aleatoria larga, distinta de la de desarrollo.'],
    ['DJANGO_DEBUG', 'Modo de depuración.', 'False, sin excepción.'],
    ['DJANGO_ALLOWED_HOSTS', 'Dominios o direcciones desde los que se admite servir.',
     'La dirección pública del servidor.'],
    ['DJANGO_CSRF_TRUSTED', 'Orígenes confiables para los formularios.',
     'La dirección del servidor con su esquema.'],
    ['DB_ENGINE', 'Motor de base de datos.', 'postgres'],
    ['DB_NAME, DB_USER, DB_PASSWORD', 'Credenciales de la base.',
     'Las creadas al preparar PostgreSQL.'],
    ['DB_HOST, DB_PORT', 'Ubicación de la base.', 'localhost y 5432'],
]

REQUISITOS = [
    ['Componente', 'Versión', 'Nota'],
    ['Sistema operativo', 'Ubuntu 24.04 LTS', 'Instancia EC2 t3.small: 2 vCPU y 2 GB.'],
    ['Python', '3.12', 'Con entorno virtual propio en app/.venv'],
    ['PostgreSQL', '16', 'En la misma instancia; no se usa servicio gestionado.'],
    ['Nginx', '1.24 o superior', 'Proxy inverso y entrega de archivos estáticos.'],
    ['Gunicorn', '22 o superior', 'Tres procesos de trabajo.'],
    ['Git', 'Cualquiera reciente', 'Con llave de despliegue de solo lectura.'],
]


def main():
    doc = Document()
    s = doc.sections[0]
    s.left_margin = s.right_margin = Inches(1.0)
    s.top_margin = s.bottom_margin = Inches(0.9)

    p(doc, '', despues=90)
    p(doc, 'SmileeSync', 36, True, AZUL, despues=0, centrado=True)
    p(doc, 'Manual técnico', 20, False, GRIS, despues=4, centrado=True)
    p(doc, 'Instalación, operación y mantenimiento', 12, False, GRIS, despues=120,
      centrado=True)
    p(doc, 'Clínica Dental Smilee', 12, True, None, despues=2, centrado=True)
    p(doc, 'Versión 1.0 · Octubre de 2026', 10.5, False, GRIS, centrado=True)
    doc.add_page_break()

    h(doc, '1. Alcance')
    p(doc, 'Este manual está dirigido a quien instala, opera y mantiene el sistema. '
      'Documenta la arquitectura desplegada, el procedimiento de instalación desde '
      'cero, la configuración, las tareas periódicas, el respaldo y la restauración '
      'de la base de datos, el diagnóstico de los problemas más frecuentes y el '
      'entorno de desarrollo. El manual de usuario, que explica cómo operar el '
      'sistema desde las pantallas, es un documento aparte.')

    h(doc, '2. Arquitectura desplegada')
    p(doc, 'Todos los componentes residen en una sola instancia de cómputo: la '
      'aplicación, el servidor web, la base de datos y el modelo entrenado comparten '
      'los dos gigabytes de memoria y el mismo disco. La decisión responde al costo '
      'de operación de una clínica pequeña y tiene una consecuencia que debe tenerse '
      'presente: la instancia es un punto único de falla y el respaldo de la base de '
      'datos es la única protección contra la pérdida total de la información.')
    imagen(doc, RAIZ / 'diagramas' / 'despliegue.png',
           'Despliegue en producción: nodos, procesos y puertos')
    p(doc, 'El código de la aplicación se organiza en ocho componentes, uno por cada '
      'aplicación de Django más el paquete de configuración. La figura siguiente '
      'muestra sus dependencias, obtenidas del análisis de las importaciones del '
      'código fuente.')
    imagen(doc, RAIZ / 'diagramas' / 'componentes_app.png',
           'Componentes de la aplicación y sus dependencias')

    h(doc, '3. Requisitos')
    tabla(doc, REQUISITOS, [1.8, 1.6, 2.9])

    h(doc, '4. Instalación desde cero', salto=True)
    p(doc, 'El procedimiento completo está en la guía de despliegue del repositorio. '
      'Lo que sigue es la secuencia mínima, suponiendo una instancia recién creada con '
      'Ubuntu 24.04 y acceso por SSH.')

    h(doc, '4.1 Clonar la aplicación', 2)
    p(doc, 'El repositorio es privado, de modo que el servidor necesita una llave de '
      'despliegue de solo lectura. Se genera en el servidor y se registra en el '
      'repositorio como deploy key, sin permiso de escritura.')
    codigo(doc, [
        'ssh-keygen -t ed25519 -C "smileesync-deploy" -f ~/.ssh/id_ed25519 -N ""',
        'cat ~/.ssh/id_ed25519.pub        # registrar en el repositorio',
        '',
        'cd ~ && git clone git@github.com:<organizacion>/SmileeSync.git smileesync',
        'cd smileesync/app',
        'python3 -m venv .venv && source .venv/bin/activate',
        'pip install -r requirements.txt',
    ], '# en el servidor')

    h(doc, '4.2 Configurar las variables de entorno', 2)
    p(doc, 'Ninguna credencial se escribe en el código. La aplicación las lee de un '
      'archivo de entorno que no forma parte del repositorio y que el servicio del '
      'sistema carga al arrancar.')
    codigo(doc, ['cp .env.example .env', 'nano .env'])
    tabla(doc, ENTORNO, [2.1, 2.3, 1.9])
    nota(doc, 'El archivo .env nunca debe incorporarse al repositorio. Si una '
         'credencial llega a quedar registrada en el historial, no basta con borrar el '
         'archivo: hay que rotar la credencial y reescribir el historial, porque '
         'cualquier copia del repositorio la conserva.', 'Sobre las credenciales')

    h(doc, '4.3 Preparar la base de datos', 2)
    codigo(doc, [
        'sudo -u postgres psql -c "CREATE DATABASE smileesync;"',
        'sudo -u postgres psql -c "CREATE USER smileesync WITH PASSWORD \'<clave>\';"',
        'sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smileesync '
        'TO smileesync;"',
        'sudo -u postgres psql -c "ALTER DATABASE smileesync OWNER TO smileesync;"',
        '',
        'python manage.py migrate',
        'python manage.py seed              # solo en un entorno de demostración',
        'python manage.py collectstatic --noinput',
    ])
    nota(doc, 'El comando seed carga el conjunto de datos de demostración. No debe '
         'ejecutarse en una instalación que vaya a operar con datos reales.')

    h(doc, '4.4 Publicar los servicios', 2)
    codigo(doc, [
        'cd ~/smileesync',
        'sudo cp infra/deploy/gunicorn.service /etc/systemd/system/',
        'sudo systemctl daemon-reload && sudo systemctl enable --now gunicorn',
        '',
        'sudo cp infra/deploy/nginx-smileesync.conf /etc/nginx/sites-available/smileesync',
        'sudo ln -sf /etc/nginx/sites-available/smileesync /etc/nginx/sites-enabled/',
        'sudo rm -f /etc/nginx/sites-enabled/default',
        'sudo nginx -t && sudo systemctl restart nginx',
    ])
    doc.save(str(SALIDA_TECNICO))
    print('Manual técnico: secciones 1 a 4.')


if __name__ == '__main__':
    main()
