# core/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    """
    Gestiona el inicio de sesión de todos los usuarios, asegurando que no haya
    conflictos de sesión.
    """
    # Si un usuario ya está logueado, lo deslogueamos primero para evitar conflictos.
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('login_redirect')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def login_redirect(request):
    """
    Redirige al usuario a la página apropiada según su rol.
    Esta es la única fuente de verdad para la redirección post-login.
    """
    user = request.user

    if not user.is_authenticated:
        return redirect(reverse('login'))

    # Prioridad 1: El rol de Operaciones va al portal de validación.
    if hasattr(user, 'rol') and user.rol and user.rol.nombre_rol == 'Operaciones':
        return redirect('validar_asegurabilidad')
    
    # Prioridad 2: Superusuarios y personal de staff van al panel de admin.
    if user.is_superuser or user.is_staff:
        return redirect('admin:index')

    # Si llega aquí, es un usuario autenticado sin rol ni permisos de staff.
    # Lo expulsamos por seguridad.
    messages.error(request, "No tiene permisos para acceder al sistema.")
    logout(request)
    return redirect('login')