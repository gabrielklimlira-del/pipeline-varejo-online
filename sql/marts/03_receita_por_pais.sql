-- INDICADOR 3: receita por país.
-- Pergunta: de onde vem a receita e quantos clientes identificados cada país tem?
--
-- JOIN: ref_itens_fatura -> ref_faturas (país da fatura) -> ref_produtos (só produtos).
-- Usa o país da própria fatura. clientes_identificados conta só faturas com Customer ID.
-- participacao_pct = receita líquida do país / receita líquida total.
-- Atenção: 'Unspecified' e 'European Community' são rótulos da fonte, mantidos como vieram.

DROP TABLE IF EXISTS mart_receita_por_pais;

CREATE TABLE mart_receita_por_pais AS
WITH por_pais AS (
    SELECT
        f.pais,
        SUM(i.valor_linha)                                                  AS receita_liquida,
        COUNT(DISTINCT CASE WHEN i.tipo_linha = 'venda' THEN f.fatura_id END) AS faturas_venda,
        COUNT(DISTINCT f.cliente_id)                                        AS clientes_identificados
    FROM ref_itens_fatura i
    JOIN ref_faturas  f ON f.fatura_id      = i.fatura_id
    JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
    WHERE p.eh_produto = 1
      AND i.tipo_linha IN ('venda', 'cancelamento')
    GROUP BY f.pais
)
SELECT
    RANK() OVER (ORDER BY receita_liquida DESC)                 AS posicao,
    pais,
    ROUND(receita_liquida, 2)                                   AS receita_liquida,
    ROUND(100.0 * receita_liquida / SUM(receita_liquida) OVER (), 2) AS participacao_pct,
    faturas_venda,
    clientes_identificados
FROM por_pais;
