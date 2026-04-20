from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0027_solicitacao_numero_missao_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacao',
            name='nova_funcao',
            field=models.BooleanField(
                default=False,
                help_text='Se True, a função será criada na aprovação com base em nome_funcao e critérios',
                verbose_name='Criar nova função',
            ),
        ),
    ]
