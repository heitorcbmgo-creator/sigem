# Generated manually on 2026-01-31

from django.db import migrations, models
import django.db.models.deletion


def migrate_designacoes_to_funcao(apps, schema_editor):
    """
    Migra designações existentes para o novo modelo com Funcao.
    Para cada designação existente:
    1. Cria uma Funcao com valores padrão (TDE=2, NQT=2, GRS=2, DEC=2)
    2. Associa a designação à nova Funcao
    """
    Designacao = apps.get_model('missoes', 'Designacao')
    Funcao = apps.get_model('missoes', 'Funcao')

    # Processar cada designação que ainda tem funcao_na_missao
    designacoes = Designacao.objects.all()

    for designacao in designacoes:
        if hasattr(designacao, 'funcao_na_missao') and designacao.funcao_na_missao:
            # Verificar se já existe uma função com o mesmo nome para esta missão
            funcao_existente = Funcao.objects.filter(
                missao=designacao.missao,
                funcao=designacao.funcao_na_missao
            ).first()

            if funcao_existente:
                # Usar função existente
                designacao.funcao = funcao_existente
            else:
                # Criar nova função com valores padrão (Média complexidade)
                nova_funcao = Funcao.objects.create(
                    missao=designacao.missao,
                    funcao=designacao.funcao_na_missao,
                    tde=2,  # Médio
                    nqt=2,  # Médio
                    grs=2,  # Médio
                    dec=2   # Médio
                )
                designacao.funcao = nova_funcao

            designacao.save()


def reverse_migration(apps, schema_editor):
    """Reverter: copiar funcao.funcao de volta para funcao_na_missao"""
    Designacao = apps.get_model('missoes', 'Designacao')

    for designacao in Designacao.objects.all():
        if designacao.funcao:
            designacao.funcao_na_missao = designacao.funcao.funcao
            if hasattr(designacao, 'complexidade'):
                designacao.complexidade = designacao.funcao.complexidade
            designacao.save()


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0015_create_funcao_model'),
    ]

    operations = [
        # PASSO 1: Remover unique_together antigo
        migrations.AlterUniqueTogether(
            name='designacao',
            unique_together=set(),
        ),

        # PASSO 2: Adicionar campo funcao (nullable temporariamente)
        migrations.AddField(
            model_name='designacao',
            name='funcao',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='designacoes',
                to='missoes.funcao',
                verbose_name='Função'
            ),
        ),

        # PASSO 3: Migrar dados existentes
        migrations.RunPython(
            migrate_designacoes_to_funcao,
            reverse_migration
        ),

        # PASSO 4: Remover campos antigos
        migrations.RemoveField(
            model_name='designacao',
            name='funcao_na_missao',
        ),
        migrations.RemoveField(
            model_name='designacao',
            name='complexidade',
        ),

        # PASSO 5: Tornar funcao obrigatório (NOT NULL)
        migrations.AlterField(
            model_name='designacao',
            name='funcao',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='designacoes',
                to='missoes.funcao',
                verbose_name='Função'
            ),
        ),

        # PASSO 6: Adicionar novo unique_together
        migrations.AlterUniqueTogether(
            name='designacao',
            unique_together={('missao', 'oficial', 'funcao')},
        ),
    ]