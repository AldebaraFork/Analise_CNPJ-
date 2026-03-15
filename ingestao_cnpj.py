import pandas as pd
from sqlalchemy import create_engine
import zipfile
import io
import os
import sys

# 1. CONFIGURAÇÃO DO BANCO (Ajuste sua senha do Postgres)
USUARIO = "postgres"
SENHA = "194550" 
HOST = "localhost"
PORTA = "5432"
DB = "tcc_cnpj"

URL_BANCO = f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{DB}"
engine = create_engine(URL_BANCO)

def processar_zip_local():
    # O arquivo que você baixou manualmente
    arquivo_principal = "2026-02.zip"
    # O arquivo que queremos dentro dele
    arquivo_interno = "2026-02/Empresas1.zip"

    if not os.path.exists(arquivo_principal):
        print(f"❌ Erro: O arquivo '{arquivo_principal}' não foi encontrado na pasta!")
        print(f"Diretório atual: {os.getcwd()}")
        return

    try:
        print(f"📦 Abrindo pacote principal: {arquivo_principal}...")
        with zipfile.ZipFile(arquivo_principal) as z_ext:
            
            # Verificando se o Empresas1.zip existe lá dentro
            if arquivo_interno not in z_ext.namelist():
                print(f"❌ Erro: '{arquivo_interno}' não encontrado dentro de {arquivo_principal}")
                return

            print(f"🔍 Extraindo {arquivo_interno} para a memória...")
            with z_ext.open(arquivo_interno) as z_int_bytes:
                
                # Abrindo o Empresas1.zip que está na memória (buffer)
                with zipfile.ZipFile(io.BytesIO(z_int_bytes.read())) as z_int:
                    
                    # Pegando o nome do CSV (Tratando erro de lista do Python 3.14)
                    lista_nomes = z_int.namelist()
                    while isinstance(lista_nomes, list) and len(lista_nomes) > 0:
                        lista_nomes = lista_nomes[0]
                    
                    nome_csv = str(lista_nomes).strip()
                    print(f"⚙️ Processando dados de: {nome_csv}")
                    
                    with z_int.open(nome_csv) as f:
                        print("📊 Lendo 20.000 linhas com Pandas...")
                        # Lemos 20 mil linhas para ter uma amostra boa no TCC
                        df = pd.read_csv(f, sep=";", encoding="latin-1", header=None, nrows=20000, low_memory=False)
                        
                        # Criando o DataFrame final (Lógica do Santander: selecionar só o necessário)
                        df_final = pd.DataFrame()
                        df_final['cnpj_basico'] = df.iloc[:, 0]
                        df_final['razao_social'] = df.iloc[:, 1]
                        df_final['natureza_juridica'] = df.iloc[:, 2]
                        
                        # Limpeza do Capital Social (Vem como '1000,00' -> vira 1000.00)
                        capitais = df.iloc[:, 4].astype(str).str.replace(',', '.')
                        df_final['capital_social'] = pd.to_numeric(capitais, errors='coerce').fillna(0.0)

                        print(f"🚀 Enviando {len(df_final)} registros para a tabela 'empresas_amostra'...")
                        df_final.to_sql('empresas_amostra', con=engine, if_exists='replace', index=False)
                        
                        print("-" * 35)
                        print("✅ SUCESSO! Dados carregados no Postgres.")
                        print("-" * 35)

    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    processar_zip_local()