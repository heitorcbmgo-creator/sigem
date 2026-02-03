"""
View para a página de Classificação de Funções.
Permite transparência sobre a avaliação de complexidade.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from collections import defaultdict

from ..models import Funcao, Missao


@login_required
def classificacao_funcoes(request):
    """
    Página de transparência da classificação de funções.
    Agrupa funções por tipo de missão e depois por missão.
    """

    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    complexidade_filtro = request.GET.get('complexidade', '')
    busca = request.GET.get('busca', '').strip()

    # Query base com select_related para otimização
    funcoes = Funcao.objects.select_related('missao').all()

    # Aplicar filtros
    if tipo_filtro:
        funcoes = funcoes.filter(missao__tipo=tipo_filtro)

    if complexidade_filtro:
        funcoes = funcoes.annotate(
            soma=F('tde') + F('nqt') + F('grs') + F('dec')
        )
        if complexidade_filtro == 'BAIXA':
            funcoes = funcoes.filter(soma__gte=4, soma__lte=6)
        elif complexidade_filtro == 'MEDIA':
            funcoes = funcoes.filter(soma__gte=7, soma__lte=9)
        elif complexidade_filtro == 'ALTA':
            funcoes = funcoes.filter(soma__gte=10, soma__lte=12)

    if busca:
        funcoes = funcoes.filter(
            Q(funcao__icontains=busca) |
            Q(missao__nome__icontains=busca)
        )

    # Ordenar por tipo de missão, depois por missão, depois por função
    funcoes = funcoes.order_by('missao__tipo', 'missao__nome', 'funcao')

    # Agrupar por tipo de missão e depois por missão
    funcoes_agrupadas = defaultdict(lambda: defaultdict(list))

    for funcao in funcoes:
        tipo = funcao.missao.get_tipo_display()
        missao_nome = funcao.missao.nome_completo
        funcoes_agrupadas[tipo][missao_nome].append(funcao)

    # Converter para estrutura serializable para o template
    dados_agrupados = []
    for tipo, missoes in funcoes_agrupadas.items():
        tipo_data = {
            'tipo': tipo,
            'missoes': []
        }
        for missao_nome, lista_funcoes in missoes.items():
            tipo_data['missoes'].append({
                'nome': missao_nome,
                'funcoes': lista_funcoes
            })
        dados_agrupados.append(tipo_data)

    # Estatísticas
    total_funcoes = Funcao.objects.count()
    total_por_complexidade = {
        'baixa': Funcao.objects.annotate(
            soma=F('tde') + F('nqt') + F('grs') + F('dec')
        ).filter(soma__gte=4, soma__lte=6).count(),
        'media': Funcao.objects.annotate(
            soma=F('tde') + F('nqt') + F('grs') + F('dec')
        ).filter(soma__gte=7, soma__lte=9).count(),
        'alta': Funcao.objects.annotate(
            soma=F('tde') + F('nqt') + F('grs') + F('dec')
        ).filter(soma__gte=10, soma__lte=12).count(),
    }

    context = {
        'dados_agrupados': dados_agrupados,
        'filtros': {
            'tipo': tipo_filtro,
            'complexidade': complexidade_filtro,
            'busca': busca,
        },
        'tipo_choices': Missao.TIPO_CHOICES,
        'complexidade_choices': Funcao.COMPLEXIDADE_CHOICES,
        'stats': {
            'total': total_funcoes,
            **total_por_complexidade
        }
    }

    return render(request, 'pages/classificacao_funcoes.html', context)
