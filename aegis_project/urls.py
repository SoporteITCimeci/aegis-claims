# aegis_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from core import views as core_views

admin.site.site_header = "Sistema Integrado de Gestión de Riesgos"
admin.site.site_title = "Portal de CIMECI Médicas"
admin.site.index_title = "Menú de Opciones"

urlpatterns = [
    path('login/', core_views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login_redirect/', core_views.login_redirect, name='login_redirect'),
    path('admin/', admin.site.urls),
    path('operaciones/', include('operaciones.urls')),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
]