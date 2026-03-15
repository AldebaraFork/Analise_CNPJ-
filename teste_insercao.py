from database import SessionLocal
import models, security

def inserir_usuario_teste():
    db = SessionLocal()
    
    # Dados do seu usuário de teste
    nome = "Usuario Teste"
    email = "teste@email.com"
    senha_pura = "123456"
    
    # Verifica se já existe para não dar erro
    existe = db.query(models.User).filter(models.User.email == email).first()
    if existe:
        print("Usuário de teste já existe no banco!")
        return

    # Criando o usuário com HASH na senha
    novo_usuario = models.User(
        full_name=nome,
        email=email,
        hashed_password=security.gerar_hash_senha(senha_pura)
    )

    db.add(novo_usuario)
    db.commit()
    print(f"Usuário {email} inserido com sucesso! Senha: {senha_pura}")
    db.close()

if __name__ == "__main__":
    inserir_usuario_teste()