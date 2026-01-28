-- ============================================================
-- SIGEM - Script de Migração para Tabela Solicitação Unificada
-- Executar no Neon PostgreSQL
-- ============================================================

-- Criar tabela de solicitações unificada
CREATE TABLE IF NOT EXISTS missoes_solicitacao (
    id SERIAL PRIMARY KEY,
    tipo_solicitacao VARCHAR(20) NOT NULL,
    solicitante_id INTEGER NOT NULL REFERENCES missoes_oficial(id) ON DELETE CASCADE,
    
    -- Campos de MISSÃO (para tipo NOVA_MISSAO)
    nome_missao VARCHAR(200) DEFAULT '',
    tipo_missao VARCHAR(20) DEFAULT '',
    status_missao VARCHAR(20) DEFAULT 'EM_ANDAMENTO',
    local_missao VARCHAR(20) DEFAULT '',
    data_inicio DATE NULL,
    data_fim DATE NULL,
    documento_sei_missao VARCHAR(100) DEFAULT '',
    
    -- Campos de DESIGNAÇÃO
    missao_existente_id INTEGER NULL REFERENCES missoes_missao(id) ON DELETE CASCADE,
    funcao_na_missao VARCHAR(100) NOT NULL,
    documento_sei_designacao VARCHAR(100) NOT NULL,
    
    -- Controle
    status VARCHAR(20) DEFAULT 'PENDENTE',
    complexidade VARCHAR(20) DEFAULT '',
    avaliado_por_id INTEGER NULL REFERENCES missoes_usuario(id) ON DELETE SET NULL,
    data_avaliacao TIMESTAMP NULL,
    observacao_avaliador TEXT DEFAULT '',
    
    -- Resultados
    missao_criada_id INTEGER NULL REFERENCES missoes_missao(id) ON DELETE SET NULL,
    designacao_criada_id INTEGER NULL REFERENCES missoes_designacao(id) ON DELETE SET NULL,
    
    -- Timestamps
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_solicitacao_solicitante ON missoes_solicitacao(solicitante_id);
CREATE INDEX IF NOT EXISTS idx_solicitacao_status ON missoes_solicitacao(status);
CREATE INDEX IF NOT EXISTS idx_solicitacao_tipo ON missoes_solicitacao(tipo_solicitacao);
CREATE INDEX IF NOT EXISTS idx_solicitacao_criado_em ON missoes_solicitacao(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_solicitacao_missao_existente ON missoes_solicitacao(missao_existente_id);

-- Comentários
COMMENT ON TABLE missoes_solicitacao IS 'Tabela unificada de solicitações de missões e designações';
COMMENT ON COLUMN missoes_solicitacao.tipo_solicitacao IS 'NOVA_MISSAO ou DESIGNACAO';
COMMENT ON COLUMN missoes_solicitacao.complexidade IS 'Definida pelo BM/3 na aprovação: BAIXA, MEDIA, ALTA';

-- ============================================================
-- OPCIONAL: Migrar dados das tabelas antigas (se existirem)
-- ============================================================

-- Migrar solicitações de missão antigas
-- INSERT INTO missoes_solicitacao (
--     tipo_solicitacao, solicitante_id, nome_missao, tipo_missao, status_missao,
--     local_missao, data_inicio, data_fim, documento_sei_missao,
--     funcao_na_missao, documento_sei_designacao, status, avaliado_por_id,
--     data_avaliacao, observacao_avaliador, missao_criada_id, criado_em, atualizado_em
-- )
-- SELECT 
--     'NOVA_MISSAO', solicitante_id, nome_missao, tipo_missao, status_missao,
--     local, data_inicio, data_fim, documento_sei,
--     'Solicitante', documento_sei, status, avaliado_por_id,
--     data_avaliacao, observacao_avaliador, missao_criada_id, criado_em, atualizado_em
-- FROM missoes_solicitacaomissao;

-- Migrar solicitações de designação antigas
-- INSERT INTO missoes_solicitacao (
--     tipo_solicitacao, solicitante_id, missao_existente_id,
--     funcao_na_missao, documento_sei_designacao, status, complexidade,
--     avaliado_por_id, data_avaliacao, observacao_avaliador,
--     designacao_criada_id, criado_em, atualizado_em
-- )
-- SELECT 
--     'DESIGNACAO', solicitante_id, missao_id,
--     funcao_na_missao, documento_sei, status, complexidade,
--     avaliado_por_id, data_avaliacao, observacao_avaliador,
--     designacao_criada_id, criado_em, atualizado_em
-- FROM missoes_solicitacaodesignacao;

-- ============================================================
-- Verificação
-- ============================================================
SELECT 'Tabela missoes_solicitacao criada com sucesso!' AS resultado;
SELECT COUNT(*) AS total_solicitacoes FROM missoes_solicitacao;
