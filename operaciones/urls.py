# operaciones/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('validar/', views.validar_asegurabilidad, name='validar_asegurabilidad'),
    path('historial/<int:asegurado_id>/', views.consultar_servicios, name='consultar_servicios'),
    path('crear-os/<int:asegurado_id>/', views.crear_orden_de_servicio, name='crear_orden_de_servicio'),
    path('ajax/puntos-atencion/', views.get_puntos_atencion, name='ajax_get_puntos_atencion'),
    path('seleccionar-servicios/<int:os_id>/', views.seleccionar_servicios, name='seleccionar_servicios'),
    path('cancelar-os/<int:os_id>/', views.cancelar_creacion_os, name='cancelar_creacion_os'),
]
