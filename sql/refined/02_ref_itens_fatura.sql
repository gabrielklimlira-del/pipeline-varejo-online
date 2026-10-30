-- CAMADA REFINADA, passo 2: uma linha por item de fatura, já classificada.
--
-- DECISÃO 5 - tipo da linha. Só 'venda' entra como receita de produto.
--   cancelamento    fatura começa com 'C' (quantidade negativa, preço positivo).
--   ajuste_contabil fatura começa com 'A' ('Adjust bad debt'): é acerto de dívida,
--                   não venda; entra com valores de +-11 mil por linha e distorceria a receita.
--   sem_preco       preço = 0 (brinde, perda de estoque, correção manual). Sem preço não
--                   há receita; as 3.457 linhas com quantidade negativa e preço 0 têm
--                   descrições como 'short' e 'mixed', sem cliente: são acertos de estoque.
--   venda           quantidade > 0 e preço > 0.
--   outro           qualquer coisa que não caiba acima. No dado atual não há nenhuma;
--                   a tabela de conferência avisa se aparecer (ver marts/06).
--
-- valor_linha = quantidade * preço, sem arredondar (o arredondamento fica nos indicadores).

DROP TABLE IF EXISTS ref_itens_fatura;

CREATE TABLE ref_itens_fatura AS
SELECT
    ROW_NUMBER() OVER (ORDER BY aba, linha_origem) AS item_id,
    fatura_id,
    codigo_produto,
    quantidade,
    preco_unitario,
    quantidade * preco_unitario AS valor_linha,
    CASE
        WHEN SUBSTR(fatura_id, 1, 1) = 'C' THEN 'cancelamento'
        WHEN SUBSTR(fatura_id, 1, 1) = 'A' THEN 'ajuste_contabil'
        WHEN preco_unitario = 0             THEN 'sem_preco'
        WHEN quantidade > 0 AND preco_unitario > 0 THEN 'venda'
        ELSE 'outro'
    END AS tipo_linha
FROM ref_linhas_base;
