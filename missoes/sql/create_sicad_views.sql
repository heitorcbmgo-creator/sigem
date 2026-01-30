-- ============================================================
-- VIEWS DE INTEGRAÇÃO SIGEM ↔ SICAD
-- ============================================================
-- Estas views expõem os dados do SIGEM com a nomenclatura
-- do SICAD para facilitar integração futura
-- ============================================================

-- View: Oficial → UsuarioVW (SICAD)
-- Expõe oficiais do SIGEM com nomenclatura do SICAD
DROP VIEW IF EXISTS sicad_usuario_vw CASCADE;
CREATE VIEW sicad_usuario_vw AS
SELECT
    o.id AS "ID",
    o.cpf AS "CPF",
    o.nome AS "NOME_PESSOA",
    o.rg AS "RG_MILITAR",
    o.nome_guerra AS "NOME_GUERRA",
    o.posto AS "PATENTE",
    o.posto AS "SIGLA_PATENTE",
    NULL AS "LOGIN",  -- SIGEM usa CPF, não tem login
    o.email AS "EMAIL",
    NULL AS "SENHA",  -- Não expor senhas
    o.quadro AS "SIGLA_QUADRO",
    o.ativo AS "ATIVO",
    o.criado_em AS "DATA_CRIACAO",
    o.atualizado_em AS "DATA_ATUALIZACAO"
FROM missoes_oficial o
WHERE o.ativo = true;

COMMENT ON VIEW sicad_usuario_vw IS 'View de oficiais do SIGEM compatível com UsuarioVW do SICAD';


-- View: Unidade → ObmVw (SICAD)
-- Expõe unidades do SIGEM com nomenclatura do SICAD
DROP VIEW IF EXISTS sicad_obm_vw CASCADE;
CREATE VIEW sicad_obm_vw AS
SELECT
    u.id AS "ID",
    u.comando_superior_id AS "IDUNIDADEPAI",
    u.nome AS "NOME",
    u.sigla AS "SIGLA",
    u.tipo AS "TIPO",
    NULL AS "SITUACAO",  -- Não existe no SIGEM ainda
    NULL AS "LOGRADOURO",
    NULL AS "NUMERO",
    NULL AS "TELEFONE",
    NULL AS "CEP",
    NULL AS "QUADRA",
    NULL AS "LOTE",
    NULL AS "COMPLEMENTO",
    NULL AS "BAIRRO_ID",
    NULL AS "NOME_BAIRRO",
    NULL AS "MUNICIPIO_ID",
    NULL AS "NOME_CIDADE",
    u.criado_em AS "DATA_CRIACAO",
    u.atualizado_em AS "DATA_ATUALIZACAO"
FROM missoes_unidade u;

COMMENT ON VIEW sicad_obm_vw IS 'View de unidades do SIGEM compatível com ObmVw do SICAD';


-- View: Usuario + Oficial → UsuarioComFuncaoVW (SICAD)
-- Expõe usuários do SIGEM com dados do oficial associado
DROP VIEW IF EXISTS sicad_usuario_funcao_vw CASCADE;
CREATE VIEW sicad_usuario_funcao_vw AS
SELECT
    u.id AS "ID",
    NULL AS "FUNCAO_ID",  -- Mapeamento de role para função
    NULL AS "ID_USUARIO_SICAD",
    o.cpf AS "CPF",
    o.nome AS "NOME_PESSOA",
    o.rg AS "RG_MILITAR",
    o.nome_guerra AS "NOME_GUERRA",
    o.posto AS "PATENTE",
    o.quadro AS "NOME_PGQ",
    u.cpf AS "LOGIN",
    o.email AS "EMAIL",
    NULL AS "SENHA",
    u.role AS "COD_FUNCAO",
    CASE u.role
        WHEN 'admin' THEN 'Administrador'
        WHEN 'corregedor' THEN 'Corregedor'
        WHEN 'bm3' THEN 'BM/3'
        WHEN 'comando_geral' THEN 'Comando Geral'
        WHEN 'comandante' THEN 'Comandante'
        WHEN 'oficial' THEN 'Oficial'
        ELSE 'Sem Função'
    END AS "DESC_FUNCAO",
    o.obm AS "DESC_UNIDADE",
    NULL AS "SIGLA_UNIDADE"
FROM missoes_usuario u
LEFT JOIN missoes_oficial o ON u.oficial_id = o.id
WHERE u.is_active = true;

COMMENT ON VIEW sicad_usuario_funcao_vw IS 'View de usuários com função compatível com UsuarioComFuncaoVW do SICAD';


-- View: Designações → Para consulta de escalas/missões
DROP VIEW IF EXISTS sicad_designacao_vw CASCADE;
CREATE VIEW sicad_designacao_vw AS
SELECT
    d.id AS "ID",
    d.oficial_id AS "OFICIAL_ID",
    o.cpf AS "CPF_OFICIAL",
    o.nome AS "NOME_OFICIAL",
    o.posto AS "PATENTE",
    d.missao_id AS "MISSAO_ID",
    m.nome AS "NOME_MISSAO",
    m.tipo AS "TIPO_MISSAO",
    d.funcao_na_missao AS "FUNCAO",
    d.complexidade AS "COMPLEXIDADE",
    d.status AS "STATUS",
    m.data_inicio AS "DATA_INICIO",
    m.data_fim AS "DATA_FIM",
    m.local AS "LOCAL",
    d.criado_em AS "DATA_DESIGNACAO",
    d.observacoes AS "OBSERVACOES"
FROM missoes_designacao d
INNER JOIN missoes_oficial o ON d.oficial_id = o.id
INNER JOIN missoes_missao m ON d.missao_id = m.id;

COMMENT ON VIEW sicad_designacao_vw IS 'View de designações (escalas) para consulta externa';


-- View: Missões ativas para consulta
DROP VIEW IF EXISTS sicad_missao_ativa_vw CASCADE;
CREATE VIEW sicad_missao_ativa_vw AS
SELECT
    m.id AS "ID",
    m.nome AS "NOME",
    m.tipo AS "TIPO",
    m.status AS "STATUS",
    m.local AS "LOCAL",
    m.data_inicio AS "DATA_INICIO",
    m.data_fim AS "DATA_FIM",
    m.documento_referencia AS "DOCUMENTO_SEI",
    COUNT(DISTINCT d.oficial_id) AS "TOTAL_OFICIAIS",
    m.criado_em AS "DATA_CRIACAO"
FROM missoes_missao m
LEFT JOIN missoes_designacao d ON m.id = d.missao_id
WHERE m.status IN ('PLANEJAMENTO', 'EM_ANDAMENTO')
GROUP BY m.id, m.nome, m.tipo, m.status, m.local, m.data_inicio,
         m.data_fim, m.documento_referencia, m.criado_em;

COMMENT ON VIEW sicad_missao_ativa_vw IS 'View de missões ativas para consulta externa';


-- ============================================================
-- GRANTS (ajustar conforme necessário)
-- ============================================================
-- Quando criar usuário de integração, conceder acesso:
-- GRANT SELECT ON sicad_usuario_vw TO usuario_integracao_sicad;
-- GRANT SELECT ON sicad_obm_vw TO usuario_integracao_sicad;
-- GRANT SELECT ON sicad_usuario_funcao_vw TO usuario_integracao_sicad;
-- GRANT SELECT ON sicad_designacao_vw TO usuario_integracao_sicad;
-- GRANT SELECT ON sicad_missao_ativa_vw TO usuario_integracao_sicad;