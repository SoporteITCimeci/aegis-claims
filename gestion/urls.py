# gestion/urls.py

from django.urls import path
from . import admin_views

urlpatterns = [
    path('mapa-proveedores/', admin_views.mapa_proveedores_view, name='mapa_proveedores'),
    path('api/proveedores-activos/', admin_views.proveedores_activos_api, name='proveedores_activos_api'),
]