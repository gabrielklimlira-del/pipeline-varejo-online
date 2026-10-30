"""Refinada: linhas base, itens e faturas (arquivos 01, 02 e 03 de sql/refined)."""
from src.pipeline import PASTA_REFINADA, executar_pasta
from tests.helpers import consultar, criar_banco, linha, rodar_refinada


def test_executar_pasta_inexistente_nao_faz_nada():
    con = criar_banco()
    assert executar_pasta(con, PASTA_REFINADA.parent / "nao_existe") == []


def test_fatura_repetida_entre_abas_conta_uma_vez():
    aba1 = [linha(100, "A1", "ITEM A", 1, "2010-12-02 10:00:00", 5, 1),
            linha(100, "A2", "ITEM B", 1, "2010-12-02 10:00:00", 5, 1),
            linha(200, "A1", "ITEM A", 2, "2010-12-03 11:00:00", 5, 2)]
    aba2 = [linha(200, "A1", "ITEM A", 2, "2010-12-03 11:00:00", 5, 2),   # repetida
            linha(300, "A1", "ITEM A", 1, "2010-12-10 09:00:00", 5, 3)]   # só na aba 2
    con = criar_banco(aba1, aba2)
    rodar_refinada(con)

    assert consultar(con, "SELECT COUNT(*) FROM ref_itens_fatura") == [(4,)]
    assert consultar(con, "SELECT COUNT(*) FROM ref_itens_fatura WHERE fatura_id='200'") == [(1,)]
    assert consultar(con, "SELECT COUNT(*) FROM ref_faturas") == [(3,)]


def test_tipos_sao_convertidos():
    con = criar_banco([linha(1, "A1", "X", 3, "2010-01-05 08:00:00", 2.5, 7)])
    rodar_refinada(con)
    assert consultar(con, """SELECT typeof(quantidade), typeof(preco_unitario),
                                    typeof(cliente_id)
                             FROM ref_linhas_base""") == [("integer", "real", "integer")]
    assert consultar(con, "SELECT valor_linha FROM ref_itens_fatura") == [(7.5,)]


def test_codigo_normalizado_e_descricao_vazia_vira_nulo():
    con = criar_banco([linha(1, "15056bl", " ", 1, "2010-01-05 08:00:00", 3, 7),
                       linha(2, " 15056BL ", "NOME", 1, "2010-01-06 08:00:00", 3, 7)])
    rodar_refinada(con)
    assert consultar(con, "SELECT DISTINCT codigo_produto FROM ref_itens_fatura") == [("15056BL",)]
    assert consultar(con, "SELECT descricao FROM ref_linhas_base WHERE fatura_id='1'") == [(None,)]


def test_tipo_da_linha():
    con = criar_banco([
        linha(1,    "P1", "X", 2,  "2010-01-05 08:00:00", 10, 1),   # venda
        linha("C2", "P1", "X", -1, "2010-01-06 08:00:00", 10, 1),   # cancelamento
        linha("A3", "B",  "Adjust bad debt", 1, "2010-01-07 08:00:00", 99, None),  # ajuste
        linha(4,    "P1", "X", 5,  "2010-01-08 08:00:00", 0, None), # preço zero
        linha(5,    "P1", "short", -96, "2010-01-09 08:00:00", 0, None),  # perda de estoque
    ])
    rodar_refinada(con)
    tipos = dict(consultar(con, "SELECT fatura_id, tipo_linha FROM ref_itens_fatura"))
    assert tipos == {"1": "venda", "C2": "cancelamento", "A3": "ajuste_contabil",
                     "4": "sem_preco", "5": "sem_preco"}


def test_tipo_da_fatura_pelo_prefixo():
    con = criar_banco([linha(1, "P1", "X", 1, "2010-01-05 08:00:00", 1, 1),
                       linha("C2", "P1", "X", -1, "2010-01-06 08:00:00", 1, 1),
                       linha("A3", "B", "X", 1, "2010-01-07 08:00:00", 1, None)])
    rodar_refinada(con)
    assert dict(consultar(con, "SELECT fatura_id, tipo_fatura FROM ref_faturas")) == {
        "1": "venda", "C2": "cancelamento", "A3": "ajuste_contabil"}


def test_data_da_fatura_e_o_menor_horario_e_mes_sai_dela():
    con = criar_banco([linha(1, "P1", "X", 1, "2010-01-31 23:58:00", 1, 1),
                       linha(1, "P2", "Y", 1, "2010-01-31 23:50:00", 1, 1)])
    rodar_refinada(con)
    assert consultar(con, "SELECT data_hora, data, mes FROM ref_faturas") == [
        ("2010-01-31 23:50:00", "2010-01-31", "2010-01")]


def test_fatura_sem_cliente_continua_com_cliente_nulo():
    con = criar_banco([linha(1, "P1", "X", 1, "2010-01-05 08:00:00", 1, None)])
    rodar_refinada(con)
    assert consultar(con, "SELECT cliente_id FROM ref_faturas") == [(None,)]
