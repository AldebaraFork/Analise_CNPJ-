# 🏛️ Board de Inteligência: Mercado Empresarial (CNPJ Brasil)

Este projeto consiste em uma plataforma de **Engenharia de Dados** ponta-a-ponta, desenvolvida para processar e analisar o capital social das empresas brasileiras com base nos dados abertos da Receita Federal. O sistema integra um banco de dados relacional a um dashboard interativo com camadas de segurança e governança de dados.

## 🚀 Status do Projeto
Atualmente em fase de implementação de módulos de segurança e conformidade com a LGPD.

| Funcionalidade | Status | Descrição |
| :--- | :--- | :--- |
| **Ingestão & ETL** | ✅ Concluído | Processamento de ZIPs e carga no PostgreSQL. |
| **Board Interativo** | ✅ Concluído | Visualização de médias e faixas de capital social. |
| **Sistema de Login/E-mail** | 🚀 **Em Progresso** | Autenticação de usuários via E-mail e Senha. |
| **Segurança & Regras** | ✅ Concluído | Validação de senha (8+ char, 1 Maiúscula). |
| **Gestão de Perfil** | ✅ Concluído | Exclusão definitiva de conta (Direito ao esquecimento). |
| **Segurança do usuário** | ✅ Concluído | Segurança do Usuário com Hash |
| **Gestão de dados Medalion** | ✅ Concluído | Separação e caracterização de dados em camadas bronze silver e gold |
| **Exportação de Dados** | ⏳ Pendente | Download de relatórios em CSV/Excel. |

---

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.14
* **Interface:** Streamlit
* **Gráficos:** Plotly Express
* **Banco de Dados:** PostgreSQL
* **ORM:** SQLAlchemy
* **Manipulação de Dados:** Pandas

---
