"""
Legacy Solicitações System - Uses SolicitacaoMissao and SolicitacaoDesignacao models - Maintained for backward compatibility
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import SolicitacaoMissao, SolicitacaoDesignacao, Missao, Designacao, Oficial


@login_required
@require_POST
def htmx_solicitacao_missao_criar(request):
    """Cria uma solicitação de inclusão de missão."""

    if not request.user.oficial:
        messages.error(request, 'Usuário não vinculado a um oficial.')
        return HttpResponse('<div class="alert alert-danger">Usuário não vinculado a um oficial.</div>')

    try:
        # Processar datas
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim') or None
        status_missao = request.POST.get('status_missao', 'EM_ANDAMENTO')

        # Se status for CONCLUIDA, data_fim é obrigatória
        if status_missao == 'CONCLUIDA' and not data_fim:
            return HttpResponse('<div class="alert alert-danger">Data de término é obrigatória para missões concluídas.</div>')

        SolicitacaoMissao.objects.create(
            solicitante=request.user.oficial,
            nome_missao=request.POST.get('nome_missao', ''),
            tipo_missao=request.POST.get('tipo_missao', ''),
            status_missao=status_missao,
            local=request.POST.get('local', ''),
            data_inicio=data_inicio,
            data_fim=data_fim,
            documento_sei=request.POST.get('documento_sei', ''),
        )

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação de missão enviada com sucesso! Aguarde avaliação.</div><script>lucide.createIcons();</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Erro ao criar solicitação: {str(e)}</div>')


@login_required
@require_POST
def htmx_solicitacao_designacao_criar(request):
    """Cria uma solicitação de inclusão de designação."""

    if not request.user.oficial:
        messages.error(request, 'Usuário não vinculado a um oficial.')
        return HttpResponse('<div class="alert alert-danger">Usuário não vinculado a um oficial.</div>')

    try:
        missao_id = request.POST.get('missao_id')
        if not missao_id:
            return HttpResponse('<div class="alert alert-danger">Selecione uma missão.</div>')

        missao = Missao.objects.get(id=missao_id)

        # Verificar se já existe designação para este oficial nesta missão
        if Designacao.objects.filter(oficial=request.user.oficial, missao=missao).exists():
            return HttpResponse('<div class="alert alert-warning">Você já está designado para esta missão.</div>')

        # Verificar se já existe solicitação pendente
        if SolicitacaoDesignacao.objects.filter(
            solicitante=request.user.oficial,
            missao=missao,
            status='PENDENTE'
        ).exists():
            return HttpResponse('<div class="alert alert-warning">Já existe uma solicitação pendente para esta missão.</div>')

        SolicitacaoDesignacao.objects.create(
            solicitante=request.user.oficial,
            missao=missao,
            funcao_na_missao=request.POST.get('funcao_na_missao', ''),
            documento_sei=request.POST.get('documento_sei', ''),
        )

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação de designação enviada com sucesso! Aguarde avaliação.</div><script>lucide.createIcons();</script>')

    except Missao.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Missão não encontrada.</div>')
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Erro ao criar solicitação: {str(e)}</div>')


@login_required
def htmx_solicitacoes_lista(request):
    """Lista solicitações de missão e designação com paginação e filtros."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    # Buscar solicitações de ambos os tipos
    tipo_solicitacao = request.GET.get('tipo_solicitacao', 'todas')

    # Filtros comuns
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')

    # Listas separadas
    solicitacoes_missao = []
    solicitacoes_designacao = []

    if tipo_solicitacao in ['todas', 'missao']:
        qs_missao = SolicitacaoMissao.objects.select_related('solicitante', 'avaliado_por').all()
        if busca:
            qs_missao = qs_missao.filter(
                Q(solicitante__nome__icontains=busca) |
                Q(solicitante__nome_guerra__icontains=busca) |
                Q(nome_missao__icontains=busca)
            )
        if status:
            qs_missao = qs_missao.filter(status=status)
        solicitacoes_missao = list(qs_missao.order_by('-criado_em'))

    if tipo_solicitacao in ['todas', 'designacao']:
        qs_designacao = SolicitacaoDesignacao.objects.select_related('solicitante', 'avaliado_por', 'missao').all()
        if busca:
            qs_designacao = qs_designacao.filter(
                Q(solicitante__nome__icontains=busca) |
                Q(solicitante__nome_guerra__icontains=busca) |
                Q(missao__nome__icontains=busca)
            )
        if status:
            qs_designacao = qs_designacao.filter(status=status)
        solicitacoes_designacao = list(qs_designacao.order_by('-criado_em'))

    # Contadores
    pendentes_missao = SolicitacaoMissao.objects.filter(status='PENDENTE').count()
    pendentes_designacao = SolicitacaoDesignacao.objects.filter(status='PENDENTE').count()

    context = {
        'solicitacoes_missao': solicitacoes_missao,
        'solicitacoes_designacao': solicitacoes_designacao,
        'pendentes_missao': pendentes_missao,
        'pendentes_designacao': pendentes_designacao,
        'filtros': {
            'busca': busca,
            'status': status,
            'tipo_solicitacao': tipo_solicitacao,
        },
        'status_choices': SolicitacaoDesignacao.STATUS_CHOICES,
        'complexidade_choices': Designacao.COMPLEXIDADE_CHOICES,
        'user': request.user,
    }

    return render(request, 'htmx/solicitacoes_lista.html', context)


@login_required
@require_POST
def htmx_solicitacao_missao_avaliar(request, pk):
    """Avalia uma solicitação de missão (aprovar/recusar)."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoMissao, pk=pk)
    acao = request.POST.get('acao')  # 'aprovar' ou 'recusar'

    try:
        solicitacao.avaliado_por = request.user
        solicitacao.data_avaliacao = timezone.now()
        solicitacao.observacao_avaliador = request.POST.get('observacao', '')

        if acao == 'aprovar':
            # Criar a missão automaticamente
            missao = Missao.objects.create(
                nome=solicitacao.nome_missao,
                tipo=solicitacao.tipo_missao,
                status=solicitacao.status_missao,
                local=dict(SolicitacaoMissao.LOCAL_CHOICES).get(solicitacao.local, solicitacao.local),
                data_inicio=solicitacao.data_inicio,
                data_fim=solicitacao.data_fim,
                documento_referencia=solicitacao.documento_sei,
            )
            solicitacao.status = 'APROVADA'
            solicitacao.missao_criada = missao
            messages.success(request, f'Solicitação aprovada! Missão "{missao.nome}" criada com sucesso.')
        else:
            solicitacao.status = 'RECUSADA'
            messages.info(request, 'Solicitação recusada.')

        solicitacao.save()

    except Exception as e:
        messages.error(request, f'Erro ao avaliar: {str(e)}')

    return htmx_solicitacoes_lista(request)


@login_required
@require_POST
def htmx_solicitacao_designacao_avaliar(request, pk):
    """Avalia uma solicitação de designação (aprovar/recusar)."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoDesignacao, pk=pk)
    acao = request.POST.get('acao')  # 'aprovar' ou 'recusar'

    try:
        solicitacao.avaliado_por = request.user
        solicitacao.data_avaliacao = timezone.now()
        solicitacao.observacao_avaliador = request.POST.get('observacao', '')

        if acao == 'aprovar':
            # Complexidade é definida pelo BM/3 na aprovação
            complexidade = request.POST.get('complexidade', 'MEDIA')
            solicitacao.complexidade = complexidade

            # Criar a designação automaticamente
            designacao = Designacao.objects.create(
                oficial=solicitacao.solicitante,
                missao=solicitacao.missao,
                funcao_na_missao=solicitacao.funcao_na_missao,
                complexidade=complexidade,
                observacoes=f'Criado via solicitação. SEI: {solicitacao.documento_sei}',
            )
            solicitacao.status = 'APROVADA'
            solicitacao.designacao_criada = designacao
            messages.success(request, f'Solicitação aprovada! {solicitacao.solicitante} designado para "{solicitacao.missao.nome}".')
        else:
            solicitacao.status = 'RECUSADA'
            messages.info(request, 'Solicitação recusada.')

        solicitacao.save()

    except Exception as e:
        messages.error(request, f'Erro ao avaliar: {str(e)}')

    return htmx_solicitacoes_lista(request)


@login_required
def htmx_solicitacao_missao_dados(request, pk):
    """Retorna os dados de uma solicitação de missão para edição."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoMissao, pk=pk)

    context = {
        'solicitacao': solicitacao,
        'tipo_choices': Missao.TIPO_CHOICES,
        'status_missao_choices': Missao.STATUS_CHOICES,
        'local_choices': SolicitacaoMissao.LOCAL_CHOICES,
    }

    return render(request, 'htmx/solicitacao_missao_form.html', context)


@login_required
@require_POST
def htmx_solicitacao_missao_editar(request, pk):
    """Edita uma solicitação de missão."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoMissao, pk=pk)

    try:
        solicitacao.nome_missao = request.POST.get('nome_missao', solicitacao.nome_missao)
        solicitacao.tipo_missao = request.POST.get('tipo_missao', solicitacao.tipo_missao)
        solicitacao.status_missao = request.POST.get('status_missao', solicitacao.status_missao)
        solicitacao.local = request.POST.get('local', solicitacao.local)
        solicitacao.data_inicio = request.POST.get('data_inicio', solicitacao.data_inicio)
        data_fim = request.POST.get('data_fim')
        solicitacao.data_fim = data_fim if data_fim else None
        solicitacao.documento_sei = request.POST.get('documento_sei', solicitacao.documento_sei)
        solicitacao.save()

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação atualizada com sucesso!</div><script>lucide.createIcons(); setTimeout(() => location.reload(), 1000);</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Erro ao atualizar: {str(e)}</div>')


@login_required
def htmx_solicitacao_designacao_dados(request, pk):
    """Retorna os dados de uma solicitação de designação para edição."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoDesignacao, pk=pk)
    missoes = Missao.objects.filter(status__in=['PLANEJADA', 'EM_ANDAMENTO']).order_by('nome')

    context = {
        'solicitacao': solicitacao,
        'missoes': missoes,
    }

    return render(request, 'htmx/solicitacao_designacao_form.html', context)


@login_required
@require_POST
def htmx_solicitacao_designacao_editar(request, pk):
    """Edita uma solicitação de designação."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(SolicitacaoDesignacao, pk=pk)

    try:
        missao_id = request.POST.get('missao_id')
        if missao_id:
            solicitacao.missao = Missao.objects.get(id=missao_id)
        solicitacao.funcao_na_missao = request.POST.get('funcao_na_missao', solicitacao.funcao_na_missao)
        solicitacao.documento_sei = request.POST.get('documento_sei', solicitacao.documento_sei)
        solicitacao.save()

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação atualizada com sucesso!</div><script>lucide.createIcons(); setTimeout(() => location.reload(), 1000);</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Erro ao atualizar: {str(e)}</div>')