from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, HistorialUsuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puede_usuarios', 'puede_catalogos', 'puede_agenda', 'estado')
    list_filter = ('estado',)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('SmileeSync', {'fields': ('rol', 'telefono', 'estado')}),
    )
    list_display = ('username', 'email', 'rol', 'estado', 'is_staff')
    list_filter = ('rol', 'estado', 'is_staff')


@admin.register(HistorialUsuario)
class HistorialUsuarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'username', 'accion', 'realizado_por', 'estado_anterior')
    list_filter = ('accion',)
    readonly_fields = [f.name for f in HistorialUsuario._meta.fields]
