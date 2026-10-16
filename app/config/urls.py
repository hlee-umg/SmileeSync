from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from usuarios.forms import LoginCorreoForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html',
                                                 authentication_form=LoginCorreoForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # El módulo Principal (calendario de la agenda) es la raíz del sitio.
    path('', include('agenda.urls')),

    path('usuarios/', include('usuarios.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('catalogo/', include('catalogo.urls')),
    path('', include('clinico.urls')),
    path('', include('reportes.urls')),
    path('', include('inteligencia.urls')),
]
