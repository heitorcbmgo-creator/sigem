"""
============================================================
🔐 SIGEM - Decorators de Controle de Acesso
============================================================
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def acesso_dashboard(view_func):
    """Permite acesso apenas a: admin, comando_geral"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_ver_dashboard:
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('missoes_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def acesso_comparar(view_func):
    """Permite acesso apenas a: admin, corregedor, bm3, comando_geral, comandante"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_ver_comparar:
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('painel_oficial')
        return view_func(request, *args, **kwargs)
    return wrapper


def acesso_admin_painel(view_func):
    """Permite acesso apenas a: admin, corregedor, bm3"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_ver_admin:
            messages.error(request, 'Acesso restrito a administradores.')
            return redirect('missoes_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_oficiais(view_func):
    """Permite CRUD de oficiais apenas para: admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_oficiais:
            messages.error(request, 'Você não tem permissão para gerenciar oficiais.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_missoes(view_func):
    """Permite CRUD de missões para: admin, corregedor, bm3"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_missoes:
            messages.error(request, 'Você não tem permissão para gerenciar missões.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_designacoes(view_func):
    """Permite CRUD de designações para: admin, corregedor, bm3"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_designacoes:
            messages.error(request, 'Você não tem permissão para gerenciar designações.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_unidades(view_func):
    """Permite CRUD de unidades apenas para: admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_unidades:
            messages.error(request, 'Você não tem permissão para gerenciar unidades.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_usuarios(view_func):
    """Permite CRUD de usuários apenas para: admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_usuarios:
            messages.error(request, 'Você não tem permissão para gerenciar usuários.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper


def permissao_gerenciar_solicitacoes(view_func):
    """Permite gerenciar solicitações para: admin, bm3"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.pode_gerenciar_solicitacoes:
            messages.error(request, 'Você não tem permissão para gerenciar solicitações.')
            return HttpResponseForbidden('Sem permissão')
        return view_func(request, *args, **kwargs)
    return wrapper