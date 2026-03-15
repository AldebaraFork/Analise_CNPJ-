from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String) # Certifique-se que tem o P aqui
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)



class Empresa(Base):
    __tablename__ = "empresas_amostra"

    id = Column(Integer, primary_key=True, index=True)
    cnpj_basico = Column(String(8), index=True)
    razao_social = Column(String)
    natureza_juridica = Column(String)
    capital_social = Column(String)