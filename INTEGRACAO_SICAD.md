# Integração SIGEM ↔ SICAD

## Visão Geral

Este documento descreve como o SIGEM está preparado para integração futura com o sistema SICAD (Oracle) para sincronização de dados de oficiais e fotos.

## Status Atual

### ✅ Preparações Implementadas

1. **Campos de Foto do SICAD** (modelo `Oficial`)
   - `foto_sicad_id`: ID do arquivo no filesystem do SICAD
   - `foto_sicad_hash`: Hash SHA do arquivo
   - `foto_origem`: 'LOCAL' ou 'SICAD' para determinar origem

2. **Property `foto_url` Atualizada**
   - Prioriza fotos do SICAD quando disponíveis
   - Fallback automático para fotos locais
   - Imagem padrão se nenhuma foto disponível

3. **Configuração**
   - `SICAD_FILESYSTEM_URL` em settings.py
   - Configurável via variável de ambiente

## Mapeamento de Dados

### Oficial (SIGEM) ↔ UsuarioVW (SICAD)

| SIGEM | SICAD | Observações |
|-------|-------|-------------|
| `cpf` | `CPF` | Chave primária para matching |
| `nome` | `NOME_PESSOA` | Nome completo |
| `nome_guerra` | `NOME_GUERRA` | Nome de guerra |
| `rg` | `RG_MILITAR` | RG Militar |
| `posto` | `PATENTE` ou `SIGLA_PATENTE` | Posto/Patente |
| `quadro` | `SIGLA_QUADRO` | Quadro (QOC, QOS, etc) |
| `email` | `EMAIL` | ✅ Já existe no SIGEM |
| - | `LOGIN` | ⚠️ Não usado (SIGEM usa CPF) |

### Unidade (SIGEM) ↔ ObmVw (SICAD)

| SIGEM | SICAD | Observações |
|-------|-------|-------------|
| `nome` | `NOME` | Nome da unidade |
| `sigla` | `SIGLA` | Sigla da unidade |
| `comando_superior` | `IDUNIDADEPAI` | FK para unidade pai |
| - | `SITUACAO` | ⚠️ Pode ser adicionado futuro |
| - | Endereços completos | ⚠️ Pode ser adicionado no futuro |

## Como Integrar Fotos do SICAD

### 1. Configurar URL do Filesystem

No arquivo `.env` ou variáveis de ambiente do Render:

```bash
SICAD_FILESYSTEM_URL=https://sicad.seguranca.go.gov.br/filesystem/fotos
```

### 2. Sincronizar Dados de Fotos

Quando importar ou sincronizar oficiais do SICAD:

```python
from missoes.models import Oficial

# Ao criar/atualizar oficial com dados do SICAD
oficial = Oficial.objects.get(cpf=cpf_do_sicad)
oficial.foto_sicad_id = dados_sicad['FOTO_ID']
oficial.foto_sicad_hash = dados_sicad['FOTO_HASH']
oficial.foto_origem = 'SICAD'
oficial.save()

# A property foto_url agora retornará:
# https://sicad.seguranca.go.gov.br/filesystem/fotos/{id}/{hash}
```

### 3. Uso nos Templates

Nenhuma mudança necessária nos templates! A property `foto_url` já funciona:

```django
<img src="{{ oficial.foto_url }}" alt="{{ oficial.nome }}">
```

## Estratégia de Sincronização Futura

### Opção A: Sincronização Manual
- Comando Django para importar dados do SICAD
- Executado sob demanda pelo administrador

### Opção B: Sincronização Periódica
- Celery task que roda diariamente
- Sincroniza dados alterados no SICAD

### Opção C: API em Tempo Real
- Integração via API REST com SICAD
- Dados sempre atualizados

## Layer de Integração Implementado

### ✅ O que foi criado:

1. **Views SQL** ([missoes/sql/create_sicad_views.sql](missoes/sql/create_sicad_views.sql))
   - `sicad_usuario_vw` - Oficiais com nomenclatura SICAD
   - `sicad_obm_vw` - Unidades com nomenclatura SICAD
   - `sicad_usuario_funcao_vw` - Usuários + Funções
   - `sicad_designacao_vw` - Designações/Escalas
   - `sicad_missao_ativa_vw` - Missões ativas

2. **Adaptadores Python** ([missoes/integrations/sicad_adapter.py](missoes/integrations/sicad_adapter.py))
   - `SicadAdapter` - Conversão de dados SIGEM ↔ SICAD
   - `SicadQueryBuilder` - Construtor de queries SQL
   - `SicadSyncHelper` - Helper de sincronização

3. **Comando Django** ([missoes/management/commands/sync_sicad.py](missoes/management/commands/sync_sicad.py))
   ```bash
   # Sincronizar todos os oficiais
   python manage.py sync_sicad --oficiais

   # Sincronizar oficial específico
   python manage.py sync_sicad --cpf 12345678900

   # Modo dry-run (testar sem salvar)
   python manage.py sync_sicad --oficiais --dry-run

   # Sincronizar tudo
   python manage.py sync_sicad --all
   ```

## Como Usar o Layer de Integração

### 1. Criar as Views SQL

Execute o script SQL no banco de dados:

```bash
psql -U usuario -d sigem < missoes/sql/create_sicad_views.sql
```

Ou via Django:

```bash
python manage.py dbshell < missoes/sql/create_sicad_views.sql
```

### 2. Usar Adaptadores em Código

```python
from missoes.integrations.sicad_adapter import SicadAdapter, SicadSyncHelper

# Converter dados
adapter = SicadAdapter()
dados_sicad = adapter.oficial_to_sicad(oficial)

# Sincronizar do SICAD
helper = SicadSyncHelper()
oficial, created = helper.sync_oficial_from_sicad(dados_do_sicad)

# Comparar diferenças
diferencas = helper.compare_oficial(oficial, dados_do_sicad)
```

### 3. Consultar Views

As views podem ser consultadas diretamente:

```sql
-- Ver todos os oficiais no formato SICAD
SELECT * FROM sicad_usuario_vw;

-- Ver unidades no formato SICAD
SELECT * FROM sicad_obm_vw;

-- Ver designações ativas
SELECT * FROM sicad_designacao_vw WHERE "STATUS" = 'ATIVA';
```

## Próximos Passos

Quando for implementar a integração:

1. **Configurar conexão com banco SICAD**
   - Adicionar database router para SICAD
   - Configurar credenciais de acesso

2. **Adaptar comando sync_sicad**
   - Modificar `_execute_sicad_query()` para acessar banco SICAD
   - Implementar sincronização de unidades

3. **Adicionar campos adicionais se necessário**
   - LOGIN do SICAD (se precisar)
   - Endereços completos das unidades

4. **Criar tabelas de log/auditoria**
   - Registrar sincronizações
   - Detectar conflitos

## Questões a Resolver

- [ ] Como tratar conflitos entre dados locais e SICAD?
- [ ] Quais dados têm precedência (SICAD ou SIGEM)?
- [ ] Como sincronizar unidades que não existem no SICAD?
- [ ] Período de cache de fotos?
- [ ] CDN para fotos do SICAD?

## Contato

Para dúvidas sobre integração SICAD, consultar:
- Equipe de Infraestrutura SSP-GO
- Documentação do cliente PostgreSQL do SICAD