from passlib.context import CryptContext

# Aqui definimos que vamos usar o algoritmo bcrypt (padrão de mercado)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha_pura: str):
    """Transforma nosasa senha em um hash em '$2b$12$Kpx...'"""
    return pwd_context.hash(senha_pura)

def verificar_senha(senha_pura, senha_hash):
    """Compara a senha que o usuário digitou com o hash do banco"""
    return pwd_context.verify(senha_pura, senha_hash)