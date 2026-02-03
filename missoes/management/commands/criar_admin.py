"""
Comando para criar superusuário automaticamente no deploy.
Usa variáveis de ambiente para definir as credenciais.
"""

import os
from django.core.management.base import BaseCommand
from missoes.models import Usuario


class Command(BaseCommand):
    help = 'Cria um superusuário automaticamente se não existir'

    def handle(self, *args, **options):
        # Pegar credenciais das variáveis de ambiente ou usar padrão
        cpf = os.environ.get('ADMIN_CPF', '12345678901')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        # Verificar se já existe
        if Usuario.objects.filter(cpf=cpf).exists():
            self.stdout.write(
                self.style.WARNING(f'Usuário admin com CPF {cpf} já existe.')
            )
            return
        
        # Criar superusuário
        user = Usuario.objects.create_superuser(
            cpf=cpf,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superusuário criado com sucesso!')
        )
        self.stdout.write(f'  CPF: {cpf}')
        self.stdout.write(f'  Senha: {password}')
        self.stdout.write(
            self.style.WARNING('⚠️  IMPORTANTE: Troque a senha após o primeiro login!')
        )
