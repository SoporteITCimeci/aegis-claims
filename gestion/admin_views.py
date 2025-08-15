# gestion/admin_views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from .models import PuntoAtencion
import unicodedata

def normalize_text(text):
    if not text:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()

@staff_member_required
def mapa_proveedores_view(request):
    """Renderiza la página del mapa dentro del entorno del panel de administración."""
    context = {
        'title': 'Mapa de Proveedores',
        'site_header': 'Administración de CIMECI Médicas',
        'site_title': 'Portal de CIMECI Médicas',
        'has_permission': True,
    }
    return render(request, 'admin/mapa_proveedores.html', context)

@staff_member_required
def proveedores_activos_api(request):
    """API que devuelve los estados con proveedores activos, normalizados."""
    puntos_activos = PuntoAtencion.objects.filter(activo=True, proveedor__activo=True)
    estados = list(set(normalize_text(e) for e in puntos_activos.values_list('estado', flat=True) if e))
    data = {'estados': estados}
    return JsonResponse(data)