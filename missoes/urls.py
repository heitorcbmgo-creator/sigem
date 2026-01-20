"""
============================================================
🔗 SIGEM - URLs do App Missões
============================================================
"""

from django.urls import path
from . import views

urlpatterns = [
    # ============================================================
    # 🔐 AUTENTICAÇÃO
    # ============================================================
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.redirecionar_por_perfil, name='redirecionar_por_perfil'),
    
    # ============================================================
    # 📊 PÁGINAS PRINCIPAIS
    # ============================================================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('comparar/', views.comparar_oficiais, name='comparar_oficiais'),
    path('missoes/', views.missoes_dashboard, name='missoes_dashboard'),
    path('painel/', views.painel_oficial, name='painel_oficial'),
    
    # ============================================================
    # 🔧 ADMINISTRAÇÃO
    # ============================================================
    path('admin-painel/', views.admin_painel, name='admin_painel'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - OFICIAIS
    # ============================================================
    path('htmx/oficiais/lista/', views.htmx_oficiais_lista, name='htmx_oficiais_lista'),
    path('htmx/oficiais/cards/', views.htmx_oficiais_cards, name='htmx_oficiais_cards'),
    path('htmx/oficial/<int:pk>/card/', views.htmx_oficial_card, name='htmx_oficial_card'),
    path('htmx/oficial/criar/', views.htmx_oficial_criar, name='htmx_oficial_criar'),
    path('htmx/oficial/<int:pk>/editar/', views.htmx_oficial_editar, name='htmx_oficial_editar'),
    path('htmx/oficial/<int:pk>/excluir/', views.htmx_oficial_excluir, name='htmx_oficial_excluir'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - MISSÕES
    # ============================================================
    path('htmx/missoes/lista/', views.htmx_missoes_lista, name='htmx_missoes_lista'),
    path('htmx/missao/<int:pk>/organograma/', views.htmx_missao_organograma, name='htmx_missao_organograma'),
    path('htmx/missao/criar/', views.htmx_missao_criar, name='htmx_missao_criar'),
    path('htmx/missao/<int:pk>/editar/', views.htmx_missao_editar, name='htmx_missao_editar'),
    path('htmx/missao/<int:pk>/excluir/', views.htmx_missao_excluir, name='htmx_missao_excluir'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - DESIGNAÇÕES
    # ============================================================
    path('htmx/designacoes/lista/', views.htmx_designacoes_lista, name='htmx_designacoes_lista'),
    path('htmx/designacao/criar/', views.htmx_designacao_criar, name='htmx_designacao_criar'),
    path('htmx/designacao/<int:pk>/editar/', views.htmx_designacao_editar, name='htmx_designacao_editar'),
    path('htmx/designacao/<int:pk>/excluir/', views.htmx_designacao_excluir, name='htmx_designacao_excluir'),
        # Endpoint para dados JSON (edição)
    path('htmx/designacao/<int:pk>/dados/', views.htmx_designacao_dados, name='htmx_designacao_dados'),
    path('htmx/missao/<int:pk>/dados/', views.htmx_missao_dados, name='htmx_missao_dados'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - UNIDADES
    # ============================================================
    path('htmx/unidades/lista/', views.htmx_unidades_lista, name='htmx_unidades_lista'),
    path('htmx/unidade/criar/', views.htmx_unidade_criar, name='htmx_unidade_criar'),
    path('htmx/unidade/<int:pk>/editar/', views.htmx_unidade_editar, name='htmx_unidade_editar'),
    path('htmx/unidade/<int:pk>/excluir/', views.htmx_unidade_excluir, name='htmx_unidade_excluir'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - USUÁRIOS
    # ============================================================
    path('htmx/usuarios/lista/', views.htmx_usuarios_lista, name='htmx_usuarios_lista'),
    path('htmx/usuario/criar/', views.htmx_usuario_criar, name='htmx_usuario_criar'),
    path('htmx/usuario/<int:pk>/editar/', views.htmx_usuario_editar, name='htmx_usuario_editar'),
    path('htmx/usuario/<int:pk>/excluir/', views.htmx_usuario_excluir, name='htmx_usuario_excluir'),
    path('htmx/usuario/<int:pk>/reset-senha/', views.htmx_usuario_reset_senha, name='htmx_usuario_reset_senha'),
    
    # ============================================================
    # 🔄 ENDPOINTS HTMX - SOLICITAÇÕES
    # ============================================================
    path('htmx/solicitacao/criar/', views.htmx_solicitacao_criar, name='htmx_solicitacao_criar'),
    path('htmx/solicitacoes/lista/', views.htmx_solicitacoes_lista, name='htmx_solicitacoes_lista'),
    path('htmx/solicitacao/<int:pk>/avaliar/', views.htmx_solicitacao_avaliar, name='htmx_solicitacao_avaliar'),
    
    # ============================================================
    # 📥 EXPORTAÇÃO
    # ============================================================
    path('exportar/excel/<str:tipo>/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/<str:tipo>/', views.exportar_pdf, name='exportar_pdf'),
    
    # ============================================================
    # 📤 IMPORTAÇÃO EM MASSA
    # ============================================================
    path('importar/<str:tipo>/', views.importar_excel, name='importar_excel'),
]