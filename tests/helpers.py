"""Apoio dos testes: banco em memória com dados inventados.

Os testes NUNCA abrem data/varejo.db. Cada teste monta as tabelas brutas na memória
com poucas linhas inventadas, roda os arquivos .sql de verdade e confere o resultado
com contas feitas à mão.
"""
import sqlite3

from src.pipeline import PASTA_INDICADORES, PASTA_REFINADA, executar_pasta

COLUNAS_BRUTAS = ["Invoice", "StockCode", "Description", "Quantity",
                  "InvoiceDate", "Price", "Customer ID", "Country"]


def linha(fatura, codigo, descricao, quantidade, data_hora, preco, cliente,
          pais="United Kingdom"):
    """Uma linha bruta inventada. Tudo vira texto, como a camada bruta guarda."""
    def texto(valor):
        return None if valor is None else str(valor)
    return (texto(fatura), texto(codigo), texto(descricao), texto(quantidade),
            texto(data_hora), texto(preco), texto(cliente), texto(pais))


def criar_banco(aba1=(), aba2=()):
    """Banco em memória com as duas tabelas brutas preenchidas."""
    con = sqlite3.connect(":memory:")
    colunas = ", ".join(f'"{c}" TEXT' for c in COLUNAS_BRUTAS)
    marcas = ", ".join("?" for _ in COLUNAS_BRUTAS)
    for tabela, linhas in (("raw_vendas_2009_2010", aba1),
                           ("raw_vendas_2010_2011", aba2)):
        con.execute(f'CREATE TABLE "{tabela}" ({colunas})')
        con.executemany(f'INSERT INTO "{tabela}" VALUES ({marcas})', list(linhas))
    return con


def rodar_refinada(con):
    executar_pasta(con, PASTA_REFINADA)


def rodar_tudo(con):
    executar_pasta(con, PASTA_REFINADA)
    executar_pasta(con, PASTA_INDICADORES)


def consultar(con, sql, parametros=()):
    return con.execute(sql, parametros).fetchall()
