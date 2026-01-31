"""
Unified Solicitações System - Uses the unified Solicitacao model - This is the current/preferred system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST

from ..models import Solicitacao, Missao, Designacao, Oficial, Funcao


@login_required
def minhas_solicitacoes(request):
    """Página com histórico de solicitações do oficial logado (modelo unificado)."""

    if not request.user.oficial:
        messages.error(request, 'Você não possui um oficial vinculado ao seu usuário.')
        return redirect('missoes_dashboard')

    oficial = request.user.oficial

    # Filtros
    tipo = request.GET.get('tipo', 'todas')
    status_filtro = request.GET.get('status', '')

    # Buscar solicitações do novo modelo unificado
    solicitacoes = Solicitacao.objects.filter(solicitante=oficial)

    if tipo == 'missao':
        solicitacoes = solicitacoes.filter(tipo_solicitacao='NOVA_MISSAO')
    elif tipo == 'designacao':
        solicitacoes = solicitacoes.filter(tipo_solicitacao='DESIGNACAO')

    if status_filtro:
        solicitacoes = solicitacoes.filter(status=status_filtro)

    solicitacoes = solicitacoes.select_related('missao_existente', 'missao_criada', 'designacao_criada', 'avaliado_por').order_by('-criado_em')

    # Contadores
    total_nova_missao = Solicitacao.objects.filter(solicitante=oficial, tipo_solicitacao='NOVA_MISSAO').count()
    total_designacao = Solicitacao.objects.filter(solicitante=oficial, tipo_solicitacao='DESIGNACAO').count()
    pendentes = Solicitacao.objects.filter(solicitante=oficial, status='PENDENTE').count()

    context = {
        'oficial': oficial,
        'solicitacoes': solicitacoes,
        'total_nova_missao': total_nova_missao,
        'total_designacao': total_designacao,
        'pendentes': pendentes,
        'filtros': {
            'tipo': tipo,
            'status': status_filtro,
        },
        'status_choices': Solicitacao.STATUS_CHOICES,
    }

    return render(request, 'pages/minhas_solicitacoes.html', context)


@login_required
@require_POST
def htmx_solicitacao_criar(request):
    """Cria uma solicitação unificada (nova missão + designação OU apenas designação)."""

    if not request.user.oficial:
        return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Usuário não vinculado a um oficial.</div>')

    tipo_solicitacao = request.POST.get('tipo_solicitacao')

    try:
        if tipo_solicitacao == 'NOVA_MISSAO':
            # Validações para nova missão
            nome_missao = request.POST.get('nome_missao', '').strip()
            ano_missao = request.POST.get('ano_missao') or None
            tipo_missao = request.POST.get('tipo_missao', '')
            status_missao = request.POST.get('status_missao', 'EM_ANDAMENTO')
            local_missao = request.POST.get('local_missao', '')
            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim') or None
            documento_sei_missao = request.POST.get('documento_sei_missao', '').strip()
            nome_funcao = request.POST.get('nome_funcao', '').strip()
            documento_sei_designacao = request.POST.get('documento_sei_designacao', '').strip()

            if not all([nome_missao, tipo_missao, local_missao, data_inicio, documento_sei_missao, nome_funcao, documento_sei_designacao]):
                return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Preencha todos os campos obrigatórios.</div>')

            if status_missao == 'CONCLUIDA' and not data_fim:
                return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Data de término é obrigatória para missões concluídas.</div>')

            # Criar solicitação
            Solicitacao.objects.create(
                tipo_solicitacao='NOVA_MISSAO',
                solicitante=request.user.oficial,
                nome_missao=nome_missao,
                ano_missao=ano_missao,
                tipo_missao=tipo_missao,
                status_missao=status_missao,
                local_missao=local_missao,
                data_inicio=data_inicio,
                data_fim=data_fim,
                documento_sei_missao=documento_sei_missao,
                nome_funcao=nome_funcao,
                documento_sei_designacao=documento_sei_designacao,
            )

            return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação de nova missão enviada com sucesso! Aguarde avaliação da BM/3.</div><script>lucide.createIcons();</script>')

        elif tipo_solicitacao == 'DESIGNACAO':
            # Validações para designação em missão existente
            missao_id = request.POST.get('missao_id')
            funcao_id = request.POST.get('funcao_id')
            documento_sei_designacao = request.POST.get('documento_sei_designacao', '').strip()

            if not all([missao_id, funcao_id, documento_sei_designacao]):
                return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Preencha todos os campos obrigatórios.</div>')

            missao = Missao.objects.get(id=missao_id)

            # Validar que a função pertence à missão selecionada
            funcao = get_object_or_404(Funcao, pk=funcao_id, missao=missao)

            # Verificar se já existe designação para esta missão e função
            if Designacao.objects.filter(oficial=request.user.oficial, missao=missao, funcao=funcao).exists():
                return HttpResponse('<div class="alert alert-warning"><i data-lucide="alert-triangle"></i> Você já está designado para esta função nesta missão.</div>')

            # Verificar se já existe solicitação pendente para esta função
            if Solicitacao.objects.filter(
                solicitante=request.user.oficial,
                missao_existente=missao,
                funcao_existente=funcao,
                status='PENDENTE'
            ).exists():
                return HttpResponse('<div class="alert alert-warning"><i data-lucide="alert-triangle"></i> Já existe uma solicitação pendente para esta função nesta missão.</div>')

            # Criar solicitação
            Solicitacao.objects.create(
                tipo_solicitacao='DESIGNACAO',
                solicitante=request.user.oficial,
                missao_existente=missao,
                funcao_existente=funcao,
                documento_sei_designacao=documento_sei_designacao,
            )

            return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação de designação enviada com sucesso! Aguarde avaliação da BM/3.</div><script>lucide.createIcons();</script>')

        else:
            return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Tipo de solicitação inválido.</div>')

    except Missao.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Missão não encontrada.</div>')
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Erro ao criar solicitação: {str(e)}</div>')


@login_required
def htmx_buscar_missoes_disponiveis(request):
    """Busca missões disponíveis para designação com filtros (HTMX)."""

    # Filtros
    tipo = request.GET.get('tipo', '')
    ano = request.GET.get('ano', '')
    busca = request.GET.get('busca', '').strip()

    # Base query - missões Planejadas ou Em Andamento
    missoes = Missao.objects.filter(status__in=['PLANEJADA', 'EM_ANDAMENTO'])

    if tipo:
        missoes = missoes.filter(tipo=tipo)

    if ano:
        missoes = missoes.filter(data_inicio__year=ano)

    if busca:
        missoes = missoes.filter(
            Q(nome__icontains=busca) |
            Q(documento_ref__icontains=busca)
        )

    # Ordenar e limitar
    missoes = missoes.order_by('-data_inicio', 'nome')[:30]

    # Anos disponíveis para o filtro
    from datetime import datetime
    ano_atual = datetime.now().year
    anos_disponiveis = list(range(ano_atual, ano_atual - 5, -1))

    return render(request, 'htmx/missoes_disponiveis.html', {
        'missoes': missoes,
        'tipo_choices': Missao.TIPO_CHOICES,
        'anos_disponiveis': anos_disponiveis,
        'filtros': {
            'tipo': tipo,
            'ano': ano,
            'busca': busca,
        }
    })


@login_required
def htmx_solicitacoes_unificadas_lista(request):
    """Lista solicitações unificadas para BM/3 e Admin."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    # Filtros
    tipo_solicitacao = request.GET.get('tipo_solicitacao', 'todas')
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')

    # Base query
    solicitacoes = Solicitacao.objects.select_related(
        'solicitante', 'missao_existente', 'avaliado_por', 'missao_criada', 'designacao_criada'
    )

    if tipo_solicitacao == 'missao':
        solicitacoes = solicitacoes.filter(tipo_solicitacao='NOVA_MISSAO')
    elif tipo_solicitacao == 'designacao':
        solicitacoes = solicitacoes.filter(tipo_solicitacao='DESIGNACAO')

    if busca:
        solicitacoes = solicitacoes.filter(
            Q(solicitante__nome__icontains=busca) |
            Q(solicitante__nome_guerra__icontains=busca) |
            Q(nome_missao__icontains=busca) |
            Q(missao_existente__nome__icontains=busca)
        )

    if status:
        solicitacoes = solicitacoes.filter(status=status)

    solicitacoes = solicitacoes.order_by('-criado_em')

    # Contadores
    pendentes_total = Solicitacao.objects.filter(status='PENDENTE').count()
    pendentes_missao = Solicitacao.objects.filter(status='PENDENTE', tipo_solicitacao='NOVA_MISSAO').count()
    pendentes_designacao = Solicitacao.objects.filter(status='PENDENTE', tipo_solicitacao='DESIGNACAO').count()

    context = {
        'solicitacoes': solicitacoes,
        'pendentes_total': pendentes_total,
        'pendentes_missao': pendentes_missao,
        'pendentes_designacao': pendentes_designacao,
        'tipo_solicitacao': tipo_solicitacao,
        'busca': busca,
        'status_filtro': status,
        'tipo_missao_choices': Missao.TIPO_CHOICES,
        'local_choices': Solicitacao.LOCAL_CHOICES,
        'nivel_tde_nqt_grs_choices': Funcao.NIVEL_TDE_NQT_GRS_CHOICES,
        'nivel_dec_choices': Funcao.NIVEL_DEC_CHOICES,
        'missoes_disponiveis': Missao.objects.filter(status__in=['PLANEJADA', 'EM_ANDAMENTO']).order_by('nome'),
        'oficiais_disponiveis': Oficial.objects.filter(ativo=True).order_by('posto', 'nome'),
    }

    return render(request, 'htmx/solicitacoes_unificadas_lista.html', context)


@login_required
def htmx_solicitacao_dados(request, pk):
    """Retorna dados de uma solicitação para edição."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    # Missões disponíveis (para caso seja designação)
    missoes_disponiveis = Missao.objects.filter(status__in=['PLANEJADA', 'EM_ANDAMENTO']).order_by('nome')

    context = {
        'solicitacao': solicitacao,
        'tipo_missao_choices': Missao.TIPO_CHOICES,
        'status_missao_choices': Missao.STATUS_CHOICES,
        'local_choices': Solicitacao.LOCAL_CHOICES,
        'nivel_tde_nqt_grs_choices': Funcao.NIVEL_TDE_NQT_GRS_CHOICES,
        'nivel_dec_choices': Funcao.NIVEL_DEC_CHOICES,
        'missoes_disponiveis': missoes_disponiveis,
    }

    # Funções da missão (se for designação e missão já selecionada)
    if solicitacao.missao_existente:
        context['funcoes_disponiveis'] = Funcao.objects.filter(missao=solicitacao.missao_existente).order_by('funcao')

    return render(request, 'htmx/solicitacao_form_edicao.html', context)


@login_required
@require_POST
def htmx_solicitacao_editar(request, pk):
    """Edita uma solicitação pendente."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.status != 'PENDENTE':
        return HttpResponse('<div class="alert alert-warning">Somente solicitações pendentes podem ser editadas.</div>')

    try:
        if solicitacao.tipo_solicitacao == 'NOVA_MISSAO':
            solicitacao.nome_missao = request.POST.get('nome_missao', solicitacao.nome_missao)
            solicitacao.ano_missao = request.POST.get('ano_missao') or solicitacao.ano_missao
            solicitacao.tipo_missao = request.POST.get('tipo_missao', solicitacao.tipo_missao)
            solicitacao.status_missao = request.POST.get('status_missao', solicitacao.status_missao)
            solicitacao.local_missao = request.POST.get('local_missao', solicitacao.local_missao)
            solicitacao.data_inicio = request.POST.get('data_inicio') or solicitacao.data_inicio
            solicitacao.data_fim = request.POST.get('data_fim') or None
            solicitacao.documento_sei_missao = request.POST.get('documento_sei_missao', solicitacao.documento_sei_missao)
            solicitacao.nome_funcao = request.POST.get('nome_funcao', solicitacao.nome_funcao)

            # Campos TDE/NQT/GRS/DEC (preenchidos pelo avaliador)
            if request.POST.get('tde'):
                solicitacao.tde = int(request.POST.get('tde'))
            if request.POST.get('nqt'):
                solicitacao.nqt = int(request.POST.get('nqt'))
            if request.POST.get('grs'):
                solicitacao.grs = int(request.POST.get('grs'))
            if request.POST.get('dec'):
                solicitacao.dec = int(request.POST.get('dec'))
        else:
            missao_id = request.POST.get('missao_id')
            if missao_id:
                solicitacao.missao_existente = Missao.objects.get(id=missao_id)

            # Atualizar função existente (FK)
            funcao_id = request.POST.get('funcao_id')
            if funcao_id:
                funcao = get_object_or_404(Funcao, pk=funcao_id, missao=solicitacao.missao_existente)
                solicitacao.funcao_existente = funcao

        solicitacao.documento_sei_designacao = request.POST.get('documento_sei_designacao', solicitacao.documento_sei_designacao)
        solicitacao.save()

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação atualizada com sucesso!</div><script>lucide.createIcons(); setTimeout(() => { document.getElementById("modal-editar").style.display="none"; htmx.trigger("#tab-content", "refresh"); }, 1000);</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Erro ao atualizar: {str(e)}</div>')


@login_required
@require_POST
def htmx_solicitacao_aprovar(request, pk):
    """Aprova uma solicitação e cria os registros correspondentes."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.status != 'PENDENTE':
        return HttpResponse('<div class="alert alert-warning">Esta solicitação já foi avaliada.</div>')

    observacao = request.POST.get('observacao', '').strip()

    # Validar campos obrigatórios conforme tipo de solicitação
    if solicitacao.tipo_solicitacao == 'NOVA_MISSAO':
        # Para nova missão, TDE/NQT/GRS/DEC são obrigatórios
        tde = request.POST.get('tde')
        nqt = request.POST.get('nqt')
        grs = request.POST.get('grs')
        dec = request.POST.get('dec')

        if not all([tde, nqt, grs, dec]):
            return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Preencha TDE, NQT, GRS e DEC para aprovar nova missão.</div>')
    else:
        # Para designação, complexidade virá da função selecionada
        tde = nqt = grs = dec = None

    try:
        # Atualizar dados editados antes de aprovar (caso tenham sido modificados)
        if solicitacao.tipo_solicitacao == 'NOVA_MISSAO':
            if request.POST.get('nome_missao'):
                solicitacao.nome_missao = request.POST.get('nome_missao')
            if request.POST.get('tipo_missao'):
                solicitacao.tipo_missao = request.POST.get('tipo_missao')
            if request.POST.get('status_missao'):
                solicitacao.status_missao = request.POST.get('status_missao')
            if request.POST.get('local_missao'):
                solicitacao.local_missao = request.POST.get('local_missao')
            if request.POST.get('data_inicio'):
                solicitacao.data_inicio = request.POST.get('data_inicio')
            if request.POST.get('data_fim'):
                solicitacao.data_fim = request.POST.get('data_fim')
            if request.POST.get('documento_sei_missao'):
                solicitacao.documento_sei_missao = request.POST.get('documento_sei_missao')
            if request.POST.get('nome_funcao'):
                solicitacao.nome_funcao = request.POST.get('nome_funcao')

            # Salvar TDE/NQT/GRS/DEC na solicitação
            solicitacao.tde = int(tde)
            solicitacao.nqt = int(nqt)
            solicitacao.grs = int(grs)
            solicitacao.dec = int(dec)
        else:
            missao_id = request.POST.get('missao_id')
            if missao_id:
                solicitacao.missao_existente = Missao.objects.get(id=missao_id)

            # Atualizar função existente (FK)
            funcao_id = request.POST.get('funcao_id')
            if funcao_id:
                funcao = get_object_or_404(Funcao, pk=funcao_id, missao=solicitacao.missao_existente)
                solicitacao.funcao_existente = funcao

        if request.POST.get('documento_sei_designacao'):
            solicitacao.documento_sei_designacao = request.POST.get('documento_sei_designacao')

        solicitacao.save()

        # Aprovar usando o método do modelo
        solicitacao.aprovar(
            avaliador=request.user,
            observacao=observacao
        )

        return HttpResponse('<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação aprovada com sucesso! Registros criados.</div><script>lucide.createIcons(); setTimeout(() => { document.getElementById("modal-avaliar").style.display="none"; htmx.trigger("#tab-content", "refresh"); }, 1500);</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Erro ao aprovar: {str(e)}</div>')


@login_required
@require_POST
def htmx_solicitacao_recusar(request, pk):
    """Recusa uma solicitação."""

    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.status != 'PENDENTE':
        return HttpResponse('<div class="alert alert-warning">Esta solicitação já foi avaliada.</div>')

    observacao = request.POST.get('observacao', '').strip()

    try:
        solicitacao.recusar(
            avaliador=request.user,
            observacao=observacao
        )

        return HttpResponse('<div class="alert alert-info"><i data-lucide="x-circle"></i> Solicitação recusada.</div><script>lucide.createIcons(); setTimeout(() => { document.getElementById("modal-avaliar").style.display="none"; htmx.trigger("#tab-content", "refresh"); }, 1500);</script>')

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Erro ao recusar: {str(e)}</div>')


# ========================================
# VALIDATION PANEL VIEWS (Modern System)
# ========================================

@login_required
def htmx_solicitacoes_validacao(request):
    """
    Painel de validação moderno para BM/3 e Admin.
    Lista compacta com filtros, seleção em lote e modal de edição.
    """
    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    status_filtro = request.GET.get('status', 'PENDENTE')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    busca = request.GET.get('busca', '').strip()

    # Base query com otimização
    solicitacoes = Solicitacao.objects.select_related(
        'solicitante',
        'missao_existente',
        'funcao_existente'
    ).only(
        'id', 'tipo_solicitacao', 'status', 'criado_em', 'nome_funcao',
        'nome_missao', 'tde', 'nqt', 'grs', 'dec',
        'solicitante__nome', 'solicitante__nome_guerra', 'solicitante__posto',
        'missao_existente__nome', 'funcao_existente__funcao'
    )

    # Aplicar filtros
    if tipo_filtro:
        solicitacoes = solicitacoes.filter(tipo_solicitacao=tipo_filtro)

    if status_filtro:
        solicitacoes = solicitacoes.filter(status=status_filtro)

    if data_inicio:
        solicitacoes = solicitacoes.filter(criado_em__gte=data_inicio)

    if data_fim:
        from datetime import datetime, timedelta
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_final = data_fim_obj + timedelta(days=1)
        solicitacoes = solicitacoes.filter(criado_em__lt=data_fim_final)

    if busca:
        solicitacoes = solicitacoes.filter(
            Q(solicitante__nome__icontains=busca) |
            Q(solicitante__nome_guerra__icontains=busca) |
            Q(nome_missao__icontains=busca) |
            Q(missao_existente__nome__icontains=busca) |
            Q(nome_funcao__icontains=busca) |
            Q(funcao_existente__funcao__icontains=busca)
        )

    solicitacoes = solicitacoes.order_by('-criado_em')

    # Estatísticas
    stats = {
        'total': Solicitacao.objects.count(),
        'pendentes': Solicitacao.objects.filter(status='PENDENTE').count(),
        'count_missao': Solicitacao.objects.filter(tipo_solicitacao='NOVA_MISSAO').count(),
        'count_designacao': Solicitacao.objects.filter(tipo_solicitacao='DESIGNACAO').count(),
    }

    context = {
        'solicitacoes': solicitacoes,
        'stats': stats,
        'filtros': {
            'tipo': tipo_filtro,
            'status': status_filtro,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'busca': busca,
        },
        'status_choices': Solicitacao.STATUS_CHOICES,
        'complexidade_choices': Funcao.COMPLEXIDADE_CHOICES,
    }

    return render(request, 'htmx/solicitacoes_validacao.html', context)


@login_required
@require_POST
def htmx_solicitacao_quick_approve(request, pk):
    """
    Aprovação rápida: pede apenas complexidade.
    Não permite edição dos dados antes de aprovar.
    """
    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.status != 'PENDENTE':
        return HttpResponse('<div class="alert alert-warning">Esta solicitação já foi avaliada.</div>')

    complexidade = request.POST.get('complexidade')

    if not complexidade:
        return HttpResponse('<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Selecione a complexidade.</div>')

    try:
        solicitacao.aprovar(
            avaliador=request.user,
            complexidade=complexidade,
            observacao='Aprovação rápida'
        )

        return HttpResponse(
            '<div class="alert alert-success"><i data-lucide="check-circle"></i> Solicitação aprovada!</div>'
            '<script>lucide.createIcons(); setTimeout(() => { htmx.trigger("#validation-content", "refresh"); }, 1000);</script>'
        )

    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger"><i data-lucide="alert-circle"></i> Erro: {str(e)}</div>')


@login_required
@require_POST
def htmx_solicitacao_batch_approve(request):
    """
    Aprovação em lote: recebe lista de IDs e complexidade única.
    """
    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    ids = request.POST.getlist('ids[]')
    complexidade = request.POST.get('complexidade')
    observacao = request.POST.get('observacao', 'Aprovação em lote').strip()

    if not ids:
        return HttpResponse('<div class="alert alert-warning">Nenhuma solicitação selecionada.</div>')

    if not complexidade:
        return HttpResponse('<div class="alert alert-danger">Selecione a complexidade.</div>')

    aprovadas = 0
    erros = []

    for sol_id in ids:
        try:
            solicitacao = Solicitacao.objects.get(id=sol_id, status='PENDENTE')
            solicitacao.aprovar(
                avaliador=request.user,
                complexidade=complexidade,
                observacao=observacao
            )
            aprovadas += 1
        except Solicitacao.DoesNotExist:
            erros.append(f'Solicitação {sol_id} não encontrada ou já avaliada')
        except Exception as e:
            erros.append(f'Erro na solicitação {sol_id}: {str(e)}')

    mensagem = f'<div class="alert alert-success"><i data-lucide="check-circle"></i> {aprovadas} solicitação(ões) aprovada(s)!'
    if erros:
        mensagem += f'<br><small>{len(erros)} erro(s): {"; ".join(erros[:3])}</small>'
    mensagem += '</div><script>lucide.createIcons(); setTimeout(() => { htmx.trigger("#validation-content", "refresh"); }, 1500);</script>'

    return HttpResponse(mensagem)


@login_required
@require_POST
def htmx_solicitacao_batch_reject(request):
    """
    Recusa em lote: recebe lista de IDs e observação obrigatória.
    """
    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    ids = request.POST.getlist('ids[]')
    observacao = request.POST.get('observacao', '').strip()

    if not ids:
        return HttpResponse('<div class="alert alert-warning">Nenhuma solicitação selecionada.</div>')

    if not observacao:
        return HttpResponse('<div class="alert alert-danger">A justificativa é obrigatória para recusa em lote.</div>')

    recusadas = 0
    erros = []

    for sol_id in ids:
        try:
            solicitacao = Solicitacao.objects.get(id=sol_id, status='PENDENTE')
            solicitacao.recusar(
                avaliador=request.user,
                observacao=observacao
            )
            recusadas += 1
        except Solicitacao.DoesNotExist:
            erros.append(f'Solicitação {sol_id} não encontrada ou já avaliada')
        except Exception as e:
            erros.append(f'Erro na solicitação {sol_id}: {str(e)}')

    mensagem = f'<div class="alert alert-info"><i data-lucide="x-circle"></i> {recusadas} solicitação(ões) recusada(s)!'
    if erros:
        mensagem += f'<br><small>{len(erros)} erro(s): {"; ".join(erros[:3])}</small>'
    mensagem += '</div><script>lucide.createIcons(); setTimeout(() => { htmx.trigger("#validation-content", "refresh"); }, 1500);</script>'

    return HttpResponse(mensagem)


@login_required
def htmx_solicitacao_detalhes_modal(request, pk):
    """
    Carrega modal com detalhes completos e aba de edição.
    """
    if not request.user.pode_gerenciar_solicitacoes:
        return HttpResponse('Sem permissão', status=403)

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related('solicitante', 'missao_existente', 'avaliado_por', 'missao_criada', 'designacao_criada'),
        pk=pk
    )

    # Missões disponíveis para dropdown (caso seja DESIGNACAO)
    missoes_disponiveis = Missao.objects.filter(
        status__in=['PLANEJADA', 'EM_ANDAMENTO']
    ).order_by('nome')

    context = {
        'sol': solicitacao,
        'tipo_missao_choices': Missao.TIPO_CHOICES,
        'status_missao_choices': Missao.STATUS_CHOICES,
        'local_choices': Solicitacao.LOCAL_CHOICES,
        'nivel_tde_nqt_grs_choices': Funcao.NIVEL_TDE_NQT_GRS_CHOICES,
        'nivel_dec_choices': Funcao.NIVEL_DEC_CHOICES,
        'missoes_disponiveis': missoes_disponiveis,
    }

    # Funções da missão (se for designação e missão já selecionada)
    if solicitacao.missao_existente:
        context['funcoes_disponiveis'] = Funcao.objects.filter(missao=solicitacao.missao_existente).order_by('funcao')

    return render(request, 'htmx/solicitacao_detalhes_modal.html', context)