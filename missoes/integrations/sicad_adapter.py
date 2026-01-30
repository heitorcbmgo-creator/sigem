"""
============================================================
🔗 SIGEM - Adaptador de Integração com SICAD
============================================================
Converte dados entre nomenclatura SIGEM ↔ SICAD
"""

from typing import Dict, Any, Optional
from datetime import datetime


class SicadAdapter:
    """
    Adaptador para conversão de dados entre SIGEM e SICAD.

    Uso:
        adapter = SicadAdapter()
        dados_sicad = adapter.oficial_to_sicad(oficial)
        oficial_obj = adapter.sicad_to_oficial(dados_sicad)
    """

    # Mapeamento de postos SIGEM → SICAD
    POSTO_MAP = {
        'Cel': 'CORONEL',
        'TC': 'TENENTE-CORONEL',
        'Maj': 'MAJOR',
        'Cap': 'CAPITAO',
        '1º Ten': 'PRIMEIRO-TENENTE',
        '2º Ten': 'SEGUNDO-TENENTE',
        'Asp': 'ASPIRANTE',
    }

    # Mapeamento reverso SICAD → SIGEM
    POSTO_MAP_REVERSE = {v: k for k, v in POSTO_MAP.items()}

    # Mapeamento de quadros
    QUADRO_MAP = {
        'QOC': 'QOABM',
        'QOS': 'QOBM',
        'QOP': 'QOPM',
    }

    QUADRO_MAP_REVERSE = {v: k for k, v in QUADRO_MAP.items()}

    @staticmethod
    def oficial_to_sicad(oficial) -> Dict[str, Any]:
        """
        Converte objeto Oficial do SIGEM para formato SICAD.

        Args:
            oficial: Instância do modelo Oficial

        Returns:
            Dicionário com dados no formato SICAD
        """
        return {
            'ID': oficial.id,
            'CPF': oficial.cpf,
            'NOME_PESSOA': oficial.nome,
            'RG_MILITAR': oficial.rg,
            'NOME_GUERRA': oficial.nome_guerra,
            'PATENTE': oficial.posto,
            'SIGLA_PATENTE': oficial.posto,
            'LOGIN': oficial.cpf,  # SIGEM usa CPF como login
            'EMAIL': oficial.email or '',
            'SIGLA_QUADRO': oficial.quadro,
            'ATIVO': oficial.ativo,
            'FOTO_ID': oficial.foto_sicad_id or '',
            'FOTO_HASH': oficial.foto_sicad_hash or '',
            'FOTO_ORIGEM': oficial.foto_origem,
        }

    @staticmethod
    def sicad_to_oficial_data(dados_sicad: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados do SICAD para formato do modelo Oficial SIGEM.

        Args:
            dados_sicad: Dicionário com dados do SICAD

        Returns:
            Dicionário pronto para criar/atualizar Oficial
        """
        return {
            'cpf': dados_sicad.get('CPF', ''),
            'nome': dados_sicad.get('NOME_PESSOA', ''),
            'rg': dados_sicad.get('RG_MILITAR', ''),
            'nome_guerra': dados_sicad.get('NOME_GUERRA', ''),
            'posto': dados_sicad.get('SIGLA_PATENTE', dados_sicad.get('PATENTE', '')),
            'quadro': dados_sicad.get('SIGLA_QUADRO', ''),
            'email': dados_sicad.get('EMAIL', ''),
            'ativo': dados_sicad.get('ATIVO', True),
            # Campos de foto do SICAD
            'foto_sicad_id': dados_sicad.get('FOTO_ID', ''),
            'foto_sicad_hash': dados_sicad.get('FOTO_HASH', ''),
            'foto_origem': 'SICAD' if dados_sicad.get('FOTO_ID') else 'LOCAL',
        }

    @staticmethod
    def unidade_to_sicad(unidade) -> Dict[str, Any]:
        """
        Converte objeto Unidade do SIGEM para formato SICAD.

        Args:
            unidade: Instância do modelo Unidade

        Returns:
            Dicionário com dados no formato SICAD
        """
        return {
            'ID': unidade.id,
            'IDUNIDADEPAI': unidade.comando_superior_id,
            'NOME': unidade.nome,
            'SIGLA': unidade.sigla,
            'TIPO': unidade.tipo,
        }

    @staticmethod
    def sicad_to_unidade_data(dados_sicad: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados do SICAD para formato do modelo Unidade SIGEM.

        Args:
            dados_sicad: Dicionário com dados do SICAD

        Returns:
            Dicionário pronto para criar/atualizar Unidade
        """
        return {
            'nome': dados_sicad.get('NOME', ''),
            'sigla': dados_sicad.get('SIGLA', ''),
            'tipo': dados_sicad.get('TIPO', 'OPERACIONAL'),
            # comando_superior precisa ser resolvido por ID
        }

    @staticmethod
    def usuario_to_sicad_funcao(usuario) -> Dict[str, Any]:
        """
        Converte objeto Usuario do SIGEM para formato UsuarioComFuncaoVW SICAD.

        Args:
            usuario: Instância do modelo Usuario

        Returns:
            Dicionário com dados no formato SICAD
        """
        oficial = usuario.oficial

        # Mapeamento de roles SIGEM → Funções SICAD
        role_map = {
            'admin': ('ADM', 'Administrador'),
            'corregedor': ('COR', 'Corregedor'),
            'bm3': ('BM3', 'BM/3'),
            'comando_geral': ('CMDG', 'Comando Geral'),
            'comandante': ('CMD', 'Comandante'),
            'oficial': ('OF', 'Oficial'),
        }

        cod_funcao, desc_funcao = role_map.get(usuario.role, ('OF', 'Oficial'))

        return {
            'ID': usuario.id,
            'CPF': usuario.cpf,
            'NOME_PESSOA': oficial.nome if oficial else '',
            'RG_MILITAR': oficial.rg if oficial else '',
            'NOME_GUERRA': oficial.nome_guerra if oficial else '',
            'PATENTE': oficial.posto if oficial else '',
            'LOGIN': usuario.cpf,
            'EMAIL': oficial.email if oficial else '',
            'COD_FUNCAO': cod_funcao,
            'DESC_FUNCAO': desc_funcao,
            'DESC_UNIDADE': oficial.obm if oficial else '',
        }


class SicadQueryBuilder:
    """
    Construtor de queries para consultar dados do SICAD via views PostgreSQL.

    Uso:
        query_builder = SicadQueryBuilder()
        sql = query_builder.get_oficial_by_cpf('12345678900')
        # Executar SQL no banco SICAD
    """

    @staticmethod
    def get_oficial_by_cpf(cpf: str) -> str:
        """Retorna SQL para buscar oficial no SICAD por CPF."""
        return f"""
            SELECT
                "ID", "CPF", "NOME_PESSOA", "RG_MILITAR",
                "NOME_GUERRA", "PATENTE", "SIGLA_PATENTE",
                "EMAIL", "SIGLA_QUADRO"
            FROM sicad.usuario_vw
            WHERE "CPF" = '{cpf}'
            LIMIT 1
        """

    @staticmethod
    def get_unidade_by_sigla(sigla: str) -> str:
        """Retorna SQL para buscar unidade no SICAD por sigla."""
        return f"""
            SELECT
                "ID", "IDUNIDADEPAI", "NOME", "SIGLA", "SITUACAO"
            FROM sicad.obm_vw
            WHERE "SIGLA" = '{sigla}'
            LIMIT 1
        """

    @staticmethod
    def get_all_oficiais_ativos() -> str:
        """Retorna SQL para buscar todos oficiais ativos no SICAD."""
        return """
            SELECT
                "ID", "CPF", "NOME_PESSOA", "RG_MILITAR",
                "NOME_GUERRA", "PATENTE", "SIGLA_PATENTE",
                "EMAIL", "SIGLA_QUADRO"
            FROM sicad.usuario_vw
            WHERE "SITUACAO" = 'ATIVO'
            ORDER BY "PATENTE", "NOME_PESSOA"
        """


class SicadSyncHelper:
    """
    Helper para sincronização de dados entre SIGEM e SICAD.

    Uso:
        helper = SicadSyncHelper()
        result = helper.sync_oficial_from_sicad(dados_sicad)
    """

    def __init__(self):
        self.adapter = SicadAdapter()

    def sync_oficial_from_sicad(self, dados_sicad: Dict[str, Any]) -> tuple:
        """
        Sincroniza oficial do SICAD para SIGEM.

        Args:
            dados_sicad: Dicionário com dados do oficial do SICAD

        Returns:
            Tupla (oficial, created) onde:
                - oficial: Instância do Oficial criado/atualizado
                - created: Boolean indicando se foi criado (True) ou atualizado (False)
        """
        from missoes.models import Oficial

        cpf = dados_sicad.get('CPF')
        if not cpf:
            raise ValueError('CPF é obrigatório para sincronização')

        # Converter dados SICAD → SIGEM
        oficial_data = self.adapter.sicad_to_oficial_data(dados_sicad)

        # Buscar ou criar oficial
        oficial, created = Oficial.objects.update_or_create(
            cpf=cpf,
            defaults=oficial_data
        )

        return oficial, created

    def sync_unidade_from_sicad(self, dados_sicad: Dict[str, Any]) -> tuple:
        """
        Sincroniza unidade do SICAD para SIGEM.

        Args:
            dados_sicad: Dicionário com dados da unidade do SICAD

        Returns:
            Tupla (unidade, created)
        """
        from missoes.models import Unidade

        sigla = dados_sicad.get('SIGLA')
        if not sigla:
            raise ValueError('SIGLA é obrigatória para sincronização')

        # Converter dados SICAD → SIGEM
        unidade_data = self.adapter.sicad_to_unidade_data(dados_sicad)

        # Buscar ou criar unidade
        unidade, created = Unidade.objects.update_or_create(
            sigla=sigla,
            defaults=unidade_data
        )

        return unidade, created

    def compare_oficial(self, oficial, dados_sicad: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara dados do oficial SIGEM com dados do SICAD.

        Args:
            oficial: Instância do Oficial SIGEM
            dados_sicad: Dicionário com dados do SICAD

        Returns:
            Dicionário com diferenças encontradas
        """
        diferencias = {}

        campos_map = {
            'nome': 'NOME_PESSOA',
            'rg': 'RG_MILITAR',
            'nome_guerra': 'NOME_GUERRA',
            'posto': 'PATENTE',
            'quadro': 'SIGLA_QUADRO',
            'email': 'EMAIL',
        }

        for campo_sigem, campo_sicad in campos_map.items():
            valor_sigem = getattr(oficial, campo_sigem, '')
            valor_sicad = dados_sicad.get(campo_sicad, '')

            if valor_sigem != valor_sicad:
                diferencias[campo_sigem] = {
                    'sigem': valor_sigem,
                    'sicad': valor_sicad,
                }

        return diferencias