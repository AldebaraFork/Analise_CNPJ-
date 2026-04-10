import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import bcrypt

# --- CONFIGURAÇÃO DE CONEXÃO ---
DB_URL = "postgresql://postgres:194550@localhost:5432/tcc_cnpj"
engine = create_engine(DB_URL)

# --- FUNÇÕES DE SEGURANÇA E BANCO ---
def init_db():
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

def gerar_hash_senha(senha):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_login(email, password):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM usuarios WHERE email = :email")
            df = pd.read_sql(query, conn, params={"email": email})
            if not df.empty:
                hash_banco = df.iloc[0]['senha']
                if bcrypt.checkpw(password.encode('utf-8'), hash_banco.encode('utf-8')):
                    return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def cadastrar_usuario(nome, email, password):
    try:
        hash_seguro = gerar_hash_senha(password)
        with engine.connect() as conn:
            query = text("INSERT INTO usuarios (nome, email, senha) VALUES (:nome, :email, :senha)")
            conn.execute(query, {"nome": nome, "email": email, "senha": hash_seguro})
            conn.commit()
        return True
    except: return False

def excluir_conta_db(email):
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM usuarios WHERE email = :email"), {"email": email})
            conn.commit()
        return True
    except: return False

# --- CACHE DE FILTROS (ESSENCIAL PARA 10M DE LINHAS) ---
@st.cache_data(ttl=3600)
def carregar_opcoes_filtros():
    """Busca as opções de filtros direto das tabelas de referência para ser rápido"""
    try:
        with engine.connect() as conn:
            cnaes = pd.read_sql("SELECT DISTINCT descricao FROM cnaes_referencia ORDER BY 1", conn)
            cidades = pd.read_sql("SELECT DISTINCT descricao FROM municipios_referencia ORDER BY 1", conn)
            return cnaes['descricao'].tolist(), cidades['descricao'].tolist()
    except:
        return [], []

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inteligência CNPJ Gold", layout="wide")
init_db()

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# --- INTERFACE DE ACESSO ---
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Sistema de Inteligência CNPJ")
        t_log, t_cad = st.tabs(["Login", "Criar Conta"])
        
        with t_log:
            e_l = st.text_input("E-mail", key="l_email")
            p_l = st.text_input("Senha", type="password", key="l_pass")
            if st.button("Entrar"):
                u = verificar_login(e_l, p_l)
                if not u.empty:
                    st.session_state['logado'] = True
                    st.session_state['user_nome'] = u.iloc[0]['nome']
                    st.session_state['user_email'] = u.iloc[0]['email']
                    st.rerun()
                else: st.error("Acesso Negado.")
        
        with t_cad:
            n_n = st.text_input("Nome")
            n_e = st.text_input("E-mail")
            n_p = st.text_input("Senha (min 8 carac.)", type="password")
            if st.button("Cadastrar"):
                if len(n_p) >= 8 and cadastrar_usuario(n_n, n_e, n_p):
                    st.success("Cadastrado! Faça o login.")
                else: st.error("Erro no cadastro ou senha curta.")

# --- DASHBOARD LOGADO ---
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👋 Olá, {st.session_state['user_nome']}")
        if st.button("Sair do Sistema", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.subheader("🎯 Filtros Rápidos")
        
        # Carregando filtros via Cache
        lista_cnaes, lista_cidades = carregar_opcoes_filtros()
        
        setor_sel = st.selectbox("Setor (CNAE)", ["Todos"] + lista_cnaes)
        cidade_sel = st.selectbox("Cidade", ["Todas"] + lista_cidades)
        
        st.markdown("---")
        with st.expander("⚙️ Gerenciar Conta"):
            confirma = st.checkbox("Confirmar exclusão")
            if st.button("EXCLUIR MINHA CONTA", type="primary"):
                if confirma and excluir_conta_db(st.session_state['user_email']):
                    st.session_state.clear()
                    st.rerun()

    # --- CORPO DO DASHBOARD ---
    st.title("📊 Conselho de Análise Estratégica (Dados Reais)")

    try:
        with engine.connect() as conn:
            # SQL OTIMIZADO: Usamos joins e filtros diretos
            sql = """
                SELECT e.razao_social, e.capital_social, e.data_abertura, 
                       c.descricao as setor, m.descricao as cidade
                FROM empresas_gold e
                LEFT JOIN cnaes_referencia c ON e.cnae_fiscal = c.codigo
                LEFT JOIN municipios_referencia m ON e.cod_municipio = m.codigo
                WHERE e.capital_social > 0
            """
            
            if setor_sel != "Todos":
                sql += f" AND c.descricao = '{setor_sel}'"
            if cidade_sel != "Todas":
                sql += f" AND m.descricao = '{cidade_sel}'"
            
            # Limitamos em 30k para garantir que o Streamlit não trave os 16GB de RAM
            sql += " LIMIT 30000"
            
            df = pd.read_sql(text(sql), conn)

        if not df.empty:
            df['data_abertura'] = pd.to_datetime(df['data_abertura'])
            df['ano'] = df['data_abertura'].dt.year

            # KPIs Superiores
            k1, k2, k3 = st.columns(3)
            k1.metric("Empresas Identificadas", f"{len(df):,}")
            k2.metric("Capital Total", f"R$ {df['capital_social'].sum():,.2f}")
            k3.metric("Média de Capital", f"R$ {df['capital_social'].mean():,.2f}")

            st.divider()

            # GRÁFICOS
            col_esq, col_dir = st.columns([2, 1])
            with col_esq:
                st.subheader("📈 Histórico Real de Abertura")
                df_evol = df.groupby('ano').size().reset_index(name='qtd')
                fig_l = px.line(df_evol, x='ano', y='qtd', markers=True, template="plotly_dark")
                st.plotly_chart(fig_l, use_container_width=True)
            
            with col_dir:
                st.subheader("🍕 Divisão por Cidade")
                # Mostra as top cidades no gráfico para não virar bagunça
                df_top_cidades = df.groupby('cidade')['capital_social'].sum().nlargest(10).reset_index()
                fig_p = px.pie(df_top_cidades, names='cidade', values='capital_social', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)

            st.divider()

            # TABELA RANKING
            st.subheader("🏆 Maiores Empresas do Recorte")
            st.dataframe(
                df.nlargest(20, 'capital_social'), 
                use_container_width=True, hide_index=True,
                column_config={
                    "capital_social": st.column_config.NumberColumn("Capital (R$)", format="R$ %.2f"),
                    "data_abertura": st.column_config.DateColumn("Abertura")
                }
            )
        else:
            st.warning("⚠️ Nenhum dado encontrado. Tente ajustar os filtros.")

    except Exception as e:
        st.error(f"❌ Erro de Processamento: {e}")