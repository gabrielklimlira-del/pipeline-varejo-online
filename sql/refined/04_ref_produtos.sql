-- CAMADA REFINADA, passo 4: uma linha por produto (tabela de dimensão).
--
-- DECISÃO 9 - o que NÃO é produto.
--   Alguns 'códigos de produto' são serviços, taxas ou acertos: frete (POST, DOT, C2),
--   lançamento manual (M), desconto (D), amostras (S), tarifas (BANK CHARGES, AMAZONFEE,
--   CRUK), acertos (ADJUST, ADJUST2, B), testes (TEST001, TEST002, C3) e vales-presente
--   (GIFT...). Somados, mexem com centenas de milhares de libras (AMAZONFEE sozinho
--   tem -260 mil) e não dizem nada sobre o que o cliente comprou. Ficam marcados com
--   eh_produto = 0 e saem dos indicadores de receita e de produto.
--   Os códigos DCGS... (itens da loja virtual) e PADS/SP1002 têm nome de produto
--   de verdade e continuam como produto.
--
-- DECISÃO 10 - descrição do produto.
--   1.210 códigos aparecem com mais de uma descrição (erros, 'short', 'mixed', 'ebay').
--   Escolho a descrição mais usada em linhas de venda; se empatar, a mais usada no total;
--   se ainda empatar, a primeira em ordem alfabética (resultado sempre o mesmo).

DROP TABLE IF EXISTS ref_codigos_nao_produto;

CREATE TABLE ref_codigos_nao_produto (
    codigo_produto TEXT PRIMARY KEY,
    motivo         TEXT NOT NULL
);

INSERT INTO ref_codigos_nao_produto (codigo_produto, motivo) VALUES
    ('POST',         'frete'),
    ('DOT',          'frete'),
    ('C2',           'frete'),
    ('M',            'lancamento_manual'),
    ('D',            'desconto'),
    ('S',            'amostra'),
    ('BANK CHARGES', 'tarifa'),
    ('AMAZONFEE',    'tarifa'),
    ('CRUK',         'tarifa'),
    ('ADJUST',       'acerto'),
    ('ADJUST2',      'acerto'),
    ('B',            'acerto'),
    ('TEST001',      'teste'),
    ('TEST002',      'teste'),
    ('C3',           'teste');

INSERT OR IGNORE INTO ref_codigos_nao_produto (codigo_produto, motivo)
SELECT DISTINCT codigo_produto, 'vale_presente'
FROM ref_linhas_base
WHERE codigo_produto LIKE 'GIFT%';

DROP TABLE IF EXISTS ref_produtos;

CREATE TABLE ref_produtos AS
WITH contagem AS (
    SELECT
        codigo_produto,
        descricao,
        SUM(CASE WHEN quantidade > 0 AND preco_unitario > 0
                  AND SUBSTR(fatura_id, 1, 1) NOT IN ('C', 'A')
                 THEN 1 ELSE 0 END) AS usos_em_venda,
        COUNT(*)                     AS usos_total
    FROM ref_linhas_base
    WHERE descricao IS NOT NULL
    GROUP BY codigo_produto, descricao
),
ranqueada AS (
    SELECT
        codigo_produto,
        descricao,
        ROW_NUMBER() OVER (
            PARTITION BY codigo_produto
            ORDER BY usos_em_venda DESC, usos_total DESC, descricao
        ) AS posicao
    FROM contagem
)
SELECT
    c.codigo_produto,
    r.descricao,
    CASE WHEN n.codigo_produto IS NULL THEN 1 ELSE 0 END AS eh_produto
FROM (SELECT DISTINCT codigo_produto FROM ref_linhas_base) AS c
LEFT JOIN ranqueada r
       ON r.codigo_produto = c.codigo_produto AND r.posicao = 1
LEFT JOIN ref_codigos_nao_produto n
       ON n.codigo_produto = c.codigo_produto;
