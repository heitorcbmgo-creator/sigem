"""
============================================================
📚 EXEMPLOS DE USO - Integração SICAD
============================================================
Exemplos práticos de como usar o layer de integração
"""

from missoes.models import Oficial
from missoes.integrations.sicad_adapter import (
    SicadAdapter,
    SicadSyncHelper,
    SicadQueryBuilder
)


# ============================================================
# EXEMPLO 1: Converter Oficial SIGEM → Formato SICAD
# ============================================================
def exemplo_converter_para_sicad():
    """Converte dados de um oficial para formato SICAD."""
    # Buscar oficial no SIGEM
    oficial = Oficial.objects.get(cpf='12345678900')

    # Converter para formato SICAD
    adapter = SicadAdapter()
    dados_sicad = adapter.oficial_to_sicad(oficial)

    print('Dados no formato SICAD:')
    print(f"CPF: {dados_sicad['CPF']}")
    print(f"NOME_PESSOA: {dados_sicad['NOME_PESSOA']}")
    print(f"PATENTE: {dados_sicad['PATENTE']}")
    print(f"RG_MILITAR: {dados_sicad['RG_MILITAR']}")

    return dados_sicad


# ============================================================
# EXEMPLO 2: Importar Oficial do SICAD → SIGEM
# ============================================================
def exemplo_importar_do_sicad():
    """Importa dados de um oficial do SICAD para SIGEM."""
    # Dados vindos do SICAD (exemplo)
    dados_sicad = {
        'CPF': '98765432100',
        'NOME_PESSOA': 'João Silva Santos',
        'RG_MILITAR': '123456',
        'NOME_GUERRA': 'Silva',
        'PATENTE': 'Cap',
        'SIGLA_PATENTE': 'Cap',
        'SIGLA_QUADRO': 'QOC',
        'EMAIL': 'silva@cbm.go.gov.br',
        'ATIVO': True,
        'FOTO_ID': 'abc123',
        'FOTO_HASH': 'sha256hash...',
    }

    # Sincronizar com SIGEM
    helper = SicadSyncHelper()
    oficial, created = helper.sync_oficial_from_sicad(dados_sicad)

    if created:
        print(f'✅ Oficial {oficial.nome} criado com sucesso!')
    else:
        print(f'🔄 Oficial {oficial.nome} atualizado!')

    # Verificar se foto do SICAD foi configurada
    if oficial.foto_origem == 'SICAD':
        print(f'📷 Foto do SICAD: {oficial.foto_url}')

    return oficial


# ============================================================
# EXEMPLO 3: Comparar Dados SIGEM vs SICAD
# ============================================================
def exemplo_comparar_dados():
    """Compara dados entre SIGEM e SICAD para detectar divergências."""
    # Buscar oficial no SIGEM
    oficial = Oficial.objects.get(cpf='12345678900')

    # Dados atualizados do SICAD (exemplo)
    dados_sicad = {
        'CPF': '12345678900',
        'NOME_PESSOA': 'João Silva Santos',  # Nome pode ter mudado
        'RG_MILITAR': '123456',
        'NOME_GUERRA': 'Silva',
        'PATENTE': 'Maj',  # Promoção!
        'SIGLA_QUADRO': 'QOC',
        'EMAIL': 'novo.email@cbm.go.gov.br',  # Email mudou
    }

    # Comparar
    helper = SicadSyncHelper()
    diferencas = helper.compare_oficial(oficial, dados_sicad)

    if diferencas:
        print('⚠️  Divergências encontradas:')
        for campo, valores in diferencas.items():
            print(f"  {campo}:")
            print(f"    SIGEM: {valores['sigem']}")
            print(f"    SICAD: {valores['sicad']}")
    else:
        print('✅ Dados sincronizados!')

    return diferencas


# ============================================================
# EXEMPLO 4: Sincronização em Lote
# ============================================================
def exemplo_sincronizacao_lote():
    """Sincroniza múltiplos oficiais em lote."""
    # Lista de dados vindos do SICAD
    oficiais_sicad = [
        {
            'CPF': '11111111111',
            'NOME_PESSOA': 'Oficial Um',
            'PATENTE': 'Cap',
            # ... outros campos
        },
        {
            'CPF': '22222222222',
            'NOME_PESSOA': 'Oficial Dois',
            'PATENTE': 'Maj',
            # ... outros campos
        },
        # ... mais oficiais
    ]

    helper = SicadSyncHelper()
    resultados = {
        'criados': 0,
        'atualizados': 0,
        'erros': []
    }

    for dados in oficiais_sicad:
        try:
            oficial, created = helper.sync_oficial_from_sicad(dados)
            if created:
                resultados['criados'] += 1
            else:
                resultados['atualizados'] += 1
        except Exception as e:
            resultados['erros'].append({
                'cpf': dados.get('CPF'),
                'erro': str(e)
            })

    print(f"✅ Criados: {resultados['criados']}")
    print(f"🔄 Atualizados: {resultados['atualizados']}")
    print(f"❌ Erros: {len(resultados['erros'])}")

    return resultados


# ============================================================
# EXEMPLO 5: Consultar Views SICAD
# ============================================================
def exemplo_consultar_views():
    """Exemplos de queries nas views de integração."""
    from django.db import connection

    queries_exemplo = {
        'Todos oficiais': """
            SELECT * FROM sicad_usuario_vw
            ORDER BY "PATENTE", "NOME_PESSOA"
        """,

        'Oficiais de uma unidade': """
            SELECT * FROM sicad_usuario_funcao_vw
            WHERE "DESC_UNIDADE" LIKE '%1º GBM%'
        """,

        'Missões ativas': """
            SELECT * FROM sicad_missao_ativa_vw
            WHERE "STATUS" = 'EM_ANDAMENTO'
        """,

        'Designações de um oficial': """
            SELECT * FROM sicad_designacao_vw
            WHERE "CPF_OFICIAL" = '12345678900'
            ORDER BY "DATA_DESIGNACAO" DESC
        """,
    }

    with connection.cursor() as cursor:
        for titulo, sql in queries_exemplo.items():
            print(f"\n{titulo}:")
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            print(f"  Resultados: {len(results)}")
            if results:
                print(f"  Colunas: {', '.join(columns)}")


# ============================================================
# EXEMPLO 6: Usar com Django Admin Actions
# ============================================================
def exemplo_admin_action():
    """
    Exemplo de como criar ação no Django Admin para sincronizar com SICAD.

    Adicione em missoes/admin.py:
    """
    exemplo_code = '''
from django.contrib import admin
from missoes.integrations.sicad_adapter import SicadSyncHelper

@admin.register(Oficial)
class OficialAdmin(admin.ModelAdmin):
    actions = ['sync_with_sicad']

    def sync_with_sicad(self, request, queryset):
        """Sincroniza oficiais selecionados com SICAD."""
        helper = SicadSyncHelper()
        atualizados = 0

        for oficial in queryset:
            try:
                # Buscar dados atualizados do SICAD
                # dados_sicad = buscar_do_sicad(oficial.cpf)
                # oficial, _ = helper.sync_oficial_from_sicad(dados_sicad)
                atualizados += 1
            except Exception as e:
                self.message_user(request, f"Erro ao sincronizar {oficial}: {e}", level='error')

        self.message_user(request, f"{atualizados} oficiais sincronizados com SICAD")

    sync_with_sicad.short_description = "🔄 Sincronizar com SICAD"
    '''

    print(exemplo_code)


# ============================================================
# EXEMPLO 7: Task Celery para Sincronização Periódica
# ============================================================
def exemplo_celery_task():
    """
    Exemplo de task Celery para sincronização automática.

    Crie arquivo missoes/tasks.py:
    """
    exemplo_code = '''
from celery import shared_task
from missoes.integrations.sicad_adapter import SicadSyncHelper
from missoes.models import Oficial
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_oficiais_with_sicad():
    """
    Task que sincroniza todos os oficiais com SICAD.
    Executar diariamente.
    """
    helper = SicadSyncHelper()
    stats = {'criados': 0, 'atualizados': 0, 'erros': 0}

    # Buscar todos oficiais ativos no SICAD
    # oficiais_sicad = buscar_todos_do_sicad()

    # for dados in oficiais_sicad:
    #     try:
    #         oficial, created = helper.sync_oficial_from_sicad(dados)
    #         if created:
    #             stats['criados'] += 1
    #         else:
    #             stats['atualizados'] += 1
    #     except Exception as e:
    #         stats['erros'] += 1
    #         logger.error(f"Erro ao sincronizar {dados.get('CPF')}: {e}")

    logger.info(f"Sincronização SICAD concluída: {stats}")
    return stats

# Em celerybeat_schedule (settings.py):
# CELERY_BEAT_SCHEDULE = {
#     'sync-sicad-daily': {
#         'task': 'missoes.tasks.sync_oficiais_with_sicad',
#         'schedule': crontab(hour=2, minute=0),  # Todo dia às 2h
#     },
# }
    '''

    print(exemplo_code)


if __name__ == '__main__':
    print("📚 Exemplos de Integração SICAD")
    print("=" * 60)
    print("\nExecute as funções individualmente para ver exemplos:")
    print("  - exemplo_converter_para_sicad()")
    print("  - exemplo_importar_do_sicad()")
    print("  - exemplo_comparar_dados()")
    print("  - exemplo_sincronizacao_lote()")
    print("  - exemplo_consultar_views()")
    print("  - exemplo_admin_action()")
    print("  - exemplo_celery_task()")