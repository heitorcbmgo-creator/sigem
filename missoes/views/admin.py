"""
============================================================
SIGEM - Admin Panel View
============================================================
Administrative panel with CRUD for all entities
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..decorators import acesso_admin_painel


@login_required
@acesso_admin_painel
def admin_painel(request):
    """Painel administrativo com CRUD de todas as entidades."""

    user = request.user

    # Determinar aba inicial baseado nas permissões
    if user.is_admin:
        aba_padrao = 'oficiais'
    elif user.is_corregedor or user.is_bm3:
        aba_padrao = 'missoes'
    else:
        aba_padrao = 'missoes'

    context = {
        'aba_ativa': request.GET.get('aba', aba_padrao),
    }

    return render(request, 'pages/admin_painel.html', context)