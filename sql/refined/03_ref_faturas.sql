-- CAMADA REFINADA, passo 3: uma linha por fatura (tabela-pai dos itens).
--
-- DECISÃO 6 - data da fatura.
--   83 faturas têm itens lançados em minutos diferentes. Uso o menor horário como
--   data da fatura, para cada fatura cair em um único mês.
--
-- DECISÃO 7 - cliente e país da fatura.
--   Conferi: nenhuma fatura tem mais de um cliente nem mais de um país, então MAX()
--   só escolhe o único valor (e ignora NULL quando há cliente).
--   Cerca de 20% das linhas não têm Customer ID (107.927 na aba 1 e 135.080 na aba 2).
--   Essas faturas ficam, com cliente_id NULL: contam na receita, mas não entram em
--   indicadores por cliente.
--
-- DECISÃO 8 - tipo da fatura pelo prefixo: 'C' cancelamento, 'A' ajuste contábil,
--   o resto é venda (mesma regra dos itens).

DROP TABLE IF EXISTS ref_faturas;

CREATE TABLE ref_faturas AS
WITH por_fatura AS (
    SELECT
        fatura_id,
        MIN(data_hora)  AS data_hora,
        MAX(cliente_id) AS cliente_id,
        MAX(pais)       AS pais
    FROM ref_linhas_base
    GROUP BY fatura_id
)
SELECT
    fatura_id,
    CASE
        WHEN SUBSTR(fatura_id, 1, 1) = 'C' THEN 'cancelamento'
        WHEN SUBSTR(fatura_id, 1, 1) = 'A' THEN 'ajuste_contabil'
        ELSE 'venda'
    END                         AS tipo_fatura,
    cliente_id,
    data_hora,
    SUBSTR(data_hora, 1, 10)    AS data,
    SUBSTR(data_hora, 1, 7)     AS mes,
    pais
FROM por_fatura;
