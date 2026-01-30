# Generated manually on 2026-01-30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0006_remove_legacy_solicitacao_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Solicitacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_solicitacao', models.CharField(choices=[('NOVA_MISSAO', 'Nova Missão + Designação'), ('DESIGNACAO', 'Designação em Missão Existente')], max_length=20, verbose_name='Tipo de Solicitação')),
                ('nome_missao', models.CharField(blank=True, max_length=200, verbose_name='Nome da Missão')),
                ('tipo_missao', models.CharField(blank=True, choices=[('OPERACIONAL', 'Operacional'), ('ADMINISTRATIVA', 'Administrativa'), ('ENSINO', 'Ensino'), ('CORREICIONAL', 'Correicional'), ('COMISSAO', 'Comissão'), ('ACAO_SOCIAL', 'Ação Social')], max_length=20, verbose_name='Tipo da Missão')),
                ('status_missao', models.CharField(blank=True, choices=[('PLANEJAMENTO', 'Planejamento'), ('EM_ANDAMENTO', 'Em Andamento'), ('SUSPENSA', 'Suspensa'), ('CONCLUIDA', 'Concluída'), ('CANCELADA', 'Cancelada')], default='EM_ANDAMENTO', max_length=20, verbose_name='Status da Missão')),
                ('local_missao', models.CharField(blank=True, choices=[('INTERNACIONAL', 'Internacional'), ('NACIONAL', 'Nacional'), ('ESTADUAL', 'Estadual'), ('CAPITAL', 'Capital'), ('1_CRBM', '1º CRBM'), ('2_CRBM', '2º CRBM'), ('3_CRBM', '3º CRBM'), ('4_CRBM', '4º CRBM'), ('5_CRBM', '5º CRBM'), ('6_CRBM', '6º CRBM'), ('7_CRBM', '7º CRBM'), ('8_CRBM', '8º CRBM'), ('9_CRBM', '9º CRBM')], max_length=20, verbose_name='Local da Missão')),
                ('data_inicio', models.DateField(blank=True, null=True, verbose_name='Data de Início')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Data de Término')),
                ('documento_sei_missao', models.CharField(blank=True, max_length=100, verbose_name='Nº SEI da Missão')),
                ('funcao_na_missao', models.CharField(max_length=100, verbose_name='Função na Missão')),
                ('documento_sei_designacao', models.CharField(max_length=100, verbose_name='Nº SEI/BG da Designação')),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('APROVADA', 'Aprovada'), ('RECUSADA', 'Recusada')], default='PENDENTE', max_length=20, verbose_name='Status')),
                ('complexidade', models.CharField(blank=True, choices=[('BAIXA', 'Baixa'), ('MEDIA', 'Média'), ('ALTA', 'Alta')], help_text='Definida pelo BM/3 na aprovação', max_length=20, verbose_name='Complexidade')),
                ('data_avaliacao', models.DateTimeField(blank=True, null=True, verbose_name='Data da Avaliação')),
                ('observacao_avaliador', models.TextField(blank=True, verbose_name='Observação do Avaliador')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('avaliado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitacoes_avaliadas', to='missoes.usuario', verbose_name='Avaliado por')),
                ('designacao_criada', models.ForeignKey(blank=True, help_text='Preenchido automaticamente na aprovação', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitacao_origem', to='missoes.designacao', verbose_name='Designação Criada')),
                ('missao_criada', models.ForeignKey(blank=True, help_text='Preenchido automaticamente na aprovação se tipo=NOVA_MISSAO', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitacao_origem_missao', to='missoes.missao', verbose_name='Missão Criada')),
                ('missao_existente', models.ForeignKey(blank=True, help_text='Preenchido apenas se tipo=DESIGNACAO', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes_designacao', to='missoes.missao', verbose_name='Missão Existente')),
                ('solicitante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes', to='missoes.oficial', verbose_name='Solicitante')),
            ],
            options={
                'verbose_name': 'Solicitação',
                'verbose_name_plural': 'Solicitações',
                'ordering': ['-criado_em'],
            },
        ),
        # Adicionar índices para performance
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['status'], name='missoes_sol_status_unif_idx'),
        ),
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['criado_em'], name='missoes_sol_criado_unif_idx'),
        ),
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['solicitante'], name='missoes_sol_solicit_unif_idx'),
        ),
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['tipo_solicitacao'], name='missoes_sol_tipo_idx'),
        ),
    ]