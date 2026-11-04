from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
from django.db import models


class Rol(models.Model):
    """Rol del sistema. Los campos 'puede_*' controlan tanto el menú
    visible como el acceso a cada módulo (RBAC)."""

    nombre = models.CharField("nombre", max_length=50, unique=True)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

    puede_usuarios = models.BooleanField("módulo usuarios", default=False)
    puede_pacientes = models.BooleanField("módulo pacientes", default=False)
    puede_catalogos = models.BooleanField("módulo catálogos", default=False)
    puede_agenda = models.BooleanField("módulo agenda", default=False)
    puede_clinico = models.BooleanField("módulo expediente clínico", default=False)
    puede_finanzas = models.BooleanField("módulo cobros", default=False)
    puede_inteligencia = models.BooleanField("módulo inteligencia", default=False)
    puede_reportes = models.BooleanField("módulo reportes", default=False)

    # Los campos 'puede_*' conceden acceso al módulo; este determina si ese
    # acceso incluye escritura. Un rol de solo consulta ve la información de
    # sus módulos, pero no puede crearla ni modificarla.
    solo_lectura = models.BooleanField(
        "solo consulta",
        default=False,
        help_text=(
            "Permite ver los módulos asignados, sin crear ni modificar registros."
        ),
    )

    # El expediente clínico es un acto profesional, no una tarea
    # administrativa: quien lo escribe es el odontólogo, aunque su rol sea de
    # solo consulta para la agenda, y no lo escribe la recepción, aunque sí
    # modifique otros módulos. Por eso la escritura del expediente se declara
    # aparte en lugar de derivarse de `solo_lectura`.
    escritura_clinica = models.BooleanField(
        "puede registrar en el expediente",
        default=False,
        help_text="Permite registrar odontograma, notas clínicas y planes de "
        "tratamiento. Corresponde al personal odontológico.",
    )

    estado = models.BooleanField("activo", default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rol"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Usuario del sistema. El inicio de sesión se realiza con el CORREO
    electrónico (único). Se agregan rol, teléfono, estado (borrado lógico) y
    una pregunta secreta para la recuperación de contraseña."""

    PREGUNTAS = [
        ("MASCOTA", "¿Cuál fue el nombre de tu primera mascota?"),
        ("CIUDAD", "¿En qué ciudad naciste?"),
        ("ESCUELA", "¿Cuál fue el nombre de tu primera escuela?"),
        ("MADRE", "¿Cuál es el segundo nombre de tu madre?"),
        ("APODO", "¿Cuál era tu apodo de la infancia?"),
    ]
    # El correo pasa a ser único (identificador de inicio de sesión).
    email = models.EmailField("correo electrónico", unique=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="rol",
    )
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    estado = models.BooleanField("activo", default=True)  # borrado lógico
    pregunta_secreta = models.CharField(
        "pregunta secreta", max_length=10, choices=PREGUNTAS, blank=True
    )
    respuesta_secreta = models.CharField(
        "respuesta secreta (cifrada)", max_length=128, blank=True
    )

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def es_admin(self):
        return self.is_superuser or (
            self.rol is not None and self.rol.nombre == "Administrador"
        )

    def puede(self, modulo):
        """Devuelve True si el usuario tiene acceso al módulo indicado."""
        if self.es_admin:
            return True
        return bool(self.rol and getattr(self.rol, f"puede_{modulo}", False))

    @property
    def es_solo_consulta(self):
        """Un rol de solo consulta no modifica información en ningún módulo."""
        if self.es_admin:
            return False
        return bool(self.rol and self.rol.solo_lectura)

    def puede_escribir(self, modulo):
        """Acceso de escritura: exige el módulo y que el rol no sea de consulta.

        El módulo clínico es la excepción y se rige por `escritura_clinica`: el
        expediente lo escribe quien tiene competencia profesional declarada,
        con independencia de sus privilegios administrativos.
        """
        if self.es_admin:
            return True
        if not self.puede(modulo):
            return False
        if modulo == "clinico":
            return bool(self.rol and self.rol.escritura_clinica)
        return not self.es_solo_consulta

    def set_respuesta_secreta(self, texto):
        """Guarda la respuesta secreta cifrada (normalizada a minúsculas)."""
        self.respuesta_secreta = make_password((texto or "").strip().lower())

    def check_respuesta_secreta(self, texto):
        """Compara una respuesta con la guardada."""
        if not self.respuesta_secreta:
            return False
        return check_password((texto or "").strip().lower(), self.respuesta_secreta)


class HistorialUsuario(models.Model):
    """Tabla de histórico (auditoría). Antes de actualizar, desactivar o
    eliminar un usuario se inserta aquí una copia de su estado previo."""

    ACCIONES = [
        ("CREACION", "Creación"),
        ("ACTUALIZACION", "Actualización"),
        ("DESACTIVACION", "Desactivación"),
        ("ACTIVACION", "Activación"),
    ]
    usuario_ref = models.IntegerField("id de usuario")
    username = models.CharField(max_length=150)
    nombre_completo = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    rol = models.CharField(max_length=50, blank=True)
    estado_anterior = models.BooleanField()
    accion = models.CharField(max_length=20, choices=ACCIONES)
    realizado_por = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_usuario"
        verbose_name = "Historial de usuario"
        verbose_name_plural = "Historial de usuarios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.username}: {self.accion} por {self.realizado_por}"

    @classmethod
    def registrar(cls, usuario, accion, realizado_por):
        cls.objects.create(
            usuario_ref=usuario.pk,
            username=usuario.username,
            nombre_completo=usuario.get_full_name(),
            email=usuario.email,
            rol=usuario.rol.nombre if usuario.rol else "",
            estado_anterior=usuario.estado,
            accion=accion,
            realizado_por=realizado_por,
        )
