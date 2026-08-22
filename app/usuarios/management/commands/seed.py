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

        admin = Usuario.objects.filter(email__iexact='admin@smileesync.local').first()
        if not admin:
            admin = Usuario.objects.create_superuser(
                'admin@smileesync.local', 'admin@smileesync.local', 'Admin123!',
                first_name='Administrador', last_name='General')
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin@smileesync.local / Admin123!'))
        admin.rol = objetos['Administrador']
        admin.pregunta_secreta = 'MASCOTA'
        admin.set_respuesta_secreta('firulais')
        admin.save()

        recep = Usuario.objects.filter(email__iexact='recepcion@smileesync.local').first()
        if not recep:
            recep = Usuario.objects.create_user(
                'recepcion@smileesync.local', 'recepcion@smileesync.local', 'Recepcion123!',
                first_name='Ana', last_name='Recepción')
            self.stdout.write(self.style.SUCCESS('Usuario creado: recepcion@smileesync.local / Recepcion123!'))
        recep.rol = objetos['Recepcionista']
        recep.pregunta_secreta = 'CIUDAD'
        recep.set_respuesta_secreta('guatemala')
        recep.save()

        self.stdout.write(self.style.SUCCESS('Seed completado. Login por CORREO. '
                                             'Pregunta secreta admin: mascota=firulais; recepcion: ciudad=guatemala'))
