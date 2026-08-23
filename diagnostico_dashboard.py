"""
Prova numérica dos quatro bugs de apresentação do dashboard.

Cada bloco roda a consulta ANTIGA (a que o dashboard fazia) e a NOVA lado a
lado, sobre a mesma empresas_gold. Se os pares baterem, o bug não era de
apresentação e a investigação tem de voltar para o ETL. Se divergirem como
descrito, a base está certa e era a pergunta que estava errada.

    python diagnostico_dashboard.py

Pré-requisito: python aplicar_indices.py mv_correcoes_painel.sql
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()

COMPETENCIA = os.environ.get("CNPJ_COMPETENCIA", "2026-02-28")

LARGURA = 78


def titulo(n: int, texto: str) -> None:
    print(f"\n{'=' * LARGURA}\nBUG {n} — {texto}\n{'=' * LARGURA}")


def linha(rotulo: str, valor) -> None:
    print(f"  {rotulo:<44} {valor}")


def checar_pre_requisitos(cur) -> None:
    """Falha cedo e com mensagem clara em vez de estourar no meio do relatório."""
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'empresas_gold' AND column_name = 'uf'
    """)
    if not cur.fetchone():
        sys.exit(
            "empresas_gold não tem a coluna 'uf' — esta é a Gold antiga.\n"
            "Rode 'python etl_cnpj.py' antes deste diagnóstico."
        )

    faltando = []
    for mv in ("mv_sobrevivencia_geral", "mv_kpis_uf", "mv_crescimento_uf",
               "mv_painel_ano", "mv_painel_cidade"):
        cur.execute("SELECT to_regclass(%s)", (mv,))
        if cur.fetchone()[0] is None:
            faltando.append(mv)
    if faltando:
        sys.exit(
            "Views ausentes: " + ", ".join(faltando) + "\n"
            "Rode: python aplicar_indices.py mv_correcoes_painel.sql"
        )


def bug1_limit_30000(cur) -> None:
    titulo(1, "LIMIT 30000 sem ORDER BY no painel principal")

    # Exatamente a consulta antiga do dashboard.
    cur.execute("""
        WITH amostra AS (
            SELECT e.data_abertura, e.capital_social, e.cod_municipio
            FROM empresas_gold e
            LEFT JOIN cnaes_referencia      c ON e.cnae_fiscal   = c.codigo
            LEFT JOIN municipios_referencia m ON e.cod_municipio = m.codigo
            WHERE e.capital_social > 0
            LIMIT 30000
        )
        SELECT count(*),
               min(EXTRACT(YEAR FROM data_abertura))::int,
               max(EXTRACT(YEAR FROM data_abertura))::int,
               round(avg(capital_social)::numeric, 2),
               mode() WITHIN GROUP (ORDER BY EXTRACT(YEAR FROM data_abertura)::int)
        FROM amostra
    """)
    n, ano_min, ano_max, cap_medio, ano_moda = cur.fetchone()

    # Quanto da "amostra" cai no ano mais frequente dela.
    cur.execute("""
        WITH amostra AS (
            SELECT EXTRACT(YEAR FROM e.data_abertura)::int AS ano
            FROM empresas_gold e
            WHERE e.capital_social > 0
            LIMIT 30000
        )
        SELECT round(100.0 * count(*) FILTER (WHERE ano = %s) / count(*), 1)
        FROM amostra
    """, (ano_moda,))
    concentracao = cur.fetchone()[0]

    print("\n ANTES — as 30 mil linhas que o dashboard plotava:")
    linha("linhas", f"{n:,}".replace(",", "."))
    linha("intervalo de anos", f"{ano_min} a {ano_max}")
    linha("ano mais frequente", ano_moda)
    linha("% da amostra nesse único ano", f"{concentracao}%")
    linha("capital médio da amostra", f"R$ {cap_medio:,.2f}")

    cur.execute("""
        SELECT SUM(empresas),
               round((SUM(capital_total) / SUM(empresas))::numeric, 2),
               min(ano), max(ano)
        FROM mv_painel_ano
    """)
    total, cap_real, ano_ini, ano_fim = cur.fetchone()
    total = int(total)

    cur.execute("""
        SELECT ano, empresas
        FROM mv_painel_ano
        ORDER BY empresas DESC
        LIMIT 1
    """)
    ano_pico, qtd_pico = cur.fetchone()

    print("\n DEPOIS — a base inteira, agregada no PostgreSQL:")
    linha("empresas com capital > 0", f"{total:,}".replace(",", "."))
    linha("intervalo de anos", f"{ano_ini} a {ano_fim}")
    linha("ano de pico real", f"{ano_pico} ({qtd_pico:,} aberturas)".replace(",", "."))
    linha("capital médio real", f"R$ {cap_real:,.2f}")

    print(f"\n  A amostra representa {100.0 * n / total:.3f}% da base.")

    # Qual plano o PostgreSQL escolhe define QUAIS 30 mil linhas voltam. Não é
    # sorteio: se entrar pelo índice parcial de capital, volta o topo da lista
    # de capital social; se for Seq Scan, volta a ordem física da tabela.
    # Melhor ler o plano real do que supor.
    cur.execute("""
        EXPLAIN (COSTS OFF)
        SELECT e.razao_social, e.capital_social, e.data_abertura
        FROM empresas_gold e
        LEFT JOIN cnaes_referencia      c ON e.cnae_fiscal   = c.codigo
        LEFT JOIN municipios_referencia m ON e.cod_municipio = m.codigo
        WHERE e.capital_social > 0
        LIMIT 30000
    """)
    print("\n  Plano que decidia quais 30 mil linhas o gráfico recebia:")
    for (passo,) in cur.fetchall():
        print(f"    {passo}")


def bug2_mediana_sobrevivencia(cur) -> None:
    titulo(2, "Mediana de sobrevivência: média de medianas de um top enviesado")

    cur.execute("""
        SELECT round(SUM(mediana * total) / SUM(total), 1),
               round(SUM(media   * total) / SUM(total), 1),
               SUM(total)
        FROM (
            SELECT mediana, media, total
            FROM mv_sobrevivencia_setor
            ORDER BY mediana DESC
            LIMIT 20
        ) t
    """)
    med_falsa, media_falsa, total_falso = cur.fetchone()
    total_falso = int(total_falso)

    print("\n ANTES — média ponderada das medianas dos 20 setores mais longevos:")
    linha("'mediana' exibida", f"{med_falsa} anos")
    linha("'média' exibida", f"{media_falsa} anos")
    linha("baixadas consideradas", f"{total_falso:,}".replace(",", "."))

    cur.execute("SELECT total, media, mediana, q1, q3, p90 FROM mv_sobrevivencia_geral")
    total, media, mediana, q1, q3, p90 = cur.fetchone()

    print("\n DEPOIS — percentile_cont sobre TODAS as baixadas:")
    linha("mediana nacional", f"{mediana} anos")
    linha("média nacional", f"{media} anos")
    linha("quartis (q1 / q3 / p90)", f"{q1} / {q3} / {p90} anos")
    linha("baixadas consideradas", f"{total:,}".replace(",", "."))

    cobertura = 100.0 * total_falso / total
    print(f"\n  O recorte antigo cobria {cobertura:.1f}% das baixadas, escolhidas")
    print("  justamente por terem a maior mediana. Média de medianas também não")
    print("  é mediana: as duas coisas se somavam.")

    # Confronto com o IBGE: ~60% não chegam aos 5 anos.
    cur.execute("""
        WITH duracao AS (
            SELECT (data_situacao - data_abertura) / 365.25 AS anos
            FROM empresas_gold
            WHERE situacao_cadastral = 8
              AND data_situacao IS NOT NULL
              AND data_situacao >= data_abertura
        )
        SELECT round(100.0 * count(*) FILTER (WHERE anos < 5) / count(*), 1)
        FROM duracao
    """)
    print(f"\n  Validação cruzada — baixadas com menos de 5 anos: {cur.fetchone()[0]}%")
    print("  (IBGE aponta ~60% de mortalidade antes dos 5 anos)")


def bug3_uf_falsa(cur) -> None:
    titulo(3, "UF derivada de LEFT(cod_municipio,2) — não é código IBGE")

    cur.execute("""
        SELECT LEFT(cod_municipio::text, 2) AS pseudo_uf, count(*)
        FROM empresas_gold
        GROUP BY 1 ORDER BY 2 DESC LIMIT 5
    """)
    print("\n ANTES — 'UFs' que o comparador oferecia:")
    for pseudo, qtd in cur.fetchall():
        linha(f"grupo {pseudo}", f"{qtd:,}".replace(",", "."))

    cur.execute("""
        SELECT uf, total_empresas FROM mv_kpis_uf
        ORDER BY total_empresas DESC LIMIT 5
    """)
    print("\n DEPOIS — UFs de verdade, da coluna uf:")
    for uf, qtd in cur.fetchall():
        linha(uf, f"{qtd:,}".replace(",", "."))

    # A prova de que o agrupamento antigo cruzava fronteiras estaduais.
    cur.execute("""
        SELECT LEFT(cod_municipio::text, 2) AS pseudo_uf,
               count(DISTINCT uf)           AS ufs_misturadas,
               string_agg(DISTINCT uf, ', ' ORDER BY uf)
        FROM empresas_gold
        WHERE cod_municipio IS NOT NULL AND uf IS NOT NULL
        GROUP BY 1
        HAVING count(DISTINCT uf) > 1
        ORDER BY 2 DESC
        LIMIT 5
    """)
    misturas = cur.fetchall()
    if misturas:
        print("\n  Grupos que juntavam estados diferentes num 'estado' só:")
        for pseudo, n_ufs, lista in misturas:
            linha(f"grupo {pseudo} ({n_ufs} UFs)", lista[:60])
    else:
        print("\n  Nenhum grupo cruzou fronteira estadual — a coincidência era")
        print("  parcial, mas o rótulo continuava errado.")


def bug4_ano_parcial(cur) -> None:
    titulo(4, f"Ano da competência ({COMPETENCIA[:4]}) é parcial")

    cur.execute("""
        SELECT EXTRACT(YEAR FROM data_abertura)::int AS ano, count(*)
        FROM empresas_gold
        WHERE data_abertura IS NOT NULL
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 4
    """)
    print("\n Aberturas nos últimos anos da base:")
    for ano, qtd in cur.fetchall():
        linha(str(ano), f"{qtd:,}".replace(",", "."))

    cur.execute("SELECT max(data_abertura) FROM empresas_gold")
    print()
    linha("data de abertura mais recente", cur.fetchone()[0])
    linha("competência configurada", COMPETENCIA)

    cur.execute("""
        SELECT count(*) FROM empresas_gold WHERE data_abertura > %s
    """, (COMPETENCIA,))
    depois = cur.fetchone()[0]
    linha("registros posteriores à competência", f"{depois:,}".replace(",", "."))

    print("\n  A queda no último ponto de toda série era esta: a base termina na")
    print("  competência, não a atividade empresarial. Os gráficos agora encerram")
    print("  no último ano completo.")


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL ausente. Preencha o .env.")

    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            checar_pre_requisitos(cur)
            bug1_limit_30000(cur)
            bug2_mediana_sobrevivencia(cur)
            bug3_uf_falsa(cur)
            bug4_ano_parcial(cur)

    print(f"\n{'=' * LARGURA}")
    print("Nenhum destes números depende de recarregar a base: os quatro saem da")
    print("mesma empresas_gold. O que mudou foi a pergunta feita a ela.")
    print(f"{'=' * LARGURA}\n")


if __name__ == "__main__":
    main()
