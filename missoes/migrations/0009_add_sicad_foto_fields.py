# Generated manually on 2026-01-30
# Adiciona campos para integração com fotos do SICAD

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0008_remove_solicitacaodesignacao_missoes_sol_status_2578a5_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='oficial',
            name='foto_sicad_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='ID da Foto no SICAD'),
        ),
        migrations.AddField(
            model_name='oficial',
            name='foto_sicad_hash',
            field=models.CharField(blank=True, max_length=64, verbose_name='Hash da Foto no SICAD'),
        ),
        migrations.AddField(
            model_name='oficial',
            name='foto_origem',
            field=models.CharField(
                blank=True,
                choices=[('LOCAL', 'Local'), ('SICAD', 'SICAD')],
                default='LOCAL',
                max_length=10,
                verbose_name='Origem da Foto'
            ),
        ),
    ]