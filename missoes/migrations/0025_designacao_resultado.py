# Generated manually for adding resultado field to Designacao

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0024_merge_20260205_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='designacao',
            name='resultado',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', '-'),
                    ('CUMPRIDA', 'Cumprida'),
                    ('NAO_CUMPRIDA', 'Não cumprida'),
                    ('SUBSTITUIDO', 'Substituído(a)'),
                ],
                default='',
                help_text='Preenchido apenas pelo administrador após conclusão da missão',
                max_length=20,
                verbose_name='Resultado'
            ),
        ),
    ]
