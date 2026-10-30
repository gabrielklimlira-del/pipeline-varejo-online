"""Indicadores de cliente: RFM e novos x recorrentes (arquivos 04 e 05 de sql/marts)."""
from datetime import date, timedelta

from tests.helpers import consultar, criar_banco, linha, rodar_tudo


def _rfm_dados():
    """10 clientes, 2 por nota de recência (NTILE(5) dá exatamente 2 por faixa).

    Cada cliente tem: (quantas faturas de venda, dia da última compra em jan/2010).
    A última compra do cliente i é em 1 de janeiro + i dias; as anteriores são em dez/2009.
    Data de referência = dia seguinte à última fatura = 2010-01-11.
    """
    perfis = [  # (frequência, segmento esperado)
        (1, "inativo"),    # i=0  r=1 f=1
        (10, "em_risco"),  # i=1  r=1 f=5
        (1, "inativo"),    # i=2  r=2 f=1
        (3, "em_risco"),   # i=3  r=2 f=3
        (1, "ocasional"),  # i=4  r=3 f=1
        (3, "leal"),       # i=5  r=3 f=3
        (2, "novo"),       # i=6  r=4 f=2
        (5, "campeao"),    # i=7  r=4 f=4
        (1, "novo"),       # i=8  r=5 f=1
        (10, "campeao"),   # i=9  r=5 f=5
    ]
    linhas, numero = [], 1000
    for i, (freq, _) in enumerate(perfis):
        cliente = 100 + i
        ultima = date(2010, 1, 1) + timedelta(days=i)
        for k in range(freq):
            dia = ultima if k == freq - 1 else date(2009, 12, 1) + timedelta(days=k)
            numero += 1
            linhas.append(linha(numero, "P1", "PRODUTO", 1, f"{dia} 10:00:00", 10 * (i + 1), cliente))
    return linhas, perfis


def test_rfm_recencia_frequencia_valor_e_segmentos():
    linhas, perfis = _rfm_dados()
    # clientes que NÃO podem aparecer no RFM:
    linhas.append(linha(2001, "P1", "PRODUTO", 1, "2010-01-02 10:00:00", 10, None))      # sem Customer ID
    linhas.append(linha("C2002", "P1", "PRODUTO", -1, "2010-01-02 10:00:00", 10, 555))   # só cancelamento
    con = criar_banco(linhas)
    rodar_tudo(con)

    por_cliente = {r[0]: r for r in consultar(con, """SELECT cliente_id, recencia_dias, frequencia,
                                                             valor, segmento FROM mart_rfm_clientes""")}
    assert len(por_cliente) == 10                       # sem o anônimo e sem o cliente 555
    assert 555 not in por_cliente
    for i, (freq, segmento) in enumerate(perfis):
        cliente, recencia, frequencia, valor, seg = por_cliente[100 + i]
        assert frequencia == freq
        assert recencia == 10 - i                       # referência 2010-01-11
        assert valor == freq * 10 * (i + 1)             # cada fatura: 1 unidade x (10*(i+1))
        assert seg == segmento, f"cliente {cliente}: esperado {segmento}, veio {seg}"


def test_rfm_valor_desconta_cancelamento():
    d1, d2 = "2010-01-05 10:00:00", "2010-01-06 10:00:00"
    con = criar_banco([linha(1, "P1", "A", 3, d1, 10, 7),
                       linha("C2", "P1", "A", -1, d2, 10, 7)])
    rodar_tudo(con)
    # valor: 3x10 - 1x10 = 20. A data de referência é o dia seguinte à última fatura do dado
    # (o cancelamento, 01-06, então 01-07); a última COMPRA foi em 01-05, logo recência = 2.
    assert consultar(con, "SELECT frequencia, valor, recencia_dias FROM mart_rfm_clientes") == [(1, 20.0, 2)]


def test_novos_e_recorrentes_por_mes():
    con = criar_banco([
        linha(1, "P1", "A", 1, "2010-01-10 10:00:00", 10, 1),         # cliente 1 compra em jan
        linha(2, "P1", "A", 1, "2010-02-10 10:00:00", 10, 1),         # e em fev (recorrente)
        linha(3, "P1", "A", 1, "2010-02-11 10:00:00", 10, 2),         # cliente 2: novo em fev
        linha(4, "P1", "A", 1, "2010-02-12 10:00:00", 10, 3),         # cliente 3: novo em fev
        linha(5, "P1", "A", 1, "2010-02-13 10:00:00", 10, None),      # anônimo não conta
        linha("C6", "P1", "A", -1, "2010-03-10 10:00:00", 10, 3),     # cancelamento não é atividade
        linha(7, "POST", "POSTAGE", 1, "2010-03-11 10:00:00", 15, 1), # só frete não é compra
    ])
    rodar_tudo(con)
    assert consultar(con, """SELECT mes, clientes_ativos, clientes_novos, clientes_recorrentes,
                                    recorrentes_pct
                             FROM mart_clientes_novos_recorrentes ORDER BY mes""") == [
        ("2010-01", 1, 1, 0, 0.0),
        ("2010-02", 3, 2, 1, 33.33),
    ]
