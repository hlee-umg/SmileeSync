from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from usuarios import views as uviews
from usuarios.forms import LoginCorreoForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html',
                                                 authentication_form=LoginCorreoForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', uviews.dashboard, name='dashboard'),
    path('usuarios/', include('usuarios.urls')),
]
