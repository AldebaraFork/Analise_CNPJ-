"""
Testes das funções de análise de sobrevivência.

Não tocam no banco: exercitam a matemática pura sobre o histograma
(safra x ano da baixa) que as views materializadas produzem.

Cada teste aqui corresponde a um erro que já foi cometido neste projeto ou que
seria fácil cometer. A curva de sobrevivência tem duas armadilhas — contar a
empresa viva como morta, e estender a curva além do que a base permite
observar — e as duas passariam despercebidas numa inspeção visual do gráfico.

    python -m pytest tests/test_analises.py -v
"""

import pandas as pd
import pytest


@pytest.fixture
def histograma():
    """Uma safra de 2015 com 1.000 empresas e mortes espalhadas.

    ano_baixa = -1 é a convenção da MV para 'não baixada até a competência'.
    """
    return pd.DataFrame([
        {"coorte": 2015, "ano_baixa": -1, "qtd": 600},   # ainda vivas
        {"coorte": 2015, "ano_baixa": 0,  "qtd": 100},   # morreram no 1º ano
        {"coorte": 2015, "ano_baixa": 1,  "qtd": 80},
        {"coorte": 2015, "ano_baixa": 2,  "qtd": 70},
        {"coorte": 2015, "ano_baixa": 5,  "qtd": 90},
        {"coorte": 2015, "ano_baixa": 9,  "qtd": 60},
    ])


def test_curva_comeca_em_100(dashboard, histograma, monkeypatch):
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    curva = dashboard.curva_de_sobrevivencia(histograma, 2015)
    assert curva.iloc[0]["anos"] == 0
    assert curva.iloc[0]["pct"] == pytest.approx(100.0)


def test_curva_nunca_sobe(dashboard, histograma, monkeypatch):
    """Sobrevivência é monótona não-crescente. Se subir, a soma acumulada
    está sendo recalculada errado em algum ponto."""
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    pct = dashboard.curva_de_sobrevivencia(histograma, 2015)["pct"].tolist()
    assert all(b <= a + 1e-9 for a, b in zip(pct, pct[1:])), pct


def test_nao_baixadas_contam_como_vivas(dashboard, histograma, monkeypatch):
    """ano_baixa = -1 não pode ser lido como 'morreu no ano -1'.

    Se o filtro `ano_baixa >= 0` sumir, as 600 empresas vivas entrariam na
    soma de mortas já no primeiro ponto e a curva despencaria.
    """
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    curva = dashboard.curva_de_sobrevivencia(histograma, 2015)
    # Mortas até o ano 3: 100 + 80 + 70 = 250 de 1.000 → 75% vivas.
    aos_3 = curva[curva["anos"] == 3]["pct"].iloc[0]
    assert aos_3 == pytest.approx(75.0)
    assert curva["pct"].min() >= 60.0   # nunca abaixo das 600 que seguem vivas


def test_janela_de_observacao_limita_a_curva(dashboard, histograma, monkeypatch):
    """Uma safra de 2015 numa base de 2025 tem 10 anos observáveis — nem um
    a mais. Estender a curva desenharia platô de 100% por falta de tempo
    decorrido, não por resiliência."""
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    curva = dashboard.curva_de_sobrevivencia(histograma, 2015)
    assert curva["anos"].max() == 10
    assert len(curva) == 11          # de 0 a 10, inclusive


def test_safra_recente_tem_janela_curta(dashboard, monkeypatch):
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    df = pd.DataFrame([{"coorte": 2023, "ano_baixa": -1, "qtd": 500},
                       {"coorte": 2023, "ano_baixa": 0, "qtd": 100}])
    curva = dashboard.curva_de_sobrevivencia(df, 2023)
    assert curva["anos"].max() == 2   # 2025 - 2023


def test_safra_inexistente_devolve_vazio(dashboard, histograma, monkeypatch):
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    assert dashboard.curva_de_sobrevivencia(histograma, 1999).empty


def test_curva_por_regime_isola_o_recorte(dashboard, monkeypatch):
    """A curva de um regime não pode contaminar a do outro."""
    monkeypatch.setattr(dashboard, "ULTIMO_ANO_COMPLETO", 2025)
    df = pd.DataFrame([
        {"coorte": 2015, "regime": "MEI", "ano_baixa": -1, "qtd": 400},
        {"coorte": 2015, "regime": "MEI", "ano_baixa": 0, "qtd": 600},
        {"coorte": 2015, "regime": "Regime normal", "ano_baixa": -1, "qtd": 900},
        {"coorte": 2015, "regime": "Regime normal", "ano_baixa": 0, "qtd": 100},
    ])
    mei = dashboard.curva_por_regime(df, 2015, "MEI")
    normal = dashboard.curva_por_regime(df, 2015, "Regime normal")

    assert mei[mei["anos"] == 1]["pct"].iloc[0] == pytest.approx(40.0)
    assert normal[normal["anos"] == 1]["pct"].iloc[0] == pytest.approx(90.0)


def test_top_k_por_mediana_infla_a_mediana_nacional():
    """Regressão conceitual do bug que exibia 20,9 anos de sobrevivência.

    O dashboard calculava a 'mediana nacional' assim:
      1. pegava os 20 setores de MAIOR mediana   → viés de seleção
      2. tirava a média ponderada dessas medianas → média não é mediana

    Os dois erros empilhados. Este teste reconstrói a situação em miniatura:
    18 setores comuns e de vida curta, mais 2 setores longevos e pequenos. O
    procedimento antigo enxerga só os dois longevos e devolve um número uma
    ordem de grandeza acima da mediana verdadeira.
    """
    setores = {f"comum_{i}": pd.Series([1, 2, 2, 3] * 25) for i in range(18)}
    setores["cartorios"] = pd.Series([28, 30, 32])
    setores["siderurgia"] = pd.Series([26, 30, 34])

    # --- procedimento ANTIGO: top 2 por mediana, depois média ponderada ---
    ranking = sorted(setores.items(), key=lambda kv: kv[1].median(), reverse=True)
    top = ranking[:2]
    estimativa_antiga = (
        sum(s.median() * len(s) for _, s in top) / sum(len(s) for _, s in top)
    )

    # --- procedimento CORRETO: percentil sobre o conjunto inteiro ---
    mediana_real = pd.concat(setores.values()).median()

    assert estimativa_antiga == pytest.approx(30.0)
    assert mediana_real == pytest.approx(2.0)
    # Uma ordem de grandeza de diferença — foi o que aconteceu na vida real.
    assert estimativa_antiga > 10 * mediana_real
