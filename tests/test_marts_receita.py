"""Indicadores de receita: mensal, produtos e países (arquivos 01 a 03 de sql/marts)."""
from tests.helpers import consultar, criar_banco, linha, rodar_tudo


def _dados():
    """Dados inventados, com as contas feitas à mão nos comentários.

    Janeiro/2010: fatura 1 (cliente 1, UK):  P1 2x10 = 20 + P2 1x5 = 5  (POST 15 fica de fora)
                  fatura 2 (cliente 2, Germany): P1 1x10 = 10
                  fatura C3 (cliente 1, UK): cancela 1x P1 = -10
    Fevereiro/2010: fatura 4 (cliente 3, UK): P2 4x5 = 20
                  A5 (ajuste contábil) e fatura 6 (preço zero) não contam como receita.
    """
    return [
        linha(1,    "P1",   "PRODUTO UM",   2, "2010-01-10 10:00:00", 10, 1, "United Kingdom"),
        linha(1,    "P2",   "PRODUTO DOIS", 1, "2010-01-10 10:00:00", 5,  1, "United Kingdom"),
        linha(1,    "POST", "POSTAGE",      1, "2010-01-10 10:00:00", 15, 1, "United Kingdom"),
        linha(2,    "P1",   "PRODUTO UM",   1, "2010-01-20 10:00:00", 10, 2, "Germany"),
        linha("C3", "P1",   "PRODUTO UM",  -1, "2010-01-25 10:00:00", 10, 1, "United Kingdom"),
        linha(4,    "P2",   "PRODUTO DOIS", 4, "2010-02-05 10:00:00", 5,  3, "United Kingdom"),
        linha("A5", "B",    "Adjust bad debt", 1, "2010-02-06 10:00:00", 100, None, "United Kingdom"),
        linha(6,    "P1",   "short",       -3, "2010-02-07 10:00:00", 0, None, "United Kingdom"),
    ]


def test_receita_mensal():
    con = criar_banco(_dados())
    rodar_tudo(con)
    linhas = consultar(con, """SELECT mes, receita_bruta, valor_cancelado, receita_liquida,
                                      faturas_venda, ticket_medio, taxa_cancelamento_pct,
                                      mes_parcial
                               FROM mart_receita_mensal ORDER BY mes""")
    assert linhas == [
        ("2010-01", 35.0, 10.0, 25.0, 2, 17.5, 28.57, 0),
        ("2010-02", 20.0, 0.0, 20.0, 1, 20.0, 0.0, 1),   # dado termina em 02-07: mês parcial
    ]


def test_top_produtos_ordena_por_receita_liquida():
    con = criar_banco(_dados())
    rodar_tudo(con)
    linhas = consultar(con, """SELECT posicao, codigo_produto, descricao, unidades_vendidas,
                                      unidades_canceladas, receita_bruta, receita_liquida,
                                      taxa_cancelamento_qtd_pct
                               FROM mart_top_produtos ORDER BY posicao""")
    assert linhas == [
        (1, "P2", "PRODUTO DOIS", 5, 0, 25.0, 25.0, 0.0),
        (2, "P1", "PRODUTO UM",   3, 1, 30.0, 20.0, 33.33),
    ]
    # frete não aparece no ranking de produtos
    assert consultar(con, "SELECT COUNT(*) FROM mart_top_produtos WHERE codigo_produto='POST'") == [(0,)]


def test_receita_por_pais():
    con = criar_banco(_dados())
    rodar_tudo(con)
    linhas = consultar(con, """SELECT posicao, pais, receita_liquida, participacao_pct,
                                      faturas_venda, clientes_identificados
                               FROM mart_receita_por_pais ORDER BY posicao""")
    # Reino Unido: 25 (fatura 1) - 10 (cancelamento) + 20 (fatura 4) = 35; Alemanha: 10; total 45
    assert linhas == [
        (1, "United Kingdom", 35.0, 77.78, 2, 2),
        (2, "Germany",        10.0, 22.22, 1, 1),
    ]
    assert abs(sum(r[0] for r in consultar(con, "SELECT participacao_pct FROM mart_receita_por_pais")) - 100) < 0.01
