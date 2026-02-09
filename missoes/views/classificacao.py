"""
View para a página de Classificação de Funções.
Permite transparência sobre a avaliação de complexidade.

Suporta dois modos:
- Modo Template: Agrupa por template, mostrando funções únicas
- Modo Expandido: Mostra todas as instâncias de funções (por missão)
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Count
from collections import defaultdict

from ..models import Funcao, Missao, TemplateEstruturaMissao, TemplateFuncao


@login_required
def classificacao_funcoes(request):
    """
    Página de transparência da classificação de funções.

    Modos:
    - template: Agrupa por template (elimina duplicatas)
    - expandido: Mostra todas as instâncias (comportamento original)
    """

    # Modo de visualização (padrão: template)
    modo = request.GET.get('modo', 'template')

    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    complexidade_filtro = request.GET.get('complexidade', '')
    busca = request.GET.get('busca', '').strip()

    if modo == 'template':
        # MODO TEMPLATE: Agrupa por template de missão
        dados_agrupados = _get_dados_modo_template(tipo_filtro, complexidade_filtro, busca)
    else:
        # MODO EXPANDIDO: Mostra todas as instâncias
        dados_agrupados = _get_dados_modo_expandido(tipo_filtro, complexidade_filtro, busca)

    # Estatísticas gerais
    stats = _get_estatisticas()

    # Estatísticas de templates
    total_templates = TemplateEstruturaMissao.objects.filter(ativo=True).count()
    total_templates_funcoes = TemplateFuncao.objects.count()

    context = {
        'dados_agrupados': dados_agrupados,
        'modo': modo,
        'filtros': {
            'tipo': tipo_filtro,
            'complexidade': complexidade_filtro,
            'busca': busca,
        },
        'tipo_choices': Missao.TIPO_CHOICES,
        'complexidade_choices': Funcao.COMPLEXIDADE_CHOICES,
        'stats': {
            **stats,
            'templates': total_templates,
            'templates_funcoes': total_templates_funcoes,
        }
    }

    return render(request, 'pages/classificacao_funcoes.html', context)


def _get_dados_modo_template(tipo_filtro, complexidade_filtro, busca):
    """
    Retorna dados agrupados por template.
    Elimina duplicatas mostrando apenas funções de templates.
    """
    dados = []

    # Buscar templates ativos
    templates = TemplateEstruturaMissao.objects.filter(ativo=True).prefetch_related('funcoes_template')

    if tipo_filtro:
        templates = templates.filter(tipo=tipo_filtro)

    for template in templates:
        funcoes = template.funcoes_template.all()

        # Filtro de complexidade
        if complexidade_filtro:
            funcoes_filtradas = []
            for f in funcoes:
                if complexidade_filtro == 'BAIXA' and f.complexidade == 'BAIXA':
                    funcoes_filtradas.append(f)
                elif complexidade_filtro == 'MEDIA' and f.complexidade == 'MEDIA':
                    funcoes_filtradas.append(f)
                elif complexidade_filtro == 'ALTA' and f.complexidade == 'ALTA':
                    funcoes_filtradas.append(f)
            funcoes = funcoes_filtradas

        # Filtro de busca
        if busca:
            funcoes = [f for f in funcoes if busca.lower() in f.nome.lower() or busca.lower() in template.nome.lower()]

        if funcoes:
            # Contar instâncias (quantas missões usam este template)
            total_instancias = template.total_instancias

            dados.append({
                'tipo': template.get_tipo_display(),
                'nome': f"{template.sigla or template.nome}",
                'descricao': template.nome if template.sigla else '',
                'is_template': True,
                'total_instancias': total_instancias,
                'funcoes': funcoes,
            })

    # Buscar missões SEM template (modo híbrido)
    missoes_sem_template = Missao.objects.filter(template__isnull=True).prefetch_related('funcoes')

    if tipo_filtro:
        missoes_sem_template = missoes_sem_template.filter(tipo=tipo_filtro)

    funcoes_sem_template_agrupadas = defaultdict(list)

    for missao in missoes_sem_template:
        funcoes = missao.funcoes.all()

        # Filtro de complexidade
        if complexidade_filtro:
            funcoes = [f for f in funcoes if f.complexidade == complexidade_filtro]

        # Filtro de busca
        if busca:
            funcoes = [f for f in funcoes if busca.lower() in f.funcao.lower() or busca.lower() in missao.nome.lower()]

        for funcao in funcoes:
            key = (missao.get_tipo_display(), missao.nome_completo)
            funcoes_sem_template_agrupadas[key].append(funcao)

    # Adicionar missões sem template
    for (tipo, nome), funcoes_lista in funcoes_sem_template_agrupadas.items():
        dados.append({
            'tipo': tipo,
            'nome': nome,
            'descricao': '',
            'is_template': False,
            'total_instancias': 1,
            'funcoes': funcoes_lista,
        })

    # Ordenar por tipo e nome
    dados.sort(key=lambda x: (x['tipo'], x['nome']))

    return dados


def _get_dados_modo_expandido(tipo_filtro, complexidade_filtro, busca):
    """
    Retorna dados no modo expandido (todas as instâncias de funções).
    Comportamento original.
    """
    funcoes = Funcao.objects.select_related('missao', 'template_funcao').all()

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

    funcoes = funcoes.order_by('missao__tipo', 'missao__nome', 'funcao')

    # Agrupar por tipo de missão e depois por missão
    funcoes_agrupadas = defaultdict(lambda: defaultdict(list))

    for funcao in funcoes:
        tipo = funcao.missao.get_tipo_display()
        missao_nome = funcao.missao.nome_completo
        funcoes_agrupadas[tipo][missao_nome].append(funcao)

    # Converter para estrutura para o template
    dados = []
    for tipo, missoes in funcoes_agrupadas.items():
        for missao_nome, lista_funcoes in missoes.items():
            dados.append({
                'tipo': tipo,
                'nome': missao_nome,
                'descricao': '',
                'is_template': False,
                'total_instancias': 1,
                'funcoes': lista_funcoes,
            })

    # Ordenar por tipo e nome
    dados.sort(key=lambda x: (x['tipo'], x['nome']))

    return dados


def _get_estatisticas():
    """Retorna estatísticas gerais de funções."""
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

    return {
        'total': total_funcoes,
        **total_por_complexidade
    }
