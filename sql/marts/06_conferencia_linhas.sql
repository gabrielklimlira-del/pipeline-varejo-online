-- CONTROLE (não é indicador de negócio): conferência de linhas entre as camadas.
-- Mostra quantas linhas entram, quantas saem e por quê. A última linha, 'diferença',
-- deve ser sempre 0. Se não for, alguma linha foi perdida ou criada sem querer.
-- Esta é a tabela que permite conferir o pipeline contando linhas antes e depois.

DROP TABLE IF EXISTS mart_conferencia_linhas;

CREATE TABLE mart_conferencia_linhas AS
SELECT 1  AS ordem, 'bruta: aba 2009-2010'                       AS etapa, COUNT(*) AS linhas FROM raw_vendas_2009_2010
UNION ALL
SELECT 2,  'bruta: aba 2010-2011',                                COUNT(*) FROM raw_vendas_2010_2011
UNION ALL
SELECT 3,  'removidas: faturas repetidas entre as abas',          COUNT(*)
  FROM raw_vendas_2010_2011
 WHERE "Invoice" IN (SELECT "Invoice" FROM raw_vendas_2009_2010)
UNION ALL
SELECT 4,  'esperado na refinada (bruta - removidas)',
       (SELECT COUNT(*) FROM raw_vendas_2009_2010)
     + (SELECT COUNT(*) FROM raw_vendas_2010_2011)
     - (SELECT COUNT(*) FROM raw_vendas_2010_2011
         WHERE "Invoice" IN (SELECT "Invoice" FROM raw_vendas_2009_2010))
UNION ALL
SELECT 5,  'refinada: ref_itens_fatura',                          COUNT(*) FROM ref_itens_fatura
UNION ALL
SELECT 6,  'refinada: tipo venda',                                COUNT(*) FROM ref_itens_fatura WHERE tipo_linha = 'venda'
UNION ALL
SELECT 7,  'refinada: tipo cancelamento',                         COUNT(*) FROM ref_itens_fatura WHERE tipo_linha = 'cancelamento'
UNION ALL
SELECT 8,  'refinada: tipo sem_preco',                            COUNT(*) FROM ref_itens_fatura WHERE tipo_linha = 'sem_preco'
UNION ALL
SELECT 9,  'refinada: tipo ajuste_contabil',                      COUNT(*) FROM ref_itens_fatura WHERE tipo_linha = 'ajuste_contabil'
UNION ALL
SELECT 10, 'refinada: tipo outro (esperado 0)',                   COUNT(*) FROM ref_itens_fatura WHERE tipo_linha = 'outro'
UNION ALL
SELECT 11, 'itens de venda/cancelamento que não são produto (ficam fora dos indicadores)', COUNT(*)
  FROM ref_itens_fatura i
  JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
 WHERE p.eh_produto = 0 AND i.tipo_linha IN ('venda', 'cancelamento')
UNION ALL
SELECT 12, 'itens de venda/cancelamento sem cliente identificado', COUNT(*)
  FROM ref_itens_fatura i
  JOIN ref_faturas f ON f.fatura_id = i.fatura_id
 WHERE f.cliente_id IS NULL AND i.tipo_linha IN ('venda', 'cancelamento')
UNION ALL
SELECT 13, 'diferença (refinada - esperado; deve ser 0)',
       (SELECT COUNT(*) FROM ref_itens_fatura)
     - ((SELECT COUNT(*) FROM raw_vendas_2009_2010)
      + (SELECT COUNT(*) FROM raw_vendas_2010_2011)
      - (SELECT COUNT(*) FROM raw_vendas_2010_2011
          WHERE "Invoice" IN (SELECT "Invoice" FROM raw_vendas_2009_2010)));
