# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelo para los Roles
# Define los diferentes niveles de acceso que un usuario puede tener.
class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre_rol

# Modelo de Usuario Personalizado
# Extendemos el usuario base de Django para añadir campos propios, como el rol.
class Usuario(AbstractUser):
    nombre_completo = models.CharField(max_length=100, blank=True, null=True)
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Agregamos related_name para evitar conflictos con el modelo User base de Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username