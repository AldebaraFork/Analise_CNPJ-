import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import re

# --- CONFIGURAÇÕES DE CONEXÃO ---
DB_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"
engine = create_engine(DB_URL)

def init_db():
    """Garante que a tabela existe com a estrutura correta"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            );
        """))
        conn.commit()

# --- FUNÇÕES DE LÓGICA E VALIDAÇÃO ---
def validar_senha(senha):
    """Verifica se tem 8+ caracteres e uma letra maiúscula"""
    if len(senha) < 8:
        return False, "A senha deve ter no mínimo 8 caracteres."
    if not any(c.isupper() for c in senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    return True, ""

def cadastrar_usuario(nome, email, password):
    try:
        with engine.connect() as conn:
            query = text("INSERT INTO usuarios (nome, email, senha) VALUES (:nome, :email, :senha)")
            conn.execute(query, {"nome": nome, "email": email, "senha": password})
            conn.commit()
        return True
    except Exception:
        return False

def excluir_conta(email):
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM usuarios WHERE email = :email")
            conn.execute(query, {"email": email})
            conn.commit()
        return True
    except Exception:
        return False

def verificar_login(email, password):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM usuarios WHERE email = :email AND senha = :senha")
            df = pd.read_sql(query, conn, params={"email": email, "senha": password})
            return df
    except Exception:
        return pd.DataFrame()

# --- INTERFACE ---
st.set_page_config(page_title="Board CNPJ Brasil", layout="wide")
init_db()

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Sistema de Inteligência CNPJ")
    tab_login, tab_cad = st.tabs(["Login", "Criar Conta"])

    with tab_login:
        email_l = st.text_input("E-mail", key="login_email")
        pass_l = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            user = verificar_login(email_l, pass_l)
            if not user.empty:
                st.session_state['logado'] = True
                st.session_state['user_nome'] = user.iloc[0]['nome']
                st.session_state['user_email'] = user.iloc[0]['email']
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

    with tab_cad:
        n_nome = st.text_input("Nome Completo", key="cad_nome")
        n_email = st.text_input("E-mail", key="cad_email")
        n_pass = st.text_input("Nova Senha", type="password", help="Mínimo 8 caracteres e 1 letra maiúscula")
        
        if st.button("Cadastrar"):
            # Validação de Senha
            senha_valida, msg_erro = validar_senha(n_pass)
            
            if not senha_valida:
                st.error(msg_erro)
            elif cadastrar_usuario(n_nome, n_email, n_pass):
                st.success("Cadastro realizado! Faça o login.")
            else:
                st.error("Erro ao cadastrar. E-mail já existe.")

else:
    # --- ÁREA LOGADA (BOARD) ---
    st.sidebar.title(f"Olá, {st.session_state['user_nome']}")
    
    # Seção de Configurações na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configurações da Conta")
    
    if st.sidebar.button("Fazer Logout"):
        st.session_state.clear()
        st.rerun()

    # Opção de Excluir Conta
    with st.sidebar.expander("❌ Excluir Minha Conta"):
        st.warning("Ação irreversível!")
        confirma = st.checkbox("Confirmo que desejo apagar meus dados")
        if st.button("EXCLUIR DEFINITIVAMENTE"):
            if confirma:
                if excluir_conta(st.session_state['user_email']):
                    st.toast("Conta excluída com sucesso.")
                    st.session_state.clear()
                    st.rerun()
            else:
                st.error("Marque a confirmação primeiro.")

    # --- CONTEÚDO DO BOARD ---
    st.title("📊 Board de Análise Estratégica")
    
    with engine.connect() as conn:
        query = text("""
            SELECT e.razao_social, n.descricao as natureza, e.capital_social 
            FROM empresas_amostra e
            JOIN naturezas_referencia n ON CAST(e.natureza_juridica AS INTEGER) = CAST(n.codigo AS INTEGER)
            WHERE e.capital_social > 0
        """)
        df = pd.read_sql(query, conn)

    # Métricas
    c1, c2 = st.columns(2)
    c1.metric("Empresas Analisadas", len(df))
    c2.metric("Capital Social Total", f"R$ {df['capital_social'].sum():,.2f}")

    # Visualização
    fig = px.pie(df, names='natureza', values='capital_social', hole=0.4, 
                 title="Distribuição do Capital por Natureza Jurídica")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Maiores Empresas (Amostra)")
    st.table(df.nlargest(5, 'capital_social')[['razao_social', 'capital_social']])