"""Oficiais views - Officer management, consultation, and HTMX endpoints"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from ..models import Oficial, Designacao, Missao, Usuario, Unidade, Solicitacao


@login_required
def consultar_oficial(request, oficial_id=None):
    """
    Consulta painel de um oficial.
    - Oficial comum: não tem acesso (usa painel_oficial)
    - Comandante: vê oficiais da sua OBM e subordinadas
    - BM/3, Corregedor, Comando-Geral, Admin: vê todos os oficiais
    """

    usuario = request.user
    oficial = None

    # Verificar se pode consultar outros oficiais
    pode_consultar_outros = usuario.pode_ver_consultar_oficial

    # Se não pode consultar outros, redireciona
    if not pode_consultar_outros:
        messages.warning(request, 'Você não tem permissão para acessar esta página.')
        return redirect('painel_oficial')

    # Determinar qual oficial será exibido
    if oficial_id:
        # Tentando ver outro oficial
        oficial = get_object_or_404(Oficial, pk=oficial_id)

        # Verificar permissão (comandante só vê sua OBM)
        if not usuario.pode_ver_oficial(oficial):
            messages.error(request, 'Você não tem permissão para visualizar este oficial.')
            return redirect('consultar_oficial')
    else:
        # Mostrar apenas a tela de busca (sem oficial pré-selecionado)
        oficial = None

    # Lista de OBMs disponíveis para o filtro
    obms_disponiveis = []
    if usuario.role in ['admin', 'comando_geral', 'bm3', 'corregedor']:
        # Estes perfis veem todas as OBMs
        obms_disponiveis = list(
            Oficial.objects.filter(ativo=True)
            .exclude(obm__isnull=True)
            .exclude(obm='')
            .values_list('obm', flat=True)
            .distinct()
            .order_by('obm')
        )
    elif usuario.role == 'comandante':
        # Comandante vê apenas sua OBM e subordinadas
        obms_disponiveis = usuario.get_obm_subordinadas()

    # Designações do oficial (se houver oficial selecionado)
    designacoes = []
    if oficial:
        designacoes = Designacao.objects.filter(oficial=oficial).select_related('missao').order_by('-criado_em')

        # Filtros
        tipo = request.GET.get('tipo', '')
        status = request.GET.get('status', '')
        complexidade = request.GET.get('complexidade', '')

        if tipo:
            designacoes = designacoes.filter(missao__tipo=tipo)
        if status:
            designacoes = designacoes.filter(missao__status=status)
        if complexidade:
            designacoes = designacoes.filter(complexidade=complexidade)

    # Verificar se está vendo o próprio painel
    visualizando_proprio = oficial and usuario.oficial and usuario.oficial.id == oficial.id

    context = {
        'oficial': oficial,
        'designacoes': designacoes,
        'tipo_choices': Missao.TIPO_CHOICES,
        'status_choices': Missao.STATUS_CHOICES,
        'complexidade_choices': Designacao.COMPLEXIDADE_CHOICES,
        'pode_consultar_outros': pode_consultar_outros,
        'obms_disponiveis': obms_disponiveis,
        'posto_choices': Oficial.POSTO_CHOICES,
        'quadro_choices': Oficial.QUADRO_CHOICES,
        'visualizando_proprio': visualizando_proprio,
    }

    return render(request, 'pages/consultar_oficial.html', context)


@login_required
def htmx_buscar_oficiais(request):
    """Busca oficiais para o painel de consulta (HTMX)."""

    usuario = request.user

    # Verificar permissão
    if not usuario.pode_ver_consultar_oficial:
        return HttpResponse('<p class="text-danger">Sem permissão.</p>')

    # Base query
    oficiais = Oficial.objects.filter(ativo=True)

    # Filtrar por permissão do comandante
    if usuario.role == 'comandante':
        obms_permitidas = usuario.get_obm_subordinadas()
        if obms_permitidas:
            q_filter = Q()
            for obm in obms_permitidas:
                q_filter |= Q(obm__icontains=obm)
            oficiais = oficiais.filter(q_filter)

    # Aplicar filtros da busca
    rg = request.GET.get('rg', '').strip()
    nome = request.GET.get('nome', '').strip()
    obm = request.GET.get('obm', '').strip()
    posto = request.GET.get('posto', '').strip()
    quadro = request.GET.get('quadro', '').strip()

    if rg:
        oficiais = oficiais.filter(rg__icontains=rg)
    if nome:
        oficiais = oficiais.filter(
            Q(nome__icontains=nome) | Q(nome_guerra__icontains=nome)
        )
    if obm:
        oficiais = oficiais.filter(obm__icontains=obm)
    if posto:
        oficiais = oficiais.filter(posto=posto)
    if quadro:
        oficiais = oficiais.filter(quadro=quadro)

    # Limitar resultados
    oficiais = oficiais.order_by('posto', 'nome')[:20]

    # Verificar se há filtros ativos
    tem_filtros = any([rg, nome, obm, posto, quadro])

    return render(request, 'htmx/oficiais_busca_resultado.html', {
        'oficiais': oficiais,
        'tem_filtros': tem_filtros,
        'total': oficiais.count(),
    })


# Alias para manter compatibilidade com URLs antigas
@login_required
def painel_oficial(request):
    """Painel do oficial logado com suas designações e formulários de solicitação."""

    usuario = request.user

    if not usuario.oficial:
        messages.error(request, 'Você não possui um oficial vinculado ao seu usuário.')
        return redirect('missoes_dashboard')

    oficial = usuario.oficial

    # Designações do oficial
    designacoes = Designacao.objects.filter(oficial=oficial).select_related('missao').order_by('-criado_em')

    # Filtros
    tipo = request.GET.get('tipo', '')
    status_filtro = request.GET.get('status', '')
    complexidade = request.GET.get('complexidade', '')

    if tipo:
        designacoes = designacoes.filter(missao__tipo=tipo)
    if status_filtro:
        designacoes = designacoes.filter(missao__status=status_filtro)
    if complexidade:
        designacoes = designacoes.filter(complexidade=complexidade)

    # Missões disponíveis para solicitar designação (Planejada ou Em Andamento)
    missoes_disponiveis = Missao.objects.filter(
        status__in=['PLANEJADA', 'EM_ANDAMENTO']
    ).order_by('-data_inicio', 'nome')[:30]

    # Anos disponíveis para filtro
    from datetime import datetime
    ano_atual = datetime.now().year
    anos_disponiveis = list(range(ano_atual, ano_atual - 5, -1))

    context = {
        'oficial': oficial,
        'designacoes': designacoes,
        'missoes_disponiveis': missoes_disponiveis,
        'anos_disponiveis': anos_disponiveis,
        'tipo_choices': Missao.TIPO_CHOICES,
        'status_choices': Missao.STATUS_CHOICES,
        'complexidade_choices': Designacao.COMPLEXIDADE_CHOICES,
        'local_choices': Solicitacao.LOCAL_CHOICES,
    }

    return render(request, 'pages/painel_oficial.html', context)


# ============================================================
# 🔄 HTMX - OFICIAIS
# ============================================================
@login_required
def htmx_oficiais_lista(request):
    """Retorna a lista de oficiais para a tabela administrativa ou comparação."""

    user = request.user
    oficiais = Oficial.objects.all().order_by('posto', 'nome')

    # Se for comandante, filtrar apenas OBMs permitidas
    if user.is_comandante:
        obms_permitidas = user.get_obm_subordinadas()
        if obms_permitidas:
            q_filter = Q()
            for obm in obms_permitidas:
                q_filter |= Q(obm__icontains=obm)
            oficiais = oficiais.filter(q_filter)

    # Filtros da interface
    posto = request.GET.get('posto', '')
    quadro = request.GET.get('quadro', '')
    obm = request.GET.get('obm', '')
    busca = request.GET.get('busca', '')
    ativo = request.GET.get('ativo', '')

    if posto:
        oficiais = oficiais.filter(posto=posto)
    if quadro:
        oficiais = oficiais.filter(quadro=quadro)
    if obm:
        oficiais = oficiais.filter(obm__icontains=obm)
    if busca:
        oficiais = oficiais.filter(
            Q(nome__icontains=busca) |
            Q(nome_guerra__icontains=busca) |
            Q(cpf__icontains=busca) |
            Q(rg__icontains=busca)
        )
    if ativo:
        oficiais = oficiais.filter(ativo=(ativo == 'true'))

    # Determinar qual template usar
    template = request.GET.get('template', 'tabela')

    if template == 'lista':
        return render(request, 'htmx/oficiais_lista.html', {'oficiais': oficiais})

    # Ordenação
    ordenar = request.GET.get('ordenar', 'posto')
    direcao = request.GET.get('direcao', 'asc')

    if direcao == 'desc' and not ordenar.startswith('-'):
        ordenar = f'-{ordenar}'
    elif direcao == 'asc' and ordenar.startswith('-'):
        ordenar = ordenar[1:]

    oficiais = oficiais.order_by(ordenar, 'nome')

    # Paginação
    por_pagina = int(request.GET.get('por_pagina', 25))
    pagina = request.GET.get('pagina', 1)

    paginator = Paginator(oficiais, por_pagina)
    page_obj = paginator.get_page(pagina)

    # Query string para paginação
    query_params = request.GET.copy()
    if 'pagina' in query_params:
        del query_params['pagina']
    query_string = query_params.urlencode()

    # Lista de OBMs disponíveis para filtro
    obms_disponiveis = Oficial.objects.values_list('obm', flat=True).distinct().order_by('obm')

    context = {
        'page_obj': page_obj,
        'filtros': {
            'busca': busca,
            'posto': posto,
            'quadro': quadro,
            'obm': obm,
            'ativo': ativo,
            'por_pagina': str(por_pagina),
        },
        'ordenacao': {
            'campo': ordenar.lstrip('-'),
            'direcao': direcao,
        },
        'query_string': query_string,
        'posto_choices': Oficial.POSTO_CHOICES,
        'quadro_choices': Oficial.QUADRO_CHOICES,
        'obms_disponiveis': obms_disponiveis,
        'user': user,
    }

    return render(request, 'htmx/oficiais_tabela.html', context)


@login_required
def htmx_oficiais_selecao(request):
    """Retorna lista de oficiais com checkboxes para seleção (página Comparar)."""

    user = request.user
    oficiais = Oficial.objects.filter(ativo=True)

    # Filtros
    posto = request.GET.get('posto', '')
    quadro = request.GET.get('quadro', '')
    obm = request.GET.get('obm', '')
    busca = request.GET.get('busca', '')

    if posto:
        oficiais = oficiais.filter(posto=posto)
    if quadro:
        oficiais = oficiais.filter(quadro=quadro)
    if obm:
        oficiais = oficiais.filter(obm__icontains=obm)
    if busca:
        oficiais = oficiais.filter(
            Q(nome__icontains=busca) |
            Q(nome_guerra__icontains=busca)
        )

    # Filtro de OBM para comandante
    if user.role == 'comandante' and hasattr(user, 'get_obm_subordinadas'):
        obms_permitidas = user.get_obm_subordinadas()
        if obms_permitidas:
            q_filter = Q()
            for obm_perm in obms_permitidas:
                q_filter |= Q(obm__icontains=obm_perm)
            oficiais = oficiais.filter(q_filter)

    oficiais = oficiais.order_by('posto', 'nome')

    # Lista de OBMs disponíveis
    obms_disponiveis = Oficial.objects.filter(ativo=True).values_list('obm', flat=True).distinct().order_by('obm')

    context = {
        'oficiais': oficiais,
        'filtros': {
            'busca': busca,
            'posto': posto,
            'quadro': quadro,
            'obm': obm,
        },
        'posto_choices': Oficial.POSTO_CHOICES,
        'quadro_choices': Oficial.QUADRO_CHOICES,
        'obms_disponiveis': obms_disponiveis,
    }

    return render(request, 'htmx/oficiais_selecao.html', context)


@login_required
def htmx_oficiais_cards(request):
    """Retorna cards de oficiais para comparação com gráficos."""

    ids = request.GET.get('ids', '')

    if ids:
        ids_list = [int(id) for id in ids.split(',') if id.isdigit()]
        oficiais = Oficial.objects.filter(id__in=ids_list)

        # Para cada oficial, buscar dados para o card
        oficiais_data = []
        for oficial in oficiais:
            ultimas_missoes = oficial.designacoes.select_related('missao').filter(
                missao__status='EM_ANDAMENTO'
            ).order_by('-criado_em')[:5]

            oficiais_data.append({
                'oficial': oficial,
                'total_baixa': oficial.total_baixa,
                'total_media': oficial.total_media,
                'total_alta': oficial.total_alta,
                'carga_total': oficial.carga_total,
                'ultimas_missoes': ultimas_missoes,
            })
    else:
        oficiais_data = []

    return render(request, 'htmx/oficiais_cards.html', {'oficiais_data': oficiais_data})


@login_required
def htmx_oficial_card(request, pk):
    """Retorna o card de um oficial específico."""

    oficial = get_object_or_404(Oficial, pk=pk)

    # Últimas missões ativas
    ultimas_missoes = oficial.designacoes.select_related('missao').filter(
        missao__status='EM_ANDAMENTO'
    ).order_by('-criado_em')[:5]

    context = {
        'oficial': oficial,
        'total_baixa': oficial.total_baixa,
        'total_media': oficial.total_media,
        'total_alta': oficial.total_alta,
        'carga_total': oficial.carga_total,
        'ultimas_missoes': ultimas_missoes,
    }

    return render(request, 'htmx/oficial_card.html', context)


@login_required
@require_POST
def htmx_oficial_criar(request):
    """Cria um novo oficial via HTMX."""

    if not request.user.pode_gerenciar_oficiais:
        return HttpResponse('Sem permissão', status=403)

    try:
        oficial = Oficial.objects.create(
            cpf=request.POST.get('cpf', '').replace('.', '').replace('-', ''),
            rg=request.POST.get('rg', ''),
            nome=request.POST.get('nome', ''),
            nome_guerra=request.POST.get('nome_guerra', ''),
            posto=request.POST.get('posto', ''),
            quadro=request.POST.get('quadro', ''),
            obm=request.POST.get('obm', ''),
            funcao=request.POST.get('funcao', ''),
            email=request.POST.get('email', ''),
            telefone=request.POST.get('telefone', ''),
        )

        # Criar usuário automaticamente
        Usuario.objects.create_user(
            cpf=oficial.cpf,
            password='123456',
            oficial=oficial,
            role='oficial'
        )

        messages.success(request, f'Oficial {oficial} criado com sucesso!')

    except Exception as e:
        messages.error(request, f'Erro ao criar oficial: {str(e)}')

    return htmx_oficiais_lista(request)


@login_required
@require_POST
def htmx_oficial_editar(request, pk):
    """Edita um oficial via HTMX."""

    if not request.user.pode_gerenciar_oficiais:
        return HttpResponse('Sem permissão', status=403)

    oficial = get_object_or_404(Oficial, pk=pk)

    try:
        oficial.nome = request.POST.get('nome', oficial.nome)
        oficial.nome_guerra = request.POST.get('nome_guerra', oficial.nome_guerra)
        oficial.posto = request.POST.get('posto', oficial.posto)
        oficial.quadro = request.POST.get('quadro', oficial.quadro)
        oficial.obm = request.POST.get('obm', oficial.obm)
        oficial.funcao = request.POST.get('funcao', oficial.funcao)
        oficial.email = request.POST.get('email', oficial.email)
        oficial.telefone = request.POST.get('telefone', oficial.telefone)
        oficial.save()

        messages.success(request, f'Oficial {oficial} atualizado!')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')

    return htmx_oficiais_lista(request)


@login_required
def htmx_oficial_dados(request, pk):
    """Retorna dados de um oficial em JSON para edição."""

    oficial = get_object_or_404(Oficial, pk=pk)

    return JsonResponse({
        'id': oficial.id,
        'cpf': oficial.cpf,
        'rg': oficial.rg,
        'nome': oficial.nome,
        'nome_guerra': oficial.nome_guerra,
        'posto': oficial.posto,
        'quadro': oficial.quadro,
        'obm': oficial.obm,
        'funcao': oficial.funcao,
        'email': oficial.email,
        'telefone': oficial.telefone,
        'ativo': oficial.ativo,
    })


@login_required
@require_POST
def htmx_oficial_excluir(request, pk):
    """Exclui um oficial via HTMX."""

    if not request.user.pode_gerenciar_oficiais:
        return HttpResponse('Sem permissão', status=403)

    oficial = get_object_or_404(Oficial, pk=pk)
    nome = str(oficial)

    try:
        oficial.delete()
        messages.success(request, f'Oficial {nome} excluído!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')

    return htmx_oficiais_lista(request)