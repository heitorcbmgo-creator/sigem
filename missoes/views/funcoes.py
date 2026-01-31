"""Funções views - Function management and HTMX endpoints"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from ..models import Funcao, Missao


# ============================================================
# 🔄 HTMX - FUNÇÕES
# ============================================================
@login_required
def htmx_funcoes_tabela(request):
    """Retorna tabela de funções com paginação e filtros (para Admin)."""

    # Verificar permissão: apenas Administrador e Comando-Geral
    if not (request.user.is_superuser or request.user.unidade.tipo == 'COMANDO_GERAL'):
        return HttpResponse('<p class="text-danger">Acesso negado.</p>', status=403)

    funcoes = Funcao.objects.select_related('missao').all()

    # ============================================================
    # 🔍 FILTROS
    # ============================================================
    busca = request.GET.get('busca', '').strip()
    missao_id = request.GET.get('missao', '').strip()
    complexidade = request.GET.get('complexidade', '').strip()

    if busca:
        funcoes = funcoes.filter(
            Q(funcao__icontains=busca) |
            Q(missao__nome__icontains=busca)
        )

    if missao_id:
        funcoes = funcoes.filter(missao_id=missao_id)

    # Filtro por complexidade (calculado em Python, então filtramos depois)
    funcoes_list = list(funcoes)
    if complexidade:
        funcoes_list = [f for f in funcoes_list if f.complexidade == complexidade]

    # ============================================================
    # 📄 PAGINAÇÃO
    # ============================================================
    por_pagina = int(request.GET.get('por_pagina', 25))
    paginator = Paginator(funcoes_list, por_pagina)
    pagina = request.GET.get('pagina', 1)
    page_obj = paginator.get_page(pagina)

    # Query string para paginação
    query_dict = request.GET.copy()
    if 'pagina' in query_dict:
        query_dict.pop('pagina')
    query_string = query_dict.urlencode()

    # ============================================================
    # 📊 CONTEXTO
    # ============================================================
    context = {
        'page_obj': page_obj,
        'query_string': query_string,
        'filtros': {
            'busca': busca,
            'missao': missao_id,
            'complexidade': complexidade,
            'por_pagina': str(por_pagina),
        },
        'missoes_disponiveis': Missao.objects.filter(status='EM_ANDAMENTO').order_by('nome'),
        'nivel_tde_nqt_grs_choices': Funcao.NIVEL_TDE_NQT_GRS_CHOICES,
        'nivel_dec_choices': Funcao.NIVEL_DEC_CHOICES,
        'complexidade_choices': Funcao.COMPLEXIDADE_CHOICES,
    }

    return render(request, 'htmx/funcoes_tabela.html', context)


@login_required
@require_POST
def htmx_funcao_criar(request):
    """Cria uma nova função."""

    # Verificar permissão
    if not (request.user.is_superuser or request.user.unidade.tipo == 'COMANDO_GERAL'):
        return HttpResponse('<p class="text-danger">Acesso negado.</p>', status=403)

    try:
        missao_id = request.POST.get('missao')
        funcao_nome = request.POST.get('funcao', '').strip()
        tde = int(request.POST.get('tde', 2))
        nqt = int(request.POST.get('nqt', 2))
        grs = int(request.POST.get('grs', 2))
        dec = int(request.POST.get('dec', 2))

        # Validações
        if not missao_id or not funcao_nome:
            return HttpResponse('<p class="text-danger">Missão e Função são obrigatórios.</p>', status=400)

        missao = get_object_or_404(Missao, pk=missao_id)

        # Verificar se já existe função com esse nome na missão
        if Funcao.objects.filter(missao=missao, funcao=funcao_nome).exists():
            return HttpResponse(
                f'<p class="text-danger">Já existe a função "{funcao_nome}" nesta missão.</p>',
                status=400
            )

        # Criar função
        Funcao.objects.create(
            missao=missao,
            funcao=funcao_nome,
            tde=tde,
            nqt=nqt,
            grs=grs,
            dec=dec
        )

        # Retornar tabela atualizada
        return htmx_funcoes_tabela(request)

    except Exception as e:
        return HttpResponse(f'<p class="text-danger">Erro: {str(e)}</p>', status=400)


@login_required
@require_POST
def htmx_funcao_editar(request, pk):
    """Edita uma função existente."""

    # Verificar permissão
    if not (request.user.is_superuser or request.user.unidade.tipo == 'COMANDO_GERAL'):
        return HttpResponse('<p class="text-danger">Acesso negado.</p>', status=403)

    funcao = get_object_or_404(Funcao, pk=pk)

    try:
        missao_id = request.POST.get('missao')
        funcao_nome = request.POST.get('funcao', '').strip()
        tde = int(request.POST.get('tde', 2))
        nqt = int(request.POST.get('nqt', 2))
        grs = int(request.POST.get('grs', 2))
        dec = int(request.POST.get('dec', 2))

        if not missao_id or not funcao_nome:
            return HttpResponse('<p class="text-danger">Missão e Função são obrigatórios.</p>', status=400)

        missao = get_object_or_404(Missao, pk=missao_id)

        # Verificar duplicata (excluindo a própria função)
        if Funcao.objects.filter(missao=missao, funcao=funcao_nome).exclude(pk=pk).exists():
            return HttpResponse(
                f'<p class="text-danger">Já existe a função "{funcao_nome}" nesta missão.</p>',
                status=400
            )

        # Atualizar
        funcao.missao = missao
        funcao.funcao = funcao_nome
        funcao.tde = tde
        funcao.nqt = nqt
        funcao.grs = grs
        funcao.dec = dec
        funcao.save()

        return htmx_funcoes_tabela(request)

    except Exception as e:
        return HttpResponse(f'<p class="text-danger">Erro: {str(e)}</p>', status=400)


@login_required
@require_POST
def htmx_funcao_excluir(request, pk):
    """Exclui uma função."""

    # Verificar permissão
    if not (request.user.is_superuser or request.user.unidade.tipo == 'COMANDO_GERAL'):
        return HttpResponse('<p class="text-danger">Acesso negado.</p>', status=403)

    funcao = get_object_or_404(Funcao, pk=pk)

    try:
        funcao.delete()
        return htmx_funcoes_tabela(request)
    except Exception as e:
        return HttpResponse(f'<p class="text-danger">Erro ao excluir: {str(e)}</p>', status=400)


@login_required
def htmx_funcao_dados(request, pk):
    """Retorna dados de uma função em JSON para edição."""

    # Verificar permissão
    if not (request.user.is_superuser or request.user.unidade.tipo == 'COMANDO_GERAL'):
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    funcao = get_object_or_404(Funcao, pk=pk)

    return JsonResponse({
        'id': funcao.id,
        'missao': funcao.missao_id,
        'funcao': funcao.funcao,
        'tde': funcao.tde,
        'nqt': funcao.nqt,
        'grs': funcao.grs,
        'dec': funcao.dec,
        'complexidade': funcao.complexidade,
        'soma_criterios': funcao.soma_criterios,
    })


@login_required
def htmx_buscar_funcoes_por_missao(request):
    """Retorna funções de uma missão específica em JSON para popular dropdown."""

    missao_id = request.GET.get('missao_id')

    if not missao_id:
        return JsonResponse({'funcoes': []})

    funcoes = Funcao.objects.filter(missao_id=missao_id).order_by('funcao')

    funcoes_list = [{
        'id': f.id,
        'funcao': f.funcao,
        'complexidade': f.complexidade,
        'complexidade_display': f.get_complexidade_display(),
        'soma_criterios': f.soma_criterios,
    } for f in funcoes]

    return JsonResponse({'funcoes': funcoes_list})