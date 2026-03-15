import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações
USUARIO = "postgres"
SENHA = "194550"
HOST = "localhost"
DB = "tcc_cnpj"

def gerar_analises_completas():
    print("📊 Iniciando geração de todos os gráficos...")
    try:
        conn = psycopg2.connect(host=HOST, database=DB, user=USUARIO, password=SENHA)
        conn.set_client_encoding('UTF8')
        
        # Puxando os dados necessários 
        query = """
            SELECT 
                n.descricao as natureza, 
                e.capital_social
            FROM empresas_amostra e
            JOIN naturezas_referencia n ON CAST(e.natureza_juridica AS INTEGER) = CAST(n.codigo AS INTEGER)
            WHERE e.capital_social > 0
        """
        df = pd.read_sql(query, conn)
        conn.close()

        # --- GRÁFICO 1: MÉDIA POR NATUREZA  ---
        print("📈 Gerando 'grafico_media.png'...")
        plt.figure(figsize=(12, 7))
        top_10 = df.groupby('natureza')['capital_social'].mean().sort_values(ascending=False).head(10)
        sns.barplot(x=top_10.values, y=top_10.index, palette="viridis", hue=top_10.index, legend=False)
        plt.title("Top 10: Investimento Médio por Natureza Jurídica", fontsize=14)
        plt.xlabel("Média de Capital Social (R$)")
        plt.tight_layout()
        plt.savefig("grafico_media.png")
        plt.close()

        # --- GRÁFICO 2: CONTAGEM POR FAIXAS  ---
        print("📈 Gerando 'grafico_distribuicao.png'...")
        bins = [0, 10000, 100000, 1000000, float('inf')]
        labels = ['Até 10k', '10k - 100k', '100k - 1M', 'Acima de 1M']
        df['faixa_capital'] = pd.cut(df['capital_social'], bins=bins, labels=labels)

        plt.figure(figsize=(10, 6))
        sns.countplot(data=df, x='faixa_capital', palette="Blues_d", hue='faixa_capital', legend=False)
        plt.title("Quantidade de Empresas por Faixa de Capital Social", fontsize=14)
        plt.ylabel("Número de Empresas")
        plt.xlabel("Faixa de Investimento")
        plt.tight_layout()
        plt.savefig("grafico_distribuicao.png")
        plt.close()
        
        print("✅ SUCESSO! Ambos os gráficos foram gerados.")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    gerar_analises_completas()