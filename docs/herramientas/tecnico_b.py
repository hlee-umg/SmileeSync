"""Manual técnico: operación, respaldo, diagnóstico, desarrollo y seguridad."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).parent))
from manual_comun import (SALIDA_TECNICO, codigo, h, nota, p, tabla)  # noqa: E402

FALLAS = [
    ['Síntoma', 'Causa más frecuente', 'Qué hacer'],
    ['El sitio responde «502 Bad Gateway».',
     'Gunicorn no está corriendo o falló al arrancar.',
     'systemctl status gunicorn y revisar el journal. Casi siempre es un error de '
     'sintaxis en el último despliegue o una variable de entorno ausente.'],
    ['El sitio carga sin estilos.',
     'Los archivos estáticos no se recolectaron tras el último cambio.',
     'Ejecutar collectstatic y reiniciar Gunicorn.'],
    ['Error de conexión a la base de datos.',
     'PostgreSQL detenido o credenciales cambiadas.',
     'systemctl status postgresql y verificar las variables DB_* del archivo de '
     'entorno.'],
    ['La estimación siempre devuelve la duración del catálogo.',
     'No hay modelo entrenado, el archivo del modelo no existe o scikit-learn no '
     'está instalado en el entorno virtual.',
     'Revisar el panel de inteligencia: si no hay versión activa, ejecutar el '
     'entrenamiento. El sistema sigue operando, solo pierde precisión.'],
    ['El entrenamiento falla por registros insuficientes.',
     'La base tiene menos de sesenta atenciones con sus tiempos reales.',
     'Es el comportamiento correcto. Se resuelve registrando atenciones; en un '
     'entorno de demostración, ejecutando seed.'],
    ['El despliegue automático no actualiza el servidor.',
     'Los secretos del repositorio cambiaron o la llave de despliegue fue revocada.',
     'Revisar la ejecución en el repositorio y los tres secretos del despliegue.'],
]

SEGURIDAD = [
    ['Medida', 'Estado'],
    ['Contraseñas y respuesta secreta almacenadas como resumen PBKDF2-SHA256 con '
     '720 000 iteraciones.', 'Implementado'],
    ['Control de acceso por rol aplicado en el servidor, no en la plantilla.',
     'Implementado'],
    ['Consultas con parámetros enlazados y escape automático en las plantillas.',
     'Implementado'],
    ['Secretos fuera del código, en archivo de entorno excluido del repositorio.',
     'Implementado'],
    ['Borrado lógico e historial de auditoría por entidad.', 'Implementado'],
    ['Degradación en cascada del componente predictivo ante fallas.', 'Implementado'],
    ['Cifrado en tránsito (HTTPS con certificado).', 'Pendiente: requiere dominio'],
    ['Límite de intentos de ingreso fallidos y segundo factor.', 'Pendiente'],
    ['Registro centralizado de eventos de seguridad y alertas.', 'Pendiente'],
    ['Respaldo periódico de la base de datos, con restauración probada.', 'Pendiente'],
]


def main():
    doc = Document(str(SALIDA_TECNICO))

    h(doc, '5. Operación diaria', salto=True)
    p(doc, 'El sistema no requiere intervención rutinaria. Los comandos siguientes '
      'cubren la verificación del estado y el reinicio de los servicios.')
    codigo(doc, [
        'systemctl status gunicorn nginx postgresql',
        'journalctl -u gunicorn -n 100 --no-pager      # últimas líneas del registro',
        'sudo systemctl restart gunicorn               # tras un cambio manual',
        'systemctl list-timers smileesync-entrenar.timer',
    ])

    h(doc, '6. Despliegue continuo')
    p(doc, 'Cada cambio incorporado a la rama principal del repositorio dispara la '
      'revisión automática del proyecto y la comprobación de migraciones pendientes. '
      'Superadas ambas, el servidor se actualiza por conexión segura: obtiene los '
      'cambios, aplica las migraciones, recolecta los archivos estáticos y reinicia '
      'el servicio de la aplicación. El despliegue no ejecuta el comando de carga de '
      'datos ni el entrenamiento, de modo que ningún despliegue altera la '
      'información.')
    p(doc, 'El flujo necesita tres secretos registrados en el repositorio: la '
      'dirección del servidor, el usuario y la llave privada de acceso.')

    h(doc, '7. Reentrenamiento del modelo')
    p(doc, 'El reentrenamiento está programado mediante una unidad temporizada del '
      'sistema operativo que se ejecuta el primer día de cada mes a las 3:30, con un '
      'retardo aleatorio y con límite de memoria, de modo que no compita con la '
      'operación. La unidad entrena solo si el resultado mejora al modelo vigente; en '
      'caso contrario conserva la versión en producción y deja la nueva como '
      'histórico.')
    codigo(doc, [
        'sudo cp infra/deploy/smileesync-entrenar.service /etc/systemd/system/',
        'sudo cp infra/deploy/smileesync-entrenar.timer /etc/systemd/system/',
        'sudo systemctl daemon-reload',
        'sudo systemctl enable --now smileesync-entrenar.timer',
        '',
        'python manage.py entrenar                     # ejecución manual',
        'python manage.py contrastar                   # contraste de la hipótesis',
    ])

    h(doc, '8. Respaldo y restauración', salto=True)
    p(doc, 'Es la tarea más importante del mantenimiento y la única protección contra '
      'la pérdida de la información, porque todos los componentes residen en una sola '
      'instancia. El procedimiento siguiente genera un respaldo comprimido diario, '
      'conserva los últimos treinta y descarta los anteriores.')

    h(doc, '8.1 Respaldo automático diario', 2)
    codigo(doc, [
        '#!/bin/bash',
        'set -e',
        'DESTINO=/home/ubuntu/respaldos',
        'mkdir -p "$DESTINO"',
        'FECHA=$(date +%Y%m%d-%H%M)',
        'export PGPASSWORD="<clave de la base>"',
        'pg_dump -U smileesync -h localhost smileesync \\',
        '  | gzip > "$DESTINO/smileesync-$FECHA.sql.gz"',
        'find "$DESTINO" -name "smileesync-*.sql.gz" -mtime +30 -delete',
    ], '# /home/ubuntu/respaldar.sh')
    p(doc, 'Se le da permiso de ejecución y se programa con una entrada de cron:')
    codigo(doc, [
        'chmod +x /home/ubuntu/respaldar.sh',
        'crontab -e',
        '30 2 * * *  /home/ubuntu/respaldar.sh >> /home/ubuntu/respaldos/registro.log 2>&1',
    ])
    nota(doc, 'El respaldo en el mismo disco protege contra el borrado accidental de '
         'datos, pero no contra la pérdida de la instancia. Conviene copiar los '
         'archivos a un almacenamiento externo —un bucket de objetos o una carpeta en '
         'otra máquina— al menos una vez por semana.')

    h(doc, '8.2 Restauración', 2)
    p(doc, 'Un respaldo que nunca se ha restaurado no es un respaldo. Conviene probar '
      'este procedimiento sobre una base de prueba antes de necesitarlo de verdad.')
    codigo(doc, [
        'sudo systemctl stop gunicorn',
        'gunzip -c /home/ubuntu/respaldos/smileesync-AAAAMMDD-HHMM.sql.gz \\',
        '  | psql -U smileesync -h localhost smileesync',
        'sudo systemctl start gunicorn',
    ])

    h(doc, '9. Diagnóstico de fallas frecuentes')
    tabla(doc, FALLAS, [1.7, 2.0, 2.6])

    h(doc, '10. Entorno de desarrollo y pruebas', salto=True)
    p(doc, 'En desarrollo el sistema usa SQLite, que no requiere servidor y permite '
      'reconstruir la base completa borrando un archivo. El resto de la configuración '
      'es idéntica a la de producción.')
    codigo(doc, [
        'python -m venv .venv && source .venv/bin/activate',
        'pip install -r requirements.txt',
        'python manage.py migrate',
        'python manage.py seed',
        'python manage.py runserver',
    ])
    p(doc, 'El sistema incorpora 336 verificaciones automatizadas agrupadas en ocho '
      'conjuntos. Cada una formula una afirmación sobre el sistema y la comprueba '
      'contra la base de datos y contra las pantallas. Deben ejecutarse sobre una '
      'base recién sembrada: encadenadas sobre una base ya usada, el conjunto de '
      'capacidad falla por los registros que dejan las anteriores.')
    codigo(doc, [
        'python manage.py migrate && python manage.py seed   # base limpia',
        'python prueba_horarios.py',
        'python prueba_permisos.py',
        'python prueba_calendario.py',
        'python prueba_recomendacion.py',
        'python prueba_flujos.py',
        'python prueba_capacidad.py',
        'python prueba_clinico.py',
        'python prueba_modelo.py      # requiere un modelo entrenado',
    ])

    h(doc, '11. Estado de la seguridad')
    p(doc, 'El sistema implementa las medidas de la columna izquierda. Las marcadas '
      'como pendientes deben resolverse antes de operar con información de pacientes '
      'reales; la primera de ellas, el cifrado en tránsito, es condición de las '
      'demás.')
    tabla(doc, SEGURIDAD, [4.6, 1.7])
    doc.save(str(SALIDA_TECNICO))
    print('Manual técnico: secciones 5 a 11.')


if __name__ == '__main__':
    main()
