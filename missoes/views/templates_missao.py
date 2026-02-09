"""
============================================================
SIGEM - Views de Missões Padronizadas
============================================================
CRUD para TemplateEstruturaMissao (Missões Padronizadas) e TemplateFuncao
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from ..models import TemplateEstruturaMissao, TemplateFuncao, Missao
from ..decorators import permissao_gerenciar_missoes


# ============================================================
# LISTAGEM DE MISSÕES PADRONIZADAS
# ============================================================
@login_required
@permissao_gerenciar_missoes
def htmx_templates_lista(request):
    """Lista todas as missões padronizadas."""
    templates = TemplateEstruturaMissao.objects.prefetch_related('funcoes_template').all()

    context = {
        'templates': templates,
        'tipo_choices': TemplateEstruturaMissao.TIPO_CHOICES,
    }
    return render(request, 'htmx/templates_lista.html', context)


# ============================================================
# CRUD DE MISSÃO PADRONIZADA
# ============================================================
@login_required
@permissao_gerenciar_missoes
@require_http_methods(["GET", "POST"])
def htmx_template_criar(request):
    """Cria uma nova missão padronizada."""
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sigla = request.POST.get('sigla', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', '')

        if not nome or not tipo:
            return HttpResponse(
                '<div class="alert alert-danger">Nome e tipo são obrigatórios.</div>',
                status=400
            )

        # Verificar duplicidade
        if TemplateEstruturaMissao.objects.filter(nome__iexact=nome).exists():
            return HttpResponse(
                '<div class="alert alert-danger">Já existe uma missão padronizada com este nome.</div>',
                status=400
            )

        template = TemplateEstruturaMissao.objects.create(
            nome=nome,
            sigla=sigla,
            descricao=descricao,
            tipo=tipo
        )

        # Retornar lista atualizada
        return htmx_templates_lista(request)

    # GET - exibe formulário
    context = {
        'tipo_choices': TemplateEstruturaMissao.TIPO_CHOICES,
    }
    return render(request, 'htmx/template_form.html', context)


@login_required
@permissao_gerenciar_missoes
@require_http_methods(["GET", "POST"])
def htmx_template_editar(request, pk):
    """Edita uma missão padronizada existente."""
    template = get_object_or_404(TemplateEstruturaMissao, pk=pk)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sigla = request.POST.get('sigla', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', '')
        ativo = request.POST.get('ativo') == 'on'

        if not nome or not tipo:
            return HttpResponse(
                '<div class="alert alert-danger">Nome e tipo são obrigatórios.</div>',
                status=400
            )

        # Verificar duplicidade (exceto o próprio)
        if TemplateEstruturaMissao.objects.filter(nome__iexact=nome).exclude(pk=pk).exists():
            return HttpResponse(
                '<div class="alert alert-danger">Já existe outra missão padronizada com este nome.</div>',
                status=400
            )

        template.nome = nome
        template.sigla = sigla
        template.descricao = descricao
        template.tipo = tipo
        template.ativo = ativo
        template.save()

        # Retornar lista atualizada
        return htmx_templates_lista(request)

    # GET - exibe formulário preenchido
    context = {
        'template': template,
        'tipo_choices': TemplateEstruturaMissao.TIPO_CHOICES,
        'editando': True,
    }
    return render(request, 'htmx/template_form.html', context)


@login_required
@permissao_gerenciar_missoes
@require_http_methods(["DELETE", "POST"])
def htmx_template_excluir(request, pk):
    """Exclui uma missão padronizada."""
    template = get_object_or_404(TemplateEstruturaMissao, pk=pk)

    # Verificar se há missões usando esta missão padronizada
    if template.instancias.exists():
        return HttpResponse(
            '<div class="alert alert-danger">Não é possível excluir: existem missões usando esta missão padronizada.</div>',
            status=400
        )

    template.delete()
    return htmx_templates_lista(request)


# ============================================================
# CRUD DE FUNÇÃO DE MISSÃO PADRONIZADA
# ============================================================
@login_required
@permissao_gerenciar_missoes
def htmx_template_funcoes_lista(request, template_pk):
    """Lista as funções de uma missão padronizada."""
    template = get_object_or_404(TemplateEstruturaMissao, pk=template_pk)
    funcoes = template.funcoes_template.all()

    context = {
        'template': template,
        'funcoes': funcoes,
    }
    return render(request, 'htmx/template_funcoes_lista.html', context)


@login_required
@permissao_gerenciar_missoes
@require_http_methods(["GET", "POST"])
def htmx_template_funcao_criar(request, template_pk):
    """Cria uma nova função na missão padronizada."""
    template = get_object_or_404(TemplateEstruturaMissao, pk=template_pk)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tde = request.POST.get('tde', 2)
        nqt = request.POST.get('nqt', 2)
        grs = request.POST.get('grs', 2)
        dec = request.POST.get('dec', 1)

        if not nome:
            return HttpResponse(
                '<div class="alert alert-danger">Nome da função é obrigatório.</div>',
                status=400
            )

        # Verificar duplicidade
        if TemplateFuncao.objects.filter(template_missao=template, nome__iexact=nome).exists():
            return HttpResponse(
                '<div class="alert alert-danger">Já existe uma função com este nome nesta missão padronizada.</div>',
                status=400
            )

        TemplateFuncao.objects.create(
            template_missao=template,
            nome=nome,
            tde=int(tde),
            nqt=int(nqt),
            grs=int(grs),
            dec=int(dec)
        )

        # Retornar lista completa de templates (form targets #tab-content)
        return htmx_templates_lista(request)

    # GET - formulário
    context = {
        'template': template,
        'nivel_choices': TemplateFuncao.NIVEL_TDE_NQT_GRS_CHOICES,
        'dec_choices': TemplateFuncao.NIVEL_DEC_CHOICES,
    }
    return render(request, 'htmx/template_funcao_form.html', context)


@login_required
@permissao_gerenciar_missoes
@require_http_methods(["GET", "POST"])
def htmx_template_funcao_editar(request, pk):
    """Edita uma função da missão padronizada."""
    funcao = get_object_or_404(TemplateFuncao, pk=pk)
    template = funcao.template_missao

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tde = request.POST.get('tde', 2)
        nqt = request.POST.get('nqt', 2)
        grs = request.POST.get('grs', 2)
        dec = request.POST.get('dec', 1)

        if not nome:
            return HttpResponse(
                '<div class="alert alert-danger">Nome da função é obrigatório.</div>',
                status=400
            )

        # Verificar duplicidade
        if TemplateFuncao.objects.filter(template_missao=template, nome__iexact=nome).exclude(pk=pk).exists():
            return HttpResponse(
                '<div class="alert alert-danger">Já existe outra função com este nome nesta missão padronizada.</div>',
                status=400
            )

        funcao.nome = nome
        funcao.tde = int(tde)
        funcao.nqt = int(nqt)
        funcao.grs = int(grs)
        funcao.dec = int(dec)
        funcao.save()

        # Retornar lista completa de templates (form targets #tab-content)
        return htmx_templates_lista(request)

    # GET - formulário preenchido
    context = {
        'template': template,
        'funcao': funcao,
        'nivel_choices': TemplateFuncao.NIVEL_TDE_NQT_GRS_CHOICES,
        'dec_choices': TemplateFuncao.NIVEL_DEC_CHOICES,
        'editando': True,
    }
    return render(request, 'htmx/template_funcao_form.html', context)


@login_required
@permissao_gerenciar_missoes
@require_http_methods(["DELETE", "POST"])
def htmx_template_funcao_excluir(request, pk):
    """Exclui uma função da missão padronizada."""
    funcao = get_object_or_404(TemplateFuncao, pk=pk)
    template_pk = funcao.template_missao.pk

    # Verificar se há funções instanciadas usando esta função padronizada
    if funcao.instancias.exists():
        return HttpResponse(
            '<div class="alert alert-danger">Não é possível excluir: existem funções de missão usando esta função padronizada.</div>',
            status=400
        )

    funcao.delete()
    return htmx_template_funcoes_lista(request, template_pk)
