# operaciones/views.py

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum, Q

from gestion.models import Asegurado, Contrato, DetallePlan, Proveedor, PuntoAtencion, BaremoProveedor, CoberturaCategoriaPlan
from .models import OrdenDeServicio, Siniestro


@login_required
def validar_asegurabilidad(request):
    contexto = {}
    query = request.GET.get('q', '')
    cliente_filtro = request.GET.get('cliente', '')
    aseguradora_filtro = request.GET.get('aseguradora', '')
    ente_filtro = request.GET.get('ente', '')

    if query:
        # Búsqueda parcial por nombre o cédula
        search_condition = Q(cedula__icontains=query) | Q(nombre_completo__icontains=query)
        asegurados_encontrados = Asegurado.objects.filter(search_condition).select_related(
            'contrato', 'contrato__cliente', 'contrato__plan'
        )

        # Aplicar filtros si se especifican
        if cliente_filtro:
            asegurados_encontrados = asegurados_encontrados.filter(contrato__cliente__razon_social=cliente_filtro)
        if aseguradora_filtro:
            asegurados_encontrados = asegurados_encontrados.filter(contrato__aseguradora=aseguradora_filtro)
        if ente_filtro:
            asegurados_encontrados = asegurados_encontrados.filter(contrato__ente=ente_filtro)

        if asegurados_encontrados.exists():
            resultados_validacion = []
            hoy = timezone.now().date()
            for asegurado in asegurados_encontrados:
                es_elegible = True
                mensajes = []
                contrato_actual = asegurado.contrato
                if not (contrato_actual.activo and contrato_actual.fecha_inicio_vigencia <= hoy and contrato_actual.fecha_fin_vigencia >= hoy):
                    es_elegible = False
                    mensajes.append(f"El Contrato N° {contrato_actual.numero_contrato} no está activo o se encuentra vencido.")
                if asegurado.fecha_baja and asegurado.fecha_baja <= hoy:
                    es_elegible = False
                    mensajes.append(f"El asegurado fue dado de baja en fecha {asegurado.fecha_baja.strftime('%d/%m/%Y')}.")
                if asegurado.estado_individual != Asegurado.EstadoAsegurado.ACTIVO:
                    es_elegible = False
                    mensajes.append(f"El estado del asegurado es: {asegurado.get_estado_individual_display()}.")
                
                resultados_validacion.append({
                    'asegurado': asegurado,
                    'es_elegible': es_elegible,
                    'mensajes_validacion': mensajes,
                })
            contexto['resultados'] = resultados_validacion
        else:
            contexto['error'] = f"No se encontró ningún asegurado que coincida con '{query}'."

        # Solo pasamos los filtros si hay una búsqueda
        contexto['show_filters'] = True
        contexto['clientes'] = Contrato.objects.order_by('cliente__razon_social').values_list('cliente__razon_social', flat=True).distinct()
        contexto['aseguradoras'] = Contrato.objects.order_by('aseguradora').values_list('aseguradora', flat=True).distinct()
        contexto['entes'] = Contrato.objects.order_by('ente').values_list('ente', flat=True).distinct()

    contexto.update({
        'query': query,
        'cliente_filtro': cliente_filtro,
        'aseguradora_filtro': aseguradora_filtro,
        'ente_filtro': ente_filtro,
    })

    return render(request, 'operaciones/validacion.html', contexto)

@login_required
def consultar_servicios(request, asegurado_id):
    asegurado = get_object_or_404(Asegurado.objects.select_related('contrato'), pk=asegurado_id)
    contrato_actual = asegurado.contrato
    
    ordenes_de_servicio = OrdenDeServicio.objects.filter(
        siniestro__asegurado=asegurado,
        fecha_emision__date__range=(contrato_actual.fecha_inicio_vigencia, contrato_actual.fecha_fin_vigencia)
    ).order_by('-fecha_emision')

    # --- Cálculo de Coberturas y Consumo por Categoría ---
    coberturas = []
    coberturas_plan = CoberturaCategoriaPlan.objects.filter(plan=contrato_actual.plan).select_related('categoria')
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    for cobertura in coberturas_plan:
        # Consumo anual por categoría
        consumo_anual = ordenes_de_servicio.filter(
            servicios_prestados__sub_servicio__categoria=cobertura.categoria
        ).count()
        
        disponible_anual = max(0, cobertura.cantidad_maxima - consumo_anual)
        disponible_final = disponible_anual

        # Consumo mensual si aplica
        consumo_mensual = None
        if cobertura.limite_mensual > 0:
            consumo_mensual = ordenes_de_servicio.filter(
                servicios_prestados__sub_servicio__categoria=cobertura.categoria,
                fecha_emision__date__gte=inicio_mes
            ).count()
            disponible_mensual = max(0, cobertura.limite_mensual - consumo_mensual)
            # El disponible es el menor de los dos límites
            disponible_final = min(disponible_anual, disponible_mensual)

        coberturas.append({
            'descripcion': cobertura.categoria.nombre,
            'cantidad_maxima': cobertura.cantidad_maxima,
            'limite_mensual': cobertura.limite_mensual,
            'consumido_anual': consumo_anual,
            'consumido_mensual': consumo_mensual,
            'disponible': disponible_final
        })
    
    # Resumen de servicios solicitados
    resumen_servicios = ordenes_de_servicio.values(
        'servicios_prestados__sub_servicio__descripcion'
    ).annotate(
        cantidad=Count('servicios_prestados__sub_servicio')
    ).order_by('-cantidad')

    contexto = {
        'asegurado': asegurado,
        'contrato': contrato_actual,
        'ordenes': ordenes_de_servicio,
        'coberturas': coberturas,
        'resumen_servicios': resumen_servicios,
    }
    
    return render(request, 'operaciones/historial_servicios.html', contexto)
    pass

@login_required
def crear_orden_de_servicio(request, asegurado_id):
    asegurado = get_object_or_404(Asegurado, pk=asegurado_id)
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion_siniestro')
        punto_atencion_id = request.POST.get('punto_atencion')
        
        if not (descripcion and punto_atencion_id):
            return redirect(request.path_info)

        siniestro = Siniestro.objects.create(
            asegurado=asegurado,
            descripcion_siniestro=descripcion
        )

        punto_atencion = get_object_or_404(PuntoAtencion, pk=punto_atencion_id)
        orden_servicio = OrdenDeServicio.objects.create(
            siniestro=siniestro,
            punto_atencion=punto_atencion
        )
        
        return redirect('seleccionar_servicios', os_id=orden_servicio.siniestro_id)

    proveedores = Proveedor.objects.filter(activo=True).order_by('razon_social')
    contexto = {
        'asegurado': asegurado,
        'proveedores': proveedores,
    }
    return render(request, 'operaciones/crear_os.html', contexto)
    pass

@login_required
def seleccionar_servicios(request, os_id):
    orden_servicio = get_object_or_404(OrdenDeServicio, pk=os_id)
    proveedor = orden_servicio.punto_atencion.proveedor
    
    plan_asegurado = orden_servicio.siniestro.asegurado.contrato.plan
    subservicios_incluidos = DetallePlan.objects.filter(plan=plan_asegurado).values_list('sub_servicio_id', flat=True)
    
    servicios_disponibles = BaremoProveedor.objects.filter(
        proveedor=proveedor,
        activo=True,
        sub_servicio_id__in=subservicios_incluidos
    )

    if request.method == 'POST':
        servicios_seleccionados_ids = request.POST.getlist('servicios')
        
        orden_servicio.servicios_prestados.set(servicios_seleccionados_ids)
        
        total = orden_servicio.servicios_prestados.aggregate(Sum('precio'))['precio__sum'] or 0.00
        orden_servicio.monto_referencial_os = total
        orden_servicio.save()
        
        # Redirigimos a una página de confirmación de "solicitud enviada"
        return redirect('validar_asegurabilidad') # Por ahora, redirigimos al validador

    contexto = {
        'orden_servicio': orden_servicio,
        'servicios_disponibles': servicios_disponibles,
    }
    return render(request, 'operaciones/seleccionar_servicios.html', contexto)
    pass

@login_required
def get_puntos_atencion(request):
    proveedor_id = request.GET.get('proveedor_id')
    puntos = PuntoAtencion.objects.filter(proveedor_id=proveedor_id, activo=True).order_by('nombre_sede')
    return JsonResponse(list(puntos.values('id', 'nombre_sede')), safe=False)
    pass

@login_required
def cancelar_creacion_os(request, os_id):
    """
    Elimina un Siniestro y su OS asociada si el operador cancela el proceso
    a mitad de camino, para no dejar registros huérfanos.
    """
    orden_servicio = get_object_or_404(OrdenDeServicio, pk=os_id)
    asegurado = orden_servicio.siniestro.asegurado
    
    # Eliminamos el siniestro, y la OS se borrará en cascada.
    orden_servicio.siniestro.delete()
    
    # Redirigimos de vuelta al formulario inicial para ese asegurado.
    return redirect('crear_orden_de_servicio', asegurado_id=asegurado.id)