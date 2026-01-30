# Generated manually on 2026-01-30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('missoes', '0005_remove_oficial_score'),
    ]

    operations = [
        # Deletar tabelas legadas se existirem (seguro para ambientes local e produção)
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS missoes_solicitacaomissao CASCADE;
                DROP TABLE IF EXISTS missoes_solicitacaodesignacao CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]