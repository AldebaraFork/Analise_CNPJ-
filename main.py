from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
import models, security

# Cria as tabelas do zero ao iniciar (se você deu o DROP TABLE, ele recria certo)

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/cadastro")
def cadastrar_usuario(nome: str, email: str, senha: str, db: Session = Depends(get_db)):
    # 1. Verifica se o e-mail já existe
    email_existe = db.query(models.User).filter(models.User.email == email).first()
    if email_existe:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    # 2. Cria o usuário usando o nome correto: nome_completo
    novo_usuario = models.User(
        nome_completo=nome,
        email=email,
        hashed_password=security.gerar_hash_senha(senha)
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return {"mensagem": "Usuário criado com sucesso!", "usuario": novo_usuario.email}

@app.post("/login")
def login(email_digitado: str, senha_digitada: str, db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.email == email_digitado).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    senha_valida = security.verificar_senha(senha_digitada, usuario.hashed_password)
    
    if not senha_valida:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    return {"mensagem": f"Bem-vindo {usuario.nome_completo}, login realizado!"}