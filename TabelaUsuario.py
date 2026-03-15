import psycopg2

# Configurações
conn = psycopg2.connect(host="localhost", database="tcc_cnpj", user="postgres", password="194550")
cur = conn.cursor()

# Cria a tabela de usuários
cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )
""")
conn.commit()
cur.close()
conn.close()
print("✅ Tabela de usuários pronta!")