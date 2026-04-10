import pandas as pd
from sqlalchemy import create_engine
import zipfile
import os
import time
import numpy as np

# --- CONEXÃO COM O POSTGRES ---
DB_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"
engine = create_engine(DB_URL)

def tratar_dados_simulado():
    # Caminho da pasta onde estão os seus arquivos ZIP
    caminho_pasta = r'C:\Users\eduar\OneDrive\Desktop\tccCNPJ\2026-02\2026-02'
    
    if not os.path.exists(caminho_pasta):
        print(f"❌ Caminho não encontrado: {caminho_pasta}")
        return

    # Busca apenas arquivos de empresas para evitar erro de coluna
    arquivos_zip = [f for f in os.listdir(caminho_pasta) if f.lower().endswith('.zip') and "EMPRE" in f.upper()]
    
    if not arquivos_zip:
        print("❌ Nenhum arquivo ZIP de empresas localizado.")
        return

    print(f"📂 Encontrados {len(arquivos_zip)} arquivos. Iniciando carga com SIMULAÇÃO DE DATAS...")

    primeira_carga = True 

    for nome_zip in arquivos_zip:
        caminho_completo = os.path.join(caminho_pasta, nome_zip)
        print(f"\n📦 Processando: {nome_zip}...")
        
        try:
            with zipfile.ZipFile(caminho_completo, 'r') as z:
                nome_interno = z.namelist()[0]
                with z.open(nome_interno) as f:
                    # Chunksize de 50k para não estourar seus 16GB de RAM
                    reader = pd.read_csv(
                        f, sep=';', encoding='latin-1', header=None, dtype=str, 
                        usecols=[0, 1, 2, 4], chunksize=50000
                    )

                    for i, chunk in enumerate(reader):
                        chunk.columns = ['cnpj_basico', 'razao_social', 'natureza_juridica', 'capital_social']

                        # --- TRATAMENTO E LIMPEZA ---
                        chunk['capital_social'] = pd.to_numeric(chunk['capital_social'].str.replace(',', '.'), errors='coerce').fillna(0)
                        chunk['natureza_juridica'] = pd.to_numeric(chunk['natureza_juridica'], errors='coerce').fillna(0).astype(int)
                        chunk['razao_social'] = chunk['razao_social'].str.strip().str.upper()

                        # --- SIMULAÇÃO DE DATAS (Para o gráfico de BI ter movimento) ---
                        # Como o arquivo Empresa não tem data, geramos aleatórias entre 2018 e 2026
                        intervalo_datas = pd.date_range(start='2018-01-01', end='2026-01-01', freq='D')
                        chunk['data_abertura'] = np.random.choice(intervalo_datas, size=len(chunk))

                        # --- CARGA NO BANCO ---
                        # 'replace' na primeira vez para limpar a estrutura velha e 'append' nas próximas
                        modo = 'replace' if primeira_carga else 'append'
                        chunk.to_sql('empresas_amostra', engine, if_exists=modo, index=False)
                        
                        primeira_carga = False
                        print(f"   > Lote {i+1} (50k linhas) enviado...")
                        
                        # Pausa para o Windows não travar o disco (IO)
                        time.sleep(0.3)
                    
                    # Se quiser carregar apenas o primeiro arquivo para teste rápido, descomente a linha abaixo:
                    # break 

        except Exception as e:
            print(f"⚠️ Erro ao processar {nome_zip}: {e}")

    print("\n🚀 PROCESSO CONCLUÍDO! O banco está pronto e o histórico simulado.")

if __name__ == "__main__":
    tratar_dados_simulado()