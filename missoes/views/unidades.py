"""
============================================================
SIGEM - Unidades Views
============================================================
HTMX views for managing military units (Unidades)
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

from ..models import Unidade


# ============================================================
# 🔄 HTMX - UNIDADES
# ============================================================
@login_required
def htmx_unidades_lista(request):
    """Retorna a lista de unidades com paginação e filtros."""

    unidades = Unidade.objects.all()

    # Filtros
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')

    if busca:
        unidades = unidades.filter(
            Q(nome__icontains=busca) |
            Q(sigla__icontains=busca)
        )

    if tipo:
        unidades = unidades.filter(tipo=tipo)

    # Ordenação
    ordenar = request.GET.get('ordenar', 'nome')
    direcao = request.GET.get('direcao', 'asc')

    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    unidades = unidades.order_by(ordenar)

    # Paginação
    por_pagina = int(request.GET.get('por_pagina', 25))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(unidades, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Query string
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'filtros': {
            'busca': busca,
            'tipo': tipo,
            'por_pagina': str(por_pagina),
        },
        'ordenacao': {
            'campo': ordenar.lstrip('-'),
            'direcao': direcao,
        },
        'query_string': query_string,
        'tipo_choices': Unidade.TIPO_CHOICES,
        'unidades_disponiveis': Unidade.objects.all().order_by('nome'),
        'user': request.user,
    }

    return render(request, 'htmx/unidades_tabela.html', context)


@login_required
@require_POST
def htmx_unidade_criar(request):
    """Cria uma nova unidade via HTMX."""

    if not request.user.pode_gerenciar_unidades:
        return HttpResponse('Sem permissão', status=403)

    try:
        comando_superior_id = request.POST.get('comando_superior_id')

        Unidade.objects.create(
            nome=request.POST.get('nome', ''),
            sigla=request.POST.get('sigla', ''),
            tipo=request.POST.get('tipo', ''),
            comando_superior_id=comando_superior_id if comando_superior_id else None,
        )
        messages.success(request, 'Unidade criada!')

    except Exception as e:
        messages.error(request, f'Erro ao criar unidade: {str(e)}')

    return htmx_unidades_lista(request)


@login_required
@require_POST
def htmx_unidade_editar(request, pk):
    """Edita uma unidade via HTMX."""

    if not request.user.pode_gerenciar_unidades:
        return HttpResponse('Sem permissão', status=403)

    unidade = get_object_or_404(Unidade, pk=pk)

    try:
        unidade.nome = request.POST.get('nome', unidade.nome)
        unidade.sigla = request.POST.get('sigla', unidade.sigla)
        unidade.tipo = request.POST.get('tipo', unidade.tipo)

        comando_superior_id = request.POST.get('comando_superior_id')
        unidade.comando_superior_id = comando_superior_id if comando_superior_id else None

        unidade.save()
        messages.success(request, 'Unidade atualizada!')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')

    return htmx_unidades_lista(request)


@login_required
@require_POST
def htmx_unidade_excluir(request, pk):
    """Exclui uma unidade via HTMX."""

    if not request.user.pode_gerenciar_unidades:
        return HttpResponse('Sem permissão', status=403)

    unidade = get_object_or_404(Unidade, pk=pk)
    nome = unidade.nome

    try:
        unidade.delete()
        messages.success(request, f'Unidade "{nome}" excluída!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')

    return htmx_unidades_lista(request)