# core/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    """
    Gestiona el inicio de sesión de todos los usuarios.
    """
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
    """
    user = request.user

    if not user.is_authenticated:
        return redirect(reverse('login'))

    if user.is_superuser:
        return redirect('admin:index')
    
    if hasattr(user, 'rol') and user.rol:
        rol_nombre = user.rol.nombre_rol.lower()
        
        if rol_nombre == 'operaciones' or 'supervisor' in rol_nombre:
            return redirect('validar_asegurabilidad')
        
        # --- LÓGICA ACTUALIZADA ---
        # Si el rol es Convenios y es staff, va al panel de admin.
        if 'convenios' in rol_nombre and user.is_staff:
            return redirect('admin:index')
    
    if user.is_staff:
        return redirect('admin:index')

    messages.error(request, "No tiene permisos para acceder al sistema.")
    logout(request)
    return redirect('login')