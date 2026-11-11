# Decisões sobre o dado

Cada decisão tem o motivo, a evidência medida no dado e o efeito conhecido.
Os números vieram de consultas feitas no banco do projeto. Na camada refinada,
o mesmo texto está no comentário do arquivo `.sql` que aplica a regra.
Valores em libras esterlinas (£), a moeda da fonte.

## Camada bruta

| # | Decisão | Motivo |
|---|---------|--------|
| B1 | Uma tabela bruta por aba do Excel (`raw_vendas_2009_2010`, `raw_vendas_2010_2011`), com os nomes de coluna originais. | Nada é alterado na bruta. As duas abas têm o mesmo formato, mas se sobrepõem (decisão 1), então juntá-las é trabalho da refinada. |
| B2 | Todos os valores são gravados como texto. | Tipos só são definidos na refinada, assim a bruta nunca perde ou muda um valor. |
| B3 | Datas gravadas como texto ISO (`AAAA-MM-DD HH:MM:SS`) e números inteiros que o Excel entrega como decimal (`13085.0`) gravados como `13085`. | Conversão de formato sem perda de informação. É a única mudança entre o Excel e a bruta. |

Conferência: 525.461 + 541.910 = 1.067.371 linhas, o mesmo total que a fonte informa.

## Camada refinada

| # | Decisão | Motivo e evidência | Efeito conhecido |
|---|---------|--------------------|------------------|
| 1 | Faturas presentes nas duas abas ficam só com a cópia da aba 2009-2010. | As abas repetem 01/12/2010 a 09/12/2010: 22.523 linhas e 1.088 faturas. Comparei as linhas nos dois sentidos (`EXCEPT`) e são idênticas. Sem tratar, a receita dessa semana seria contada em dobro. | Refinada = 1.067.371 − 22.523 = 1.044.848 linhas. |
| 2 | Tipos definidos aqui (quantidade inteira, preço decimal, cliente inteiro). | A bruta é só texto (B2). | Nenhum. |
| 3 | Código do produto em maiúsculas e sem espaços. | 5.305 códigos distintos viram 5.131 (`15056bl` e `15056BL` eram o mesmo produto). | Nenhum. |
| 4 | Descrição sem espaços nas pontas; vazia vira `NULL`. | Há descrições como `' WHITE CHERRY LIGHTS'`. | 353 produtos ficam sem descrição, todos sem linha de venda com nome. |
| 5 | Linha classificada em `venda`, `cancelamento`, `ajuste_contabil` ou `sem_preco`. Só venda e cancelamento viram receita. | Prefixo `C` = cancelamento; `A` = acerto de dívida (`Adjust bad debt`, ±£11 mil por linha); preço 0 = brinde ou acerto de estoque (3.457 linhas com quantidade negativa, preço 0, sem cliente, descrições como `short`). | 1.019.653 vendas, 19.165 cancelamentos, 6.024 sem preço, 6 ajustes. Nenhuma linha `outro`. |
| 6 | Data da fatura = menor horário entre os itens. | 83 faturas têm itens lançados em minutos diferentes. | Cada fatura cai em um único mês. |
| 7 | Faturas sem Customer ID são mantidas, com `cliente_id` vazio. | 229.327 de 1.038.818 linhas de venda e cancelamento (22,08%) não têm cliente identificado. | Contam na receita e não entram em indicadores por cliente. |
| 8 | Tipo da fatura pelo prefixo (`C`, `A`, resto = venda). | Mesma regra dos itens. | Nenhum. |
| 9 | Códigos de serviço, tarifa, frete, acerto, teste e vale-presente marcados com `eh_produto = 0`. | Somam valores enormes e não dizem o que o cliente comprou (`AMAZONFEE` sozinho tem −£260 mil). Lista explícita na tabela `ref_codigos_nao_produto`. Os códigos `DCGS...`, `PADS` e `SP1002` têm nome de produto e ficam. | Ver limitação L1. |
| 10 | Descrição do produto = a mais usada em linhas de venda (desempate: mais usada no total, depois ordem alfabética). | 1.210 códigos têm mais de uma descrição (`short`, `mixed`, `ebay`, erros de digitação). | Resultado sempre o mesmo. |
| 11 | País do cliente = país da fatura mais recente. | 13 clientes aparecem em mais de um país. Nenhuma fatura tem mais de um país. | Nenhum. |
| 12 | Linhas duplicadas exatas dentro de uma mesma aba **não** são removidas. | O dado não permite separar um lançamento repetido de um item comprado duas vezes na mesma fatura. Remover sem prova reduziria a receita. | Ver limitação L2. |

## Indicadores

| # | Decisão | Motivo |
|---|---------|--------|
| 13 | Receita líquida = vendas − cancelamentos, só de produtos, com o cancelamento contado no mês em que foi emitido. | O dado não liga o cancelamento à fatura de origem. Por isso a taxa de cancelamento de um mês pode ser alta por causa de compras de meses anteriores. |
| 14 | RFM usa como data de referência o dia seguinte à última fatura do dado (2011-12-10). | Com a data de hoje, todo cliente pareceria inativo há anos. |
| 15 | Nota de frequência por faixas fixas (1, 2, 3–4, 5–9, 10+); recência e valor por `NTILE(5)` com desempate por `cliente_id`. | Muitos clientes têm 1 ou 2 faturas; `NTILE` separaria clientes idênticos em notas diferentes. |
| 16 | As duas encomendas gigantes canceladas no mesmo dia foram mantidas. | São lançamentos reais e a receita líquida delas é zero: `581483`/`C581484` (£168.469,60, 09/12/2011) e `541431`/`C541433` (£77.183,60, 18/01/2011). |
| 17 | `mart_receita_mensal` marca `mes_parcial = 1` para dez/2011. | O dado termina em 09/12/2011. |

## Limitações conhecidas

- **L1 - lançamentos manuais (código `M`).** Classificados como não produtos e excluídos dos indicadores. Apresentam saldo líquido de -£82.935,57, equivalente a aproximadamente 0,44% da receita líquida apresentada. A exclusão desses lançamentos faz com que a receita líquida dos indicadores fique maior nesse valor.
- **L2 - duplicatas exatas mantidas.** Foram identificados 11.001 grupos de duplicatas, totalizando 11.812 linhas extras. O valor líquido dessas linhas é de £54.228,42; considerando os valores absolutos, o montante é de £60.734,52. O valor líquido representa aproximadamente 0,28% da receita bruta. As duplicatas foram mantidas porque não é possível distinguir, com segurança, uma duplicação indevida de uma compra legítima de itens idênticos na mesma fatura.
- **L3 - picos de dez/2011 e jan/2011.** Os cancelamentos de 28% e 14% nesses meses vêm das duas encomendas da decisão 16. A receita bruta e o ticket médio desses meses ficam inflados; a líquida não muda.
- **L4 - dez/2009 em `clientes novos`.** O dado começa nesse mês, então todo cliente dele aparece como novo, mesmo os que já compravam antes.
- **L5 - clientes anônimos.** Clientes identificados respondem por 86,46% da receita líquida. Os indicadores RFM e a análise de recorrência consideram apenas esses clientes.
