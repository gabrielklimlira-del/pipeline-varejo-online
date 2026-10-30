-- INDICADOR 2: ranking de produtos.
-- Pergunta: quais produtos geram mais receita e quais são mais cancelados?
--
-- JOIN: ref_itens_fatura -> ref_produtos. Só produtos (eh_produto = 1) e só linhas de
-- venda e cancelamento. Posição por receita líquida (RANK: empate divide a posição).
-- taxa_cancelamento_qtd_pct = unidades canceladas / unidades vendidas. O cancelamento não
-- tem vínculo com a venda original, então é uma razão entre totais do período inteiro.

DROP TABLE IF EXISTS mart_top_produtos;

CREATE TABLE mart_top_produtos AS
WITH base AS (
    SELECT
        p.codigo_produto,
        p.descricao,
        SUM(CASE WHEN i.tipo_linha = 'venda' THEN i.quantidade ELSE 0 END)           AS unidades_vendidas,
        -SUM(CASE WHEN i.tipo_linha = 'cancelamento' THEN i.quantidade ELSE 0 END)   AS unidades_canceladas,
        SUM(CASE WHEN i.tipo_linha = 'venda' THEN i.valor_linha ELSE 0 END)          AS receita_bruta,
        SUM(i.valor_linha)                                                           AS receita_liquida
    FROM ref_itens_fatura i
    JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
    WHERE p.eh_produto = 1
      AND i.tipo_linha IN ('venda', 'cancelamento')
    GROUP BY p.codigo_produto, p.descricao
)
SELECT
    RANK() OVER (ORDER BY receita_liquida DESC)                    AS posicao,
    codigo_produto,
    descricao,
    unidades_vendidas,
    unidades_canceladas,
    ROUND(receita_bruta, 2)                                        AS receita_bruta,
    ROUND(receita_liquida, 2)                                      AS receita_liquida,
    ROUND(100.0 * unidades_canceladas / NULLIF(unidades_vendidas, 0), 2) AS taxa_cancelamento_qtd_pct
FROM base;
