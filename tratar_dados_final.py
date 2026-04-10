import pandas as pd
from sqlalchemy import create_engine
import zipfile
import os
import time

# --- CONEXÃO COM O POSTGRES ---
DB_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"
engine = create_engine(DB_URL)

def processar_dados_reais():
    caminho_pasta = r'C:\Users\eduar\OneDrive\Desktop\tccCNPJ\2026-02\2026-02'
    
    # Definindo a amostra para 1 milhão de registros
    amostra = 50000000
    
    if not os.path.exists(caminho_pasta):
        print(f"❌ Pasta não encontrada: {caminho_pasta}")
        return

    print(f"📂 Iniciando processamento de {amostra} registros (Base Real)...")

    try:
        # 1. PROCESSAMENTO DE EMPRESAS
        print(f"⏳ Lendo Empresas0.zip...")
        zip_emp = os.path.join(caminho_pasta, "Empresas0.zip")
        with zipfile.ZipFile(zip_emp, 'r') as z:
            with z.open(z.namelist()[0]) as f:
                df_emp = pd.read_csv(f, sep=';', encoding='latin-1', header=None, dtype=str, 
                                     usecols=[0, 1, 4], nrows=amostra)
                df_emp.columns = ['cnpj_basico', 'razao_social', 'capital_social']

        # 2. PROCESSAMENTO DE ESTABELECIMENTOS
        print(f"⏳ Lendo Estabelecimentos0.zip...")
        zip_est = os.path.join(caminho_pasta, "Estabelecimentos0.zip")
        with zipfile.ZipFile(zip_est, 'r') as z:
            with z.open(z.namelist()[0]) as f:
                # 0: CNPJ Básico, 10: Data Abertura, 11: CNAE Fiscal, 20: Município
                df_est = pd.read_csv(f, sep=';', encoding='latin-1', header=None, dtype=str, 
                                     usecols=[0, 10, 11, 20], nrows=amostra)
                df_est.columns = ['cnpj_basico', 'data_abertura', 'cnae_fiscal', 'cod_municipio']

        # 3. LIMPEZA TÉCNICA (Garante que o Join não falhe por zeros à esquerda)
        print("🧹 Limpando chaves de CNPJ...")
        df_emp['cnpj_basico'] = df_emp['cnpj_basico'].str.lstrip('0')
        df_est['cnpj_basico'] = df_est['cnpj_basico'].str.lstrip('0')

        # 4. CRUZAMENTO DE DADOS (INNER JOIN)
        print("🔄 Cruzando as bases (Merge)...")
        df_final = pd.merge(df_emp, df_est, on='cnpj_basico', how='inner')
        
        print(f"📊 Cruzamento concluído: {len(df_final):,} empresas encontradas em comum.")

        if len(df_final) > 0:
            # 5. TRATAMENTO DE TIPOS E FORMATOS
            print("🔧 Formatando tipos de dados...")
            df_final['capital_social'] = pd.to_numeric(df_final['capital_social'].str.replace(',', '.'), errors='coerce').fillna(0)
            df_final['data_abertura'] = pd.to_datetime(df_final['data_abertura'], format='%Y%m%d', errors='coerce')
            df_final['cnae_fiscal'] = pd.to_numeric(df_final['cnae_fiscal'], errors='coerce').fillna(0).astype(int)
            df_final['cod_municipio'] = pd.to_numeric(df_final['cod_municipio'], errors='coerce').fillna(0).astype(int)
            df_final['razao_social'] = df_final['razao_social'].str.strip().str.upper()

            # 6. CARGA FINAL PARA A TABELA GOLD
            print(f"🚀 Enviando {len(df_final):,} registros para a tabela GOLD no Postgres...")
            # Usando chunksize para não sobrecarregar a memória do banco de dados durante a inserção
            df_final.to_sql('empresas_gold', engine, if_exists='replace', index=False, chunksize=50000)
            
            print("\n✅ PROCESSO FINALIZADO COM SUCESSO!")
            print(f"Total de registros na GOLD: {len(df_final):,}")
        else:
            print("❌ ERRO: O cruzamento resultou em 0 linhas. Verifique a integridade dos ZIPs.")

    except Exception as e:
        print(f"⚠️ Erro crítico durante o ETL: {e}")

if __name__ == "__main__":
    start_time = time.time()
    processar_dados_reais()
    print(f"⏱️ Tempo total de execução: {round((time.time() - start_time)/60, 2)} minutos")