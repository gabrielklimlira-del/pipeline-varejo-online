"""Exporta cada tabela de indicadores (mart_*) para um CSV em saidas/.

Os CSVs saem direto da camada de indicadores, sem nenhum cálculo novo.
Servem para abrir em planilha ou em uma ferramenta de BI.
"""
import csv
import sqlite3
import sys
import logging
from pathlib import Path
logger = logging.getLogger(__name__)
RAIZ = Path(__file__).resolve().parent.parent


def exportar_indicadores(con: sqlite3.Connection, pasta_saida: Path) -> list:
    """Grava um CSV por tabela mart_*. Devolve os nomes dos arquivos criados."""
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    tabelas = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'mart_%' ORDER BY name")]
    criados = []
    for tabela in tabelas:
        cursor = con.execute(f'SELECT * FROM "{tabela}"')
        destino = pasta_saida / f"{tabela}.csv"
        with open(destino, "w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow([c[0] for c in cursor.description])
            escritor.writerows(cursor)
        criados.append(destino.name)
    return criados


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    db = sys.argv[1] if len(sys.argv) > 1 else str(RAIZ / "data" / "varejo.db")

    con = sqlite3.connect(db)
    try:
        arquivos = exportar_indicadores(con, RAIZ / "saidas")
        logger.info("Arquivos exportados: %s", arquivos)
    finally:
        con.close()