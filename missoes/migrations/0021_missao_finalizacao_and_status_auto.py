# Generated manually for missao finalizacao field and auto-status calculation

from django.db import migrations, models
from datetime import date


def fill_null_dates(apps, schema_editor):
    """Preenche datas nulas com valores default antes de tornar obrigatórias."""
    Missao = apps.get_model('missoes', 'Missao')
    today = date.today()

    # Missões sem data_inicio recebem hoje
    Missao.objects.filter(data_inicio__isnull=True).update(data_inicio=today)

    # Missões sem data_fim recebem data_inicio + 30 dias ou hoje + 30 dias
    for missao in Missao.objects.filter(data_fim__isnull=True):
        if missao.data_inicio:
            from datetime import timedelta
            missao.data_fim = missao.data_inicio + timedelta(days=30)
        else:
            from datetime import timedelta
            missao.data_fim = today + timedelta(days=30)
        missao.save(update_fields=['data_fim'])


def update_status_based_on_dates(apps, schema_editor):
    """Atualiza o status das missões existentes baseado nas novas regras."""
    Missao = apps.get_model('missoes', 'Missao')
    today = date.today()

    for missao in Missao.objects.all():
        # Se já tem um status de finalização, mapeia para o novo campo finalizacao
        if missao.status == 'CONCLUIDA':
            missao.finalizacao = 'CONCLUIDA'
        elif missao.status == 'CANCELADA':
            missao.finalizacao = 'CANCELADA'
        else:
            missao.finalizacao = ''

        # Recalcula o status baseado nas regras
        if missao.finalizacao == 'CONCLUIDA':
            missao.status = 'CONCLUIDA'
        elif missao.finalizacao == 'CANCELADA':
            missao.status = 'CANCELADA'
        elif missao.finalizacao == 'SUSPENSA' and missao.data_inicio and today > missao.data_inicio:
            missao.status = 'SUSPENSA'
        elif missao.data_inicio and today < missao.data_inicio:
            missao.status = 'PLANEJADA'
        elif missao.data_fim and today > missao.data_fim:
            missao.status = 'ATRASADA'
        elif missao.data_inicio and missao.data_fim and missao.data_inicio <= today <= missao.data_fim:
            missao.status = 'EM_ANDAMENTO'
        else:
            missao.status = 'PLANEJADA'

        missao.save(update_fields=['finalizacao', 'status'])


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0020_remove_solicitacaodesignacao_missoes_sol_status_2578a5_idx_and_more'),
    ]

    operations = [
        # 1. Adiciona o campo finalizacao (permite em branco)
        migrations.AddField(
            model_name='missao',
            name='finalizacao',
            field=models.CharField(
                blank=True,
                choices=[('', '-'), ('CONCLUIDA', 'Concluída'), ('CANCELADA', 'Cancelada'), ('SUSPENSA', 'Suspensa')],
                default='',
                max_length=20,
                verbose_name='Finalização'
            ),
        ),

        # 2. Atualiza choices do status para incluir ATRASADA e SUSPENSA
        migrations.AlterField(
            model_name='missao',
            name='status',
            field=models.CharField(
                choices=[
                    ('PLANEJADA', 'Planejada'),
                    ('EM_ANDAMENTO', 'Em andamento'),
                    ('ATRASADA', 'Atrasada'),
                    ('CONCLUIDA', 'Concluída'),
                    ('CANCELADA', 'Cancelada'),
                    ('SUSPENSA', 'Suspensa'),
                ],
                default='PLANEJADA',
                max_length=20,
                verbose_name='Status'
            ),
        ),

        # 3. Preenche datas nulas antes de tornar obrigatórias
        migrations.RunPython(fill_null_dates, migrations.RunPython.noop),

        # 4. Torna data_inicio obrigatória
        migrations.AlterField(
            model_name='missao',
            name='data_inicio',
            field=models.DateField(verbose_name='Data de Início'),
        ),

        # 5. Torna data_fim obrigatória
        migrations.AlterField(
            model_name='missao',
            name='data_fim',
            field=models.DateField(verbose_name='Data de Término'),
        ),

        # 6. Atualiza status das missões existentes
        migrations.RunPython(update_status_based_on_dates, migrations.RunPython.noop),

        # 7. Atualiza choices de status_missao em Solicitacao para manter consistência
        migrations.AlterField(
            model_name='solicitacao',
            name='status_missao',
            field=models.CharField(
                blank=True,
                choices=[
                    ('PLANEJADA', 'Planejada'),
                    ('EM_ANDAMENTO', 'Em andamento'),
                    ('ATRASADA', 'Atrasada'),
                    ('CONCLUIDA', 'Concluída'),
                    ('CANCELADA', 'Cancelada'),
                    ('SUSPENSA', 'Suspensa'),
                ],
                max_length=20,
                verbose_name='Status ao Solicitar'
            ),
        ),
    ]
