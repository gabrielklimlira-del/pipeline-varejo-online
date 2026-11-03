"""Executa o pipeline: bruta (Excel -> SQLite), refinada e indicadores (arquivos .sql)."""
import argparse
import sqlite3
import time
import logging
from pathlib import Path

from src.ingestao import carregar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)
RAIZ = Path(__file__).resolve().parent.parent
PASTA_REFINADA = RAIZ / "sql" / "refined"
PASTA_INDICADORES = RAIZ / "sql" / "marts"


def executar_pasta(con: sqlite3.Connection, pasta: Path) -> list:
    """Roda, em ordem alfabética, todos os .sql da pasta. Devolve os nomes executados."""
    pasta = Path(pasta)
    if not pasta.exists():
        return []
    executados = []
    for arquivo in sorted(pasta.glob("*.sql")):
        con.executescript(arquivo.read_text(encoding="utf-8"))
        executados.append(arquivo.name)
    return executados


def executar_camadas(con: sqlite3.Connection) -> list:
    """Refinada primeiro, indicadores depois (os indicadores leem só da refinada)."""
    return executar_pasta(con, PASTA_REFINADA) + executar_pasta(con, PASTA_INDICADORES)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xlsx", default=str(RAIZ / "data" / "raw" / "online_retail_II.xlsx"))
    p.add_argument("--db", default=str(RAIZ / "data" / "varejo.db"))
    p.add_argument("--pular-ingestao", action="store_true",
                   help="não recarrega o Excel; usa as tabelas brutas que já estão no banco")
    args = p.parse_args()

    if not args.pular_ingestao:
        t = time.time()
        logger.info(
    "bruta: %s (%.0fs)",
    carregar(args.xlsx, args.db),
    time.time() - t,
)

    con = sqlite3.connect(args.db)
    for pasta in (PASTA_REFINADA, PASTA_INDICADORES):
        for arquivo in executar_pasta(con, pasta):
            logger.info("ok: %s %s", pasta.name, arquivo)
    con.close()


if __name__ == "__main__":
    main()
