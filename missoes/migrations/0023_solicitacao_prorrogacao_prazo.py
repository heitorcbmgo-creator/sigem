# Generated manually for prorrogacao de prazo solicitation type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0022_remove_solicitacaodesignacao_missoes_sol_status_2578a5_idx_and_more'),
    ]

    operations = [
        # Adiciona o campo nova_data_fim para solicitações de prorrogação
        migrations.AddField(
            model_name='solicitacao',
            name='nova_data_fim',
            field=models.DateField(
                blank=True,
                help_text='Preenchido apenas se tipo=PRORROGACAO_PRAZO',
                null=True,
                verbose_name='Nova Data de Término'
            ),
        ),

        # Atualiza choices do tipo_solicitacao para incluir PRORROGACAO_PRAZO
        migrations.AlterField(
            model_name='solicitacao',
            name='tipo_solicitacao',
            field=models.CharField(
                choices=[
                    ('NOVA_MISSAO', 'Nova Missão + Designação'),
                    ('DESIGNACAO', 'Designação em Missão Existente'),
                    ('PRORROGACAO_PRAZO', 'Prorrogação de Prazo'),
                ],
                max_length=20,
                verbose_name='Tipo de Solicitação'
            ),
        ),
    ]
