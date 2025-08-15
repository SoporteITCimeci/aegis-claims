# gestion/admin.py

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import (
    Proveedor, PuntoAtencion, Cliente, Asegurado, Contrato,
    CategoriaServicio, SubServicio, Plan, DetallePlan, BaremoProveedor,
    CoberturaCategoriaPlan, ContactoProveedor, CuentaBancariaProveedor,
)

# --- Recurso para Import/Export de Asegurados ---
class AseguradoResource(resources.ModelResource):
    contrato = fields.Field(
        column_name='CONTRATO',
        attribute='contrato',
        widget=ForeignKeyWidget(Contrato, 'numero_contrato')
    )
    tipo_documento = fields.Field(column_name='ID CI BEN', attribute='tipo_documento')
    cedula = fields.Field(column_name='CEDULA BENEFICIARIO', attribute='cedula')
    nombre_completo = fields.Field(column_name='NOMBRE Y APELLIDO BEN', attribute='nombre_completo')
    fecha_nacimiento = fields.Field(column_name='FECHA NACIMIENTO', attribute='fecha_nacimiento')
    sexo = fields.Field(column_name='SEXO', attribute='sexo')
    parentesco = fields.Field(column_name='PARENTESCO', attribute='parentesco')
    telefono_celular = fields.Field(column_name='TELEFONO CELULAR', attribute='telefono_celular')
    correo_electronico = fields.Field(column_name='CORREO ELECTRONICO', attribute='correo_electronico')
    estado_residencia = fields.Field(column_name='ESTADO', attribute='estado_residencia')
    ciudad_residencia = fields.Field(column_name='CIUDAD', attribute='ciudad_residencia')
    estado_individual = fields.Field(column_name='ESTADO ASEGURADO', attribute='estado_individual', default='ACTIVO')

    class Meta:
        model = Asegurado
        fields = (
            'id', 'contrato', 'tipo_documento', 'cedula', 'nombre_completo', 
            'fecha_nacimiento', 'sexo', 'parentesco', 'telefono_celular', 
            'correo_electronico', 'estado_residencia', 'ciudad_residencia', 'estado_individual', 'fecha_baja'
        )
        import_id_fields = ['cedula']
        skip_unchanged = True
        report_skipped = True

# --- Inlines para una gestión más sencilla ---
class PuntoAtencionInline(admin.TabularInline):
    model = PuntoAtencion
    extra = 1

class BaremoProveedorInline(admin.TabularInline):
    model = BaremoProveedor
    extra = 1
    autocomplete_fields = ['sub_servicio']

class AseguradoInline(admin.TabularInline):
    model = Asegurado
    extra = 1
    fields = ('nombre_completo', 'cedula', 'parentesco', 'estado_individual')
    show_change_link = True

class CoberturaCategoriaPlanInline(admin.TabularInline):
    model = CoberturaCategoriaPlan
    extra = 1
    fields = ('categoria', 'es_ilimitada', 'cantidad_maxima', 'limite_mensual')

class DetallePlanInline(admin.TabularInline):
    model = DetallePlan
    extra = 1
    autocomplete_fields = ['sub_servicio']

# --- Inlines para la gestión de Proveedores ---
class ContactoProveedorInline(admin.TabularInline):
    model = ContactoProveedor
    extra = 1
    fields = ('nombre', 'telefono', 'correo')

class CuentaBancariaProveedorInline(admin.TabularInline):
    model = CuentaBancariaProveedor
    extra = 1

class PuntoAtencionInline(admin.TabularInline):
    model = PuntoAtencion
    extra = 1
    fields = ('nombre_sede', 'estado', 'ciudad', 'municipio','direccion', 'telefonos', 'activo')

class BaremoProveedorInline(admin.TabularInline):
    model = BaremoProveedor
    extra = 1
    autocomplete_fields = ['sub_servicio']

# --- Registros de Modelos en el Panel de Administración ---
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'rif', 'tipo_negociacion', 'activo')
    search_fields = ('razon_social', 'rif')
    list_filter = ('activo', 'tipo_negociacion')
    inlines = [
        ContactoProveedorInline,
        CuentaBancariaProveedorInline,
        PuntoAtencionInline,
        BaremoProveedorInline
    ]
    fieldsets = (
        ('Información Fiscal', {
            'fields': ('rif', 'razon_social', 'direccion_fiscal')
        }),
        ('Condiciones Comerciales', {
            'fields': ('tipo_negociacion', 'activo')
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'rif', 'activo')
    search_fields = ('razon_social', 'rif')
    list_filter = ('activo',)

@admin.register(CategoriaServicio)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)

@admin.register(SubServicio)
class SubServicioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'categoria', 'activo')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('categoria', 'activo')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre_plan', 'tipo', 'monto_cobertura_usd', 'activo')
    list_filter = ('activo', 'tipo')
    search_fields = ('nombre_plan',)
    inlines = [CoberturaCategoriaPlanInline, DetallePlanInline]
    fieldsets = (
        (None, {
            'fields': ('nombre_plan', 'tipo', 'monto_cobertura_usd', 'activo', 'descripcion')
        }),
    )

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('numero_contrato', 'cliente', 'plan', 'fecha_inicio_vigencia', 'fecha_fin_vigencia', 'activo')
    search_fields = ('numero_contrato', 'cliente__razon_social', 'plan__nombre_plan')
    list_filter = ('activo', 'plan', 'cliente')
    inlines = [AseguradoInline]
    autocomplete_fields = ['cliente', 'plan']

@admin.register(Asegurado)
class AseguradoAdmin(ImportExportModelAdmin):
    resource_class = AseguradoResource
    list_display = ('nombre_completo', 'cedula', 'contrato', 'parentesco', 'estado_individual', 'fecha_baja')
    search_fields = ('nombre_completo', 'cedula', 'contrato__numero_contrato')
    list_filter = ('estado_individual', 'parentesco', 'contrato__plan')
    autocomplete_fields = ['contrato']
    fieldsets = (
        ('Información del Contrato', {'fields': ('contrato',)}),
        ('Datos Personales', {'fields': ('tipo_documento', 'cedula', 'nombre_completo', 'fecha_nacimiento', 'sexo', 'parentesco')}),
        ('Datos de Contacto', {'fields': ('telefono_celular', 'correo_electronico', 'estado_residencia', 'ciudad_residencia')}),
        ('Estado de Cobertura', {'fields': ('estado_individual', 'fecha_baja')}),
    )

@admin.register(PuntoAtencion)
class PuntoAtencionAdmin(admin.ModelAdmin):
    list_display = ('nombre_sede', 'proveedor', 'direccion', 'activo')
    search_fields = ['nombre_sede', 'proveedor__razon_social']
    list_filter = ('activo', 'proveedor')

@admin.register(BaremoProveedor)
class BaremoProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'sub_servicio', 'precio', 'activo')
    search_fields = ['proveedor__razon_social', 'sub_servicio__descripcion', 'sub_servicio__codigo']
    list_filter = ('activo', 'proveedor')

@admin.register(CoberturaCategoriaPlan)
class CoberturaCategoriaPlanAdmin(admin.ModelAdmin):
    list_display = ('plan', 'categoria', 'es_ilimitada', 'cantidad_maxima', 'limite_mensual')
    list_filter = ('plan', 'categoria')