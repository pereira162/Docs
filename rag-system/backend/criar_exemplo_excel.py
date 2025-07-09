# Criar arquivo Excel de exemplo para teste
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Dados de exemplo - Vendas
vendas_data = {
    'Data': pd.date_range('2024-01-01', periods=100, freq='D'),
    'Produto': np.random.choice(['Notebook', 'Mouse', 'Teclado', 'Monitor', 'Webcam'], 100),
    'Categoria': np.random.choice(['Informática', 'Periféricos', 'Acessórios'], 100),
    'Quantidade': np.random.randint(1, 50, 100),
    'Preço_Unitário': np.round(np.random.uniform(50.0, 2000.0, 100), 2),
    'Vendedor': np.random.choice(['João', 'Maria', 'Pedro', 'Ana', 'Carlos'], 100),
    'Cliente': [f'Cliente_{i:03d}' for i in np.random.randint(1, 51, 100)],
    'Status': np.random.choice(['Concluída', 'Pendente', 'Cancelada'], 100),
}

# Calcular total
vendas_df = pd.DataFrame(vendas_data)
vendas_df['Total'] = vendas_df['Quantidade'] * vendas_df['Preço_Unitário']

# Dados de exemplo - Estoque
estoque_data = {
    'Código': [f'PROD{i:04d}' for i in range(1, 26)],
    'Produto': ['Notebook Dell', 'Mouse Logitech', 'Teclado Mecânico', 'Monitor 24"', 'Webcam HD'] * 5,
    'Categoria': ['Notebooks', 'Periféricos', 'Periféricos', 'Monitores', 'Acessórios'] * 5,
    'Estoque_Atual': np.random.randint(0, 100, 25),
    'Estoque_Mínimo': np.random.randint(5, 20, 25),
    'Preço_Custo': np.round(np.random.uniform(30.0, 1200.0, 25), 2),
    'Preço_Venda': np.round(np.random.uniform(50.0, 2000.0, 25), 2),
    'Fornecedor': np.random.choice(['Fornecedor A', 'Fornecedor B', 'Fornecedor C'], 25),
    'Localização': np.random.choice(['Setor A', 'Setor B', 'Setor C', 'Depósito'], 25),
}

estoque_df = pd.DataFrame(estoque_data)

# Dados de exemplo - Funcionários
funcionarios_data = {
    'ID': range(1, 21),
    'Nome': [f'Funcionário {i}' for i in range(1, 21)],
    'Departamento': np.random.choice(['Vendas', 'TI', 'RH', 'Financeiro', 'Logística'], 20),
    'Cargo': np.random.choice(['Analista', 'Supervisor', 'Gerente', 'Coordenador', 'Assistente'], 20),
    'Salário': np.round(np.random.uniform(2000.0, 15000.0, 20), 2),
    'Data_Admissão': pd.date_range('2020-01-01', periods=20, freq='30D'),
    'Status': np.random.choice(['Ativo', 'Férias', 'Licença'], 20),
    'Email': [f'funcionario{i}@empresa.com' for i in range(1, 21)],
    'Telefone': [f'(11) 9{np.random.randint(1000, 9999)}-{np.random.randint(1000, 9999)}' for _ in range(20)],
}

funcionarios_df = pd.DataFrame(funcionarios_data)

# Dados de exemplo - Relatório Financeiro
meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
financeiro_data = {
    'Mês': meses,
    'Receita_Bruta': np.round(np.random.uniform(80000, 150000, 12), 2),
    'Custos_Produtos': np.round(np.random.uniform(30000, 60000, 12), 2),
    'Despesas_Operacionais': np.round(np.random.uniform(20000, 40000, 12), 2),
    'Impostos': np.round(np.random.uniform(5000, 15000, 12), 2),
    'Marketing': np.round(np.random.uniform(3000, 10000, 12), 2),
    'Salários': np.round(np.random.uniform(25000, 35000, 12), 2),
}

financeiro_df = pd.DataFrame(financeiro_data)
financeiro_df['Lucro_Bruto'] = financeiro_df['Receita_Bruta'] - financeiro_df['Custos_Produtos']
financeiro_df['Lucro_Líquido'] = (financeiro_df['Receita_Bruta'] - 
                                  financeiro_df['Custos_Produtos'] - 
                                  financeiro_df['Despesas_Operacionais'] - 
                                  financeiro_df['Impostos'] - 
                                  financeiro_df['Marketing'] - 
                                  financeiro_df['Salários'])

# Criar arquivo Excel com múltiplas planilhas
output_file = Path("exemplo_dados_empresa.xlsx")

print("📄 Criando arquivo Excel de exemplo...")

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    vendas_df.to_excel(writer, sheet_name='Vendas', index=False)
    estoque_df.to_excel(writer, sheet_name='Estoque', index=False)
    funcionarios_df.to_excel(writer, sheet_name='Funcionários', index=False)
    financeiro_df.to_excel(writer, sheet_name='Financeiro', index=False)

print(f"✅ Arquivo criado: {output_file}")
print(f"📊 Planilhas: Vendas ({len(vendas_df)} linhas), Estoque ({len(estoque_df)} linhas), Funcionários ({len(funcionarios_df)} linhas), Financeiro ({len(financeiro_df)} linhas)")
print("\n🚀 Agora testando o extrator...")

# Testar o extrator
from excel_extractor import ExcelExtractor

try:
    extractor = ExcelExtractor()
    results = extractor.extract_from_excel(str(output_file))
    
    print("\n" + "="*60)
    print("✅ EXTRAÇÃO CONCLUÍDA!")
    print(f"📄 Planilhas processadas: {len(results['worksheets'])}")
    print(f"📊 Total de linhas: {results['summary']['total_data_rows']}")
    
    print("\n📋 PLANILHAS DETECTADAS:")
    for name, info in results["worksheets"].items():
        print(f"  • {name}: {info['shape']['rows']} linhas, {info['shape']['columns']} colunas")
        if info["content_analysis"]["patterns"]:
            print(f"    Padrões detectados: {', '.join(info['content_analysis']['patterns'])}")
    
    print("\n🎉 TESTE DO EXTRATOR EXCEL CONCLUÍDO COM SUCESSO!")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()
