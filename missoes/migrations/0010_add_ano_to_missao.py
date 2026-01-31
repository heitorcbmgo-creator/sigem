# Generated manually on 2026-01-31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0009_add_sicad_foto_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='missao',
            name='ano',
            field=models.IntegerField(default=2026, verbose_name='Ano'),
        ),
    ]