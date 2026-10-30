-- INDICADOR 5: clientes novos x recorrentes por mês.
-- Pergunta: a receita depende de clientes que voltam ou de clientes novos a cada mês?
--
-- JOIN: ref_faturas -> ref_itens_fatura -> ref_produtos. Só clientes identificados e
-- faturas de venda com ao menos um item de produto.
--   novo       = o mês é o primeiro mês em que o cliente aparece no dado.
--   recorrente = o cliente já tinha comprado em um mês anterior.
-- ATENÇÃO: o dado começa em 2009-12, então todo cliente desse mês aparece como 'novo'
-- mesmo que já fosse cliente antes. Leia 2009-12 como ponto de partida, não como resultado.

DROP TABLE IF EXISTS mart_clientes_novos_recorrentes;

CREATE TABLE mart_clientes_novos_recorrentes AS
WITH compras AS (
    SELECT DISTINCT f.cliente_id, f.mes
    FROM ref_faturas f
    JOIN ref_itens_fatura i ON i.fatura_id      = f.fatura_id
    JOIN ref_produtos     p ON p.codigo_produto = i.codigo_produto
    WHERE f.tipo_fatura = 'venda'
      AND i.tipo_linha  = 'venda'
      AND p.eh_produto  = 1
      AND f.cliente_id IS NOT NULL
),
primeira AS (
    SELECT cliente_id, MIN(mes) AS mes_primeira_compra
    FROM compras
    GROUP BY cliente_id
)
SELECT
    c.mes,
    COUNT(*)                                          AS clientes_ativos,
    SUM(c.mes = p.mes_primeira_compra)                AS clientes_novos,
    SUM(c.mes > p.mes_primeira_compra)                AS clientes_recorrentes,
    ROUND(100.0 * SUM(c.mes > p.mes_primeira_compra) / COUNT(*), 2) AS recorrentes_pct
FROM compras c
JOIN primeira p ON p.cliente_id = c.cliente_id
GROUP BY c.mes;
