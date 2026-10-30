-- INDICADOR 4: RFM de clientes (recência, frequência, valor).
-- Pergunta: quem são os melhores clientes e quem está sumindo?
--
-- JOIN: ref_itens_fatura -> ref_faturas -> ref_produtos. Só clientes identificados
-- (cliente_id não nulo) e só com ao menos uma fatura de venda.
--
-- DATA DE REFERÊNCIA: o dia seguinte à última fatura do dado (2011-12-10), não a data
-- de hoje. Com a data de hoje todo cliente pareceria inativo há anos.
--   recencia_dias = dias entre a última compra e a data de referência.
--   frequencia    = número de faturas de venda.
--   valor         = receita líquida do cliente (vendas menos cancelamentos).
--
-- NOTAS (1 a 5, 5 = melhor):
--   r_nota e v_nota usam NTILE(5) com desempate por cliente_id (resultado sempre igual).
--   f_nota usa faixas fixas, porque muitos clientes têm 1 ou 2 faturas e NTILE
--   separaria clientes idênticos em notas diferentes:
--   1 fatura = 1, 2 = 2, 3 a 4 = 3, 5 a 9 = 4, 10 ou mais = 5.
--
-- SEGMENTOS (ordem importa, vale a primeira regra que bater):
--   campeao   r >= 4 e f >= 4        leal       r >= 3 e f >= 3
--   em_risco  r <= 2 e f >= 3        novo       r >= 4 (f <= 2)
--   ocasional r = 3  (f <= 2)        inativo    r <= 2 e f <= 2

DROP TABLE IF EXISTS mart_rfm_clientes;

CREATE TABLE mart_rfm_clientes AS
WITH referencia AS (
    SELECT DATE(MAX(data), '+1 day') AS data_ref FROM ref_faturas
),
base AS (
    SELECT
        f.cliente_id,
        MAX(CASE WHEN f.tipo_fatura = 'venda' THEN f.data END)                         AS ultima_compra,
        COUNT(DISTINCT CASE WHEN f.tipo_fatura = 'venda' THEN f.fatura_id END)         AS frequencia,
        SUM(i.valor_linha)                                                             AS valor
    FROM ref_itens_fatura i
    JOIN ref_faturas  f ON f.fatura_id      = i.fatura_id
    JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
    WHERE p.eh_produto = 1
      AND i.tipo_linha IN ('venda', 'cancelamento')
      AND f.cliente_id IS NOT NULL
    GROUP BY f.cliente_id
),
clientes AS (
    SELECT
        b.cliente_id,
        c.pais,
        CAST(JULIANDAY(r.data_ref) - JULIANDAY(b.ultima_compra) AS INTEGER) AS recencia_dias,
        b.frequencia,
        b.valor
    FROM base b
    CROSS JOIN referencia r
    JOIN ref_clientes c ON c.cliente_id = b.cliente_id
    WHERE b.frequencia > 0
),
notas AS (
    SELECT
        cliente_id, pais, recencia_dias, frequencia, valor,
        NTILE(5) OVER (ORDER BY recencia_dias DESC, cliente_id) AS r_nota,
        CASE
            WHEN frequencia >= 10 THEN 5
            WHEN frequencia >= 5  THEN 4
            WHEN frequencia >= 3  THEN 3
            WHEN frequencia = 2   THEN 2
            ELSE 1
        END AS f_nota,
        NTILE(5) OVER (ORDER BY valor, cliente_id) AS v_nota
    FROM clientes
)
SELECT
    cliente_id,
    pais,
    recencia_dias,
    frequencia,
    ROUND(valor, 2) AS valor,
    r_nota,
    f_nota,
    v_nota,
    CASE
        WHEN r_nota >= 4 AND f_nota >= 4 THEN 'campeao'
        WHEN r_nota >= 3 AND f_nota >= 3 THEN 'leal'
        WHEN r_nota <= 2 AND f_nota >= 3 THEN 'em_risco'
        WHEN r_nota >= 4                 THEN 'novo'
        WHEN r_nota = 3                  THEN 'ocasional'
        ELSE 'inativo'
    END AS segmento
FROM notas;
