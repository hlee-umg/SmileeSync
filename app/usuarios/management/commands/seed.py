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
            # Según la Tabla 3 del documento, odontólogos y asistentes
            # consultan la agenda pero no la modifican.
            'Odontólogo': dict(descripcion='Consulta de agenda y pacientes',
                               puede_pacientes=True, puede_agenda=True,
                               solo_lectura=True),
            'Asistente': dict(descripcion='Consulta de la agenda',
                              puede_agenda=True, solo_lectura=True),
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
                'admin@smileesync.local', 'admin@smileesync.local', '***REMOVED***',
                first_name='Administrador', last_name='General')
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin@smileesync.local / ***REMOVED***'))
        admin.rol = objetos['Administrador']
        admin.pregunta_secreta = 'MASCOTA'
        admin.set_respuesta_secreta('firulais')
        admin.save()

        recep = Usuario.objects.filter(email__iexact='recepcion@smileesync.local').first()
        if not recep:
            recep = Usuario.objects.create_user(
                'recepcion@smileesync.local', 'recepcion@smileesync.local', '***REMOVED***',
                first_name='Ana', last_name='Recepción')
            self.stdout.write(self.style.SUCCESS('Usuario creado: recepcion@smileesync.local / ***REMOVED***'))
        recep.rol = objetos['Recepcionista']
        recep.pregunta_secreta = 'CIUDAD'
        recep.set_respuesta_secreta('guatemala')
        recep.save()

        # --- Odontólogos con cuenta de usuario ---
        odontologa = Usuario.objects.filter(email__iexact='gpaz@smileesync.local').first()
        if not odontologa:
            odontologa = Usuario.objects.create_user(
                'gpaz@smileesync.local', 'gpaz@smileesync.local', '***REMOVED***',
                first_name='Gabriela', last_name='Paz')
        odontologa.rol = objetos['Odontólogo']
        odontologa.save()

        odontologo = Usuario.objects.filter(email__iexact='cgiron@smileesync.local').first()
        if not odontologo:
            odontologo = Usuario.objects.create_user(
                'cgiron@smileesync.local', 'cgiron@smileesync.local', '***REMOVED***',
                first_name='Carlos', last_name='Girón')
        odontologo.rol = objetos['Odontólogo']
        odontologo.save()

        self.sembrar_clinica(odontologo, odontologa)

        self.stdout.write(self.style.SUCCESS('Seed completado. Login por CORREO. '
                                             'Pregunta secreta admin: mascota=firulais; recepcion: ciudad=guatemala'))

    # ==================================================================
    def sembrar_clinica(self, usuario_giron, usuario_paz):
        """Datos operativos de la clínica: catálogo, pacientes, horarios y citas.

        Permite que el módulo Principal y la agenda tengan contenido real desde
        el primer arranque. Es idempotente: se puede ejecutar varias veces.
        """
        from datetime import date, time, timedelta
        from django.utils import timezone

        from agenda.models import Cita, HorarioDisponibilidad
        from catalogo.models import Especialidad, Odontologo, Procedimiento
        from pacientes.models import AntecedenteMedico, Paciente

        # --- Especialidades ---
        especialidades = {}
        for nombre, desc in [
            ('Odontología general', 'Atención preventiva y restaurativa básica'),
            ('Endodoncia', 'Tratamiento de conductos radiculares'),
            ('Ortodoncia', 'Corrección de la posición dental'),
            ('Cirugía oral', 'Extracciones y procedimientos quirúrgicos'),
            ('Odontopediatría', 'Atención odontológica infantil'),
        ]:
            obj, _ = Especialidad.objects.get_or_create(
                nombre=nombre, defaults={'descripcion': desc})
            especialidades[nombre] = obj

        # --- Procedimientos ---
        procedimientos = {}
        for codigo, nombre, esp, compl, dur in [
            ('PROC-001', 'Profilaxis dental', 'Odontología general', 'BAJA', 30),
            ('PROC-002', 'Resina compuesta', 'Odontología general', 'MEDIA', 45),
            ('PROC-003', 'Tratamiento de conducto', 'Endodoncia', 'ALTA', 90),
            ('PROC-004', 'Extracción simple', 'Cirugía oral', 'MEDIA', 40),
            ('PROC-005', 'Colocación de brackets', 'Ortodoncia', 'ALTA', 120),
            ('PROC-006', 'Aplicación de flúor', 'Odontopediatría', 'BAJA', 20),
        ]:
            obj, _ = Procedimiento.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'especialidad': especialidades[esp],
                          'nivel_complejidad': compl, 'duracion_promedio_min': dur})
            procedimientos[codigo] = obj

        # --- Odontólogos ---
        giron, _ = Odontologo.objects.get_or_create(
            colegiado='CD-10245',
            defaults={'nombres': 'Carlos Enrique', 'apellidos': 'Girón Mejía',
                      'especialidad': especialidades['Odontología general'],
                      'telefono': '3321 7788', 'usuario': usuario_giron})
        paz, _ = Odontologo.objects.get_or_create(
            colegiado='CD-14892',
            defaults={'nombres': 'Gabriela María', 'apellidos': 'Paz Hernández',
                      'especialidad': especialidades['Endodoncia'],
                      'telefono': '3321 4455', 'usuario': usuario_paz})

        # --- Horarios de disponibilidad (lunes a viernes) ---
        for odo in (giron, paz):
            for dia in ('LUN', 'MAR', 'MIE', 'JUE', 'VIE'):
                HorarioDisponibilidad.objects.get_or_create(
                    odontologo=odo, dia_semana=dia, hora_inicio=time(8, 0),
                    defaults={'hora_fin': time(12, 0)})
                HorarioDisponibilidad.objects.get_or_create(
                    odontologo=odo, dia_semana=dia, hora_inicio=time(14, 0),
                    defaults={'hora_fin': time(18, 0)})

        # --- Pacientes ---
        pacientes = {}
        for codigo, nombres, apellidos, nac, sexo, tel in [
            ('PAC-0001', 'Sofía Alejandra', 'Castillo Ruano', date(1998, 3, 14), 'F', '5544 1122'),
            ('PAC-0002', 'Roberto Antonio', 'Méndez Solórzano', date(1981, 7, 2), 'M', '4411 8890'),
            ('PAC-0003', 'Lucía Fernanda', 'Aguilar Pineda', date(1993, 11, 25), 'F', '3398 7744'),
            ('PAC-0004', 'Diego Armando', 'Ruiz Barrientos', date(2007, 1, 9), 'M', '5566 2211'),
            ('PAC-0005', 'Carmen Elena', 'Ortiz Marroquín', date(1974, 5, 30), 'F', '4477 3300'),
            ('PAC-0006', 'Andrea Michelle', 'Hernández Solís', date(1995, 4, 17), 'F', '5533 9911'),
        ]:
            obj, _ = Paciente.objects.get_or_create(
                codigo=codigo,
                defaults={'nombres': nombres, 'apellidos': apellidos,
                          'fecha_nacimiento': nac, 'sexo': sexo, 'telefono': tel,
                          'direccion': 'Cuilapa, Santa Rosa'})
            pacientes[codigo] = obj

        AntecedenteMedico.objects.get_or_create(
            paciente=pacientes['PAC-0001'], tipo='Alergia',
            defaults={'descripcion': 'Alergia documentada a la penicilina'})
        AntecedenteMedico.objects.get_or_create(
            paciente=pacientes['PAC-0002'], tipo='Condición',
            defaults={'descripcion': 'Bruxismo nocturno en tratamiento'})

        # --- Citas: semana pasada atendidas (alimentan el historial) y
        #     semana actual programadas (llenan el calendario) ---
        hoy = timezone.localdate()
        lunes = hoy - timedelta(days=hoy.weekday())

        plan = [
            # (desplazamiento_dias, hora, paciente, procedimiento, odontólogo, estado, duración real)
            (-7, time(8, 0), 'PAC-0001', 'PROC-001', giron, 'ATENDIDA', 28),
            (-7, time(9, 0), 'PAC-0002', 'PROC-003', paz, 'ATENDIDA', 118),
            (-6, time(8, 0), 'PAC-0003', 'PROC-002', giron, 'ATENDIDA', 51),
            (-6, time(14, 0), 'PAC-0004', 'PROC-006', giron, 'ATENDIDA', 22),
            (-5, time(9, 0), 'PAC-0005', 'PROC-004', paz, 'ATENDIDA', 47),
            (-5, time(15, 0), 'PAC-0001', 'PROC-002', giron, 'ATENDIDA', 43),
            (-4, time(8, 0), 'PAC-0006', 'PROC-001', giron, 'ATENDIDA', 33),
            (-4, time(10, 0), 'PAC-0002', 'PROC-001', giron, 'ATENDIDA', 31),
            (0, time(8, 0), 'PAC-0001', 'PROC-001', giron, 'PROGRAMADA', None),
            (0, time(9, 0), 'PAC-0002', 'PROC-003', paz, 'PROGRAMADA', None),
            (1, time(8, 0), 'PAC-0004', 'PROC-002', giron, 'PROGRAMADA', None),
            (1, time(10, 0), 'PAC-0003', 'PROC-005', paz, 'PROGRAMADA', None),
            (1, time(14, 30), 'PAC-0006', 'PROC-001', giron, 'PROGRAMADA', None),
            (2, time(9, 0), 'PAC-0005', 'PROC-004', paz, 'PROGRAMADA', None),
            (2, time(11, 0), 'PAC-0003', 'PROC-001', giron, 'CANCELADA', None),
            (3, time(8, 0), 'PAC-0002', 'PROC-002', giron, 'PROGRAMADA', None),
            (3, time(15, 0), 'PAC-0001', 'PROC-006', giron, 'PROGRAMADA', None),
            (4, time(9, 0), 'PAC-0006', 'PROC-003', paz, 'PROGRAMADA', None),
        ]

        creadas = 0
        for desplazamiento, hora, cod_paciente, cod_proc, odo, estado_cita, real in plan:
            fecha = lunes + timedelta(days=desplazamiento)
            procedimiento = procedimientos[cod_proc]
            duracion = procedimiento.duracion_promedio_min
            fin_dt = (timezone.datetime.combine(fecha, hora) + timedelta(minutes=duracion))
            if Cita.objects.filter(paciente=pacientes[cod_paciente], fecha=fecha,
                                   hora_inicio_programada=hora).exists():
                continue
            Cita.objects.create(
                paciente=pacientes[cod_paciente], odontologo=odo,
                procedimiento=procedimiento, fecha=fecha,
                hora_inicio_programada=hora, hora_fin_programada=fin_dt.time(),
                duracion_asignada_min=duracion,
                hora_inicio_real=hora if real else None,
                hora_fin_real=((timezone.datetime.combine(fecha, hora) +
                                timedelta(minutes=real)).time() if real else None),
                duracion_real_min=real, estado_cita=estado_cita)
            creadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'Datos de la clínica: {Especialidad.objects.count()} especialidades, '
            f'{Procedimiento.objects.count()} procedimientos, '
            f'{Odontologo.objects.count()} odontólogos, '
            f'{Paciente.objects.count()} pacientes, '
            f'{Cita.objects.count()} citas ({creadas} nuevas).'))
