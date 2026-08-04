from django.core.management.base import BaseCommand
from usuarios.models import Rol, Usuario


class Command(BaseCommand):
    help = 'Crea los roles base y usuarios de demostración.'

    def handle(self, *args, **options):
        roles = {
            'Administrador': dict(descripcion='Acceso total al sistema',
                                  puede_usuarios=True, puede_pacientes=True, puede_catalogos=True,
                                  puede_agenda=True, puede_inteligencia=True, puede_reportes=True),
            'Recepcionista': dict(descripcion='Gestión de pacientes, agenda y reportes',
                                  puede_pacientes=True, puede_agenda=True, puede_reportes=True),
            'Odontólogo': dict(descripcion='Agenda y pacientes',
                               puede_pacientes=True, puede_agenda=True),
            'Asistente': dict(descripcion='Apoyo en la agenda',
                              puede_agenda=True),
        }
        objetos = {}
        for nombre, campos in roles.items():
            rol, creado = Rol.objects.get_or_create(nombre=nombre, defaults=campos)
            if not creado:
                for k, v in campos.items():
                    setattr(rol, k, v)
                rol.save()
            objetos[nombre] = rol
            self.stdout.write(self.style.SUCCESS(f'Rol {"creado" if creado else "actualizado"}: {nombre}'))

        if not Usuario.objects.filter(username='admin').exists():
            admin = Usuario.objects.create_superuser(
                'admin', 'admin@smileesync.local', '***REMOVED***',
                first_name='Administrador', last_name='General')
            admin.rol = objetos['Administrador']
            admin.save()
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin / ***REMOVED***'))

        if not Usuario.objects.filter(username='recepcion').exists():
            u = Usuario.objects.create_user(
                'recepcion', 'recepcion@smileesync.local', '***REMOVED***',
                first_name='Ana', last_name='Recepción')
            u.rol = objetos['Recepcionista']
            u.save()
            self.stdout.write(self.style.SUCCESS('Usuario creado: recepcion / ***REMOVED***'))

        self.stdout.write(self.style.SUCCESS('Seed completado.'))
