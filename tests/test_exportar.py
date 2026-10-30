"""Exportação dos indicadores para CSV."""
import csv
import sqlite3
import tempfile
from pathlib import Path

from src.exportar import exportar_indicadores


def test_exporta_so_tabelas_mart_com_cabecalho():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE mart_exemplo (mes TEXT, valor REAL)")
    con.execute("INSERT INTO mart_exemplo VALUES ('2010-01', 10.5), ('2010-02', 20)")
    con.execute("CREATE TABLE ref_outra (x INTEGER)")          # não deve ser exportada
    with tempfile.TemporaryDirectory() as pasta:
        criados = exportar_indicadores(con, Path(pasta) / "saidas")
        assert criados == ["mart_exemplo.csv"]
        with open(Path(pasta) / "saidas" / "mart_exemplo.csv", encoding="utf-8") as f:
            linhas = list(csv.reader(f))
    assert linhas == [["mes", "valor"], ["2010-01", "10.5"], ["2010-02", "20.0"]]
