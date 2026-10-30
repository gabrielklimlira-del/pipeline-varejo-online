"""Refinada: dimensões de produto e de cliente (arquivos 04 e 05 de sql/refined)."""
from tests.helpers import consultar, criar_banco, linha, rodar_refinada


def test_codigos_de_servico_nao_sao_produto():
    d = "2010-01-05 08:00:00"
    con = criar_banco([linha(1, "POST", "POSTAGE", 1, d, 15, 1),
                       linha(2, "BANK CHARGES", "Bank Charges", 1, d, 15, 1),
                       linha(3, "GIFT_0001_20", "Gift Voucher", 1, d, 20, 1),
                       linha(4, "85123A", "HEART HOLDER", 1, d, 3, 1),
                       linha(5, "DCGS0058", "MISO PRETTY GUM", 1, d, 3, 1),
                       linha(6, "PADS", "PADS TO MATCH", 1, d, 1, 1)])
    rodar_refinada(con)
    marcas = dict(consultar(con, "SELECT codigo_produto, eh_produto FROM ref_produtos"))
    assert marcas == {"POST": 0, "BANK CHARGES": 0, "GIFT_0001_20": 0,
                      "85123A": 1, "DCGS0058": 1, "PADS": 1}


def test_descricao_escolhida_e_a_mais_usada_em_venda():
    d = "2010-01-05 08:00:00"
    linhas = [linha(i, "X1", "NOME CERTO", 1, d, 5, 1) for i in (1, 2, 3)]
    # 'short' aparece mais vezes no total, mas só em linhas sem preço (não são venda)
    linhas += [linha(i, "X1", "short", -1, d, 0, None) for i in (10, 11, 12, 13, 14)]
    con = criar_banco(linhas)
    rodar_refinada(con)
    assert consultar(con, "SELECT descricao FROM ref_produtos WHERE codigo_produto='X1'") == [("NOME CERTO",)]


def test_descricao_empatada_fica_a_primeira_em_ordem_alfabetica():
    d = "2010-01-05 08:00:00"
    con = criar_banco([linha(1, "X1", "BETA", 1, d, 5, 1),
                       linha(2, "X1", "ALFA", 1, d, 5, 1)])
    rodar_refinada(con)
    assert consultar(con, "SELECT descricao FROM ref_produtos") == [("ALFA",)]


def test_produto_so_com_linhas_sem_descricao_fica_com_descricao_nula():
    con = criar_banco([linha(1, "X1", None, 1, "2010-01-05 08:00:00", 5, 1)])
    rodar_refinada(con)
    assert consultar(con, "SELECT descricao FROM ref_produtos") == [(None,)]


def test_pais_do_cliente_e_o_da_fatura_mais_recente():
    con = criar_banco([
        linha(1, "X1", "A", 1, "2010-01-05 08:00:00", 5, 9, "France"),
        linha(2, "X1", "A", 1, "2010-03-05 08:00:00", 5, 9, "Spain"),
        linha(3, "X1", "A", 1, "2010-02-05 08:00:00", 5, 9, "Germany")])
    rodar_refinada(con)
    assert consultar(con, "SELECT cliente_id, pais FROM ref_clientes") == [(9, "Spain")]


def test_cliente_sem_id_nao_entra_na_tabela_de_clientes():
    con = criar_banco([linha(1, "X1", "A", 1, "2010-01-05 08:00:00", 5, None),
                       linha(2, "X1", "A", 1, "2010-01-06 08:00:00", 5, 4)])
    rodar_refinada(con)
    assert consultar(con, "SELECT cliente_id FROM ref_clientes") == [(4,)]


def test_todo_item_tem_fatura_produto_e_cliente_cadastrados():
    d = "2010-01-05 08:00:00"
    con = criar_banco([linha(1, "X1", "A", 1, d, 5, 4),
                       linha(1, "POST", "POSTAGE", 1, d, 5, 4),
                       linha("C2", "X1", "A", -1, "2010-01-06 08:00:00", 5, 4),
                       linha(3, "X1", "A", 1, "2010-01-07 08:00:00", 5, None)])
    rodar_refinada(con)
    sem_fatura = consultar(con, """SELECT COUNT(*) FROM ref_itens_fatura i
        LEFT JOIN ref_faturas f ON f.fatura_id = i.fatura_id WHERE f.fatura_id IS NULL""")
    sem_produto = consultar(con, """SELECT COUNT(*) FROM ref_itens_fatura i
        LEFT JOIN ref_produtos p ON p.codigo_produto = i.codigo_produto
        WHERE p.codigo_produto IS NULL""")
    sem_cliente = consultar(con, """SELECT COUNT(*) FROM ref_faturas f
        LEFT JOIN ref_clientes c ON c.cliente_id = f.cliente_id
        WHERE f.cliente_id IS NOT NULL AND c.cliente_id IS NULL""")
    assert sem_fatura == [(0,)] and sem_produto == [(0,)] and sem_cliente == [(0,)]
