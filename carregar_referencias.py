"""
Carrega as tabelas de referência da Receita Federal (CNAEs, Municípios,
Naturezas Jurídicas, Motivos de situação cadastral).

Credenciais e caminho dos dados vêm do ambiente — veja .env.example.

    python carregar_referencias.py

Recarrega por TRUNCATE + INSERT, nunca por DROP. O `if_exists="replace"` do
pandas faz DROP TABLE por baixo, e isso passou a falhar assim que a primeira
view materializada começou a depender de cnaes_referencia:

    psycopg2.errors.DependentObjectsStillExist: não é possível remover tabela
    cnaes_referencia, porque outros objetos dependem dele

DROP ... CASCADE resolveria o erro derrubando as MVs junto — e aí a recarga de
um arquivo de referência de 22 KB destruiria views que levam minutos para
reconstruir. TRUNCATE troca o conteúdo mantendo a tabela e as dependências de
pé; as MVs continuam existindo com os dados antigos até o próximo refresh, que
este script dispara no fim.
"""

import os
import sys
import zipfile

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from database import engine

load_dotenv()

REFERENCIAS = {
    "Cnaes": "cnaes_referencia",
    "Municipios": "municipios_referencia",
    "Naturezas": "naturezas_referencia",
    # Traduz motivo_situacao — o "por que fechou" — de código para texto.
    "Motivos": "motivos_referencia",
}


def _gravar(df: pd.DataFrame, tabela: str, conn) -> None:
    """Substitui o conteúdo da tabela sem removê-la.

    O nome da tabela vem do dicionário REFERENCIAS acima — constante do código,
    nunca entrada de usuário. Por isso a interpolação no TRUNCATE é segura;
    identificadores não podem viajar como bind param no PostgreSQL.
    """
    existe = conn.execute(
        text("SELECT to_regclass(:t)"), {"t": tabela}
    ).scalar()

    if existe:
        conn.execute(text(f"TRUNCATE TABLE {tabela}"))
        df.to_sql(tabela, conn, if_exists="append", index=False)
    else:
        # Primeira carga: aqui não há dependente algum, criar é seguro.
        df.to_sql(tabela, conn, if_exists="replace", index=False)


def carregar_referencias():
    caminho_pasta = os.environ.get("CNPJ_DIR")
    if not caminho_pasta:
        sys.exit("CNPJ_DIR não definida. Veja .env.example")

    carregadas = []

    for arquivo, tabela in REFERENCIAS.items():
        zip_path = os.path.join(caminho_pasta, f"{arquivo}.zip")
        if not os.path.exists(zip_path):
            print(f"[AVISO] {arquivo}.zip não encontrado em {caminho_pasta}")
            continue

        print(f"[..] Carregando {arquivo}...")
        with zipfile.ZipFile(zip_path) as z:
            with z.open(z.namelist()[0]) as f:
                # Arquivos de referência são pequenos: cabem em memória.
                df = pd.read_csv(f, sep=";", encoding="latin-1",
                                 header=None, dtype=str)
                df.columns = ["codigo", "descricao"]
                df["codigo"] = pd.to_numeric(df["codigo"], errors="coerce")
                df["descricao"] = df["descricao"].astype(str).str.strip()

        # Uma transação por tabela: se o INSERT falhar depois do TRUNCATE, o
        # rollback devolve o conteúdo antigo. Sem isso, uma falha no meio
        # deixaria a tabela de referência vazia e o dashboard sem rótulos.
        with engine.begin() as conn:
            _gravar(df, tabela, conn)

        carregadas.append(tabela)
        print(f"[OK] {tabela}: {len(df):,} registros")

    if carregadas:
        print(
            "\nAs views materializadas ainda carregam as descrições antigas — "
            "elas guardam uma cópia. Atualize com:\n"
            "    python refresh_views.py"
        )


if __name__ == "__main__":
    carregar_referencias()
