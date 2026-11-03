"""Camada bruta: copia as abas do Excel para o SQLite sem alterar valores.

Cada aba vira uma tabela com os mesmos nomes de coluna do arquivo.
Todos os valores são gravados como texto (datas em ISO), para que nenhuma
conversão de tipo aconteça antes da camada refinada.
"""
import sqlite3
import sys
import logging
from datetime import datetime

import openpyxl
logger = logging.getLogger(__name__)

ABAS = {
    "Year 2009-2010": "raw_vendas_2009_2010",
    "Year 2010-2011": "raw_vendas_2010_2011",
}
COLUNAS = ["Invoice", "StockCode", "Description", "Quantity",
           "InvoiceDate", "Price", "Customer ID", "Country"]


def _texto(valor):
    """Converte para texto sem mexer no conteúdo; vazio continua NULL."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def carregar(caminho_xlsx: str, caminho_db: str) -> dict:
    wb = openpyxl.load_workbook(caminho_xlsx, read_only=True)
    con = sqlite3.connect(caminho_db)
    contagens = {}

    try:
        for aba, tabela in ABAS.items():
            con.execute(f'DROP TABLE IF EXISTS "{tabela}"')
            colunas_sql = ", ".join(f'"{c}" TEXT' for c in COLUNAS)
            con.execute(f'CREATE TABLE "{tabela}" ({colunas_sql})')
            marcas = ", ".join("?" for _ in COLUNAS)
            lote, total = [], 0

            for linha in wb[aba].iter_rows(min_row=2, values_only=True):
                lote.append([_texto(v) for v in linha[:len(COLUNAS)]])

                if len(lote) == 50_000:
                    con.executemany(
                        f'INSERT INTO "{tabela}" VALUES ({marcas})', lote
                    )
                    total += len(lote)
                    lote = []

            if lote:
                con.executemany(
                    f'INSERT INTO "{tabela}" VALUES ({marcas})', lote
                )
                total += len(lote)

            contagens[tabela] = total
            con.commit()

    finally:
        wb.close()
        con.close()

    return contagens


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    xlsx = sys.argv[1] if len(sys.argv) > 1 else "data/raw/online_retail_II.xlsx"
    db = sys.argv[2] if len(sys.argv) > 2 else "data/varejo.db"

    logger.info("Resultado da ingestão: %s", carregar(xlsx, db))