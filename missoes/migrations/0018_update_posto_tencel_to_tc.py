# Generated manually - Update posto from 'Ten Cel' to 'TC'

from django.db import migrations, models


def update_posto_ten_cel_to_tc(apps, schema_editor):
    """Atualiza todos os registros com posto 'Ten Cel' para 'TC'."""
    Oficial = apps.get_model('missoes', 'Oficial')
    # Atualiza oficiais
    Oficial.objects.filter(posto='Ten Cel').update(posto='TC')


def reverse_posto_tc_to_ten_cel(apps, schema_editor):
    """Reverte 'TC' para 'Ten Cel'."""
    Oficial = apps.get_model('missoes', 'Oficial')
    Oficial.objects.filter(posto='TC').update(posto='Ten Cel')


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0017_remove_solicitacao_complexidade_and_more'),
    ]

    operations = [
        # Data migration: atualizar registros existentes
        migrations.RunPython(
            update_posto_ten_cel_to_tc,
            reverse_code=reverse_posto_tc_to_ten_cel
        ),
        # Schema migration: atualizar as choices do campo posto
        migrations.AlterField(
            model_name='oficial',
            name='posto',
            field=models.CharField(
                'Posto',
                max_length=20,
                choices=[
                    ('Cel', 'Coronel'),
                    ('TC', 'Tenente-Coronel'),
                    ('Maj', 'Major'),
                    ('Cap', 'Capitão'),
                    ('1º Ten', 'Primeiro-Tenente'),
                    ('2º Ten', 'Segundo-Tenente'),
                    ('Asp', 'Aspirante'),
                ]
            ),
        ),
    ]
