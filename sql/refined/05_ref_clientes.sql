-- CAMADA REFINADA, passo 5: uma linha por cliente identificado (tabela de dimensão).
--
-- DECISÃO 11 - país do cliente.
--   13 clientes aparecem com mais de um país. Uso o país da fatura mais recente do
--   cliente, que é o dado mais atual. Desempate pelo maior número de fatura.
--   Clientes sem Customer ID não entram aqui (não dá para identificá-los).

DROP TABLE IF EXISTS ref_clientes;

CREATE TABLE ref_clientes AS
WITH ranqueada AS (
    SELECT
        cliente_id,
        pais,
        ROW_NUMBER() OVER (
            PARTITION BY cliente_id
            ORDER BY data_hora DESC, fatura_id DESC
        ) AS posicao
    FROM ref_faturas
    WHERE cliente_id IS NOT NULL
)
SELECT cliente_id, pais
FROM ranqueada
WHERE posicao = 1;
