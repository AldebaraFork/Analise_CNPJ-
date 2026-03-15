from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#python -m uvicorn main:app --reload
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função que abre a conexão e garante que ela feche depois de usar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()