# Generated manually on 2026-01-31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0011_make_ano_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacao',
            name='ano_missao',
            field=models.IntegerField(blank=True, default=2026, null=True, verbose_name='Ano da Missão'),
        ),
    ]