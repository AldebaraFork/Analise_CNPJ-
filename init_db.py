from database import engine, Base
import models

# Esse comando olha o models.py e cria as tabelas no Postgres
print("Criando tabelas no banco de dados...")
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso!")