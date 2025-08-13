# gestion/models.py

from django.db import models
from django.utils import timezone
from datetime import date
from simple_history.models import HistoricalRecords

# --- Modelos de Proveedores ---
class Proveedor(models.Model):
    razon_social = models.CharField(max_length=255, unique=True)
    activo = models.BooleanField(default=True)
    rif = models.CharField("R.I.F.", max_length=20, blank=True, unique=True)
    banco_pago = models.CharField("Banco", max_length=100, blank=True)
    numero_cuenta = models.CharField("Número de Cuenta", max_length=20, blank=True)
    class TipoCuenta(models.TextChoices):
        CORRIENTE = 'COR', 'Corriente'
        AHORROS = 'AHO', 'Ahorros'
    tipo_cuenta = models.CharField(max_length=3, choices=TipoCuenta.choices, blank=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name_plural = "Proveedores"
    def __str__(self): return self.razon_social

class PuntoAtencion(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="puntos_atencion")
    nombre_sede = models.CharField("Nombre de la Sede/APS", max_length=255)
    direccion = models.TextField("Dirección de la Sede")
    telefonos = models.CharField("Teléfonos de Contacto", max_length=150)
    persona_contacto_sede = models.CharField("Persona Contacto (Sede)", max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Punto de Atención"
        verbose_name_plural = "Puntos de Atención"
    def __str__(self): return f"{self.proveedor.razon_social} - {self.nombre_sede}"

# --- Modelos de Clientes ---
class Cliente(models.Model):
    razon_social = models.CharField(max_length=255, unique=True)
    activo = models.BooleanField(default=True)
    rif = models.CharField("R.I.F.", max_length=20, blank=True)
    direccion_fiscal = models.TextField("Dirección Fiscal", blank=True)
    persona_contacto = models.CharField("Persona Contacto", max_length=100, blank=True)
    email_contacto = models.EmailField("Email Contacto", blank=True)
    telefono_contacto = models.CharField("Teléfono Contacto", max_length=50, blank=True)
    dia_cobro = models.PositiveIntegerField("Día de Cobro", default=1)
    class Meta:
        verbose_name_plural = "Clientes"
    def __str__(self): return self.razon_social

# --- Modelos de Comercialización (ACTUALIZADOS) ---
class CategoriaServicio(models.Model):
    nombre = models.CharField("Nombre de la Categoría", max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
    def __str__(self): return self.nombre

class SubServicio(models.Model):
    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.CASCADE, related_name="subservicios")
    codigo = models.CharField("Código", max_length=50, unique=True)
    descripcion = models.CharField("Descripción del Sub-Servicio", max_length=255)
    activo = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Sub Servicio"
        verbose_name_plural = "Sub Servicios"
    def __str__(self): return f"{self.codigo} - {self.descripcion}"

class Plan(models.Model):
    nombre_plan = models.CharField("Nombre del Plan", max_length=100, unique=True)
    
    class TipoPlan(models.TextChoices):
        POR_CANTIDAD = 'CANTIDAD', 'Por Cantidad de Servicios'
        POR_MONTO = 'MONTO', 'Por Monto de Cobertura (USD)'
    
    tipo = models.CharField("Tipo de Plan", max_length=10, choices=TipoPlan.choices, default=TipoPlan.POR_CANTIDAD)
    monto_cobertura_usd = models.DecimalField(
        "Monto Cobertura (USD)",
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Monto tope para planes por cobertura. Dejar en 0 si no aplica."
    )
    descripcion = models.TextField("Descripción General", blank=True)
    activo = models.BooleanField(default=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name_plural = "Planes"
    def __str__(self): return self.nombre_plan

class CoberturaCategoriaPlan(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="coberturas_categoria")
    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.CASCADE)
    es_ilimitada = models.BooleanField("Cobertura Ilimitada", default=False, help_text="Marcar si la cobertura para esta categoría es ilimitada.")
    cantidad_maxima = models.PositiveIntegerField("Cantidad Máxima Anual", default=0, help_text="Dejar en 0 si la cobertura es ilimitada.")
    limite_mensual = models.PositiveIntegerField("Límite Mensual", default=0, help_text="Dejar en 0 si no hay límite mensual.")

    class Meta:
        verbose_name = "Cobertura por Tipo Plan"
        verbose_name_plural = "Coberturas por Tipo Plan"
        unique_together = ('plan', 'categoria')
    def __str__(self): return f"{self.plan.nombre_plan} - {self.categoria.nombre}"

class DetallePlan(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="detalles")
    sub_servicio = models.ForeignKey(SubServicio, on_delete=models.CASCADE)
    class Meta:
        verbose_name = "Detalle de Plan"
        verbose_name_plural = "Detalles de Planes"
        unique_together = ('plan', 'sub_servicio')
    def __str__(self): return f"{self.plan.nombre_plan} incluye {self.sub_servicio.descripcion}"

# --- Modelo de Baremos ---
class BaremoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="baremo")
    sub_servicio = models.ForeignKey(SubServicio, on_delete=models.PROTECT, related_name="proveedores_asociados")
    precio = models.DecimalField("Precio (USD)", max_digits=12, decimal_places=2)
    activo = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Baremo de Proveedor"
        verbose_name_plural = "Baremo Proveedores"
        unique_together = ('proveedor', 'sub_servicio')
    def __str__(self): return f"{self.proveedor.razon_social} | {self.sub_servicio.descripcion}"

# --- ESTRUCTURA DE CONTRATOS Y ASEGURADOS ---
class Contrato(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contratos")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="contratos")
    numero_contrato = models.CharField("Número de Contrato/Póliza", max_length=50, unique=True)
    aseguradora = models.CharField("Aseguradora", max_length=100, blank=True)
    ente = models.CharField("Ente", max_length=100, blank=True)
    observaciones = models.TextField("Observaciones", blank=True)
    class Ramo(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        COLECTIVO = 'COLECTIVO', 'Colectivo'
    ramo = models.CharField(max_length=10, choices=Ramo.choices, default=Ramo.COLECTIVO)
    class Fraccionamiento(models.TextChoices):
        ANUAL = 'ANUAL', 'Anual'
        SEMESTRAL = 'SEMESTRAL', 'Semestral'
        TRIMESTRAL = 'TRIMESTRAL', 'Trimestral'
        MENSUAL = 'MENSUAL', 'Mensual'
        OTRO = 'OTRO', 'Otro'
    fraccionamiento = models.CharField(max_length=20, choices=Fraccionamiento.choices, default=Fraccionamiento.ANUAL)
    fecha_emision = models.DateField("Fecha Emisión")
    fecha_inicio_vigencia = models.DateField("Fecha Inicio Vigencia")
    fecha_fin_vigencia = models.DateField("Fecha Fin Vigencia")
    activo = models.BooleanField(default=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name_plural = "Contratos"
    def __str__(self): return f"{self.numero_contrato} - {self.cliente.razon_social}"

class Asegurado(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name="asegurados")
    class TipoDocumento(models.TextChoices):
        VENEZOLANO = 'V', 'Venezolano'
        EXTRANJERO = 'E', 'Extranjero'
        PASAPORTE = 'P', 'Pasaporte'
        MENOR = 'M', 'Menor (Sin C.I.)'
    tipo_documento = models.CharField(max_length=1, choices=TipoDocumento.choices)
    cedula = models.CharField("Cédula/Documento", max_length=20)
    nombre_completo = models.CharField("Nombre Completo", max_length=100)
    fecha_nacimiento = models.DateField("Fecha de Nacimiento")
    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    class Parentesco(models.TextChoices):
        TITULAR = 'TITULAR', 'Titular'
        CONYUGE = 'CONYUGE', 'Cónyuge'
        HIJO = 'HIJO', 'Hijo/a'
        PADRE = 'PADRE', 'Padre'
        MADRE = 'MADRE', 'Madre'
        OTRO = 'OTRO', 'Otro'
    parentesco = models.CharField(max_length=10, choices=Parentesco.choices)
    telefono_celular = models.CharField("Teléfono Celular", max_length=20, blank=True)
    correo_electronico = models.EmailField("Correo Electrónico", blank=True)
    estado_residencia = models.CharField("Estado", max_length=50, blank=True)
    ciudad_residencia = models.CharField("Ciudad", max_length=50, blank=True)
    class EstadoAsegurado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo (Falta de Pago)'
        DE_BAJA = 'DE_BAJA', 'De Baja'
    estado_individual = models.CharField("Estado Individual", max_length=10, choices=EstadoAsegurado.choices, default=EstadoAsegurado.ACTIVO)
    fecha_baja = models.DateField("Fecha de Baja", blank=True, null=True)
    history = HistoricalRecords()
    
    @property
    def edad(self):
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

    @property
    def titular(self):
        if self.parentesco == self.Parentesco.TITULAR:
            return self
        try:
            return Asegurado.objects.get(contrato=self.contrato, parentesco=self.Parentesco.TITULAR)
        except Asegurado.DoesNotExist:
            return None

    class Meta:
        verbose_name_plural = "Asegurados"
        unique_together = ('contrato', 'cedula')
    def __str__(self):
        return f"{self.nombre_completo} ({self.cedula})"