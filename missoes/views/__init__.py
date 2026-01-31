"""
============================================================
SIGEM - Views Module
============================================================
Organized by feature domain for better maintainability.

This module exports all views from the organized submodules.
The refactored structure maintains 100% compatibility with the
original monolithic views.py file.
"""

# Authentication
from .auth import login_view, logout_view, redirecionar_por_perfil

# Dashboards
from .dashboards import dashboard, comparar_oficiais, missoes_dashboard

# Oficiais
from .oficiais import (
    consultar_oficial, painel_oficial,
    htmx_buscar_oficiais, htmx_oficiais_lista, htmx_oficiais_selecao,
    htmx_oficiais_cards, htmx_oficial_card, htmx_oficial_dados,
    htmx_oficial_criar, htmx_oficial_editar, htmx_oficial_excluir
)

# Missões
from .missoes import (
    htmx_missoes_lista, htmx_missoes_tabela, htmx_missao_organograma,
    htmx_missao_criar, htmx_missao_editar, htmx_missao_dados, htmx_missao_excluir
)

# Designações
from .designacoes import (
    htmx_designacoes_lista, htmx_designacao_criar, htmx_designacao_editar,
    htmx_designacao_dados, htmx_designacao_excluir
)

# Funções
from .funcoes import (
    htmx_funcoes_tabela, htmx_funcao_criar, htmx_funcao_editar,
    htmx_funcao_dados, htmx_funcao_excluir, htmx_buscar_funcoes_por_missao
)

# Unidades
from .unidades import (
    htmx_unidades_lista, htmx_unidade_criar,
    htmx_unidade_editar, htmx_unidade_excluir
)

# Usuários
from .usuarios import (
    htmx_usuarios_lista, htmx_usuario_criar, htmx_usuario_editar,
    htmx_usuario_excluir, htmx_usuario_reset_senha
)

# Solicitações (Modern System)
from .solicitacoes import (
    minhas_solicitacoes, htmx_solicitacao_criar, htmx_buscar_missoes_disponiveis,
    htmx_solicitacoes_unificadas_lista, htmx_solicitacao_dados,
    htmx_solicitacao_editar, htmx_solicitacao_aprovar, htmx_solicitacao_recusar,
    htmx_solicitacoes_validacao, htmx_solicitacao_quick_approve,
    htmx_solicitacao_batch_approve, htmx_solicitacao_batch_reject,
    htmx_solicitacao_detalhes_modal
)

# Admin
from .admin import admin_painel

# Exports/Imports
from .exports import (
    exportar_excel, exportar_pdf, importar_excel, gerar_modelo_importacao
)

# Explicit __all__ for clarity (61 functions total)
__all__ = [
    # Auth (3)
    'login_view', 'logout_view', 'redirecionar_por_perfil',
    # Dashboards (3)
    'dashboard', 'comparar_oficiais', 'missoes_dashboard',
    # Oficiais (11)
    'consultar_oficial', 'painel_oficial', 'htmx_buscar_oficiais',
    'htmx_oficiais_lista', 'htmx_oficiais_selecao', 'htmx_oficiais_cards',
    'htmx_oficial_card', 'htmx_oficial_dados', 'htmx_oficial_criar',
    'htmx_oficial_editar', 'htmx_oficial_excluir',
    # Missões (7)
    'htmx_missoes_lista', 'htmx_missoes_tabela', 'htmx_missao_organograma',
    'htmx_missao_criar', 'htmx_missao_editar', 'htmx_missao_dados',
    'htmx_missao_excluir',
    # Designações (5)
    'htmx_designacoes_lista', 'htmx_designacao_criar', 'htmx_designacao_editar',
    'htmx_designacao_dados', 'htmx_designacao_excluir',
    # Funções (6)
    'htmx_funcoes_tabela', 'htmx_funcao_criar', 'htmx_funcao_editar',
    'htmx_funcao_dados', 'htmx_funcao_excluir', 'htmx_buscar_funcoes_por_missao',
    # Unidades (4)
    'htmx_unidades_lista', 'htmx_unidade_criar', 'htmx_unidade_editar',
    'htmx_unidade_excluir',
    # Usuários (5)
    'htmx_usuarios_lista', 'htmx_usuario_criar', 'htmx_usuario_editar',
    'htmx_usuario_excluir', 'htmx_usuario_reset_senha',
    # Solicitações (13)
    'minhas_solicitacoes', 'htmx_solicitacao_criar', 'htmx_buscar_missoes_disponiveis',
    'htmx_solicitacoes_unificadas_lista', 'htmx_solicitacao_dados',
    'htmx_solicitacao_editar', 'htmx_solicitacao_aprovar', 'htmx_solicitacao_recusar',
    'htmx_solicitacoes_validacao', 'htmx_solicitacao_quick_approve',
    'htmx_solicitacao_batch_approve', 'htmx_solicitacao_batch_reject',
    'htmx_solicitacao_detalhes_modal',
    # Admin (1)
    'admin_painel',
    # Exports (4)
    'exportar_excel', 'exportar_pdf', 'importar_excel', 'gerar_modelo_importacao',
]