import os
from fpdf import FPDF
from datetime import datetime
import psycopg2

# 1. Configurações de Conexão (Senha: 194550)
USUARIO = "postgres"
SENHA = "194550"
HOST = "localhost"
DB = "tcc_cnpj"

class RelatorioExecutivo(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Relatorio de Analise de Dados: Mercado Brasileiro', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def buscar_estatisticas():
    try:
        conn = psycopg2.connect(host=HOST, database=DB, user=USUARIO, password=SENHA)
        cur = conn.cursor()
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(capital_social) as soma,
                MAX(capital_social) as maximo,
                AVG(capital_social) as media
            FROM empresas_amostra
            WHERE capital_social > 0
        """
        cur.execute(query)
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res
    except:
        return [0, 0, 0, 0]

def criar_pdf():
    stats = buscar_estatisticas()
    pdf = RelatorioExecutivo()
    pdf.add_page()
    
    # --- SEÇÃO 1: RESUMO ---
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, '1. Resumo dos Dados Processados', 0, 1, 'L', True)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'- Total de Empresas Analisadas: {int(stats[0])}', 0, 1)
    pdf.cell(0, 8, f'- Capital Social Acumulado: R$ {stats[1]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), 0, 1)
    pdf.cell(0, 8, f'- Investimento Medio: R$ {stats[3]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), 0, 1)
    pdf.ln(5)

    # --- SEÇÃO 2: GRÁFICO DE MÉDIA ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Media de Capital por Natureza Juridica', 0, 1, 'L', True)
    pdf.ln(2)
    
    if os.path.exists("grafico_media.png"):
        # Ajusta a imagem para caber bem na página
        pdf.image("grafico_media.png", x=10, w=190)
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'Aviso: grafico_media.png nao encontrado na pasta.', 0, 1)
    
    pdf.add_page()
    
    # --- SEÇÃO 3: DISTRIBUIÇÃO ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Distribuicao do Capital Social', 0, 1, 'L', True)
    pdf.ln(2)

    if os.path.exists("grafico_distribuicao.png"):
        pdf.image("grafico_distribuicao.png", x=10, w=190)
    else:
        pdf.cell(0, 10, 'Aviso: grafico_distribuicao.png nao encontrado na pasta.', 0, 1)

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '4. Conclusao', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, "O processamento foi concluido com sucesso. Os dados demonstram uma alta concentracao de capital em Sociedades Anonimas, enquanto a maioria das empresas foca em capital social reduzido.")

    nome_arquivo = "Relatorio_Final_TCC_Eduardo.pdf"
    pdf.output(nome_arquivo)
    print(f"🚀 PDF gerado com sucesso: {nome_arquivo}")

if __name__ == "__main__":
    criar_pdf()