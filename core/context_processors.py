# core/context_processors.py

from operaciones.models import OrdenDeServicio

def notifications_context(request):
    """
    Calcula el número de autorizaciones pendientes para mostrarlo en la cabecera.
    """
    pending_count = 0
    if request.user.is_authenticated:
        # Asumimos que los supervisores y superusuarios pueden ver la bandeja
        is_supervisor = request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol and 'supervisor' in request.user.rol.nombre_rol.lower())
        if is_supervisor:
            pending_count = OrdenDeServicio.objects.filter(
                estado_os=OrdenDeServicio.EstadoOS.PENDIENTE_AUTORIZACION
            ).count()
            
    return {
        'pending_authorizations_count': pending_count
    }