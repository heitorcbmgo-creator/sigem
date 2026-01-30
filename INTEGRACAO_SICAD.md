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

## Próximos Passos

Quando for implementar a integração:

1. **Criar adapter/client SICAD**
   ```python
   # sicad/client.py
   class SicadClient:
       def get_oficial(self, cpf):
           # Query PostgreSQL view do SICAD
           pass
   ```

2. **Criar comando de sincronização**
   ```bash
   python manage.py sync_sicad_oficiais
   ```

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