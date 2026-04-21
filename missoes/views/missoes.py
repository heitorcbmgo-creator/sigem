"""Missões views - Mission management and HTMX endpoints"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from ..models import Missao, Designacao, Oficial, TemplateEstruturaMissao


# ============================================================
# 🔄 HTMX - MISSÕES
# ============================================================
@login_required
def htmx_missoes_lista(request):
    """Retorna a lista de missões filtrada (cards para página de Missões)."""

    missoes = Missao.objects.all().order_by('-data_inicio')

    # Filtros
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    local = request.GET.get('local', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    if tipo:
        missoes = missoes.filter(tipo=tipo)
    if status:
        missoes = missoes.filter(status=status)
    if local:
        missoes = missoes.filter(local__icontains=local)
    if data_inicio:
        missoes = missoes.filter(data_inicio__gte=data_inicio)
    if data_fim:
        missoes = missoes.filter(data_fim__lte=data_fim)

    return render(request, 'htmx/missoes_lista.html', {'missoes': missoes})


@login_required
def htmx_missoes_tabela(request):
    """Retorna tabela de missões com paginação e filtros (para Admin)."""

    missoes = Missao.objects.all()

    # ============================================================
    # FILTROS
    # ============================================================
    busca = request.GET.get('busca', '').strip()
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    if busca:
        missoes = missoes.filter(
            Q(nome__icontains=busca) |
            Q(local__icontains=busca) |
            Q(documento_referencia__icontains=busca)
        )

    if tipo:
        missoes = missoes.filter(tipo=tipo)
    if status:
        missoes = missoes.filter(status=status)
    if data_inicio:
        missoes = missoes.filter(data_inicio__gte=data_inicio)
    if data_fim:
        missoes = missoes.filter(data_fim__lte=data_fim)

    # ============================================================
    # ORDENAÇÃO
    # ============================================================
    ordenar = request.GET.get('ordenar', '-data_inicio')
    direcao = request.GET.get('direcao', 'desc')

    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    missoes = missoes.order_by(ordenar)

    # ============================================================
    # PAGINAÇÃO
    # ============================================================
    por_pagina = int(request.GET.get('por_pagina', 25))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(missoes, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Query string para paginação
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    # Buscar templates ativos para o formulário
    templates_missao = TemplateEstruturaMissao.objects.filter(ativo=True).prefetch_related('funcoes_template')

    context = {
        'page_obj': page_obj,
        'filtros': {
            'busca': busca,
            'tipo': tipo,
            'status': status,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'por_pagina': str(por_pagina),
        },
        'ordenacao': {
            'campo': ordenar.lstrip('-'),
            'direcao': direcao,
        },
        'query_string': query_string,
        'tipo_choices': Missao.TIPO_CHOICES,
        'status_choices': Missao.STATUS_CHOICES,
        'finalizacao_choices': Missao.FINALIZACAO_CHOICES,
        'local_choices': Missao.LOCAL_CHOICES,
        'templates_missao': templates_missao,
        'user': request.user,
    }

    return render(request, 'htmx/missoes_tabela.html', context)


@login_required
def htmx_missao_organograma(request, pk):
    """Retorna o organograma de uma missão."""

    missao = get_object_or_404(Missao, pk=pk)

    designacoes = missao.designacoes.select_related('oficial', 'funcao').all()

    # Funções de liderança (nível superior - destaque em dourado)
    funcoes_lideranca = ['comandante', 'presidente', 'coordenador', 'encarregado']

    # Separar por hierarquia usando case-insensitive matching
    superiores = designacoes.filter(
        Q(funcao__funcao__iexact='comandante') |
        Q(funcao__funcao__iexact='presidente') |
        Q(funcao__funcao__iexact='coordenador') |
        Q(funcao__funcao__iexact='encarregado')
    )
    subordinados = designacoes.exclude(
        Q(funcao__funcao__iexact='comandante') |
        Q(funcao__funcao__iexact='presidente') |
        Q(funcao__funcao__iexact='coordenador') |
        Q(funcao__funcao__iexact='encarregado')
    )

    context = {
        'missao': missao,
        'superiores': superiores,
        'subordinados': subordinados,
    }

    return render(request, 'htmx/missao_organograma.html', context)


@login_required
@require_POST
def htmx_missao_criar(request):
    """Cria uma nova missão via HTMX. Suporta criação via template."""

    if not request.user.pode_gerenciar_missoes:
        return HttpResponse('Sem permissão', status=403)

    try:
        template_id = request.POST.get('template_id', '').strip()
        template = None

        if template_id:
            # Criação via template
            template = get_object_or_404(TemplateEstruturaMissao, pk=template_id)
            numero = request.POST.get('numero', '').strip()

            nome_custom = (
                request.POST.get('nome_missao_custom', '').strip()
                or request.POST.get('nome', '').strip()
            )
            missao = Missao.objects.create(
                template=template,
                numero=numero,
                tipo=template.tipo,
                nome=nome_custom or template.nome,
                descricao=request.POST.get('descricao', ''),
                local=request.POST.get('local', ''),
                data_inicio=request.POST.get('data_inicio'),
                data_fim=request.POST.get('data_fim'),
                finalizacao=request.POST.get('finalizacao', ''),
                documento_referencia=request.POST.get('documento_referencia', ''),
            )

            # Criar funções a partir do template
            funcoes_criadas = missao.criar_funcoes_do_template()
            messages.success(
                request,
                f'Missão criada com sucesso! {len(funcoes_criadas)} função(ões) criada(s) automaticamente.'
            )
        else:
            # Criação normal (sem template)
            Missao.objects.create(
                tipo=request.POST.get('tipo', ''),
                nome=request.POST.get('nome', ''),
                ano=request.POST.get('ano', 2026),
                descricao=request.POST.get('descricao', ''),
                local=request.POST.get('local', ''),
                data_inicio=request.POST.get('data_inicio'),
                data_fim=request.POST.get('data_fim'),
                finalizacao=request.POST.get('finalizacao', ''),
                documento_referencia=request.POST.get('documento_referencia', ''),
            )
            messages.success(request, 'Missão criada com sucesso!')

    except Exception as e:
        messages.error(request, f'Erro ao criar missão: {str(e)}')

    # Retorna a tabela (Admin-Painel) ou lista (página Missões) conforme o referer
    referer = request.META.get('HTTP_REFERER', '')
    if 'admin' in referer or 'painel' in referer:
        return htmx_missoes_tabela(request)
    return htmx_missoes_lista(request)


@login_required
@require_POST
def htmx_missao_editar(request, pk):
    """Edita uma missão via HTMX."""

    if not request.user.pode_gerenciar_missoes:
        return HttpResponse('Sem permissão', status=403)

    missao = get_object_or_404(Missao, pk=pk)

    try:
        missao.tipo = request.POST.get('tipo', missao.tipo)
        missao.nome = request.POST.get('nome', missao.nome)
        missao.ano = request.POST.get('ano', missao.ano)
        missao.descricao = request.POST.get('descricao', missao.descricao)
        missao.local = request.POST.get('local', missao.local)
        missao.finalizacao = request.POST.get('finalizacao', missao.finalizacao)
        missao.documento_referencia = request.POST.get('documento_referencia', missao.documento_referencia)

        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        if data_inicio:
            missao.data_inicio = data_inicio
        if data_fim:
            missao.data_fim = data_fim

        # O status é calculado automaticamente no model.save()
        missao.save()
        messages.success(request, 'Missão atualizada!')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')

    # Retorna a tabela (Admin-Painel) ou lista (página Missões) conforme o referer
    referer = request.META.get('HTTP_REFERER', '')
    if 'admin' in referer or 'painel' in referer:
        return htmx_missoes_tabela(request)
    return htmx_missoes_lista(request)


@login_required
def htmx_missao_dados(request, pk):
    """Retorna dados de uma missão em JSON para edição."""

    missao = get_object_or_404(Missao, pk=pk)

    return JsonResponse({
        'id': missao.id,
        'nome': missao.nome,
        'ano': missao.ano,
        'tipo': missao.tipo,
        'status': missao.status,
        'finalizacao': missao.finalizacao,
        'descricao': missao.descricao,
        'local': missao.local,
        'data_inicio': missao.data_inicio.strftime('%Y-%m-%d') if missao.data_inicio else '',
        'data_fim': missao.data_fim.strftime('%Y-%m-%d') if missao.data_fim else '',
        'documento_referencia': missao.documento_referencia,
    })


@login_required
@require_POST
def htmx_missao_excluir(request, pk):
    """Exclui uma missão via HTMX."""

    if not request.user.pode_gerenciar_missoes:
        return HttpResponse('Sem permissão', status=403)

    missao = get_object_or_404(Missao, pk=pk)
    nome = missao.nome

    try:
        missao.delete()
        messages.success(request, f'Missão "{nome}" excluída!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')

    # Retorna a tabela (Admin-Painel) ou lista (página Missões) conforme o referer
    referer = request.META.get('HTTP_REFERER', '')
    if 'admin' in referer or 'painel' in referer:
        return htmx_missoes_tabela(request)
    return htmx_missoes_lista(request)