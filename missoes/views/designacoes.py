"""Designações views - Assignment management and HTMX endpoints"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

from ..models import Designacao, Oficial, Missao


# ============================================================
# 🔄 HTMX - DESIGNAÇÕES
# ============================================================
@login_required
def htmx_designacoes_lista(request):
    """Retorna a lista de designações com paginação e filtros (para Admin)."""

    designacoes = Designacao.objects.select_related('missao', 'oficial').all()

    # ============================================================
    # FILTROS
    # ============================================================
    busca = request.GET.get('busca', '').strip()
    missao_id = request.GET.get('missao_id', '')
    funcao = request.GET.get('funcao', '')
    complexidade = request.GET.get('complexidade', '')

    if busca:
        designacoes = designacoes.filter(
            Q(oficial__nome__icontains=busca) |
            Q(oficial__nome_guerra__icontains=busca) |
            Q(missao__nome__icontains=busca)
        )

    if missao_id:
        designacoes = designacoes.filter(missao_id=missao_id)

    if funcao:
        designacoes = designacoes.filter(funcao_na_missao=funcao)

    if complexidade:
        designacoes = designacoes.filter(complexidade=complexidade)

    # ============================================================
    # ORDENAÇÃO
    # ============================================================
    ordenar = request.GET.get('ordenar', '-criado_em')
    direcao = request.GET.get('direcao', 'desc')

    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    designacoes = designacoes.order_by(ordenar)

    # ============================================================
    # PAGINAÇÃO
    # ============================================================
    por_pagina = int(request.GET.get('por_pagina', 25))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(designacoes, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Query string para paginação
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'filtros': {
            'busca': busca,
            'missao_id': missao_id,
            'funcao': funcao,
            'complexidade': complexidade,
            'por_pagina': str(por_pagina),
        },
        'ordenacao': {
            'campo': ordenar.lstrip('-'),
            'direcao': direcao,
        },
        'query_string': query_string,
        'funcao_choices': Designacao.FUNCAO_CHOICES,
        'complexidade_choices': Designacao.COMPLEXIDADE_CHOICES,
        'missoes_disponiveis': Missao.objects.filter(status__in=['PLANEJADA', 'EM_ANDAMENTO']).order_by('nome'),
        'oficiais_disponiveis': Oficial.objects.filter(ativo=True).order_by('posto', 'nome'),
        'user': request.user,
    }

    return render(request, 'htmx/designacoes_tabela.html', context)


@login_required
@require_POST
def htmx_designacao_criar(request):
    """Cria uma nova designação via HTMX."""

    if not request.user.pode_gerenciar_designacoes:
        return HttpResponse('Sem permissão', status=403)

    try:
        missao_id = request.POST.get('missao_id')
        oficial_id = request.POST.get('oficial_id')

        Designacao.objects.create(
            missao_id=missao_id,
            oficial_id=oficial_id,
            funcao_na_missao=request.POST.get('funcao_na_missao', 'MEMBRO'),
            complexidade=request.POST.get('complexidade', 'MEDIA'),
            observacoes=request.POST.get('observacoes', ''),
        )
        messages.success(request, 'Designação criada!')

    except Exception as e:
        messages.error(request, f'Erro ao criar designação: {str(e)}')

    return htmx_designacoes_lista(request)


@login_required
@require_POST
def htmx_designacao_editar(request, pk):
    """Edita uma designação via HTMX."""

    if not request.user.pode_gerenciar_designacoes:
        return HttpResponse('Sem permissão', status=403)

    designacao = get_object_or_404(Designacao, pk=pk)

    try:
        designacao.funcao_na_missao = request.POST.get('funcao_na_missao', designacao.funcao_na_missao)
        designacao.complexidade = request.POST.get('complexidade', designacao.complexidade)
        designacao.observacoes = request.POST.get('observacoes', designacao.observacoes)
        designacao.save()
        messages.success(request, 'Designação atualizada!')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')

    return htmx_designacoes_lista(request)


@login_required
def htmx_designacao_dados(request, pk):
    """Retorna dados de uma designação em JSON para edição."""

    designacao = get_object_or_404(Designacao, pk=pk)

    return JsonResponse({
        'id': designacao.id,
        'missao_id': designacao.missao_id,
        'oficial_id': designacao.oficial_id,
        'funcao_na_missao': designacao.funcao_na_missao,
        'complexidade': designacao.complexidade,
        'observacoes': designacao.observacoes,
    })


@login_required
@require_POST
def htmx_designacao_excluir(request, pk):
    """Exclui uma designação via HTMX."""

    if not request.user.pode_gerenciar_designacoes:
        return HttpResponse('Sem permissão', status=403)

    designacao = get_object_or_404(Designacao, pk=pk)

    try:
        designacao.delete()
        messages.success(request, 'Designação excluída!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')

    return htmx_designacoes_lista(request)