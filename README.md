Markdown
# 🏛️ Board de Inteligência: Mercado Empresarial (CNPJ Brasil)

Este projeto consiste em uma plataforma de **Engenharia de Dados** ponta-a-ponta, desenvolvida para processar e analisar o capital social das empresas brasileiras com base nos dados abertos da Receita Federal. O sistema integra um banco de dados relacional a um dashboard interativo com camadas de segurança e governança de dados.

## 🚀 Status do Projeto
Atualmente em fase de implementação de módulos de segurança e conformidade com a LGPD.

| Funcionalidade | Status | Descrição |
| :--- | :--- | :--- |
| **Ingestão & ETL** | ✅ Concluído | Processamento de ZIPs e carga no PostgreSQL. |
| **Board Interativo** | ✅ Concluído | Visualização de médias e faixas de capital social. |
| **Sistema de Login/E-mail** | 🚀 **Em Progresso** | Autenticação de usuários via E-mail e Senha. |
| **Segurança & Regras** | 🚀 **Em Progresso** | Validação de senha (8+ char, 1 Maiúscula). |
| **Gestão de Perfil** | 🚀 **Em Progresso** | Exclusão definitiva de conta (Direito ao esquecimento). |
| **Exportação de Dados** | ⏳ Pendente | Download de relatórios em CSV/Excel. |

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.14
* **Interface:** [Streamlit](https://streamlit.io/)
* **Gráficos:** [Plotly Express](https://plotly.com/python/plotly-express/)
* **Banco de Dados:** [PostgreSQL](https://www.postgresql.org/)
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
* **Manipulação de Dados:** Pandas

## 🔧 Instalação e Execução

Siga os passos abaixo para configurar o ambiente localmente:

### 1. Clonar o Repositório
```bash
git clone [https://github.com/AldebaraFork/Analise_CNPJ-.git](https://github.com/AldebaraFork/Analise_CNPJ-.git)
cd Analise_CNPJ-
2. Configurar o Ambiente Python
Recomenda-se o uso de um ambiente virtual:

Bash
python -m venv venv
# No Windows:
.\venv\Scripts\activate
3. Instalar Dependências
Bash
pip install -r requirements.txt
4. Configuração do Banco de Dados (PostgreSQL)
Crie um banco de dados chamado tcc_cnpj.

Certifique-se de que as tabelas de dados (empresas_amostra) estão populadas.

O sistema criará a tabela de usuarios automaticamente na primeira execução.

5. Executar o Dashboard
Bash
python -m streamlit run dashboard_tcc.py
🔐 Funcionalidades de Acesso
O sistema conta com controle de acesso robusto:

Cadastro: Validação de e-mail e regras de complexidade de senha.

Segurança: Prevenção contra SQL Injection via consultas parametrizadas (SQLAlchemy).

Privacidade: Opção de exclusão total de dados do usuário diretamente pela interface do Board.

📂 Estrutura do Repositório
dashboard_tcc.py: Aplicação principal em Streamlit.

requirements.txt: Lista de dependências do projeto.

.gitignore: Filtro para evitar o versionamento de dados pesados (ZIPs/CSVs).

README.md: Documentação oficial do projeto.
