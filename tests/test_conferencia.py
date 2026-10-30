"""Controle de linhas entre as camadas (arquivo 06 de sql/marts)."""
from tests.helpers import consultar, criar_banco, linha, rodar_tudo


def test_conferencia_bate_e_conta_o_que_sai():
    d = "2010-12-03 10:00:00"
    aba1 = [linha(100, "P1", "A", 1, d, 5, 1),
            linha(100, "POST", "POSTAGE", 1, d, 5, 1),
            linha(200, "P1", "A", 1, d, 5, None)]
    aba2 = [linha(200, "P1", "A", 1, d, 5, None),            # repetida da aba 1
            linha(300, "P1", "A", 1, "2010-12-10 10:00:00", 5, 2)]
    con = criar_banco(aba1, aba2)
    rodar_tudo(con)
    c = dict(consultar(con, "SELECT etapa, linhas FROM mart_conferencia_linhas"))

    assert c["bruta: aba 2009-2010"] == 3
    assert c["bruta: aba 2010-2011"] == 2
    assert c["removidas: faturas repetidas entre as abas"] == 1
    assert c["refinada: ref_itens_fatura"] == 4
    assert c["refinada: tipo outro (esperado 0)"] == 0
    assert c["itens de venda/cancelamento que não são produto (ficam fora dos indicadores)"] == 1
    assert c["itens de venda/cancelamento sem cliente identificado"] == 1
    assert c["diferença (refinada - esperado; deve ser 0)"] == 0
