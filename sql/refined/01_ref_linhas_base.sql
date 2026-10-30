-- CAMADA REFINADA, passo 1: junta as duas abas, remove a sobreposição e define os tipos.
--
-- DECISÃO 1 - sobreposição entre abas.
--   As abas "2009-2010" e "2010-2011" repetem o período de 2010-12-01 a 2010-12-09
--   (22.523 linhas, 1.088 faturas). Conferi no dado bruto que as linhas repetidas são
--   idênticas (EXCEPT nos dois sentidos devolve 0 linhas). Juntar as abas sem tratar
--   contaria a receita desse período em dobro. Fica a cópia da aba mais antiga e saem
--   da aba 2010-2011 todas as faturas que já existem na aba 2009-2010.
--
-- DECISÃO 2 - tipos.
--   A camada bruta guarda tudo como texto. Aqui a quantidade vira inteiro, o preço vira
--   número e o cliente vira inteiro. A data continua em texto ISO (AAAA-MM-DD HH:MM:SS),
--   que ordena corretamente como texto.
--
-- DECISÃO 3 - código do produto.
--   Existem códigos iguais escritos em maiúsculas e minúsculas ('15056BL' e '15056bl'):
--   5.305 códigos distintos viram 5.131 depois de UPPER(TRIM()). Normalizo para não
--   contar o mesmo produto duas vezes.
--
-- DECISÃO 4 - descrição.
--   Espaços nas pontas são removidos (' WHITE CHERRY LIGHTS') e descrição vazia vira NULL.
--
-- Linhas duplicadas EXATAS dentro da mesma aba NÃO são removidas (ver docs/decisoes.md).

DROP TABLE IF EXISTS ref_linhas_base;

CREATE TABLE ref_linhas_base AS
WITH unidas AS (
    SELECT 1 AS aba, rowid AS linha_origem, *
    FROM raw_vendas_2009_2010
    UNION ALL
    SELECT 2 AS aba, rowid AS linha_origem, *
    FROM raw_vendas_2010_2011
    WHERE "Invoice" NOT IN (SELECT "Invoice" FROM raw_vendas_2009_2010)
)
SELECT
    aba,
    linha_origem,
    TRIM("Invoice")                      AS fatura_id,
    UPPER(TRIM("StockCode"))             AS codigo_produto,
    NULLIF(TRIM("Description"), '')      AS descricao,
    CAST("Quantity" AS INTEGER)          AS quantidade,
    CAST("Price" AS REAL)                AS preco_unitario,
    "InvoiceDate"                        AS data_hora,
    CAST("Customer ID" AS INTEGER)       AS cliente_id,
    TRIM("Country")                      AS pais
FROM unidas;
