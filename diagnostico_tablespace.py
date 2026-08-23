"""
Diagnostica o tablespace das tabelas bronze.

Roda quando o ETL falha com:

    psycopg2.errors.UndefinedFile: não foi possível criar o diretório
    "pg_tblspc/<oid>/PG_18_.../<oid>": No such file or directory

Essa mensagem quer dizer uma coisa só: o tablespace existe no catálogo do
PostgreSQL, mas a pasta para onde ele aponta sumiu do disco. No seu caso o
tablespace mora em F:\\ETL CNPJ\\pgdata — um drive externo. Se o F: não está
conectado, ou voltou com outra letra, o PostgreSQL não acha o destino.

    python diagnostico_tablespace.py
"""

import os
import string
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()

TABLESPACE = "ts_cnpj_bronze"
LARGURA = 74


def linha(rotulo, valor):
    print(f"  {rotulo:<38} {valor}")


def drives_disponiveis():
    """Lista as letras de drive montadas — só faz sentido no Windows."""
    if os.name != "nt":
        return []
    return [f"{l}:" for l in string.ascii_uppercase if os.path.exists(f"{l}:\\")]


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL ausente. Preencha o .env.")

    dir_env = os.environ.get("CNPJ_TABLESPACE_DIR")

    print("=" * LARGURA)
    print("DIAGNÓSTICO DO TABLESPACE")
    print("=" * LARGURA)

    print("\n1. Configuração (.env)")
    linha("CNPJ_TABLESPACE_DIR", dir_env or "(não definida)")

    if not dir_env:
        print("\n  Sem tablespace configurado: as bronze iriam para o volume")
        print("  padrão do PostgreSQL. Se o ETL falhou mesmo assim, o problema")
        print("  é outro — me mande o erro completo.")
        return

    existe_pasta = os.path.isdir(dir_env)
    linha("A pasta existe agora?", "SIM" if existe_pasta else "NÃO")

    if not existe_pasta:
        drives = drives_disponiveis()
        if drives:
            linha("Drives montados no momento", " ".join(drives))
        letra = dir_env[:2] if len(dir_env) > 1 and dir_env[1] == ":" else None
        if letra and drives and letra.upper() not in drives:
            print(f"\n  >> O drive {letra} NÃO está montado. É a causa mais provável.")

    print("\n2. Catálogo do PostgreSQL")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT oid, pg_tablespace_location(oid) FROM pg_tablespace "
                    "WHERE spcname = %s", (TABLESPACE,))
        row = cur.fetchone()

        if not row:
            linha(f"Tablespace {TABLESPACE}", "não existe no catálogo")
            print("\n  O ETL vai criá-lo sozinho — desde que a pasta de destino")
            print("  exista e esteja vazia.")
            conn.close()
            return

        oid, local = row
        linha(f"Tablespace {TABLESPACE}", f"existe (oid {oid})")
        linha("Aponta para", local or "(vazio)")

        if local and dir_env and local.replace("/", "\\").rstrip("\\").lower() != \
                dir_env.replace("/", "\\").rstrip("\\").lower():
            print("\n  >> ATENÇÃO: o caminho gravado no catálogo é DIFERENTE do")
            print("     CNPJ_TABLESPACE_DIR do .env. O catálogo é quem manda —")
            print("     mudar o .env não move um tablespace já criado.")

        print("\n3. Tabelas bronze")
        for tabela in ("bronze_empresas", "bronze_estabelecimentos", "bronze_simples"):
            cur.execute("SELECT to_regclass(%s)", (tabela,))
            if cur.fetchone()[0] is None:
                linha(tabela, "não existe")
                continue
            try:
                cur.execute(f"SELECT count(*) FROM {tabela}")
                linha(tabela, f"{cur.fetchone()[0]:,} linhas".replace(",", "."))
            except psycopg2.Error as e:
                conn.rollback()
                linha(tabela, f"ILEGÍVEL — {str(e).strip().splitlines()[0][:44]}")

    conn.close()

    print("\n" + "=" * LARGURA)
    print("O QUE FAZER")
    print("=" * LARGURA)

    if not existe_pasta:
        print("""
  A pasta do tablespace não está acessível. Em ordem de probabilidade:

  1. O drive externo está desconectado.
     Conecte o F: e rode o ETL de novo. Se as bronze continuarem legíveis
     (o passo 3 acima mostra as contagens), nada foi perdido e o
     CNPJ_SKIP_BRONZE evita repetir os 30 min de carga.

  2. O drive voltou com OUTRA letra.
     O caminho está gravado no catálogo do PostgreSQL, não no .env —
     editar o .env não resolve. Duas saídas:
       a) devolver a letra antiga pelo Gerenciador de Disco do Windows
          (Iniciar > "Criar e formatar partições" > botão direito no
          volume > "Alterar letra de unidade"); ou
       b) recriar o tablespace apontando para o caminho novo, o que
          obriga a recarregar as bronze do zero.

  3. A pasta foi apagada ou o drive foi formatado.
     Aí os dados das bronze se foram junto. O caminho é recriar a pasta
     (VAZIA) e rodar o ETL SEM o CNPJ_SKIP_BRONZE, refazendo o COPY dos
     ZIPs. A camada Gold no volume padrão continua intacta enquanto isso —
     o dashboard segue funcionando com os dados atuais até a carga nova
     terminar.

  Se optar por abandonar o drive externo, apague CNPJ_TABLESPACE_DIR do
  .env e rode:

      DROP TABLESPACE ts_cnpj_bronze;

  (só funciona depois de derrubar as bronze que moram nele). As bronze
  passam a ocupar ~75 GB no volume padrão do PostgreSQL — confira o espaço
  antes.
""")
    else:
        print("""
  A pasta existe. Se o ETL ainda falhar ao criar arquivos ali, o problema
  é permissão: a conta que roda o serviço do PostgreSQL precisa de
  Controle Total sobre ela.

      Botão direito na pasta > Propriedades > Segurança > Editar
      Adicionar a conta do serviço (normalmente "NETWORK SERVICE" ou
      "postgres") e marcar Controle Total.
""")


if __name__ == "__main__":
    main()
