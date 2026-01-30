"""
============================================================
🔄 SIGEM - Comando de Sincronização com SICAD
============================================================
Sincroniza dados de oficiais e unidades do SICAD

Uso:
    python manage.py sync_sicad --oficiais
    python manage.py sync_sicad --unidades
    python manage.py sync_sicad --all
    python manage.py sync_sicad --cpf 12345678900
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from missoes.integrations.sicad_adapter import SicadAdapter, SicadSyncHelper, SicadQueryBuilder
from missoes.models import Oficial, Unidade
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza dados do SICAD (oficiais e unidades)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--oficiais',
            action='store_true',
            help='Sincronizar todos os oficiais',
        )
        parser.add_argument(
            '--unidades',
            action='store_true',
            help='Sincronizar todas as unidades',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizar tudo (oficiais + unidades)',
        )
        parser.add_argument(
            '--cpf',
            type=str,
            help='Sincronizar oficial específico por CPF',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sincronização sem salvar no banco',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Modo verboso com detalhes',
        )

    def handle(self, *args, **options):
        self.helper = SicadSyncHelper()
        self.query_builder = SicadQueryBuilder()
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']

        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN: Nenhuma alteração será salva'))

        try:
            if options['cpf']:
                self._sync_oficial_by_cpf(options['cpf'])
            elif options['all']:
                self._sync_all()
            elif options['oficiais']:
                self._sync_oficiais()
            elif options['unidades']:
                self._sync_unidades()
            else:
                raise CommandError('Especifique --oficiais, --unidades, --all ou --cpf')

            self.stdout.write(self.style.SUCCESS('✅ Sincronização concluída!'))

        except Exception as e:
            logger.exception('Erro na sincronização SICAD')
            raise CommandError(f'❌ Erro: {str(e)}')

    def _sync_oficial_by_cpf(self, cpf: str):
        """Sincroniza um oficial específico por CPF."""
        self.stdout.write(f'🔄 Sincronizando oficial CPF: {cpf}...')

        # Buscar dados no SICAD
        sql = self.query_builder.get_oficial_by_cpf(cpf)
        dados_sicad = self._execute_sicad_query(sql)

        if not dados_sicad:
            raise CommandError(f'Oficial com CPF {cpf} não encontrado no SICAD')

        # Sincronizar
        if not self.dry_run:
            oficial, created = self.helper.sync_oficial_from_sicad(dados_sicad[0])
            action = 'criado' if created else 'atualizado'
            self.stdout.write(
                self.style.SUCCESS(f'✅ Oficial {oficial.nome} {action}')
            )
        else:
            self.stdout.write(f'[DRY-RUN] Seria sincronizado: {dados_sicad[0].get("NOME_PESSOA")}')

    def _sync_oficiais(self):
        """Sincroniza todos os oficiais ativos do SICAD."""
        self.stdout.write('🔄 Sincronizando todos os oficiais...')

        # Buscar todos oficiais ativos no SICAD
        sql = self.query_builder.get_all_oficiais_ativos()
        dados_sicad = self._execute_sicad_query(sql)

        if not dados_sicad:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum oficial encontrado no SICAD'))
            return

        total = len(dados_sicad)
        criados = 0
        atualizados = 0
        erros = 0

        self.stdout.write(f'📊 Total de oficiais no SICAD: {total}')

        for i, dados in enumerate(dados_sicad, 1):
            try:
                if not self.dry_run:
                    oficial, created = self.helper.sync_oficial_from_sicad(dados)
                    if created:
                        criados += 1
                    else:
                        atualizados += 1

                    if self.verbose:
                        action = 'criado' if created else 'atualizado'
                        self.stdout.write(f'  [{i}/{total}] {oficial.nome} - {action}')
                else:
                    if self.verbose:
                        self.stdout.write(f'  [{i}/{total}] {dados.get("NOME_PESSOA")} - [DRY-RUN]')

            except Exception as e:
                erros += 1
                logger.error(f'Erro ao sincronizar oficial {dados.get("CPF")}: {str(e)}')
                if self.verbose:
                    self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))

        # Resumo
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 Resumo da Sincronização:')
        self.stdout.write(f'  ✅ Criados: {criados}')
        self.stdout.write(f'  🔄 Atualizados: {atualizados}')
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Erros: {erros}'))

    def _sync_unidades(self):
        """Sincroniza todas as unidades do SICAD."""
        self.stdout.write('🔄 Sincronizando unidades...')
        self.stdout.write(self.style.WARNING('⚠️  Sincronização de unidades ainda não implementada'))
        # TODO: Implementar quando necessário

    def _sync_all(self):
        """Sincroniza tudo."""
        self._sync_oficiais()
        self._sync_unidades()

    def _execute_sicad_query(self, sql: str) -> list:
        """
        Executa query no banco SICAD (ou view local).

        IMPORTANTE: Esta função deve ser adaptada para acessar
        o banco SICAD através do cliente PostgreSQL apropriado.

        Por enquanto, busca nas views locais que mapeiam SIGEM → SICAD.
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def _check_sicad_connection(self):
        """Verifica se a conexão com SICAD está disponível."""
        # TODO: Implementar verificação de conexão
        pass