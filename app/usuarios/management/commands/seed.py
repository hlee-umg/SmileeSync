from django.core.management.base import BaseCommand
from usuarios.models import Rol, Usuario


class Command(BaseCommand):
    """Comando único de preparación de datos.

    Hace tres cosas, en este orden y de forma idempotente, para que baste
    ejecutarlo una vez después de cada despliegue:

        1. SEMBRAR    — roles, usuarios, catálogo, pacientes, horarios y citas
                        de demostración.
        2. NORMALIZAR — completa los datos que las versiones anteriores del
                        sistema no llenaban (unidad dental de las citas
                        antiguas, tarifas del catálogo), de modo que no haga
                        falta correr comandos aparte tras cada migración.
        3. EXPEDIENTE — odontograma, notas de evolución y un plan de
                        tratamiento con su abono, para que el módulo clínico
                        tenga contenido real desde el primer arranque.

    Nunca reescribe una contraseña ya existente ni sustituye datos que el
    usuario haya capturado: solo llena lo que está vacío.
    """
    help = ('Crea roles, usuarios y datos de demostración, y normaliza los '
            'registros que quedaron incompletos por migraciones anteriores.')

    # Tarifas de referencia del catálogo, en quetzales. Solo se aplican a los
    # procedimientos que todavía no tienen precio: una tarifa capturada por la
    # clínica nunca se sobrescribe.
    TARIFAS = {
        'PROC-001': 150,
        'PROC-002': 350,
        'PROC-003': 1200,
        'PROC-004': 400,
        'PROC-005': 4500,
        'PROC-006': 100,
    }

    def handle(self, *args, **options):
        roles = {
            'Administrador': dict(descripcion='Acceso total al sistema',
                                  puede_usuarios=True, puede_pacientes=True, puede_catalogos=True,
                                  puede_agenda=True, puede_clinico=True, puede_finanzas=True,
                                  puede_inteligencia=True, puede_reportes=True,
                                  escritura_clinica=True),
            # La recepción cobra y agenda: consulta el expediente para saber qué
            # toca, pero no lo escribe.
            'Recepcionista': dict(descripcion='Gestión de pacientes, agenda, cobros y reportes',
                                  puede_pacientes=True, puede_agenda=True,
                                  puede_clinico=True, puede_finanzas=True,
                                  puede_reportes=True),
            # Según la Tabla 3 del documento, odontólogos y asistentes
            # consultan la agenda pero no la modifican. El expediente es la
            # excepción: es su acto profesional, así que sí lo escriben.
            'Odontólogo': dict(descripcion='Consulta de agenda y registro del expediente clínico',
                               puede_pacientes=True, puede_agenda=True,
                               puede_clinico=True, solo_lectura=True,
                               escritura_clinica=True),
            'Asistente': dict(descripcion='Consulta de la agenda y del expediente',
                              puede_agenda=True, puede_clinico=True,
                              solo_lectura=True),
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
        self.normalizar()
        self.sembrar_expediente()

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
        from agenda.disponibilidad import asignar_unidad
        from catalogo.models import Especialidad, Odontologo, Procedimiento, UnidadDental
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

        # --- Unidades dentales (sillones) ---
        # Son el recurso que limita la operación: la clínica tiene menos
        # unidades que odontólogos. Se administran como registros del catálogo,
        # de modo que incorporar otra silla es darla de alta.
        for codigo, nombre, ubicacion in [
            ('SIL-01', 'Sillón 1', 'Consultorio principal'),
            ('SIL-02', 'Sillón 2', 'Consultorio secundario'),
        ]:
            UnidadDental.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'ubicacion': ubicacion})

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
                          'nivel_complejidad': compl, 'duracion_promedio_min': dur,
                          'precio': self.TARIFAS.get(codigo, 0)})
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

        # --- Citas: atendidas en el pasado (alimentan el historial y el
        #     promedio del modelo) y programadas en los próximos días hábiles
        #     (llenan el calendario) ---
        # Las programadas no se anclan al lunes de la semana en curso: si se
        # hiciera, el sábado quedarían todas en el pasado y el calendario
        # aparecería vacío. Se colocan en los siguientes días hábiles, de modo
        # que la demostración sirva cualquier día del año.
        hoy = timezone.localdate()
        lunes = hoy - timedelta(days=hoy.weekday())

        habiles, dia = [], hoy
        while len(habiles) < 5:
            if dia.weekday() < 5:
                habiles.append(dia)
            dia += timedelta(days=1)

        plan = [
            # Desplazamiento negativo: días contados desde el lunes de esta
            # semana (quedan en el pasado). Desplazamiento 0 a 4: el n-ésimo
            # día hábil a partir de hoy.
            # (desplazamiento, hora, paciente, procedimiento, odontólogo, estado, duración real)
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
            # Simultánea con la anterior: ocupa el segundo sillón y deja la
            # clínica sin unidades libres a esa hora, para poder mostrar la
            # restricción de capacidad.
            (1, time(8, 0), 'PAC-0005', 'PROC-001', paz, 'PROGRAMADA', None),
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
            fecha = (lunes + timedelta(days=desplazamiento) if desplazamiento < 0
                     else habiles[desplazamiento])
            procedimiento = procedimientos[cod_proc]
            duracion = procedimiento.duracion_promedio_min
            fin_dt = (timezone.datetime.combine(fecha, hora) + timedelta(minutes=duracion))
            if Cita.objects.filter(paciente=pacientes[cod_paciente], fecha=fecha,
                                   hora_inicio_programada=hora).exists():
                continue
            # Se asigna la primera unidad libre, igual que hace el sistema al
            # programar desde la pantalla.
            unidad = asignar_unidad(fecha, hora, fin_dt.time())
            Cita.objects.create(
                paciente=pacientes[cod_paciente], odontologo=odo,
                procedimiento=procedimiento, unidad=unidad, fecha=fecha,
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

    # ==================================================================
    def normalizar(self):
        """Completa los registros que quedaron incompletos por migraciones.

        Cada vez que el sistema incorpora un campo nuevo, los registros
        anteriores lo reciben en nulo o en cero. Resolverlo aquí evita tener que
        recordar un comando distinto por cada migración: el seed es el único
        paso manual del despliegue.

        Solo escribe donde falta el dato; nunca sustituye un valor capturado.
        """
        from agenda.models import Cita
        from agenda.disponibilidad import asignar_unidad, unidades_activas
        from catalogo.models import Procedimiento

        # --- Tarifas del catálogo ---
        # Sin precio no se puede presupuestar un plan de tratamiento.
        con_tarifa = 0
        for codigo, precio in self.TARIFAS.items():
            actualizados = (Procedimiento.objects
                            .filter(codigo=codigo, precio=0)
                            .update(precio=precio))
            con_tarifa += actualizados
        sin_tarifa = Procedimiento.objects.filter(estado=True, precio=0).count()

        # --- Unidad dental de las citas anteriores a su incorporación ---
        # La unidad es el recurso que limita la operación; una cita sin unidad
        # asignada no aparece ocupando sillón y falsea la capacidad.
        sin_unidad = list(Cita.objects.filter(unidad__isnull=True, estado=True)
                          .exclude(estado_cita='CANCELADA')
                          .order_by('fecha', 'hora_inicio_programada'))
        asignadas = irresolubles = 0
        if unidades_activas():
            for cita in sin_unidad:
                unidad = asignar_unidad(cita.fecha, cita.hora_inicio_programada,
                                        cita.hora_fin_programada,
                                        excluir_cita=cita.pk)
                if unidad:
                    cita.unidad = unidad
                    cita.save(update_fields=['unidad'])
                    asignadas += 1
                else:
                    # Dos citas antiguas simultáneas con más profesionales que
                    # sillones: el dato histórico es contradictorio y se informa
                    # en lugar de inventar una asignación.
                    irresolubles += 1

        self.stdout.write(self.style.SUCCESS(
            f'Normalización: {con_tarifa} tarifas completadas '
            f'({sin_tarifa} procedimientos activos siguen sin precio), '
            f'{asignadas} de {len(sin_unidad)} citas recibieron unidad dental.'))
        if irresolubles:
            self.stdout.write(self.style.WARNING(
                f'  {irresolubles} cita(s) antiguas no pudieron recibir unidad: '
                f'coinciden en horario y superan las unidades activas. '
                f'Revíselas o dé de alta otra unidad en el catálogo.'))

    # ==================================================================
    def sembrar_expediente(self):
        """Odontograma, notas de evolución y planes de tratamiento de ejemplo.

        Sirve para que el módulo clínico se pueda mostrar sin capturar nada a
        mano, y para que el conjunto de entrenamiento del modelo tenga desde el
        inicio las variables que solo la nota clínica aporta: piezas tratadas,
        anestesia y complicaciones.
        """
        from datetime import time, timedelta
        from decimal import Decimal

        from django.utils import timezone

        from agenda.models import Cita
        from catalogo.models import Odontologo, Procedimiento
        from clinico.models import (DetallePlan, Hallazgo, HistorialPlan,
                                    NotaClinica, Pago, PlanTratamiento)
        from inteligencia.servicio import estimar_duracion
        from pacientes.models import Paciente

        hoy = timezone.localdate()

        def paciente(codigo):
            return Paciente.objects.filter(codigo=codigo).first()

        # ---------------------------------------------------------- odontograma
        # Hallazgos por paciente: (pieza, cara, tipo, días atrás, observación)
        odontogramas = {
            'PAC-0001': [
                (16, 'O', 'CARIES', 30, 'Caries oclusal profunda'),
                (26, 'O', 'OBTURADA', 400, 'Resina colocada en 2024'),
                (36, 'TODA', 'AUSENTE', 800, 'Extraída antes del tratamiento'),
                (46, 'TODA', 'ENDODONCIA', 200, 'Conducto tratado'),
                (11, 'TODA', 'SANA', 30, ''),
                (21, 'TODA', 'SANA', 30, ''),
            ],
            'PAC-0002': [
                (17, 'O', 'CARIES', 20, 'Caries incipiente'),
                (27, 'V', 'FRACTURA', 20, 'Fractura del ángulo vestibular'),
                (38, 'TODA', 'AUSENTE', 900, ''),
                (48, 'TODA', 'EXTRACCION', 20, 'Tercer molar retenido'),
                (45, 'O', 'OBTURADA', 300, ''),
            ],
            'PAC-0003': [
                (24, 'M', 'CARIES', 10, ''),
                (25, 'O', 'SELLANTE', 150, ''),
            ],
        }

        nuevos_hallazgos = 0
        for codigo, lista in odontogramas.items():
            pac = paciente(codigo)
            if not pac:
                continue
            for pieza, cara, tipo, dias, observacion in lista:
                _, creado = Hallazgo.objects.get_or_create(
                    paciente=pac, pieza=pieza, cara=cara, tipo=tipo,
                    defaults={'fecha': hoy - timedelta(days=dias),
                              'observacion': observacion,
                              'registrado_por': 'seed'})
                nuevos_hallazgos += 1 if creado else 0

        # -------------------------------------------------------- notas clínicas
        # Una nota por cada cita ya atendida. Los valores de piezas, anestesia y
        # complicación varían a propósito: son las variables que explican por qué
        # dos citas del mismo procedimiento no duran lo mismo.
        perfiles = {
            'PROC-001': dict(piezas=1, anestesia=False, materiales='Pasta profiláctica, flúor'),
            'PROC-002': dict(piezas=2, anestesia=True, materiales='Resina compuesta A2, adhesivo'),
            'PROC-003': dict(piezas=1, anestesia=True, materiales='Limas, gutapercha, cemento'),
            'PROC-004': dict(piezas=1, anestesia=True, materiales='Lidocaína al 2%, sutura'),
            'PROC-005': dict(piezas=14, anestesia=False, materiales='Brackets metálicos, arco 014'),
            'PROC-006': dict(piezas=1, anestesia=False, materiales='Barniz fluorado'),
        }
        nuevas_notas = 0
        atendidas = (Cita.objects
                     .filter(estado_cita='ATENDIDA', estado=True)
                     .select_related('paciente', 'odontologo', 'procedimiento')
                     .order_by('fecha'))
        for indice, cita in enumerate(atendidas):
            if NotaClinica.objects.filter(cita=cita).exists():
                continue
            perfil = perfiles.get(cita.procedimiento.codigo,
                                  dict(piezas=1, anestesia=False, materiales=''))
            # Una de cada cuatro atenciones se documenta con complicación, que es
            # el orden de magnitud que la clínica reporta y lo que permite ver el
            # efecto de esa variable en la duración real.
            complicacion = (indice % 4 == 3)
            NotaClinica.objects.create(
                cita=cita, paciente=cita.paciente, odontologo=cita.odontologo,
                fecha=cita.fecha, motivo=cita.procedimiento.nombre,
                hallazgos_clinicos='Tejidos blandos sin alteraciones aparentes.',
                procedimiento_realizado=f'{cita.procedimiento.nombre} concluido '
                                        f'según lo planificado.',
                num_piezas=perfil['piezas'], anestesia=perfil['anestesia'],
                materiales=perfil['materiales'],
                complicacion=complicacion,
                detalle_complicacion=('Sangrado que obligó a prolongar la '
                                      'hemostasia.' if complicacion else ''),
                indicaciones='Evitar alimentos duros durante 24 horas.',
                registrado_por='seed')
            nuevas_notas += 1

        # ------------------------------------------------- planes de tratamiento
        giron = Odontologo.objects.filter(colegiado='CD-10245').first()
        paz = Odontologo.objects.filter(colegiado='CD-14892').first()

        def procedimiento(codigo):
            return Procedimiento.objects.filter(codigo=codigo).first()

        planes = [
            # (código, paciente, odontólogo, estado, descuento, diagnóstico,
            #  [(fase, código de procedimiento, pieza, piezas)])
            ('PLAN-0001', 'PAC-0001', giron, 'APROBADO', Decimal('50.00'),
             'Caries oclusal en pieza 16 y necesidad de profilaxis previa. '
             'Se propone tratamiento en dos fases.',
             [(1, 'PROC-001', None, 1),
              (2, 'PROC-002', 16, 1),
              (2, 'PROC-002', 26, 1),
              (2, 'PROC-006', None, 1)]),
            ('PLAN-0002', 'PAC-0002', paz, 'BORRADOR', Decimal('0.00'),
             'Fractura del ángulo vestibular en pieza 27 y tercer molar 48 '
             'retenido con indicación quirúrgica.',
             [(1, 'PROC-004', 48, 1),
              (2, 'PROC-002', 27, 1)]),
        ]

        nuevos_planes = 0
        for codigo, cod_paciente, odontologo, estado_plan, descuento, diagnostico, renglones in planes:
            pac = paciente(cod_paciente)
            if not (pac and odontologo) or PlanTratamiento.objects.filter(codigo=codigo).exists():
                continue
            plan = PlanTratamiento.objects.create(
                codigo=codigo, paciente=pac, odontologo=odontologo,
                diagnostico=diagnostico, estado_plan=estado_plan,
                fecha=hoy - timedelta(days=7), descuento=descuento,
                fecha_aprobacion=(hoy - timedelta(days=6)
                                  if estado_plan != 'BORRADOR' else None),
                creado_por='seed')
            HistorialPlan.registrar(plan, 'CREACION', 'seed', estado_anterior='')

            orden_por_fase = {}
            for fase, cod_proc, pieza, piezas in renglones:
                proc = procedimiento(cod_proc)
                if not proc:
                    continue
                # La duración del renglón la estima el mismo servicio que usa la
                # agenda, para que el presupuesto de tiempo y el de la cita
                # provengan de la misma fuente.
                estimacion = estimar_duracion(proc, odontologo, plan.fecha,
                                              time(9, 0), piezas)
                orden_por_fase[fase] = orden_por_fase.get(fase, 0) + 1
                DetallePlan.objects.create(
                    plan=plan, fase=fase, orden=orden_por_fase[fase],
                    procedimiento=proc, pieza=pieza, num_piezas=piezas,
                    precio_unitario=proc.precio or Decimal('0.00'),
                    duracion_estimada_min=estimacion.duracion_min,
                    origen_estimacion=estimacion.origen)
            nuevos_planes += 1

            # Un abono parcial en el plan aprobado, para que la pantalla de
            # cobros muestre un saldo distinto de cero desde el inicio.
            if estado_plan == 'APROBADO' and plan.total > 0:
                Pago.objects.create(
                    plan=plan, fecha=hoy - timedelta(days=6),
                    monto=(plan.total / 2).quantize(Decimal('0.01')),
                    metodo='EFECTIVO', referencia='REC-0001',
                    observaciones='Abono inicial', recibido_por='seed')
                HistorialPlan.registrar(plan, 'PAGO', 'seed',
                                        detalle='Abono inicial del 50%')

        self.stdout.write(self.style.SUCCESS(
            f'Expediente clínico: {Hallazgo.objects.count()} hallazgos '
            f'({nuevos_hallazgos} nuevos), {NotaClinica.objects.count()} notas '
            f'({nuevas_notas} nuevas), {PlanTratamiento.objects.count()} planes '
            f'({nuevos_planes} nuevos), {Pago.objects.count()} pagos.'))
