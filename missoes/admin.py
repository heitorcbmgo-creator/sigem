"""
============================================================
🔧 SIGEM - Configuração do Django Admin
============================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Oficial, Missao, Designacao, Unidade, Usuario, SolicitacaoDesignacao, SolicitacaoMissao


@admin.register(Oficial)
class OficialAdmin(admin.ModelAdmin):
    list_display = ['posto', 'nome_guerra', 'nome', 'quadro', 'obm', 'cpf', 'rg', 'ativo']
    list_filter = ['posto', 'quadro', 'obm', 'ativo']
    search_fields = ['nome', 'nome_guerra', 'cpf', 'rg']
    ordering = ['posto', 'nome']


@admin.register(Missao)
class MissaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'status', 'local', 'data_inicio', 'data_fim']
    list_filter = ['tipo', 'status']
    search_fields = ['nome', 'local']
    ordering = ['-data_inicio']


@admin.register(Designacao)
class DesignacaoAdmin(admin.ModelAdmin):
    list_display = ['missao', 'oficial', 'funcao_na_missao', 'complexidade', 'status']
    list_filter = ['funcao_na_missao', 'complexidade', 'status']
    search_fields = ['missao__nome', 'oficial__nome']


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sigla', 'tipo', 'comando_superior']
    list_filter = ['tipo']
    search_fields = ['nome', 'sigla']


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['cpf', 'oficial', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['cpf']
    ordering = ['cpf']
    
    fieldsets = (
        (None, {'fields': ('cpf', 'password')}),
        ('Informações', {'fields': ('oficial', 'role')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cpf', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(SolicitacaoMissao)
class SolicitacaoMissaoAdmin(admin.ModelAdmin):
    list_display = ['solicitante', 'nome_missao', 'tipo_missao', 'status', 'criado_em']
    list_filter = ['status', 'tipo_missao']
    search_fields = ['nome_missao', 'solicitante__nome']
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(SolicitacaoDesignacao)
class SolicitacaoDesignacaoAdmin(admin.ModelAdmin):
    list_display = ['solicitante', 'missao', 'funcao_na_missao', 'status', 'criado_em']
    list_filter = ['status', 'complexidade']
    search_fields = ['missao__nome', 'solicitante__nome']
    readonly_fields = ['criado_em', 'atualizado_em']


# Customização do Admin
admin.site.site_header = 'SIGEM - Administração'
admin.site.site_title = 'SIGEM Admin'
admin.site.index_title = 'Painel de Administração'