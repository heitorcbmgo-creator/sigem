# Generated manually on 2026-01-31

from django.db import migrations


def rename_diretoria_to_orgao_direcao(apps, schema_editor):
    """Atualiza registros de DIRETORIA para ORGAO_DIRECAO."""
    Unidade = apps.get_model('missoes', 'Unidade')
    Unidade.objects.filter(tipo='DIRETORIA').update(tipo='ORGAO_DIRECAO')


def reverse_rename(apps, schema_editor):
    """Reverte a mudança (para rollback)."""
    Unidade = apps.get_model('missoes', 'Unidade')
    Unidade.objects.filter(tipo='ORGAO_DIRECAO').update(tipo='DIRETORIA')


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0012_add_ano_missao_to_solicitacao'),
    ]

    operations = [
        migrations.RunPython(rename_diretoria_to_orgao_direcao, reverse_rename),
    ]