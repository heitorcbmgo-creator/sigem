"""
Dashboard views - Executive dashboard, Officer comparison, and Missions dashboard
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Case, When, IntegerField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from ..models import Oficial, Missao, Designacao, Unidade, Solicitacao
from ..decorators import acesso_dashboard, acesso_comparar


# ============================================================
# 📊 DASHBOARD - VISÃO GERAL (Executivo)
# ============================================================
@login_required
@acesso_dashboard
def dashboard(request):
    """Dashboard executivo - Visão Geral para Comando-Geral e Comandantes."""

    from django.db.models import Sum, Case, When, IntegerField, F, Value
    from django.db.models.functions import TruncMonth, Coalesce
    from datetime import timedelta
    from collections import defaultdict
    import json
    import traceback

    # Em caso de erro, mostrar página de erro amigável
    try:
        hoje = timezone.now().date()
        user = request.user

        # ============================================================
        # 🔒 FILTRO POR OBM (COMANDANTE)
        # ============================================================
        is_comandante = user.is_comandante
        obms_permitidas = []
        obm_sigla = None

        if is_comandante:
            obms_permitidas = user.get_obm_subordinadas()
            if user.oficial and user.oficial.obm:
                obm_sigla = user.oficial.obm

            # QuerySets base filtrados por OBM
            oficiais_base = Oficial.objects.filter(ativo=True, obm__in=obms_permitidas)
            designacoes_base = Designacao.objects.filter(oficial__obm__in=obms_permitidas)

            # Missões onde há oficiais da OBM designados
            missoes_ids_com_oficiais_obm = designacoes_base.values_list('missao_id', flat=True).distinct()
            missoes_base = Missao.objects.filter(id__in=missoes_ids_com_oficiais_obm)
        else:
            # Visão total (admin, comando_geral)
            oficiais_base = Oficial.objects.filter(ativo=True)
            designacoes_base = Designacao.objects.all()
            missoes_base = Missao.objects.all()

        # ============================================================
        # 📌 KPIs PRINCIPAIS
        # ============================================================

        # Total de oficiais ativos
        total_oficiais = oficiais_base.count() or 0

        # Oficiais com pelo menos uma missão em andamento
        oficiais_com_missao = oficiais_base.filter(
            designacoes__missao__status='EM_ANDAMENTO'
        ).distinct().count() or 0

        # Taxa de ocupação
        taxa_ocupacao = round((oficiais_com_missao / total_oficiais * 100), 1) if total_oficiais > 0 else 0

        # Total de missões ativas (com oficiais da OBM para comandante)
        total_missoes_ativas = missoes_base.filter(status='EM_ANDAMENTO').count() or 0

        # Total de designações ativas (exclui substituídos)
        total_designacoes_ativas = designacoes_base.filter(
            missao__status='EM_ANDAMENTO'
        ).exclude(resultado='SUBSTITUIDO').count() or 0

        # Carga média por oficial (apenas os que têm missão)
        carga_media = round(total_designacoes_ativas / oficiais_com_missao, 1) if oficiais_com_missao > 0 else 0

        # Designações por complexidade (ativas, exclui substituídos)
        # Complexidade é calculada a partir da soma dos critérios da função
        from django.db.models import F
        designacoes_ativas = designacoes_base.filter(
            missao__status='EM_ANDAMENTO'
        ).exclude(resultado='SUBSTITUIDO').annotate(
            soma=F('funcao__tde') + F('funcao__nqt') + F('funcao__grs') + F('funcao__dec')
        )
        designacoes_baixa = designacoes_ativas.filter(soma__gte=4, soma__lte=6).count() or 0
        designacoes_media = designacoes_ativas.filter(soma__gte=7, soma__lte=9).count() or 0
        designacoes_alta = designacoes_ativas.filter(soma__gte=10, soma__lte=12).count() or 0

        # Carga média global de trabalho (soma da carga de todos os oficiais / total de oficiais)
        soma_carga_total = sum(oficial.carga_total for oficial in oficiais_base)
        carga_media_global = round(soma_carga_total / total_oficiais, 1) if total_oficiais > 0 else 0

        # Missões atrasadas (respeitando nível de acesso)
        # Para comandante: apenas missões onde há oficiais da sua OBM designados
        # Para admin/comando-geral: todas as missões
        missoes_atrasadas = missoes_base.filter(status='ATRASADA').count() or 0

        # Taxa de conclusão (missões concluídas / total não canceladas)
        total_missoes_nao_canceladas = missoes_base.exclude(status='CANCELADA').count() or 0
        missoes_concluidas = missoes_base.filter(status='CONCLUIDA').count() or 0
        taxa_conclusao = round((missoes_concluidas / total_missoes_nao_canceladas * 100), 1) if total_missoes_nao_canceladas > 0 else 0

        # ============================================================
        # 📈 EVOLUÇÃO MENSAL (últimos 12 meses)
        # ============================================================

        doze_meses_atras = hoje - timedelta(days=365)

        evolucao_mensal = missoes_base.filter(
            criado_em__date__gte=doze_meses_atras
        ).annotate(
            mes=TruncMonth('criado_em')
        ).values('mes').annotate(
            criadas=Count('id'),
            em_andamento=Count('id', filter=Q(status='EM_ANDAMENTO')),
            concluidas=Count('id', filter=Q(status='CONCLUIDA'))
        ).order_by('mes')

        # Formatar para Chart.js
        evolucao_labels = []
        evolucao_criadas = []
        evolucao_andamento = []
        evolucao_concluidas = []

        meses_nome = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        for item in evolucao_mensal:
            if item['mes']:
                evolucao_labels.append(f"{meses_nome[item['mes'].month - 1]}/{str(item['mes'].year)[2:]}")
                evolucao_criadas.append(item['criadas'])
                evolucao_andamento.append(item['em_andamento'])
                evolucao_concluidas.append(item['concluidas'])

        # ============================================================
        # 🥧 MISSÕES POR TIPO
        # ============================================================

        missoes_por_tipo = missoes_base.filter(
            status='EM_ANDAMENTO'
        ).values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')

        tipo_labels = []
        tipo_valores = []
        tipo_display = dict(Missao.TIPO_CHOICES)

        for item in missoes_por_tipo:
            tipo_labels.append(tipo_display.get(item['tipo'], item['tipo']))
            tipo_valores.append(item['total'])

        # ============================================================
        # 📊 CARGA POR OBM
        # ============================================================

        # Agregar dados por OBM (filtrado para comandante)
        if is_comandante:
            oficiais_por_obm = oficiais_base.exclude(
                Q(obm__isnull=True) | Q(obm='')
            ).values('obm').annotate(
                efetivo=Count('id'),
                em_missao=Count('id', filter=Q(designacoes__missao__status='EM_ANDAMENTO'), distinct=True),
            ).order_by('-efetivo')
        else:
            oficiais_por_obm = Oficial.objects.filter(ativo=True).exclude(
                Q(obm__isnull=True) | Q(obm='')
            ).values('obm').annotate(
                efetivo=Count('id'),
                em_missao=Count('id', filter=Q(designacoes__missao__status='EM_ANDAMENTO'), distinct=True),
            ).order_by('-efetivo')[:10]

        # Calcular carga por complexidade para cada OBM
        carga_por_obm = []
        for obm_data in oficiais_por_obm:
            obm_nome = obm_data['obm']

            # Contar designações por complexidade
            designacoes_obm = Designacao.objects.filter(
                oficial__obm=obm_nome,
                missao__status='EM_ANDAMENTO'
            ).annotate(
                soma=F('funcao__tde') + F('funcao__nqt') + F('funcao__grs') + F('funcao__dec')
            )
            baixa = designacoes_obm.filter(soma__gte=4, soma__lte=6).count()
            media = designacoes_obm.filter(soma__gte=7, soma__lte=9).count()
            alta = designacoes_obm.filter(soma__gte=10, soma__lte=12).count()

            carga_por_obm.append({
                'obm': obm_nome,
                'efetivo': obm_data['efetivo'],
                'em_missao': obm_data['em_missao'],
                'disponivel': obm_data['efetivo'] - obm_data['em_missao'],
                'baixa': baixa,
                'media': media,
                'alta': alta,
                'carga_total': baixa + (media * 2) + (alta * 3),
                'ocupacao': round((obm_data['em_missao'] / obm_data['efetivo'] * 100), 0) if obm_data['efetivo'] > 0 else 0
            })

        # Ordenar por carga total
        carga_por_obm.sort(key=lambda x: x['carga_total'], reverse=True)

        obm_labels = [item['obm'][:15] for item in carga_por_obm]
        obm_baixa = [item['baixa'] for item in carga_por_obm]
        obm_media = [item['media'] for item in carga_por_obm]
        obm_alta = [item['alta'] for item in carga_por_obm]

        # ============================================================
        # 🏆 TOP 10 OFICIAIS COM MAIOR CARGA
        # ============================================================

        # Para oficiais_top, calculamos a carga usando as propriedades do modelo Oficial
        oficiais_top = []
        for oficial in oficiais_base:
            total_missoes = oficial.total_missoes_ativas
            if total_missoes > 0:
                qtd_baixa = oficial.total_baixa
                qtd_media = oficial.total_media
                qtd_alta = oficial.total_alta
                carga_ponderada = oficial.carga_total

                # Contar funções de chefia
                qtd_chefia = oficial.designacoes.filter(
                    missao__status='EM_ANDAMENTO',
                    funcao__funcao__in=['COMANDANTE', 'SUBCOMANDANTE', 'COORDENADOR', 'PRESIDENTE', 'ENCARREGADO']
                ).count()

                oficiais_top.append({
                    'oficial': oficial,
                    'total_missoes': total_missoes,
                    'qtd_baixa': qtd_baixa,
                    'qtd_media': qtd_media,
                    'qtd_alta': qtd_alta,
                    'qtd_chefia': qtd_chefia,
                    'carga_ponderada': carga_ponderada,
                    # Campos adicionais para o template
                    'foto_url': oficial.foto_url,
                    'posto': oficial.posto,
                    'nome_guerra': oficial.nome_guerra,
                    'nome': oficial.nome,
                    'obm': oficial.obm,
                })

        oficiais_top = sorted(oficiais_top, key=lambda x: x['carga_ponderada'], reverse=True)[:50]

        # ============================================================
        # ⚠️ ALERTAS DO SISTEMA
        # ============================================================

        alertas = []

        # 🔴 Oficiais com sobrecarga (carga > 20)
        oficiais_sobrecarga = sum(1 for oficial in oficiais_base if oficial.carga_total > 20)

        if oficiais_sobrecarga > 0:
            alertas.append({
                'nivel': 'critico',
                'icone': 'alert-triangle',
                'mensagem': f'{oficiais_sobrecarga} oficial(is) com sobrecarga de trabalho',
                'descricao': 'Carga ponderada superior a 20 pontos'
            })

        # 🔴 OBMs com ocupação > 90%
        obms_sobrecarga = [obm for obm in carga_por_obm if obm['ocupacao'] > 90]
        if obms_sobrecarga:
            alertas.append({
                'nivel': 'critico',
                'icone': 'building',
                'mensagem': f'{len(obms_sobrecarga)} OBM(s) com ocupação acima de 90%',
                'descricao': ', '.join([o['obm'] for o in obms_sobrecarga[:3]])
            })

        # 🟠 Missões sem designação (apenas para não-comandantes)
        if not is_comandante:
            missoes_sem_designacao = Missao.objects.filter(
                status='EM_ANDAMENTO'
            ).annotate(
                total_designados=Count('designacoes')
            ).filter(total_designados=0).count()

            if missoes_sem_designacao > 0:
                alertas.append({
                    'nivel': 'alto',
                    'icone': 'users',
                    'mensagem': f'{missoes_sem_designacao} missão(ões) sem oficiais designados',
                    'descricao': 'Missões em andamento sem nenhum responsável'
                })

            # 🟠 Solicitações pendentes há mais de 7 dias
            sete_dias_atras = timezone.now() - timedelta(days=7)
            solicitacoes_atrasadas = Solicitacao.objects.filter(
                status='PENDENTE',
                criado_em__lt=sete_dias_atras
            ).count()

            if solicitacoes_atrasadas > 0:
                alertas.append({
                    'nivel': 'alto',
                    'icone': 'clock',
                    'mensagem': f'{solicitacoes_atrasadas} solicitação(ões) pendente(s) há mais de 7 dias',
                    'descricao': 'Necessitam avaliação urgente'
                })

        # 🟡 Oficiais sem missão
        oficiais_sem_missao = total_oficiais - oficiais_com_missao
        if oficiais_sem_missao > 0 and total_oficiais > 0 and (oficiais_sem_missao / total_oficiais) > 0.3:
            alertas.append({
                'nivel': 'medio',
                'icone': 'user-x',
                'mensagem': f'{oficiais_sem_missao} oficial(is) sem missão atribuída',
                'descricao': f'Representa {round((oficiais_sem_missao/total_oficiais)*100)}% do efetivo'
            })

        # 🟡 Missões próximas do prazo (7 dias)
        proxima_semana = hoje + timedelta(days=7)
        missoes_prazo = missoes_base.filter(
            status='EM_ANDAMENTO',
            data_fim__lte=proxima_semana,
            data_fim__gte=hoje
        ).count()

        if missoes_prazo > 0:
            alertas.append({
                'nivel': 'medio',
                'icone': 'calendar',
                'mensagem': f'{missoes_prazo} missão(ões) com prazo nos próximos 7 dias',
                'descricao': 'Acompanhar conclusão'
            })

        # ============================================================
        # 📋 MISSÕES RECENTES
        # ============================================================

        missoes_recentes = missoes_base.select_related().annotate(
            qtd_designados=Count('designacoes')
        ).order_by('-criado_em')[:5]

        # ============================================================
        # 👔 DISTRIBUIÇÃO POR POSTO
        # ============================================================

        distribuicao_posto = oficiais_base.values('posto').annotate(
            efetivo=Count('id'),
            em_missao=Count('id', filter=Q(designacoes__missao__status='EM_ANDAMENTO'), distinct=True),
            total_designacoes=Count('designacoes', filter=Q(designacoes__missao__status='EM_ANDAMENTO')),
            qtd_chefia=Count('designacoes', filter=Q(
                designacoes__missao__status='EM_ANDAMENTO',
                designacoes__funcao__funcao__in=['COMANDANTE', 'SUBCOMANDANTE', 'COORDENADOR', 'PRESIDENTE', 'ENCARREGADO']
            ))
        ).order_by('posto')

        posto_ordem = ['Cel', 'TC', 'Maj', 'Cap', '1º Ten', '2º Ten', 'Asp']
        posto_dict = {p['posto']: p for p in distribuicao_posto}
        distribuicao_posto_ordenada = []

        for posto in posto_ordem:
            if posto in posto_dict:
                p = posto_dict[posto]
                p['carga_media'] = round(p['total_designacoes'] / p['em_missao'], 1) if p['em_missao'] > 0 else 0
                p['perc_chefia'] = round((p['qtd_chefia'] / p['total_designacoes'] * 100), 0) if p['total_designacoes'] > 0 else 0
                distribuicao_posto_ordenada.append(p)

        posto_labels = [p['posto'] for p in distribuicao_posto_ordenada]
        posto_efetivo = [p['efetivo'] for p in distribuicao_posto_ordenada]
        posto_em_missao = [p['em_missao'] for p in distribuicao_posto_ordenada]

        # ============================================================
        # 📊 DISTRIBUIÇÃO POR QUADRO
        # ============================================================

        distribuicao_quadro = oficiais_base.values('quadro').annotate(
            efetivo=Count('id'),
            em_missao=Count('id', filter=Q(designacoes__missao__status='EM_ANDAMENTO'), distinct=True)
        ).order_by('-efetivo')

        quadro_labels = [q['quadro'] for q in distribuicao_quadro]
        quadro_valores = [q['efetivo'] for q in distribuicao_quadro]

        # ============================================================
        # 📅 DADOS PARA ABA TEMPORAL
        # ============================================================

        # Duração média por tipo de missão (apenas concluídas)
        duracao_por_tipo = []
        for tipo_code, tipo_nome in Missao.TIPO_CHOICES:
            missoes_tipo = missoes_base.filter(
                tipo=tipo_code,
                status='CONCLUIDA',
                data_inicio__isnull=False,
                data_fim__isnull=False
            )
            if missoes_tipo.exists():
                total_dias = 0
                count = 0
                for m in missoes_tipo:
                    if m.data_fim and m.data_inicio:
                        total_dias += (m.data_fim - m.data_inicio).days
                        count += 1
                if count > 0:
                    duracao_por_tipo.append({
                        'tipo': tipo_nome,
                        'duracao_media': round(total_dias / count, 0)
                    })

        duracao_por_tipo.sort(key=lambda x: x['duracao_media'], reverse=True)

        # ============================================================
        # CONTEXTO FINAL
        # ============================================================

        # Calcular percentuais de complexidade
        perc_baixa = round((designacoes_baixa / total_designacoes_ativas * 100), 0) if total_designacoes_ativas > 0 else 0
        perc_media = round((designacoes_media / total_designacoes_ativas * 100), 0) if total_designacoes_ativas > 0 else 0
        perc_alta = round((designacoes_alta / total_designacoes_ativas * 100), 0) if total_designacoes_ativas > 0 else 0

        context = {
            # Identificação do perfil
            'is_comandante': is_comandante,
            'obm_sigla': obm_sigla,

            # KPIs
            'total_oficiais': total_oficiais,
            'oficiais_com_missao': oficiais_com_missao,
            'taxa_ocupacao': taxa_ocupacao,
            'total_missoes_ativas': total_missoes_ativas,
            'total_designacoes_ativas': total_designacoes_ativas,
            'carga_media': carga_media,
            'designacoes_baixa': designacoes_baixa,
            'designacoes_media': designacoes_media,
            'designacoes_alta': designacoes_alta,
            'perc_baixa': perc_baixa,
            'perc_media': perc_media,
            'perc_alta': perc_alta,
            'carga_media_global': carga_media_global,
            'missoes_atrasadas': missoes_atrasadas,
            'taxa_conclusao': taxa_conclusao,
            'missoes_concluidas': missoes_concluidas,

            # Evolução mensal (JSON para Chart.js)
            'evolucao_labels': json.dumps(evolucao_labels),
            'evolucao_criadas': json.dumps(evolucao_criadas),
            'evolucao_andamento': json.dumps(evolucao_andamento),
            'evolucao_concluidas': json.dumps(evolucao_concluidas),

            # Missões por tipo
            'tipo_labels': json.dumps(tipo_labels),
            'tipo_valores': json.dumps(tipo_valores),

            # Carga por OBM
            'carga_por_obm': carga_por_obm,
            'obm_labels': json.dumps(obm_labels),
            'obm_baixa': json.dumps(obm_baixa),
            'obm_media': json.dumps(obm_media),
            'obm_alta': json.dumps(obm_alta),

            # Top oficiais
            'oficiais_top': oficiais_top,

            # Alertas
            'alertas': alertas,

            # Missões recentes
            'missoes_recentes': missoes_recentes,

            # Distribuição por posto
            'distribuicao_posto': distribuicao_posto_ordenada,
            'posto_labels': json.dumps(posto_labels),
            'posto_efetivo': json.dumps(posto_efetivo),
            'posto_em_missao': json.dumps(posto_em_missao),

            # Distribuição por quadro
            'distribuicao_quadro': distribuicao_quadro,
            'quadro_labels': json.dumps(quadro_labels),
            'quadro_valores': json.dumps(quadro_valores),

            # Duração por tipo
            'duracao_por_tipo': duracao_por_tipo,

            # Oficiais sem missão
            'oficiais_sem_missao': total_oficiais - oficiais_com_missao,

            # Dados para formulários de relatórios
            'tipo_labels_choices': Missao.TIPO_CHOICES,
            'obm_list': obms_permitidas if is_comandante else list(
                Oficial.objects.filter(ativo=True)
                .exclude(obm__isnull=True)
                .exclude(obm='')
                .values_list('obm', flat=True)
                .distinct()
                .order_by('obm')
            ),
        }

        return render(request, 'pages/dashboard.html', context)

    except Exception as e:
        # Em caso de erro, mostrar página com informação do erro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro no dashboard: {str(e)}\n{traceback.format_exc()}")

        # Retornar página de erro amigável com detalhes para debug
        error_context = {
            'error_message': str(e),
            'error_type': type(e).__name__,
        }
        return render(request, 'pages/dashboard_error.html', error_context)


# ============================================================
# ⚖️ COMPARAR OFICIAIS
# ============================================================
@login_required
@acesso_comparar
def comparar_oficiais(request):
    """Página para comparar carga de trabalho entre oficiais."""

    user = request.user

    # Filtros disponíveis
    postos = Oficial.POSTO_CHOICES
    quadros = Oficial.QUADRO_CHOICES

    # Para comandante, filtrar apenas OBMs permitidas
    if user.is_comandante:
        obms_permitidas = user.get_obm_subordinadas()
        obms = obms_permitidas
    else:
        obms = Oficial.objects.values_list('obm', flat=True).distinct().order_by('obm')

    context = {
        'postos': postos,
        'quadros': quadros,
        'obms': obms,
        'is_comandante': user.is_comandante,
    }

    return render(request, 'pages/comparar_oficiais.html', context)


# ============================================================
# 🗂️ DASHBOARD DE MISSÕES
# ============================================================
@login_required
def missoes_dashboard(request):
    """Dashboard completo de missões com organograma."""

    # Totalizadores por tipo (em andamento)
    tipos = ['OPERACIONAL', 'ADMINISTRATIVA', 'ENSINO', 'CORREICIONAL', 'COMISSAO', 'ACAO_SOCIAL']

    totais_por_tipo = []
    for tipo in tipos:
        total = Missao.objects.filter(tipo=tipo, status='EM_ANDAMENTO').count()
        totais_por_tipo.append({
            'tipo': tipo,
            'tipo_display': dict(Missao.TIPO_CHOICES).get(tipo, tipo),
            'total': total
        })

    # Filtros disponíveis
    status_choices = Missao.STATUS_CHOICES

    context = {
        'totais_por_tipo': totais_por_tipo,
        'status_choices': status_choices,
        'tipo_choices': Missao.TIPO_CHOICES,
    }

    return render(request, 'pages/missoes.html', context)