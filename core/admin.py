# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group # <-- Se importa el modelo Group
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.core.mail import send_mail

from .models import Usuario, Rol

# Definimos una clase de administración personalizada para nuestro modelo de Usuario
class UsuarioAdmin(UserAdmin):
    # Copiamos los fieldsets del UserAdmin original y añadimos nuestros campos
    fieldsets = UserAdmin.fieldsets + (
        ('Campos Personalizados', {'fields': ('nombre_completo', 'rol')}),
    )
    list_display = ('username', 'email', 'nombre_completo', 'rol', 'is_staff')
    
    # Añadimos nuestra nueva acción al listado
    actions = ['send_password_setup_email']

    @admin.action(description='Enviar correo para establecer contraseña')
    def send_password_setup_email(self, request, queryset):
        for user in queryset:
            # Generar token y UID seguro
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construir la URL para establecer la contraseña
            # Usamos la vista 'password_reset_confirm' que ya viene en Django
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Preparar y enviar el correo
            subject = "Configure su contraseña para Aegis Claims"
            message = (
                f"Hola {user.nombre_completo or user.username},\n\n"
                f"Se ha creado una cuenta para usted en el sistema Aegis Claims. "
                f"Por favor, haga clic en el siguiente enlace para establecer su contraseña:\n\n"
                f"{reset_url}\n\n"
                f"Si no esperaba este correo, por favor ignórelo.\n\n"
                f"El equipo de Aegis Claims"
            )
            
            send_mail(subject, message, 'no-reply@aegis-claims.com', [user.email])
            
        self.message_user(request, f"Se ha enviado el correo a {queryset.count()} usuario(s).")


# Registramos el modelo Rol de forma simple
admin.site.register(Rol)
# Registramos nuestro modelo Usuario con la clase de admin personalizada
admin.site.register(Usuario, UsuarioAdmin)

# Des-registramos el modelo Group para evitar el error 404
admin.site.unregister(Group)