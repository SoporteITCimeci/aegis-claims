# operaciones/models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from simple_history.models import HistoricalRecords

class Siniestro(models.Model):
    asegurado = models.ForeignKey('gestion.Asegurado', on_delete=models.PROTECT, related_name="siniestros")
    fecha_reporte = models.DateTimeField("Fecha de Reporte", default=timezone.now)
    descripcion_siniestro = models.TextField("Descripción del Siniestro")
    class EstadoSiniestro(models.TextChoices):
        ABIERTO = 'ABIERTO', 'Abierto'
        CERRADO = 'CERRADO', 'Cerrado con OS'
        IMPROCEDENTE = 'IMPROCEDENTE', 'Improcedente'
    estado = models.CharField("Estado del Siniestro", max_length=20, choices=EstadoSiniestro.choices, default=EstadoSiniestro.ABIERTO)
    history = HistoricalRecords()
    class Meta:
        verbose_name_plural = "Siniestros"
    def __str__(self): return f"Siniestro de {self.asegurado.nombre_completo}"

class OrdenDeServicio(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    numero_os = models.CharField("Número de OS", max_length=50, unique=True, editable=False, blank=True)
    punto_atencion = models.ForeignKey('gestion.PuntoAtencion', on_delete=models.PROTECT)
    servicios_prestados = models.ManyToManyField('gestion.BaremoProveedor')
    monto_referencial_os = models.DecimalField("Monto Referencial OS (USD)", max_digits=12, decimal_places=2, default=0.00)
    fecha_emision = models.DateTimeField("Fecha de Emisión", default=timezone.now, editable=False)
    fecha_vencimiento_activacion = models.DateField("Vencimiento para Activación", editable=False, null=True, blank=True)
    detalle_estudio = models.TextField("Detalle de la Consulta o Estudio", blank=True)

    class EstadoOS(models.TextChoices):
        PENDIENTE_AUTORIZACION = 'AUT', 'Pendiente de Autorización'
        NOTIFICADA = 'NOT', 'Notificada'
        ACTIVADA = 'ACT', 'Activada'
        SUSPENDIDA = 'SUS', 'Suspendida (Vencida)'
        PENDIENTE_PAGO = 'PEN', 'Pendiente por Pagar'
        PAGADA = 'PAG', 'Pagada'
        RECHAZADA = 'REC', 'Rechazada'

    estado_os = models.CharField("Estado de la OS", max_length=3, choices=EstadoOS.choices, default=EstadoOS.PENDIENTE_AUTORIZACION)

    es_exonerada = models.BooleanField("Exonerada (Presidencia)", default=False)
    autorizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="os_autorizadas")
    fecha_autorizacion = models.DateTimeField("Fecha de Autorización", null=True, blank=True)
    motivo_rechazo = models.TextField("Motivo de Rechazo", blank=True)
    
    # --- CORRECCIÓN: CAMPOS DE FACTURA AHORA PERMITEN NULOS ---
    numero_factura = models.CharField("Número de Factura", max_length=50, blank=True, null=True)
    numero_control_factura = models.CharField("Número de Control", max_length=50, blank=True, null=True)
    fecha_emision_factura = models.DateField("Fecha Emisión Factura", blank=True, null=True)
    fecha_recepcion_factura = models.DateField("Fecha Recepción Factura", blank=True, null=True)
    monto_factura_ves = models.DecimalField("Monto Factura (VES)", max_digits=12, decimal_places=2, null=True, blank=True)
    monto_factura_usd = models.DecimalField("Monto Factura (USD)", max_digits=12, decimal_places=2, null=True, blank=True)
    tasa_bcv = models.DecimalField("Tasa BCV", max_digits=10, decimal_places=4, null=True, blank=True)
    
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.numero_os:
            self.numero_os = f"SOL-{self.siniestro.id}"

        if self.estado_os == self.EstadoOS.NOTIFICADA and self.numero_os.startswith("SOL-"):
            self.numero_os = f"{timezone.now().year}-{timezone.now().month}-{self.siniestro.id}"
            self.fecha_vencimiento_activacion = self.fecha_emision.date() + timedelta(days=15)
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
    def __str__(self):
        return f"Solicitud de OS para {self.siniestro.asegurado.nombre_completo}"