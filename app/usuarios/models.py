from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.Model):
    """Rol del sistema. Los campos 'puede_*' controlan tanto el menú
    visible como el acceso a cada módulo (RBAC)."""
    nombre = models.CharField('nombre', max_length=50, unique=True)
    descripcion = models.CharField('descripción', max_length=200, blank=True)

    puede_usuarios = models.BooleanField('módulo usuarios', default=False)
    puede_pacientes = models.BooleanField('módulo pacientes', default=False)
    puede_catalogos = models.BooleanField('módulo catálogos', default=False)
    puede_agenda = models.BooleanField('módulo agenda', default=False)
    puede_inteligencia = models.BooleanField('módulo inteligencia', default=False)
    puede_reportes = models.BooleanField('módulo reportes', default=False)

    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Usuario del sistema. Extiende el usuario de Django y agrega rol,
    teléfono y estado (para el borrado lógico)."""
    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, null=True, blank=True, related_name='usuarios',
        verbose_name='rol')
    telefono = models.CharField('teléfono', max_length=20, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    @property
    def es_admin(self):
        return self.is_superuser or (self.rol is not None and self.rol.nombre == 'Administrador')

    def puede(self, modulo):
        """Devuelve True si el usuario tiene acceso al módulo indicado."""
        if self.es_admin:
            return True
        return bool(self.rol and getattr(self.rol, f'puede_{modulo}', False))


class HistorialUsuario(models.Model):
    """Tabla de histórico (auditoría). Antes de actualizar, desactivar o
    eliminar un usuario se inserta aquí una copia de su estado previo."""
    ACCIONES = [
        ('CREACION', 'Creación'),
        ('ACTUALIZACION', 'Actualización'),
        ('DESACTIVACION', 'Desactivación'),
        ('ACTIVACION', 'Activación'),
    ]
    usuario_ref = models.IntegerField('id de usuario')
    username = models.CharField(max_length=150)
    nombre_completo = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    rol = models.CharField(max_length=50, blank=True)
    estado_anterior = models.BooleanField()
    accion = models.CharField(max_length=20, choices=ACCIONES)
    realizado_por = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_usuario'
        verbose_name = 'Historial de usuario'
        verbose_name_plural = 'Historial de usuarios'
        ordering = ['-fecha']

    @classmethod
    def registrar(cls, usuario, accion, realizado_por):
        cls.objects.create(
            usuario_ref=usuario.pk,
            username=usuario.username,
            nombre_completo=usuario.get_full_name(),
            email=usuario.email,
            rol=usuario.rol.nombre if usuario.rol else '',
            estado_anterior=usuario.estado,
            accion=accion,
            realizado_por=realizado_por,
        )
