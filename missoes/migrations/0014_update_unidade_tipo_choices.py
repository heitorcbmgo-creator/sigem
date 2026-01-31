# Generated manually on 2026-01-31

from django.db import migrations


def update_unidade_tipos(apps, schema_editor):
    """Atualiza registros de Unidade com tipos antigos para novos valores."""
    Unidade = apps.get_model('missoes', 'Unidade')

    # CBM (Companhia BM) → CIBM (Cia Independente BM)
    count_cbm = Unidade.objects.filter(tipo='CBM').update(tipo='CIBM')

    # SECAO (Seção) → SECAO_EMG (Seção do EMG)
    count_secao = Unidade.objects.filter(tipo='SECAO').update(tipo='SECAO_EMG')

    print(f"Migração concluída: {count_cbm} CBM → CIBM, {count_secao} SECAO → SECAO_EMG")


def reverse_update(apps, schema_editor):
    """Reverte a mudança (para rollback)."""
    Unidade = apps.get_model('missoes', 'Unidade')

    # Reverter apenas se necessário (pode haver novos registros CIBM/SECAO_EMG legítimos)
    # Esta reversão é conservadora e não afetará registros criados após a migração
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0013_rename_diretoria_to_orgao_direcao'),
    ]

    operations = [
        migrations.RunPython(update_unidade_tipos, reverse_update),
    ]