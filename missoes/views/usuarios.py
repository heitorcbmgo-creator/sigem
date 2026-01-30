"""
============================================================
🎯 SIGEM - Views de Usuários (HTMX)
Sistema de Gestão de Missões - CBMGO
============================================================
Funções para gerenciamento de usuários via HTMX:
- Lista, criação, edição, exclusão e reset de senha
============================================================
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

from ..models import Usuario, Oficial


# ============================================================
# 🔄 HTMX - USUÁRIOS
# ============================================================
@login_required
def htmx_usuarios_lista(request):
    """Retorna a lista de usuários com paginação e filtros."""

    if not request.user.pode_gerenciar_usuarios:
        return HttpResponse('Sem permissão', status=403)

    usuarios = Usuario.objects.select_related('oficial').all()

    # Filtros
    busca = request.GET.get('busca', '').strip()
    role = request.GET.get('role', '')
    ativo = request.GET.get('ativo', '')

    if busca:
        usuarios = usuarios.filter(
            Q(cpf__icontains=busca) |
            Q(oficial__nome__icontains=busca) |
            Q(oficial__nome_guerra__icontains=busca)
        )

    if role:
        usuarios = usuarios.filter(role=role)

    if ativo:
        usuarios = usuarios.filter(is_active=(ativo == 'true'))

    # Ordenação
    ordenar = request.GET.get('ordenar', 'cpf')
    direcao = request.GET.get('direcao', 'asc')

    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    usuarios = usuarios.order_by(ordenar)

    # Paginação
    por_pagina = int(request.GET.get('por_pagina', 25))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(usuarios, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Query string
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    # Oficiais sem usuário (para vincular)
    oficiais_disponiveis = Oficial.objects.filter(usuario__isnull=True).order_by('posto', 'nome')

    context = {
        'page_obj': page_obj,
        'filtros': {
            'busca': busca,
            'role': role,
            'ativo': ativo,
            'por_pagina': str(por_pagina),
        },
        'ordenacao': {
            'campo': ordenar.lstrip('-'),
            'direcao': direcao,
        },
        'query_string': query_string,
        'role_choices': Usuario.ROLE_CHOICES,
        'oficiais_disponiveis': oficiais_disponiveis,
        'user': request.user,
    }

    return render(request, 'htmx/usuarios_tabela.html', context)


@login_required
@require_POST
def htmx_usuario_criar(request):
    """Cria um novo usuário via HTMX."""

    if not request.user.is_admin:
        return HttpResponse('Sem permissão', status=403)

    try:
        cpf = request.POST.get('cpf', '').replace('.', '').replace('-', '')
        oficial_id = request.POST.get('oficial_id')

        Usuario.objects.create_user(
            cpf=cpf,
            password='123456',
            role=request.POST.get('role', 'oficial'),
            oficial_id=oficial_id if oficial_id else None,
        )
        messages.success(request, f'Usuário {cpf} criado com senha padrão 123456!')

    except Exception as e:
        messages.error(request, f'Erro ao criar usuário: {str(e)}')

    return htmx_usuarios_lista(request)


@login_required
@require_POST
def htmx_usuario_editar(request, pk):
    """Edita um usuário via HTMX."""

    if not request.user.is_admin:
        return HttpResponse('Sem permissão', status=403)

    usuario = get_object_or_404(Usuario, pk=pk)

    try:
        usuario.role = request.POST.get('role', usuario.role)
        usuario.is_active = request.POST.get('is_active') == 'on'
        usuario.save()
        messages.success(request, 'Usuário atualizado!')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')

    return htmx_usuarios_lista(request)


@login_required
@require_POST
def htmx_usuario_excluir(request, pk):
    """Exclui um usuário via HTMX."""

    if not request.user.is_admin:
        return HttpResponse('Sem permissão', status=403)

    usuario = get_object_or_404(Usuario, pk=pk)

    if usuario == request.user:
        messages.error(request, 'Você não pode excluir seu próprio usuário!')
        return htmx_usuarios_lista(request)

    try:
        usuario.delete()
        messages.success(request, 'Usuário excluído!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')

    return htmx_usuarios_lista(request)


@login_required
@require_POST
def htmx_usuario_reset_senha(request, pk):
    """Reseta a senha de um usuário para 123456."""

    if not request.user.is_admin:
        return HttpResponse('Sem permissão', status=403)

    usuario = get_object_or_404(Usuario, pk=pk)

    try:
        usuario.set_password('123456')
        usuario.save()
        messages.success(request, f'Senha do usuário {usuario.cpf} redefinida para 123456!')
    except Exception as e:
        messages.error(request, f'Erro ao resetar senha: {str(e)}')

    return htmx_usuarios_lista(request)