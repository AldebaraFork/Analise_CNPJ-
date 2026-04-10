import pandas as pd
from sqlalchemy import create_engine
import zipfile
import os

DB_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"
engine = create_engine(DB_URL)

def carregar_referencias():
    caminho_pasta = r'C:\Users\eduar\OneDrive\Desktop\tccCNPJ\2026-02\2026-02'
    
    # Lista de arquivos de referência para carregar
    referencias = {
        'Cnaes': 'cnaes_referencia',
        'Municipios': 'municipios_referencia',
        'Naturezas': 'naturezas_referencia'
    }

    for arquivo, tabela in referencias.items():
        zip_path = os.path.join(caminho_pasta, f"{arquivo}.zip")
        if os.path.exists(zip_path):
            print(f"⏳ Carregando referência: {arquivo}...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                nome_csv = z.namelist()[0]
                with z.open(nome_csv) as f:
                    # Esses arquivos são pequenos, pode ler direto
                    df = pd.read_csv(f, sep=';', encoding='latin-1', header=None, dtype=str)
                    df.columns = ['codigo', 'descricao']
                    df['codigo'] = pd.to_numeric(df['codigo'], errors='coerce')
                    
                    df.to_sql(tabela, engine, if_exists='replace', index=False)
                    print(f"✅ Tabela {tabela} criada com {len(df)} registros.")
        else:
            print(f"⚠️ Arquivo {arquivo}.zip não encontrado.")

if __name__ == "__main__":
    carregar_referencias()