# Generated manually on 2026-01-31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0014_update_unidade_tipo_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Funcao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('funcao', models.CharField(max_length=100, verbose_name='Função')),
                ('tde', models.IntegerField(
                    choices=[(1, 'Baixo'), (2, 'Médio'), (3, 'Alto')],
                    default=2,
                    verbose_name='TDE (Tempo de Dedicação Exigido)'
                )),
                ('nqt', models.IntegerField(
                    choices=[(1, 'Baixo'), (2, 'Médio'), (3, 'Alto')],
                    default=2,
                    verbose_name='NQT (Nível de Qualificação Técnica Exigido)'
                )),
                ('grs', models.IntegerField(
                    choices=[(1, 'Baixo'), (2, 'Médio'), (3, 'Alto')],
                    default=2,
                    verbose_name='GRS (Grau de Responsabilidade Suportado)'
                )),
                ('dec', models.IntegerField(
                    choices=[(1, 'Pequeno'), (2, 'Médio'), (3, 'Grande')],
                    default=2,
                    verbose_name='DEC (Dimensão do Efetivo Comandado)'
                )),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('missao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='funcoes',
                    to='missoes.missao',
                    verbose_name='Missão'
                )),
            ],
            options={
                'verbose_name': 'Função',
                'verbose_name_plural': 'Funções',
                'ordering': ['missao__nome', 'funcao'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='funcao',
            unique_together={('missao', 'funcao')},
        ),
    ]