"""Camada bruta: o que está no Excel tem que chegar igual ao banco."""
import os
import sqlite3
import tempfile
from datetime import datetime

import openpyxl

from src.ingestao import ABAS, COLUNAS, _texto, carregar


def test_texto_mantem_valores_e_converte_so_o_formato():
    assert _texto(None) is None
    assert _texto("abc") == "abc"
    assert _texto(85048) == "85048"
    assert _texto(13085.0) == "13085"          # número inteiro vindo como decimal
    assert _texto(6.95) == "6.95"
    assert _texto(datetime(2009, 12, 1, 7, 45)) == "2009-12-01 07:45:00"


def test_carregar_copia_as_duas_abas_sem_alterar_valores():
    with tempfile.TemporaryDirectory() as pasta:
        xlsx = os.path.join(pasta, "mini.xlsx")
        db = os.path.join(pasta, "mini.db")

        wb = openpyxl.Workbook()
        aba1, aba2 = list(ABAS)
        ws1 = wb.active
        ws1.title = aba1
        ws1.append(COLUNAS)
        ws1.append([489434, 85048, " 15CM GLASS BALL ", 12,
                    datetime(2009, 12, 1, 7, 45), 6.95, 13085, "United Kingdom"])
        ws1.append(["489435", "79323p", None, -3,
                    datetime(2009, 12, 1, 7, 46), 0, None, "EIRE"])
        ws2 = wb.create_sheet(aba2)
        ws2.append(COLUNAS)
        ws2.append(["C536379", "D", "Discount", -1,
                    datetime(2010, 12, 1, 9, 41), 27.5, 14527, "United Kingdom"])
        wb.save(xlsx)

        contagens = carregar(xlsx, db)
        assert contagens == {"raw_vendas_2009_2010": 2, "raw_vendas_2010_2011": 1}

        con = sqlite3.connect(db)
        linhas = con.execute(
            'SELECT * FROM raw_vendas_2009_2010 ORDER BY rowid').fetchall()
        con.close()

    # espaços e minúsculas ficam como vieram: a bruta não limpa nada
    assert linhas[0] == ("489434", "85048", " 15CM GLASS BALL ", "12",
                         "2009-12-01 07:45:00", "6.95", "13085", "United Kingdom")
    # vazio continua vazio (NULL), zero continua '0'
    assert linhas[1] == ("489435", "79323p", None, "-3",
                         "2009-12-01 07:46:00", "0", None, "EIRE")
