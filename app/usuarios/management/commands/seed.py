import random
from datetime import date, datetime, time, timedelta

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
        'PROC-007': 250,
        'PROC-008': 800,
        'PROC-009': 180,
        'PROC-010': 450,
    }

    # Padrón de pacientes de demostración. Dos meses de agenda requieren un
    # padrón suficientemente amplio para que las citas no se concentren en unas
    # pocas personas.
    PACIENTES = [
        ('Sofía Alejandra', 'Castillo Ruano', date(1998, 3, 14), 'F', '5544 1122'),
        ('Roberto Antonio', 'Méndez Solórzano', date(1981, 7, 2), 'M', '4411 8890'),
        ('Lucía Fernanda', 'Aguilar Pineda', date(1993, 11, 25), 'F', '3398 7744'),
        ('Diego Armando', 'Ruiz Barrientos', date(2007, 1, 9), 'M', '5566 2211'),
        ('Carmen Elena', 'Ortiz Marroquín', date(1974, 5, 30), 'F', '4477 3300'),
        ('Andrea Michelle', 'Hernández Solís', date(1995, 4, 17), 'F', '5533 9911'),
        ('José Manuel', 'Villatoro Cruz', date(1988, 9, 23), 'M', '4455 6677'),
        ('María José', 'Figueroa Lemus', date(2001, 2, 11), 'F', '5588 2244'),
        ('Luis Eduardo', 'Morales Chacón', date(1979, 12, 5), 'M', '3366 1199'),
        ('Gabriela Isabel', 'Sandoval Ponce', date(1992, 6, 28), 'F', '4422 7755'),
        ('Marco Vinicio', 'Estrada Juárez', date(1985, 8, 16), 'M', '5511 3388'),
        ('Paola Andrea', 'Recinos Alvarado', date(2004, 10, 3), 'F', '4433 9900'),
        ('Carlos Humberto', 'Barrios Monzón', date(1968, 1, 21), 'M', '3377 4466'),
        ('Ana Lucía', 'Guzmán Herrera', date(1997, 7, 8), 'F', '5599 1177'),
        ('Fernando José', 'Orellana Pérez', date(2010, 3, 30), 'M', '4466 2288'),
        ('Claudia Patricia', 'Mejía Rodas', date(1983, 11, 12), 'F', '3322 8855'),
        ('Rodrigo Alberto', 'Paiz Contreras', date(1990, 5, 19), 'M', '5577 6633'),
        ('Mónica Alejandra', 'Castañeda Rivas', date(1999, 9, 7), 'F', '4499 5522'),
        ('Pablo Andrés', 'Quiñónez Galindo', date(2006, 4, 26), 'M', '3344 7711'),
        ('Silvia Mercedes', 'Arriaga Bonilla', date(1972, 2, 14), 'F', '5522 4499'),
        ('Daniel Alejandro', 'Cabrera Soto', date(1994, 12, 1), 'M', '4488 3366'),
        ('Karla Vanessa', 'Ixcot Ramírez', date(2002, 8, 9), 'F', '3355 9922'),
        ('Óscar Emilio', 'Zamora Letona', date(1977, 6, 22), 'M', '5566 7744'),
        ('Jennifer Nicole', 'Dubón Escobar', date(2012, 1, 15), 'F', '4411 2299'),
    ]

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
        # La clínica cuenta con dos profesionales: el odontólogo principal, con
        # especialidad en ortodoncia, y una odontóloga general.
        cuentas = {}
        for correo, nombres, apellidos in [
            ('hjlee@smileesync.local', 'Hee Joon', 'Lee'),
            ('rgiron@smileesync.local', 'Rachelle', 'Girón'),
        ]:
            cuenta = Usuario.objects.filter(email__iexact=correo).first()
            if not cuenta:
                cuenta = Usuario.objects.create_user(
                    correo, correo, '***REMOVED***',
                    first_name=nombres, last_name=apellidos)
                self.stdout.write(self.style.SUCCESS(
                    f'Usuario creado: {correo} / ***REMOVED***'))
            cuenta.rol = objetos['Odontólogo']
            cuenta.save()
            cuentas[correo] = cuenta

        self.sembrar_clinica(cuentas['hjlee@smileesync.local'],
                             cuentas['rgiron@smileesync.local'])
        self.normalizar()
        self.sembrar_expediente()

        self.stdout.write(self.style.SUCCESS('Seed completado. Login por CORREO. '
                                             'Pregunta secreta admin: mascota=firulais; recepcion: ciudad=guatemala'))

    # ==================================================================
    def sembrar_clinica(self, usuario_lee, usuario_giron):
        """Datos operativos de la clínica: catálogo, pacientes, horarios y citas.

        Permite que el módulo Principal y la agenda tengan contenido real desde
        el primer arranque. Es idempotente: se puede ejecutar varias veces.
        """
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
            ('PROC-007', 'Control de ortodoncia', 'Ortodoncia', 'BAJA', 30),
            ('PROC-008', 'Retiro de brackets', 'Ortodoncia', 'MEDIA', 60),
            ('PROC-009', 'Sellante de fosas y fisuras', 'Odontopediatría', 'BAJA', 25),
            ('PROC-010', 'Limpieza profunda por cuadrante', 'Odontología general',
             'MEDIA', 50),
        ]:
            obj, _ = Procedimiento.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'especialidad': especialidades[esp],
                          'nivel_complejidad': compl, 'duracion_promedio_min': dur,
                          'precio': self.TARIFAS.get(codigo, 0)})
            procedimientos[codigo] = obj

        # --- Odontólogos ---
        # La clínica opera con dos profesionales: el odontólogo principal, con
        # especialidad en ortodoncia, y una odontóloga general.
        lee, _ = Odontologo.objects.get_or_create(
            colegiado='CD-20451',
            defaults={'nombres': 'Hee Joon', 'apellidos': 'Lee',
                      'especialidad': especialidades['Ortodoncia'],
                      'telefono': '3312 4590', 'usuario': usuario_lee})
        giron, _ = Odontologo.objects.get_or_create(
            colegiado='CD-19877',
            defaults={'nombres': 'Rachelle', 'apellidos': 'Girón',
                      'especialidad': especialidades['Odontología general'],
                      'telefono': '3345 7712', 'usuario': usuario_giron})

        # Los odontólogos de demostración de versiones anteriores se dan de baja
        # para que no aparezcan en el filtro de la agenda. No se eliminan: sus
        # citas históricas conservan la referencia.
        retirados = (Odontologo.objects
                     .filter(colegiado__in=['CD-10245', 'CD-14892'], estado=True)
                     .update(estado=False))
        Usuario.objects.filter(
            email__in=['cgiron@smileesync.local', 'gpaz@smileesync.local'],
            estado=True).update(estado=False, is_active=False)
        if retirados:
            self.stdout.write(self.style.WARNING(
                f'  {retirados} odontólogo(s) de demostración anteriores fueron '
                f'desactivados.'))

        # --- Horarios de disponibilidad (lunes a viernes) ---
        for odo in (lee, giron):
            for dia in ('LUN', 'MAR', 'MIE', 'JUE', 'VIE'):
                HorarioDisponibilidad.objects.get_or_create(
                    odontologo=odo, dia_semana=dia, hora_inicio=time(8, 0),
                    defaults={'hora_fin': time(12, 0)})
                HorarioDisponibilidad.objects.get_or_create(
                    odontologo=odo, dia_semana=dia, hora_inicio=time(14, 0),
                    defaults={'hora_fin': time(18, 0)})

        # --- Pacientes ---
        pacientes = {}
        for i, (nombres, apellidos, nac, sexo, tel) in enumerate(self.PACIENTES, 1):
            codigo = f'PAC-{i:04d}'
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
        AntecedenteMedico.objects.get_or_create(
            paciente=pacientes['PAC-0004'], tipo='Condición',
            defaults={'descripcion': 'Hipertensión arterial controlada'})

        creadas = self.sembrar_agenda(lee, giron, pacientes, procedimientos)

        self.stdout.write(self.style.SUCCESS(
            f'Datos de la clínica: {Especialidad.objects.count()} especialidades, '
            f'{Procedimiento.objects.count()} procedimientos, '
            f'{Odontologo.objects.filter(estado=True).count()} odontólogos activos, '
            f'{Paciente.objects.count()} pacientes, '
            f'{Cita.objects.count()} citas ({creadas} nuevas).'))

    # ==================================================================
    # Generación de la agenda de demostración
    # ==================================================================
    # Semilla fija: la agenda resultante es aleatoria pero reproducible, de modo
    # que una demostración repetida muestre siempre los mismos datos.
    SEMILLA = 20261016

    # Reparto de procedimientos según la especialidad del profesional. El peso
    # refleja la frecuencia con que la clínica los realiza.
    CARGA = {
        'CD-20451': [  # ortodoncia
            ('PROC-007', 34), ('PROC-005', 8), ('PROC-008', 5),
            ('PROC-001', 16), ('PROC-002', 12), ('PROC-010', 8),
            ('PROC-004', 6), ('PROC-009', 5), ('PROC-003', 3), ('PROC-006', 3),
        ],
        'CD-19877': [  # odontología general
            ('PROC-001', 26), ('PROC-002', 22), ('PROC-010', 12),
            ('PROC-004', 11), ('PROC-006', 9), ('PROC-009', 8),
            ('PROC-003', 7), ('PROC-007', 5),
        ],
    }

    # Factor de ritmo de cada profesional. Es la señal que el modelo debe
    # aprender: el mismo procedimiento no dura lo mismo en manos distintas.
    RITMO = {'CD-20451': 0.93, 'CD-19877': 1.07}

    # Procedimientos cuya duración crece con el número de piezas tratadas.
    ADITIVOS = {'PROC-002', 'PROC-009', 'PROC-010'}

    # Semanas de historia y de agenda futura que se siembran.
    SEMANAS_ATRAS = 6
    SEMANAS_ADELANTE = 2

    # Material e indicaciones habituales de cada procedimiento, para que la nota
    # de evolución describa la atención con el detalle que el expediente exige.
    DETALLE_CLINICO = {
        'PROC-001': ('Pasta profiláctica, copa de hule, flúor en barniz',
                     'Mantener la higiene habitual; se cita a control en seis meses.',
                     False),
        'PROC-002': ('Resina compuesta, adhesivo de séptima generación, ácido grabador',
                     'Evitar alimentos duros durante veinticuatro horas.', True),
        'PROC-003': ('Limas rotatorias, hipoclorito de sodio, gutapercha, cemento sellador',
                     'Tomar el analgésico indicado; se cita para la restauración definitiva.',
                     True),
        'PROC-004': ('Lidocaína al dos por ciento con epinefrina, sutura de seda',
                     'Morder la gasa durante treinta minutos; dieta blanda y fría por un día.',
                     True),
        'PROC-005': ('Brackets metálicos de prescripción Roth, arco de níquel-titanio 014',
                     'Dieta blanda la primera semana; se cita a control en cuatro semanas.',
                     False),
        'PROC-006': ('Barniz fluorado al cinco por ciento',
                     'No ingerir alimentos durante treinta minutos.', False),
        'PROC-007': ('Arco de acero, ligaduras elásticas',
                     'Se cita a control en cuatro semanas.', False),
        'PROC-008': ('Alicate de retiro, fresa de pulido, retenedor termoformado',
                     'Uso del retenedor durante veintidós horas al día.', False),
        'PROC-009': ('Sellante fotopolimerizable, ácido grabador',
                     'No ingerir alimentos duros durante el resto del día.', False),
        'PROC-010': ('Ultrasonido, curetas Gracey, clorhexidina al cero coma doce',
                     'Enjuague con clorhexidina durante siete días.', True),
    }

    COMPLICACIONES = [
        'Sangrado que obligó a prolongar la hemostasia.',
        'Anestesia de efecto tardío; se requirió refuerzo.',
        'Paciente con reflejo nauseoso acentuado; se trabajó en intervalos.',
        'Conducto con anatomía atípica que demandó instrumentación adicional.',
        'Pieza con mayor profundidad de caries que la observada en el diagnóstico.',
    ]

    def documentar(self, cita, piezas, complicacion, rng):
        """Redacta la nota de evolución de una cita atendida.

        Las variables que la nota registra son las mismas que determinaron la
        duración real de la atención, de modo que el conjunto de entrenamiento
        quede internamente coherente.
        """
        from clinico.models import NotaClinica

        materiales, indicaciones, anestesia = self.DETALLE_CLINICO.get(
            cita.procedimiento.codigo, ('', 'Control en seis meses.', False))
        NotaClinica.objects.create(
            cita=cita, paciente=cita.paciente, odontologo=cita.odontologo,
            fecha=cita.fecha, motivo=cita.procedimiento.nombre,
            hallazgos_clinicos='Tejidos blandos sin alteraciones aparentes. '
                               'Higiene oral aceptable.',
            procedimiento_realizado=(
                f'{cita.procedimiento.nombre} concluido según lo planificado'
                + (f' en {piezas} piezas.' if piezas > 1 else '.')),
            num_piezas=piezas, anestesia=anestesia, materiales=materiales,
            complicacion=complicacion,
            detalle_complicacion=rng.choice(self.COMPLICACIONES) if complicacion else '',
            indicaciones=indicaciones, registrado_por='seed')

    def sembrar_agenda(self, lee, giron, pacientes, procedimientos):
        """Genera dos meses de agenda: historia atendida y citas por atender.

        La historia es la que alimenta al modelo predictivo, de modo que no se
        construye con duraciones iguales a las del catálogo: la duración real de
        cada atención se obtiene de un procedimiento base afectado por el ritmo
        del profesional, el número de piezas tratadas y la aparición de
        complicaciones, más una dispersión aleatoria. Así el promedio histórico
        y el modelo tienen señal real que recuperar.
        """
        from django.utils import timezone

        from agenda.models import Cita
        from agenda.disponibilidad import asignar_unidad, franjas_efectivas

        rng = random.Random(self.SEMILLA)
        hoy = timezone.localdate()
        lunes = hoy - timedelta(days=hoy.weekday())
        inicio = lunes - timedelta(weeks=self.SEMANAS_ATRAS)
        fin = lunes + timedelta(weeks=self.SEMANAS_ADELANTE, days=4)

        lista_pacientes = list(pacientes.values())
        odontologos = [lee, giron]
        # Pacientes en tratamiento de ortodoncia: vuelven cada mes a control.
        en_ortodoncia = rng.sample(lista_pacientes, 7)

        def elegir_procedimiento(odo):
            opciones = self.CARGA[odo.colegiado]
            codigos = [c for c, _ in opciones]
            pesos = [p for _, p in opciones]
            return procedimientos[rng.choices(codigos, weights=pesos)[0]]

        def piezas_de(codigo):
            if codigo == 'PROC-005':
                return rng.choice([10, 12, 14])
            if codigo in ('PROC-002', 'PROC-009'):
                return rng.choices([1, 2, 3], weights=[62, 28, 10])[0]
            if codigo == 'PROC-010':
                return rng.choice([1, 2])
            return 1

        creadas = 0
        fecha = inicio
        while fecha <= fin:
            if fecha.weekday() > 4:
                fecha += timedelta(days=1)
                continue

            for odo in odontologos:
                # La ocupación no es uniforme: los lunes y los viernes la
                # clínica agenda menos que a media semana.
                ocupacion = {0: 0.62, 1: 0.80, 2: 0.84, 3: 0.78, 4: 0.58}[fecha.weekday()]
                for f_ini, f_fin in franjas_efectivas(odo, fecha):
                    momento = datetime.combine(fecha, f_ini)
                    limite = datetime.combine(fecha, f_fin)
                    while momento < limite:
                        if rng.random() > ocupacion:
                            momento += timedelta(minutes=rng.choice([15, 30]))
                            continue

                        proc = elegir_procedimiento(odo)
                        piezas = piezas_de(proc.codigo)
                        duracion = proc.duracion_promedio_min
                        # El tiempo crece con el número de piezas solo donde el
                        # trabajo es aditivo. La colocación de brackets abarca la
                        # arcada completa en una sola sesión, de modo que su
                        # duración no se multiplica por cada bracket.
                        if piezas > 1 and proc.codigo in self.ADITIVOS:
                            duracion += int(proc.duracion_promedio_min * 0.4 * (piezas - 1))
                        duracion = max(15, int(round(duracion / 5) * 5))
                        fin_dt = momento + timedelta(minutes=duracion)
                        if fin_dt > limite:
                            break

                        inicio_h, fin_h = momento.time(), fin_dt.time()
                        if Cita.objects.filter(odontologo=odo, fecha=fecha,
                                               hora_inicio_programada=inicio_h).exists():
                            momento = fin_dt + timedelta(minutes=rng.choice([0, 5, 10]))
                            continue

                        unidad = asignar_unidad(fecha, inicio_h, fin_h)
                        if unidad is None:        # ambos sillones ocupados
                            momento += timedelta(minutes=15)
                            continue

                        # Los pacientes en ortodoncia regresan a control; el
                        # resto se reparte sobre el padrón completo.
                        if proc.codigo in ('PROC-005', 'PROC-007', 'PROC-008'):
                            paciente = rng.choice(en_ortodoncia)
                        else:
                            paciente = rng.choice(lista_pacientes)

                        if fecha < hoy:
                            estado = 'CANCELADA' if rng.random() < 0.07 else 'ATENDIDA'
                        elif fecha == hoy and fin_h < timezone.localtime().time():
                            estado = 'ATENDIDA'
                        else:
                            estado = 'CANCELADA' if rng.random() < 0.04 else 'PROGRAMADA'

                        real = inicio_real = fin_real = None
                        complicacion = False
                        if estado == 'ATENDIDA':
                            complicacion = rng.random() < 0.12
                            factor = (self.RITMO[odo.colegiado]
                                      * (1.28 if complicacion else 1.0)
                                      * rng.gauss(1.0, 0.09))
                            real = max(10, int(round(duracion * factor)))
                            retraso = rng.choice([0, 0, 0, 5, 5, 10])
                            inicio_real = (momento + timedelta(minutes=retraso)).time()
                            fin_real = (momento + timedelta(minutes=retraso + real)).time()

                        cita = Cita.objects.create(
                            paciente=paciente, odontologo=odo, procedimiento=proc,
                            unidad=unidad, fecha=fecha,
                            hora_inicio_programada=inicio_h,
                            hora_fin_programada=fin_h,
                            duracion_asignada_min=duracion,
                            hora_inicio_real=inicio_real, hora_fin_real=fin_real,
                            duracion_real_min=real, estado_cita=estado,
                            observaciones=f'Piezas por tratar: {piezas}.' if piezas > 1 else '')
                        creadas += 1
                        if estado == 'ATENDIDA':
                            self.documentar(cita, piezas, complicacion, rng)
                        momento = fin_dt + timedelta(minutes=rng.choice([0, 5, 10, 15]))
            fecha += timedelta(days=1)

        atendidas = Cita.objects.filter(estado_cita='ATENDIDA').count()
        programadas = Cita.objects.filter(estado_cita='PROGRAMADA').count()
        self.stdout.write(self.style.SUCCESS(
            f'Agenda sembrada del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}: '
            f'{atendidas} atendidas (historial del modelo) y '
            f'{programadas} programadas.'))
        return creadas

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

        # ------------------------------------------------- planes de tratamiento
        lee = Odontologo.objects.filter(colegiado='CD-20451').first()
        giron = Odontologo.objects.filter(colegiado='CD-19877').first()

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
            ('PLAN-0002', 'PAC-0002', lee, 'BORRADOR', Decimal('0.00'),
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
            f'de evolución, {PlanTratamiento.objects.count()} planes '
            f'({nuevos_planes} nuevos), {Pago.objects.count()} pagos.'))
