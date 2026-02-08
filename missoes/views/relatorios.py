"""
============================================================
SIGEM - Relatórios Views
============================================================
Views para geração de relatórios PDF de missões e oficiais
com controle de acesso hierárquico.
"""

import os
from io import BytesIO
from datetime import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, Count, F

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

from ..models import Oficial, Missao, Designacao, Funcao


def get_oficial_responsavel(missao):
    """
    Retorna o oficial responsável pela missão (posto + nome de guerra).
    Busca o oficial com função de liderança: Comandante, Presidente, Coordenador ou Encarregado.
    """
    funcoes_lideranca = ['comandante', 'presidente', 'coordenador', 'encarregado']

    designacao = Designacao.objects.filter(
        missao=missao
    ).select_related('oficial', 'funcao').filter(
        Q(funcao__funcao__iexact='comandante') |
        Q(funcao__funcao__iexact='presidente') |
        Q(funcao__funcao__iexact='coordenador') |
        Q(funcao__funcao__iexact='encarregado')
    ).first()

    if designacao and designacao.oficial:
        nome = designacao.oficial.nome_guerra or designacao.oficial.nome
        return f"{designacao.oficial.posto} {nome}"

    return '-'


def ordenar_oficiais_hierarquicamente(oficiais_queryset):
    """
    Ordena oficiais por hierarquia militar e carga.
    Ordem: Posto > Quadro > Carga (decrescente)

    Dentro de cada posto, agrupa por quadro na seguinte ordem:
    - Cel/TC: QOC > QOS
    - Demais: QOC > QOA/Adm > QOA/Mús > QOS

    Dentro de cada grupo posto+quadro, ordena por carga (maior para menor).
    """
    # Ordem dos postos (menor número = maior precedência)
    ordem_postos = {
        'Cel': 1,
        'TC': 2,
        'Maj': 3,
        'Cap': 4,
        '1º Ten': 5,
        '2º Ten': 6,
        'Asp': 7,
    }

    # Ordem dos quadros por posto
    # Para Cel e TC: QOC, QOS
    # Para os demais: QOC, QOA/Adm, QOA/Mús, QOS
    ordem_quadros_cel_tc = {
        'QOC': 1,
        'QOS': 2,
        'QOA/Adm': 3,
        'QOA/Mús': 4,
        'QOM/Médico': 5,
        'QOM/Dentista': 6,
    }

    ordem_quadros_outros = {
        'QOC': 1,
        'QOA/Adm': 2,
        'QOA/Mús': 3,
        'QOS': 4,
        'QOM/Médico': 5,
        'QOM/Dentista': 6,
    }

    def chave_ordenacao(oficial):
        # Ordem do posto
        posto = (oficial.posto or '').strip()
        posto_ordem = ordem_postos.get(posto, 99)

        # Ordem do quadro (normalizado para evitar problemas com None/espaços)
        quadro = (oficial.quadro or '').strip()

        if posto in ['Cel', 'TC']:
            quadro_ordem = ordem_quadros_cel_tc.get(quadro, 99)
        else:
            quadro_ordem = ordem_quadros_outros.get(quadro, 99)

        # Carga negativa para ordenar do maior para menor
        # Usa getattr para garantir que funciona mesmo se carga_total não existir
        try:
            carga_valor = oficial.carga_total or 0
        except:
            carga_valor = 0
        carga_negativa = -carga_valor

        return (posto_ordem, quadro_ordem, carga_negativa)

    # Converter para lista e ordenar
    oficiais_lista = list(oficiais_queryset)
    return sorted(oficiais_lista, key=chave_ordenacao)


def get_image_with_aspect_ratio(image_path, max_width, max_height, preserve_transparency=True):
    """Redimensiona imagem mantendo proporção."""
    from PIL import Image as PILImage
    from reportlab.platypus import Image

    pil_img = PILImage.open(image_path)
    orig_width, orig_height = pil_img.size

    width_ratio = max_width / orig_width
    height_ratio = max_height / orig_height
    ratio = min(width_ratio, height_ratio)

    new_width = orig_width * ratio
    new_height = orig_height * ratio

    return Image(image_path, width=new_width, height=new_height)


@login_required
def relatorio_missoes_pdf(request):
    """
    Gera relatório PDF de missões respeitando nível hierárquico.
    - Admin/Comando-Geral: todas as missões
    - Comandante: missões com oficiais da sua OBM designados
    """

    user = request.user

    # Verificar acesso
    if not user.pode_ver_dashboard:
        return HttpResponse('Sem permissão', status=403)

    # Filtros da requisição
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    local = request.GET.get('local', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    # Query base com filtro hierárquico
    if user.is_comandante:
        obms_permitidas = user.get_obm_subordinadas()
        # Missões onde há oficiais da OBM designados
        designacoes_ids = Designacao.objects.filter(
            oficial__obm__in=obms_permitidas
        ).values_list('missao_id', flat=True).distinct()
        missoes = Missao.objects.filter(id__in=designacoes_ids)
    else:
        missoes = Missao.objects.all()

    # Aplicar filtros
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

    # Ordenar (usa a property total_designados do modelo)
    missoes = missoes.order_by('-data_inicio')

    # Gerar PDF (margens laterais reduzidas para mais espaço nas colunas)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Estilos
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#8B0000'),
        alignment=TA_LEFT,
        spaceAfter=0
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=TA_LEFT,
        spaceAfter=0
    )

    # ============================================================
    # CABEÇALHO COM LOGO
    # ============================================================
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_cbmgo.png')

    titulo_principal = Paragraph("CORPO DE BOMBEIROS MILITAR<br/>DO ESTADO DE GOIÁS", title_style)
    subtitulo = Paragraph("Sistema de Gestão de Missões - SIGEM", subtitle_style)

    if os.path.exists(logo_path):
        try:
            logo = get_image_with_aspect_ratio(logo_path, 2*cm, 2*cm, preserve_transparency=True)
            header_data = [[logo, [titulo_principal, subtitulo]]]
            header_table = Table(header_data, colWidths=[2.5*cm, 16.5*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
        except Exception:
            title_style.alignment = TA_CENTER
            subtitle_style.alignment = TA_CENTER
            header_data = [[[titulo_principal, subtitulo]]]
            header_table = Table(header_data, colWidths=[19*cm])
    else:
        title_style.alignment = TA_CENTER
        subtitle_style.alignment = TA_CENTER
        header_data = [[[titulo_principal, subtitulo]]]
        header_table = Table(header_data, colWidths=[19*cm])

    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))

    # Linha separadora
    linha_sep = Table([['']], colWidths=[19*cm], rowHeights=[2])
    linha_sep.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B0000')),
    ]))
    elements.append(linha_sep)
    elements.append(Spacer(1, 0.5*cm))

    # ============================================================
    # TÍTULO DO RELATÓRIO
    # ============================================================
    elements.append(Paragraph(
        "<b>RELATÓRIO DE MISSÕES</b>",
        ParagraphStyle('ReportTitle', fontSize=12, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor('#8B0000'))
    ))

    # Informações do filtro aplicado
    filtros_texto = []
    if tipo:
        tipo_display = dict(Missao.TIPO_CHOICES).get(tipo, tipo)
        filtros_texto.append(f"Tipo: {tipo_display}")
    if status:
        status_display = dict(Missao.STATUS_CHOICES).get(status, status)
        filtros_texto.append(f"Status: {status_display}")
    if local:
        filtros_texto.append(f"Local: {local}")
    if data_inicio:
        filtros_texto.append(f"De: {data_inicio}")
    if data_fim:
        filtros_texto.append(f"Até: {data_fim}")

    if user.is_comandante and user.oficial:
        filtros_texto.append(f"OBM: {user.oficial.obm} e subordinadas")

    if filtros_texto:
        elements.append(Paragraph(
            f"<i>Filtros: {' | '.join(filtros_texto)}</i>",
            ParagraphStyle('Filtros', fontSize=9, textColor=colors.gray, alignment=TA_CENTER, spaceAfter=10)
        ))

    elements.append(Paragraph(
        f"Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        ParagraphStyle('Data', fontSize=9, textColor=colors.gray, alignment=TA_CENTER, spaceAfter=15)
    ))

    # ============================================================
    # RESUMO
    # ============================================================
    total_missoes = missoes.count()
    total_em_andamento = missoes.filter(status='EM_ANDAMENTO').count()
    total_concluidas = missoes.filter(status='CONCLUIDA').count()
    total_planejadas = missoes.filter(status='PLANEJADA').count()

    resumo_data = [
        ['RESUMO', '', '', ''],
        ['Total', 'Em Andamento', 'Concluídas', 'Planejadas'],
        [str(total_missoes), str(total_em_andamento), str(total_concluidas), str(total_planejadas)],
    ]

    resumo_table = Table(resumo_data, colWidths=[4.75*cm, 4.75*cm, 4.75*cm, 4.75*cm])
    resumo_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f3f4f6')),
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.7*cm))

    # ============================================================
    # TABELA DE MISSÕES
    # ============================================================
    if missoes.exists():
        elements.append(Paragraph("<b>DETALHAMENTO DAS MISSÕES</b>", ParagraphStyle('Heading', fontSize=11, spaceAfter=10)))

        table_data = [['Nome', 'Tipo', 'Status', 'Desig.', 'Período', 'Oficial Responsável']]

        for m in missoes[:100]:  # Limitar a 100 registros
            periodo = ''
            if m.data_inicio:
                periodo = m.data_inicio.strftime('%d/%m/%Y')
                if m.data_fim:
                    periodo += f" a {m.data_fim.strftime('%d/%m/%Y')}"

            nome_missao = m.nome_completo
            oficial_resp = get_oficial_responsavel(m)

            table_data.append([
                nome_missao[:40] + '...' if len(nome_missao) > 40 else nome_missao,
                m.get_tipo_display(),
                m.get_status_display(),
                str(m.total_designados),
                periodo or '-',
                oficial_resp[:25] if len(oficial_resp) > 25 else oficial_resp
            ])

        # Total: 5.5 + 2 + 2 + 1.2 + 3.8 + 4.5 = 19cm (margens de 1cm cada lado)
        missoes_table = Table(table_data, colWidths=[5.5*cm, 2*cm, 2*cm, 1.2*cm, 3.8*cm, 4.5*cm])
        missoes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 0), (4, -1), 'CENTER'),  # Tipo, Status, Designados, Período
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Nome
            ('ALIGN', (5, 0), (5, -1), 'LEFT'),    # Oficial Responsável
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(missoes_table)

        if missoes.count() > 100:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(
                f"<i>Exibindo 100 de {missoes.count()} registros</i>",
                ParagraphStyle('Nota', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
            ))
    else:
        elements.append(Paragraph("Nenhuma missão encontrada com os filtros aplicados.",
                                   ParagraphStyle('Empty', fontSize=10, textColor=colors.gray, alignment=TA_CENTER)))

    # Rodapé
    elements.append(Spacer(1, 1*cm))
    if user.oficial:
        usuario_nome = f"{user.oficial.posto} {user.oficial.nome}"
    else:
        usuario_nome = user.cpf
    elements.append(Paragraph(
        f"Documento gerado pelo SIGEM em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {usuario_nome}",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
    ))

    # Gerar PDF
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_missoes_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    return response


@login_required
def relatorio_oficiais_pdf(request):
    """
    Gera relatório PDF de oficiais respeitando nível hierárquico.
    - Admin/Comando-Geral/BM3/Corregedor: todos os oficiais
    - Comandante: oficiais da sua OBM e subordinadas
    """

    user = request.user

    # Verificar acesso
    if not user.pode_ver_consultar_oficial:
        return HttpResponse('Sem permissão', status=403)

    # Filtros da requisição
    rg = request.GET.get('rg', '').strip()
    nome = request.GET.get('nome', '').strip()
    obm = request.GET.get('obm', '')
    posto = request.GET.get('posto', '')
    quadro = request.GET.get('quadro', '')

    # Query base com filtro hierárquico
    if user.is_comandante:
        obms_permitidas = user.get_obm_subordinadas()
        oficiais = Oficial.objects.filter(ativo=True, obm__in=obms_permitidas)
    else:
        oficiais = Oficial.objects.filter(ativo=True)

    # Aplicar filtros
    if rg:
        oficiais = oficiais.filter(rg__icontains=rg)
    if nome:
        oficiais = oficiais.filter(
            Q(nome__icontains=nome) | Q(nome_guerra__icontains=nome)
        )
    if obm:
        oficiais = oficiais.filter(obm=obm)
    if posto:
        oficiais = oficiais.filter(posto=posto)
    if quadro:
        oficiais = oficiais.filter(quadro=quadro)

    # Ordenar hierarquicamente (Posto > Quadro > Carga decrescente)
    oficiais_ordenados = ordenar_oficiais_hierarquicamente(oficiais)

    # Gerar PDF (margens laterais reduzidas para mais espaço nas colunas)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Estilos
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#8B0000'),
        alignment=TA_LEFT,
        spaceAfter=0
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=TA_LEFT,
        spaceAfter=0
    )

    # ============================================================
    # CABEÇALHO COM LOGO
    # ============================================================
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_cbmgo.png')

    titulo_principal = Paragraph("CORPO DE BOMBEIROS MILITAR<br/>DO ESTADO DE GOIÁS", title_style)
    subtitulo = Paragraph("Sistema de Gestão de Missões - SIGEM", subtitle_style)

    if os.path.exists(logo_path):
        try:
            logo = get_image_with_aspect_ratio(logo_path, 2*cm, 2*cm, preserve_transparency=True)
            header_data = [[logo, [titulo_principal, subtitulo]]]
            header_table = Table(header_data, colWidths=[2.5*cm, 16.5*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
        except Exception:
            title_style.alignment = TA_CENTER
            subtitle_style.alignment = TA_CENTER
            header_data = [[[titulo_principal, subtitulo]]]
            header_table = Table(header_data, colWidths=[19*cm])
    else:
        title_style.alignment = TA_CENTER
        subtitle_style.alignment = TA_CENTER
        header_data = [[[titulo_principal, subtitulo]]]
        header_table = Table(header_data, colWidths=[19*cm])

    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))

    # Linha separadora
    linha_sep = Table([['']], colWidths=[19*cm], rowHeights=[2])
    linha_sep.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B0000')),
    ]))
    elements.append(linha_sep)
    elements.append(Spacer(1, 0.5*cm))

    # ============================================================
    # TÍTULO DO RELATÓRIO
    # ============================================================
    elements.append(Paragraph(
        "<b>RELATÓRIO DE OFICIAIS</b>",
        ParagraphStyle('ReportTitle', fontSize=12, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor('#8B0000'))
    ))

    # Informações do filtro aplicado
    filtros_texto = []
    if rg:
        filtros_texto.append(f"RG: {rg}")
    if nome:
        filtros_texto.append(f"Nome: {nome}")
    if obm:
        filtros_texto.append(f"OBM: {obm}")
    if posto:
        filtros_texto.append(f"Posto: {posto}")
    if quadro:
        filtros_texto.append(f"Quadro: {quadro}")

    if user.is_comandante and user.oficial:
        if not filtros_texto:
            filtros_texto.append(f"OBM: {user.oficial.obm} e subordinadas")

    if filtros_texto:
        elements.append(Paragraph(
            f"<i>Filtros: {' | '.join(filtros_texto)}</i>",
            ParagraphStyle('Filtros', fontSize=9, textColor=colors.gray, alignment=TA_CENTER, spaceAfter=10)
        ))

    elements.append(Paragraph(
        f"Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        ParagraphStyle('Data', fontSize=9, textColor=colors.gray, alignment=TA_CENTER, spaceAfter=15)
    ))

    # ============================================================
    # RESUMO
    # ============================================================
    total_oficiais = oficiais.count()

    # Calcular oficiais com missão ativa
    oficiais_com_missao = oficiais.filter(
        designacoes__missao__status='EM_ANDAMENTO'
    ).distinct().count()

    oficiais_sem_missao = total_oficiais - oficiais_com_missao
    taxa_ocupacao = round((oficiais_com_missao / total_oficiais * 100), 1) if total_oficiais > 0 else 0

    resumo_data = [
        ['RESUMO', '', '', ''],
        ['Total', 'Em Missão', 'Disponíveis', 'Taxa Ocupação'],
        [str(total_oficiais), str(oficiais_com_missao), str(oficiais_sem_missao), f'{taxa_ocupacao}%'],
    ]

    resumo_table = Table(resumo_data, colWidths=[4.75*cm, 4.75*cm, 4.75*cm, 4.75*cm])
    resumo_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f3f4f6')),
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.7*cm))

    # ============================================================
    # TABELA DE OFICIAIS
    # ============================================================
    if oficiais_ordenados:
        elements.append(Paragraph("<b>DETALHAMENTO DOS OFICIAIS</b>", ParagraphStyle('Heading', fontSize=11, spaceAfter=10)))

        # Colunas: Posto, Quadro, RG, Nome, OBM, Missões Ativas, Carga
        table_data = [['Posto', 'Quadro', 'RG', 'Nome', 'OBM', 'Missões', 'Carga']]

        for o in oficiais_ordenados[:100]:  # Limitar a 100 registros
            missoes_ativas = o.total_missoes_ativas
            carga = o.carga_total
            nome_display = o.nome_guerra or o.nome
            if len(nome_display) > 25:
                nome_display = nome_display[:25] + '...'

            table_data.append([
                o.posto,
                o.quadro or '-',
                o.rg,
                nome_display,
                o.obm or '-',
                str(missoes_ativas),
                str(carga)
            ])

        # Total: 1.5 + 2.2 + 1.8 + 5.5 + 4 + 2 + 2 = 19cm
        oficiais_table = Table(table_data, colWidths=[1.5*cm, 2.2*cm, 1.8*cm, 5.5*cm, 4*cm, 2*cm, 2*cm])
        oficiais_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),  # Nome à esquerda
            ('ALIGN', (4, 0), (4, -1), 'LEFT'),  # OBM à esquerda
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(oficiais_table)

        if len(oficiais_ordenados) > 100:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(
                f"<i>Exibindo 100 de {len(oficiais_ordenados)} registros</i>",
                ParagraphStyle('Nota', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
            ))
    else:
        elements.append(Paragraph("Nenhum oficial encontrado com os filtros aplicados.",
                                   ParagraphStyle('Empty', fontSize=10, textColor=colors.gray, alignment=TA_CENTER)))

    # Rodapé
    elements.append(Spacer(1, 1*cm))
    if user.oficial:
        usuario_nome = f"{user.oficial.posto} {user.oficial.nome}"
    else:
        usuario_nome = user.cpf
    elements.append(Paragraph(
        f"Documento gerado pelo SIGEM em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {usuario_nome}",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
    ))

    # Gerar PDF
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_oficiais_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    return response
