"""
Carrossel LinkedIn — "A caçada ao 44,5"
Gera um PDF de 3 páginas (formato aceito pelo LinkedIn como documento/carrossel)
+ PNGs individuais para preview.

Arco:
  1. O número publicado que estava errado (44,5)
  2. A base estava limpa — o problema era o join (1 em 200.000)
  3. 16% → 100%: a distribuição corrigida (81% → 39,4% na década de 2020)

Todos os números são reais, apurados sobre a base reconstruída (fev/2026).
Não requer conexão ao banco: as constantes abaixo já vêm do metricas_post.py.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---------------------------------------------------------------- CONFIG
W, H, DPI = 1080, 1350, 200
FIGSIZE = (W / DPI, H / DPI)

BG      = "#12161C"
FG      = "#F2F5F8"
MUTED   = "#8B98A8"
ACCENT  = "#4C8DFF"
WARN    = "#FF6B4A"
OK      = "#3DD68C"
GRID    = "#232A34"

NUM_ERRADO = "44,5"
MEDIANA    = "3,3"
BASE_ANTIGA_PCT = "16%"
CONC_ANTIGA = 81        # % na década de 2020 na base bugada
CONC_NOVA   = 39.4      # % na década de 2020 na base correta

# Distribuição real por década (metricas_post.py) — percentuais
DECADAS = [
    ("60", 0.4), ("70", 2.2), ("80", 5.9), ("90", 8.7),
    ("00", 10.6), ("10", 32.9), ("20", 39.4),
]


def novo_slide():
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def rodape(ax, n):
    ax.text(0.08, 0.055, "Eduardo Pereira de Amorim", color=MUTED,
            fontsize=8.5, va="center")
    ax.text(0.92, 0.055, f"{n}/3", color=MUTED, fontsize=8.5,
            va="center", ha="right")
    ax.plot([0.08, 0.92], [0.093, 0.093], color=GRID, lw=1)


# ---------------------------------------------------------------- SLIDE 1
def slide1():
    fig, ax = novo_slide()
    ax.text(0.08, 0.88, "THE NUMBER I PUBLISHED", color=WARN,
            fontsize=11, weight="bold")
    ax.text(0.08, 0.845, "O número que eu publiquei", color=MUTED, fontsize=10.5)

    ax.text(0.08, 0.66, NUM_ERRADO, color=FG, fontsize=118, weight="bold", va="center")
    ax.text(0.08, 0.545, "anos  ·  years", color=MUTED, fontsize=17, va="center")
    ax.plot([0.085, 0.80], [0.665, 0.665], color=WARN, lw=5)

    ax.text(0.08, 0.44,
            "“Empresas baixadas duraram em média\n44,5 anos ativas”",
            color=FG, fontsize=15.5, va="top", linespacing=1.55, style="italic")

    ax.plot([0.08, 0.12], [0.335, 0.335], color=WARN, lw=3)
    ax.text(0.08, 0.275, "Estava errado.", color=WARN, fontsize=25,
            weight="bold", va="center")
    ax.text(0.08, 0.215, "It was wrong. Here's how I found out.",
            color=MUTED, fontsize=13.5, va="center")
    rodape(ax, 1)
    return fig


# ---------------------------------------------------------------- SLIDE 2
def slide2():
    fig, ax = novo_slide()
    ax.text(0.08, 0.90, "THE DATA WAS CLEAN", color=OK,
            fontsize=11, weight="bold")
    ax.text(0.08, 0.865, "A base estava limpa — o problema era o join",
            color=MUTED, fontsize=10.5)

    ax.text(0.08, 0.80,
            "Meu ETL cruzava Empresas0.zip com\nEstabelecimentos0.zip — shard 0 com 0.",
            color=FG, fontsize=13.5, va="top", linespacing=1.5)

    ax.text(0.08, 0.66,
            "Mas os arquivos são fatiados diferente:\n"
            "Empresas por CNPJ, Estabelecimentos embaralhado.",
            color=MUTED, fontsize=13, va="top", linespacing=1.5)

    # O número-choque
    ax.text(0.08, 0.45, "1", color=WARN, fontsize=95, weight="bold", va="center")
    ax.text(0.28, 0.485, "registro em comum", color=FG, fontsize=17, va="center")
    ax.text(0.28, 0.435, "a cada 200.000 medidos", color=MUTED, fontsize=14, va="center")
    ax.text(0.28, 0.395, "1 shared record per 200,000", color=MUTED,
            fontsize=11.5, va="center", style="italic")

    ax.plot([0.08, 0.12], [0.29, 0.29], color=WARN, lw=3)
    ax.text(0.08, 0.235,
            "Eu cruzava dados que nunca batiam.",
            color=FG, fontsize=15, weight="bold", va="center")
    ax.text(0.08, 0.185, "I was joining data that never matched.",
            color=MUTED, fontsize=12.5, va="center")
    rodape(ax, 2)
    return fig


# ---------------------------------------------------------------- SLIDE 3
def slide3():
    fig, ax = novo_slide()
    ax.text(0.08, 0.925, "16% → 100%", color=ACCENT, fontsize=11, weight="bold")
    ax.text(0.08, 0.892, "A base inteira, com o join correto", color=MUTED, fontsize=10.5)
    ax.text(0.08, 0.845,
            f"Eu analisava {BASE_ANTIGA_PCT} do Brasil",
            color=FG, fontsize=18, weight="bold", va="top")

    # Barras de distribuição por década (base correta)
    g = fig.add_axes([0.11, 0.40, 0.81, 0.36]); g.set_facecolor(BG)
    rotulos = [d for d, _ in DECADAS]
    valores = [v for _, v in DECADAS]
    cores = [ACCENT] * (len(DECADAS) - 1) + [OK]
    g.bar(rotulos, valores, color=cores, edgecolor="none")
    g.text(len(DECADAS) - 1, CONC_NOVA + 1.5, f"{CONC_NOVA}%",
           color=OK, fontsize=13, weight="bold", ha="center")
    g.set_ylim(0, 48)
    g.set_ylabel("% das empresas", color=MUTED, fontsize=10)
    g.set_xlabel("Década de abertura  ·  Founding decade", color=MUTED, fontsize=10, labelpad=6)
    g.tick_params(colors=MUTED, labelsize=10)
    for s in ("top", "right", "left"):
        g.spines[s].set_visible(False)
    g.spines["bottom"].set_color(GRID)

    ax.text(0.08, 0.325,
            f"Base bugada: {CONC_ANTIGA}% numa década só.\n"
            f"Base correta: {CONC_NOVA}% — distribuição real.",
            color=FG, fontsize=13.5, va="top", linespacing=1.7)

    ax.text(0.08, 0.185, "Validar o dado ≠ validar o pipeline",
            color=ACCENT, fontsize=15.5, weight="bold", va="center")
    ax.text(0.08, 0.145, "Validating the data isn't validating the pipeline.",
            color=MUTED, fontsize=12, va="center")
    rodape(ax, 3)
    return fig


if __name__ == "__main__":
    figs = [slide1(), slide2(), slide3()]
    with PdfPages("carrossel_44_5.pdf") as pdf:
        for f in figs:
            pdf.savefig(f, facecolor=BG)
    for i, f in enumerate(figs, 1):
        f.savefig(f"slide{i}.png", facecolor=BG, dpi=DPI)
    print("ok: carrossel_44_5.pdf + slide1..3.png")
