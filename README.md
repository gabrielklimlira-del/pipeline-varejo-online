# Varejo online: pipeline de dados em três camadas (Python + SQL)

Pipeline que lê duas abas de um Excel com vendas de uma loja virtual do Reino Unido, organiza o dado em três camadas separadas (bruta, refinada e indicadores) e responde a cinco perguntas de negócio com SQL. Cada indicador sai de um arquivo `.sql`, cada decisão sobre o dado tem o motivo escrito em [`docs/decisoes.md`](docs/decisoes.md) e a transformação é coberta por testes com pytest.

## Fonte do dado

- **Dataset:** *Online Retail II*, de Daqing Chen, no UCI Machine Learning Repository.
- **Link:** <https://archive.ics.uci.edu/dataset/502/online+retail+ii> (DOI: [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D)).
- **Licença:** CC BY 4.0, que permite compartilhar e adaptar para qualquer fim, desde que se dê o crédito. Crédito: Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository.
- **Conteúdo:** todas as transações de uma loja virtual do Reino Unido, de 01/12/2009 a 09/12/2011, com 1.067.371 linhas em duas abas do arquivo `online_retail_II.xlsx`. Valores em libras (£).
- O arquivo não está neste repositório (45 MB). Baixe-o do link acima.

## O que é uma linha de cada tabela

| Camada | Tabela | Uma linha é... |
|--------|--------|----------------|
| Bruta | `raw_vendas_2009_2010`, `raw_vendas_2010_2011` | um item de uma fatura, exatamente como veio da aba do Excel |
| Refinada | `ref_itens_fatura` | um item de uma fatura, já com tipo (`venda`, `cancelamento`, `sem_preco`, `ajuste_contabil`) e valor |
| Refinada | `ref_faturas` | uma fatura, com data, mês, país e cliente |
| Refinada | `ref_produtos` | um código de produto, com a descrição escolhida e a marca `eh_produto` |
| Refinada | `ref_clientes` | um cliente identificado, com o país |
| Indicadores | `mart_*` | o que cada indicador define (tabela abaixo) |

As tabelas refinadas se ligam por chaves, e os indicadores usam esses `JOIN`s: `ref_itens_fatura.fatura_id → ref_faturas.fatura_id`, `ref_itens_fatura.codigo_produto → ref_produtos.codigo_produto` e `ref_faturas.cliente_id → ref_clientes.cliente_id`.

## As três camadas

```
data/raw/online_retail_II.xlsx
        │  src/ingestao.py        copia as abas sem alterar valores
        ▼
BRUTA        raw_vendas_2009_2010, raw_vendas_2010_2011
        │  sql/refined/*.sql      une, remove a sobreposição, tipa, classifica
        ▼
REFINADA     ref_itens_fatura, ref_faturas, ref_produtos, ref_clientes
        │  sql/marts/*.sql        lê só da refinada
        ▼
INDICADORES  mart_*
```

## Indicadores

| Indicador | Pergunta | Arquivo |
|-----------|----------|---------|
| `mart_receita_mensal` | Como a receita evolui por mês e quanto se perde em cancelamentos? | [`sql/marts/01_receita_mensal.sql`](sql/marts/01_receita_mensal.sql) |
| `mart_top_produtos` | Quais produtos geram mais receita e quais são mais cancelados? | [`sql/marts/02_top_produtos.sql`](sql/marts/02_top_produtos.sql) |
| `mart_receita_por_pais` | De onde vem a receita? | [`sql/marts/03_receita_por_pais.sql`](sql/marts/03_receita_por_pais.sql) |
| `mart_rfm_clientes` | Quem são os melhores clientes e quem está sumindo? | [`sql/marts/04_rfm_clientes.sql`](sql/marts/04_rfm_clientes.sql) |
| `mart_clientes_novos_recorrentes` | A receita depende de clientes que voltam ou de clientes novos? | [`sql/marts/05_clientes_novos_recorrentes.sql`](sql/marts/05_clientes_novos_recorrentes.sql) |
| `mart_conferencia_linhas` | (controle) Quantas linhas entram, saem e por quê? | [`sql/marts/06_conferencia_linhas.sql`](sql/marts/06_conferencia_linhas.sql) |

## Como rodar do zero

Precisa de Python 3.10 ou mais novo.

```bash
git clone https://github.com/gabrielklimlira-del/pipeline-varejo-online.git
cd pipeline-varejo-online

python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

# baixe online_retail_II.xlsx (link acima) e salve em data/raw/online_retail_II.xlsx

python -m src.pipeline             # bruta -> refinada -> indicadores (cria data/varejo.db)
python -m src.exportar             # grava os indicadores em saidas/*.csv

python -m pytest                   # testes (usam dados inventados, não abrem data/varejo.db)
```

O `python -m src.pipeline` leva alguns minutos, a maior parte lendo o Excel. Para refazer só a refinada e os indicadores, com as tabelas brutas já no banco, use `python -m src.pipeline --pular-ingestao`.

Para ver um indicador: abra o CSV correspondente em `saidas/`, ou consulte o banco, por exemplo
`python -c "import sqlite3; print(sqlite3.connect('data/varejo.db').execute('SELECT * FROM mart_receita_mensal').fetchall())"`.

## Resultados

Receita líquida total: **£18,98 milhões** (bruta £19,70 milhões, cancelamentos £0,72 milhão). Números de `mart_receita_mensal`, `mart_top_produtos`, `mart_receita_por_pais`, `mart_rfm_clientes` e `mart_clientes_novos_recorrentes`:

- **Sazonalidade:** nov/2010 e nov/2011 são os melhores meses (líquida de £1,40 milhão e £1,43 milhão).
- **Produto líder:** `22423` REGENCY CAKESTAND 3 TIER, £314,5 mil de receita líquida.
- **Países:** o Reino Unido responde por 85,5% da receita; em seguida vêm Irlanda (EIRE, 3,2%), Países Baixos (2,9%), Alemanha (2,0%) e França (1,6%).
- **Clientes (5.852 identificados):** 1.390 "campeões" geram £11,4 milhões, 60% da receita líquida total. Outros 711 estão "em risco" (compravam com frequência e sumiram) e valem £1,4 milhão.
- **Recorrência:** a parcela de clientes ativos que já tinham comprado antes vai de 47,5% em jan/2010 para 88,5% em nov/2011.

## Cuidados com o dado

Resumo das decisões que mais mexem nos números; todas estão em [`docs/decisoes.md`](docs/decisoes.md).

- As duas abas **se sobrepõem** em 01 a 09/12/2010 (22.523 linhas idênticas). A refinada mantém uma cópia. `mart_conferencia_linhas` mostra 1.067.371 linhas brutas, 22.523 removidas e 1.044.848 na refinada, com diferença 0.
- Frete, tarifas, acertos e vales-presente **não são produto** e ficam fora dos indicadores.
- Cerca de 20% das linhas **não têm cliente**: entram na receita, mas não nos indicadores por cliente.
- Duas encomendas gigantes (£168 mil e £77 mil) foram **canceladas no mesmo dia**. A receita líquida não muda, mas a bruta e o ticket médio de dez/2011 e jan/2011 ficam inflados.
- Limitações em aberto: lançamentos manuais (código `M`) podem fazer a receita líquida ficar até 2,2% acima do real; linhas duplicadas exatas (0,3% da bruta) foram mantidas.

## A IA neste projeto

A IA (Claude) participou de todas as etapas: leitura do arquivo, perfil de qualidade, SQL, testes e documentação. As conferências foram feitas contando linhas antes e depois de cada etapa (`mart_conferencia_linhas`) e comparando os totais com um cálculo independente em pandas, direto das tabelas brutas.

- **Erro de teste (RFM).** O teste de recência foi escrito com o valor esperado errado (1 dia em vez de 2): a IA esqueceu que a data de referência vem da última fatura do dado, que era um cancelamento. O teste falhou ao rodar e o SQL estava certo, então a correção foi no teste.
- **Assumiu sem eu pedir: o que não é produto.** A IA escolheu a lista de códigos tratados como frete, tarifa e acerto. Ao listar os 61 códigos que não começam com 5 dígitos, com contagem e valor, apareceu que o código `M` inclui cancelamentos de vendas reais (−£422 mil), o que virou a limitação L1.
- **Assumiu sem eu pedir: duplicatas e banco.** Manteve as linhas duplicadas exatas, sem tirar nenhuma, e escolheu SQLite como banco. Medir o efeito das duplicatas (£57 mil, 0,3%) mostrou que a decisão é segura.
- **Assumiu o formato dos testes.** O enunciado cita o "passo 4.6" do curso; a IA não viu esse passo e seguiu só o requisito (dado inventado, banco em memória). Por isso o estilo pode diferir do que o curso mostra.
- **Quase passou:** a sobreposição entre as abas não estava nos requisitos nem na descrição do arquivo. Só apareceu ao comparar as datas de cada aba; sem tratar, 22.523 linhas seriam contadas duas vezes.

<!-- Antes de publicar: rode os passos acima e acrescente aqui o que VOCÊ encontrou ao conferir (contagem de linhas antes e depois, totais por outro caminho). Apague os itens que não forem verdade para o seu processo. -->
