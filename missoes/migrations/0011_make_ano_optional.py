# Generated manually on 2026-01-31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0010_add_ano_to_missao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='missao',
            name='ano',
            field=models.IntegerField(blank=True, default=2026, null=True, verbose_name='Ano'),
        ),
    ]