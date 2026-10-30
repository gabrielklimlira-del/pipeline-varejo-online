-- INDICADOR 1: receita mensal.
-- Pergunta: como a receita evolui mês a mês e quanto se perde em cancelamentos?
--
-- Lê só da camada refinada. JOIN: ref_itens_fatura -> ref_faturas (mês) -> ref_produtos (só produtos).
-- Regras (motivos em sql/refined):
--   receita_bruta  = soma das linhas 'venda' de produtos.
--   valor_cancelado = soma (em valor positivo) das linhas 'cancelamento' de produtos.
--   receita_liquida = bruta - cancelado.
--   O cancelamento é contado no mês em que foi emitido, não no mês da compra original
--   (o dado não liga o cancelamento à fatura de origem). Em meses com muitos
--   cancelamentos de compras antigas, a taxa pode passar de 100% da receita do mês.
--   mes_parcial = 1 no último mês, que termina em 2011-12-09 e não tem o mês inteiro.

DROP TABLE IF EXISTS mart_receita_mensal;

CREATE TABLE mart_receita_mensal AS
WITH linhas AS (
    SELECT f.mes, f.fatura_id, i.tipo_linha, i.valor_linha
    FROM ref_itens_fatura i
    JOIN ref_faturas  f ON f.fatura_id      = i.fatura_id
    JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
    WHERE p.eh_produto = 1
      AND i.tipo_linha IN ('venda', 'cancelamento')
),
agregado AS (
    SELECT
        mes,
        SUM(CASE WHEN tipo_linha = 'venda' THEN valor_linha ELSE 0 END)         AS bruta,
        -SUM(CASE WHEN tipo_linha = 'cancelamento' THEN valor_linha ELSE 0 END) AS cancelado,
        COUNT(DISTINCT CASE WHEN tipo_linha = 'venda' THEN fatura_id END)       AS faturas
    FROM linhas
    GROUP BY mes
),
limite AS (
    SELECT MAX(data) AS ultima_data FROM ref_faturas
)
SELECT
    a.mes,
    ROUND(a.bruta, 2)                                   AS receita_bruta,
    ROUND(a.cancelado, 2)                               AS valor_cancelado,
    ROUND(a.bruta - a.cancelado, 2)                     AS receita_liquida,
    a.faturas                                           AS faturas_venda,
    ROUND(a.bruta / NULLIF(a.faturas, 0), 2)            AS ticket_medio,
    ROUND(100.0 * a.cancelado / NULLIF(a.bruta, 0), 2)  AS taxa_cancelamento_pct,
    CASE WHEN a.mes = SUBSTR(l.ultima_data, 1, 7)
          AND l.ultima_data < DATE(a.mes || '-01', '+1 month', '-1 day')
         THEN 1 ELSE 0 END                              AS mes_parcial
FROM agregado a
CROSS JOIN limite l;
