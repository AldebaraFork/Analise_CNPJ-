import pandas as pd
from sqlalchemy import create_engine
import zipfile
import io
import os

# 1. FORÇA O WINDOWS A USAR UTF-8 (Isso mata o erro 0xe7)
os.environ["PGCLIENTENCODING"] = "utf8"

# 2. Configuração do Banco (Ajuste sua senha aqui)
USUARIO = "postgres"
SENHA = "194550"
URL_BANCO = f"postgresql://{USUARIO}:{SENHA}@localhost:5432/tcc_cnpj"
engine = create_engine(URL_BANCO)

def carregar_nomes_naturezas():
    arquivo_principal = "2026-02.zip"
    arquivo_interno = "2026-02/Naturezas.zip"

    try:
        print(f"📦 Abrindo pacote principal para buscar Naturezas...")
        with zipfile.ZipFile(arquivo_principal) as z_ext:
            with z_ext.open(arquivo_interno) as z_int_bytes:
                with zipfile.ZipFile(io.BytesIO(z_int_bytes.read())) as z_int:
                    nome_csv = z_int.namelist()[0]
                    with z_int.open(nome_csv) as f:
                        # Lendo as naturezas - Encoding Latin-1 é o padrão dos arquivos da Receita
                        df = pd.read_csv(f, sep=";", encoding="latin-1", header=None)
                        df.columns = ['codigo', 'descricao']
                        
                        # Limpeza extra para garantir que não vai lixo pro banco
                        df['descricao'] = df['descricao'].astype(str).str.strip()
                        
                        print("🚀 Carregando tabela 'naturezas_referencia' no Postgres...")
                        # Usando a engine com o ambiente já configurado para UTF-8
                        df.to_sql('naturezas_referencia', con=engine, if_exists='replace', index=False)
                        print("✅ SUCESSO! Tabela de referência criada.")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    carregar_nomes_naturezas()