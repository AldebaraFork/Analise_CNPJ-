# 🏛️ Board de Inteligência: Mercado Empresarial (CNPJ Brasil)

Este projeto é uma aplicação de **Engenharia de Dados** desenvolvida para processar, armazenar e visualizar dados públicos da Receita Federal. A plataforma permite analisar o capital social de empresas brasileiras através de um dashboard interativo com controle de acesso.

## 🚀 Status do Projeto
Atualmente em desenvolvimento (Fase de Implementação de Segurança e Gestão de Usuários).

| Funcionalidade | Status |
| :--- | :--- |
| Ingestão de Dados (ETL) | ✅ Concluído |
| Dashboard Interativo | ✅ Concluído |
| Sistema de Login/Cadastro | 🚀 **Em Progresso** |
| Validação de Senha Forte | 🚀 **Em Progresso** |
| Exclusão de Conta (LGPD) | 🚀 **Em Progresso** |
| Exportação para Excel | ⏳ Pendente |

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.14
* **Interface:** [Streamlit](https://streamlit.io/)
* **Banco de Dados:** PostgreSQL
* **Gráficos:** Plotly Express
* **ORM:** SQLAlchemy

## 📋 Pré-requisitos
Antes de começar, você vai precisar ter instalado:
* Python 3.x
* PostgreSQL rodando localmente

## 🔧 Instalação e Execução

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/AldebaraFork/Analise_CNPJ-)
2. **Configurar o Ambiente Python**
   python -m venv venv
# No Windows:
.\venv\Scripts\activate

3. **Instalar Dependências**
   pip install -r requirements.txt

4. **Configuração do Banco de Dados (PostgreSQL)**
O projeto utiliza o PostgreSQL. Certifique-se de que o serviço está rodando e siga os passos:

Crie um banco de dados chamado tcc_cnpj.

O sistema de autenticação criará a tabela usuarios automaticamente na primeira execução.

Importante: Certifique-se de que as tabelas empresas_amostra e naturezas_referencia já existam e contenham os dados processados para que os gráficos sejam gerados.

5. **Executar o Dashboard**
Para iniciar a aplicação, utilize o comando:
python -m streamlit run dashboard_tcc.py



## 🔑 Credenciais de Acesso
Como o sistema possui controle de acesso:

Vá até a aba "Criar Conta".

Cadastre um e-mail válido e uma senha (mínimo 8 caracteres e 1 letra maiúscula).

Retorne à aba "Login" para acessar o Board.
