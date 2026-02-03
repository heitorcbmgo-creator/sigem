# Generated manually - Normalize local field choices

from django.db import migrations, models


def normalize_local_values(apps, schema_editor):
    """Normaliza os valores do campo local para usar as chaves corretas."""
    Missao = apps.get_model('missoes', 'Missao')
    Solicitacao = apps.get_model('missoes', 'Solicitacao')

    # Mapeamento de valores antigos para novos (chaves em maiúsculas)
    mapping = {
        # Variações de Internacional
        'internacional': 'INTERNACIONAL',
        'INTERNACIONAL': 'INTERNACIONAL',
        'Internacional': 'INTERNACIONAL',

        # Variações de Nacional
        'nacional': 'NACIONAL',
        'NACIONAL': 'NACIONAL',
        'Nacional': 'NACIONAL',

        # Variações de Estadual
        'estadual': 'ESTADUAL',
        'ESTADUAL': 'ESTADUAL',
        'Estadual': 'ESTADUAL',

        # Variações de Capital
        'capital': 'CAPITAL',
        'CAPITAL': 'CAPITAL',
        'Capital': 'CAPITAL',

        # Variações dos CRBMs
        '1_crbm': '1_CRBM',
        '1_CRBM': '1_CRBM',
        '1º CRBM': '1_CRBM',
        '1º crbm': '1_CRBM',
        '1 CRBM': '1_CRBM',

        '2_crbm': '2_CRBM',
        '2_CRBM': '2_CRBM',
        '2º CRBM': '2_CRBM',
        '2º crbm': '2_CRBM',
        '2 CRBM': '2_CRBM',

        '3_crbm': '3_CRBM',
        '3_CRBM': '3_CRBM',
        '3º CRBM': '3_CRBM',
        '3º crbm': '3_CRBM',
        '3 CRBM': '3_CRBM',

        '4_crbm': '4_CRBM',
        '4_CRBM': '4_CRBM',
        '4º CRBM': '4_CRBM',
        '4º crbm': '4_CRBM',
        '4 CRBM': '4_CRBM',

        '5_crbm': '5_CRBM',
        '5_CRBM': '5_CRBM',
        '5º CRBM': '5_CRBM',
        '5º crbm': '5_CRBM',
        '5 CRBM': '5_CRBM',

        '6_crbm': '6_CRBM',
        '6_CRBM': '6_CRBM',
        '6º CRBM': '6_CRBM',
        '6º crbm': '6_CRBM',
        '6 CRBM': '6_CRBM',

        '7_crbm': '7_CRBM',
        '7_CRBM': '7_CRBM',
        '7º CRBM': '7_CRBM',
        '7º crbm': '7_CRBM',
        '7 CRBM': '7_CRBM',

        '8_crbm': '8_CRBM',
        '8_CRBM': '8_CRBM',
        '8º CRBM': '8_CRBM',
        '8º crbm': '8_CRBM',
        '8 CRBM': '8_CRBM',

        '9_crbm': '9_CRBM',
        '9_CRBM': '9_CRBM',
        '9º CRBM': '9_CRBM',
        '9º crbm': '9_CRBM',
        '9 CRBM': '9_CRBM',
    }

    valid_values = ['INTERNACIONAL', 'NACIONAL', 'ESTADUAL', 'CAPITAL',
                    '1_CRBM', '2_CRBM', '3_CRBM', '4_CRBM', '5_CRBM',
                    '6_CRBM', '7_CRBM', '8_CRBM', '9_CRBM', '']

    # Atualizar valores na tabela Missao
    for old_value, new_value in mapping.items():
        Missao.objects.filter(local=old_value).update(local=new_value)

    # Limpar valores vazios ou inválidos em Missao
    Missao.objects.filter(local__isnull=False).exclude(
        local__in=valid_values
    ).update(local='')

    # Atualizar valores na tabela Solicitacao (campo local_missao)
    for old_value, new_value in mapping.items():
        Solicitacao.objects.filter(local_missao=old_value).update(local_missao=new_value)

    # Limpar valores vazios ou inválidos em Solicitacao
    Solicitacao.objects.filter(local_missao__isnull=False).exclude(
        local_missao__in=valid_values
    ).update(local_missao='')


def reverse_normalize(apps, schema_editor):
    """Reversão: não faz nada pois os valores normalizados são válidos."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0018_update_posto_tencel_to_tc'),
    ]

    operations = [
        # Primeiro normaliza os dados existentes
        migrations.RunPython(
            normalize_local_values,
            reverse_code=reverse_normalize
        ),
        # Depois altera o campo para usar choices e reduzir max_length
        migrations.AlterField(
            model_name='missao',
            name='local',
            field=models.CharField(
                'Local',
                max_length=20,
                blank=True,
                choices=[
                    ('INTERNACIONAL', 'Internacional'),
                    ('NACIONAL', 'Nacional'),
                    ('ESTADUAL', 'Estadual'),
                    ('CAPITAL', 'Capital'),
                    ('1_CRBM', '1º CRBM'),
                    ('2_CRBM', '2º CRBM'),
                    ('3_CRBM', '3º CRBM'),
                    ('4_CRBM', '4º CRBM'),
                    ('5_CRBM', '5º CRBM'),
                    ('6_CRBM', '6º CRBM'),
                    ('7_CRBM', '7º CRBM'),
                    ('8_CRBM', '8º CRBM'),
                    ('9_CRBM', '9º CRBM'),
                ]
            ),
        ),
    ]
