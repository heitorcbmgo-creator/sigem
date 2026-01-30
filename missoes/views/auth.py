"""
============================================================
SIGEM - Authentication Views
============================================================
Login, Logout, and Role-based Redirects
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone


def login_view(request):
    """Página de login."""
    if request.user.is_authenticated:
        return redirect('redirecionar_por_perfil')

    if request.method == 'POST':
        cpf = request.POST.get('cpf', '').replace('.', '').replace('-', '')
        senha = request.POST.get('senha', '')

        user = authenticate(request, cpf=cpf, password=senha)

        if user is not None:
            login(request, user)
            user.ultimo_acesso = timezone.now()
            user.save(update_fields=['ultimo_acesso'])
            messages.success(request, f'Bem-vindo, {user}!')
            return redirect('redirecionar_por_perfil')
        else:
            messages.error(request, 'CPF ou senha incorretos.')

    return render(request, 'auth/login.html')


@login_required
def redirecionar_por_perfil(request):
    """Redireciona o usuário para a página inicial conforme seu perfil."""
    user = request.user

    # Perfis com acesso ao dashboard
    if user.role in ['admin', 'comando_geral', 'comandante', 'bm3', 'corregedor']:
        return redirect('dashboard')
    else:  # oficial
        return redirect('painel_oficial')


@login_required
def logout_view(request):
    """Logout do usuário."""
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')