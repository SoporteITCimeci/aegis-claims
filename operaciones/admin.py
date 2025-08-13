# operaciones/admin.py

from django.contrib import admin
from .models import Siniestro, OrdenDeServicio

@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Siniestro.
    """
    list_display = ('asegurado', 'fecha_reporte', 'estado')
    list_filter = ('estado', 'fecha_reporte')
    search_fields = ('asegurado__nombre_completo', 'asegurado__cedula')
    # Habilitamos la búsqueda de asegurados para una carga más fácil
    autocomplete_fields = ['asegurado']
    
    # Hacemos que los campos de fecha sean de solo lectura una vez creados
    readonly_fields = ('fecha_reporte',)

@admin.register(OrdenDeServicio)
class OrdenDeServicioAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo OrdenDeServicio.
    Organizamos los campos en secciones lógicas para facilitar la gestión.
    """
    list_display = ('numero_os', 'siniestro', 'punto_atencion', 'estado_os', 'monto_referencial_os')
    list_filter = ('estado_os', 'punto_atencion__proveedor')
    search_fields = ('numero_os', 'siniestro__asegurado__nombre_completo', 'siniestro__asegurado__cedula')
    
    # Habilitamos la búsqueda para una carga más fácil
    autocomplete_fields = ['siniestro', 'punto_atencion', 'servicios_prestados']
    
    # Definimos qué campos no se pueden editar manualmente
    readonly_fields = (
        'numero_os',
        'fecha_emision',
        'fecha_vencimiento_activacion',
        'monto_referencial_os' # Este campo se debería calcular automáticamente
    )
    
    # Organizamos la vista de edición en secciones
    fieldsets = (
        ('Información Principal de la OS', {
            'fields': ('siniestro', 'numero_os', 'punto_atencion', 'estado_os')
        }),
        ('Servicios y Montos', {
            'fields': ('servicios_prestados', 'monto_referencial_os')
        }),
        ('Fechas Clave', {
            'fields': ('fecha_emision', 'fecha_vencimiento_activacion')
        }),
        ('Ciclo de Cuentas por Pagar', {
            'classes': ('collapse',), # Esta sección aparecerá colapsada por defecto
            'fields': (
                'numero_factura', 'numero_control_factura', 'fecha_emision_factura',
                'fecha_recepcion_factura', 'monto_factura_ves', 'monto_factura_usd', 'tasa_bcv'
            ),
        }),
    )