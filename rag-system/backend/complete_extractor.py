#!/usr/bin/env python3
"""
Extrator melhorado que reconstrói tabelas a partir do texto
"""

import re
import pdfplumber
from pathlib import Path

def extract_table_from_text(text: str) -> list:
    """
    Extrai tabela parseando o texto linha por linha
    """
    lines = text.split('\n')
    table_data = []
    
    # Procurar padrões de tabela
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Se encontrar o cabeçalho da tabela
        if "Floor plans" in line and "AutoCAD" in line and "Architecture toolset" in line:
            # Cabeçalho
            table_data.append(["Floor plans", "AutoCAD", "Architecture toolset"])
            
            # Processar as próximas linhas até encontrar "(Figures shown"
            j = i + 1
            while j < len(lines) and "(Figures shown" not in lines[j]:
                current_line = lines[j].strip()
                
                if current_line and not current_line.startswith("•") and current_line != "Advantages":
                    # Usar regex para separar texto de tempos
                    # Padrão: texto seguido de tempo seguido de tempo
                    pattern = r'^(.+?)\s+(\d+:\d+)\s+(\d+:\d+|\d+%)$'
                    match = re.match(pattern, current_line)
                    
                    if match:
                        task = match.group(1).strip()
                        autocad_time = match.group(2).strip()
                        toolset_time = match.group(3).strip()
                        table_data.append([task, autocad_time, toolset_time])
                    elif "Time savings" in current_line:
                        # Linha especial de economia de tempo
                        parts = current_line.split()
                        if len(parts) >= 2 and "%" in parts[-1]:
                            table_data.append(["Time savings with the Architecture toolset", "", parts[-1]])
                
                j += 1
            break
    
    return table_data

def create_complete_markdown():
    """
    Cria markdown completo do documento
    """
    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ Arquivo não encontrado: {pdf_file}")
        return
    
    print("📄 CRIANDO MARKDOWN COMPLETO DO DOCUMENTO...")
    print("=" * 60)
    
    markdown_lines = []
    markdown_lines.extend([
        "# The Benefits of Using the Architecture Toolset in AutoCAD",
        "",
        "## 📋 Informações do Documento",
        "- **Arquivo:** AutoCAD Architecture Toolset Productivity Study (EN).pdf",
        "- **Tamanho:** 7.06 MB",
        "- **Páginas:** 24",
        f"- **Processado em:** {Path().cwd()}",
        "",
        "---",
        ""
    ])
    
    with pdfplumber.open(pdf_file) as pdf:
        total_pages = len(pdf.pages)
        
        for page_num in range(total_pages):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Adicionar cabeçalho da página
                markdown_lines.append(f"## 📄 Página {page_num + 1}")
                markdown_lines.append("")
                
                # Se for uma página com tabela, processar diferente
                if "Floor plans" in text and "AutoCAD" in text and "Architecture toolset" in text:
                    # Extrair tabela melhorada
                    table_data = extract_table_from_text(text)
                    
                    if table_data:
                        markdown_lines.append("### 📊 Tabela de Comparação - Floor Plans")
                        markdown_lines.append("")
                        
                        # Criar tabela markdown
                        if len(table_data) > 0:
                            # Cabeçalho
                            header = "| " + " | ".join(table_data[0]) + " |"
                            separator = "|" + "|".join([" --- " for _ in table_data[0]]) + "|"
                            
                            markdown_lines.append(header)
                            markdown_lines.append(separator)
                            
                            # Dados
                            for row in table_data[1:]:
                                if len(row) == 3:
                                    row_text = f"| {row[0]} | {row[1]} | {row[2]} |"
                                    markdown_lines.append(row_text)
                        
                        markdown_lines.append("")
                    
                    # Adicionar o resto do texto
                    lines = text.split('\n')
                    in_advantages = False
                    for line in lines:
                        if "Advantages" in line:
                            in_advantages = True
                            markdown_lines.append("### ✅ Vantagens")
                            markdown_lines.append("")
                        elif in_advantages and line.strip().startswith("•"):
                            markdown_lines.append(f"- {line.strip()[1:].strip()}")
                        elif in_advantages and line.strip() and not line.strip().startswith("The benefits of"):
                            if not any(x in line for x in ["Floor plans", "AutoCAD", "Architecture toolset", ":", "Time savings"]):
                                markdown_lines.append(line.strip())
                
                else:
                    # Página normal
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            # Identificar títulos
                            if any(title in line for title in ["Introduction", "Executive summary", "Key findings", "The study", "Design task", "Conclusion"]):
                                if "Design task" in line:
                                    markdown_lines.append(f"### 🔧 {line}")
                                elif line in ["Introduction", "Executive summary", "Key findings", "The study", "Conclusion"]:
                                    markdown_lines.append(f"### 📝 {line}")
                                else:
                                    markdown_lines.append(f"**{line}**")
                            # Identificar listas
                            elif line.startswith("•"):
                                markdown_lines.append(f"- {line[1:].strip()}")
                            # Identificar números de página no rodapé
                            elif re.match(r'^The benefits of using the Architecture toolset in AutoCAD \d+$', line):
                                markdown_lines.append(f"*{line}*")
                            # Identificar destaque de palavras
                            elif line in ["Faster", "Reduced", "Saved", "Gained"]:
                                markdown_lines.append(f"**{line}**")
                            # Texto normal
                            else:
                                markdown_lines.append(line)
                            
                            markdown_lines.append("")
                
                # Processar tabelas de outras páginas
                tables = page.extract_tables()
                if tables and not ("Floor plans" in text and "AutoCAD" in text):
                    for i, table in enumerate(tables):
                        markdown_lines.append(f"### 📊 Tabela {i+1}")
                        markdown_lines.append("")
                        
                        if table and len(table) > 0:
                            # Tentar reconstruir tabela baseada no texto
                            if any("AutoCAD" in str(row) for row in table):
                                # É uma tabela de comparação, reconstruir do texto
                                table_from_text = extract_comparison_table_from_text(text)
                                if table_from_text:
                                    table = table_from_text
                            
                            # Criar cabeçalho
                            if table[0]:
                                non_none_cols = [col for col in table[0] if col is not None]
                                if len(non_none_cols) > 0:
                                    header = "| " + " | ".join(non_none_cols) + " |"
                                    separator = "|" + "|".join([" --- " for _ in non_none_cols]) + "|"
                                    
                                    markdown_lines.append(header)
                                    markdown_lines.append(separator)
                                    
                                    # Dados
                                    for row in table[1:]:
                                        if row:
                                            non_none_vals = [str(val) if val is not None else "" for val in row]
                                            if len(non_none_vals) == len(non_none_cols):
                                                row_text = "| " + " | ".join(non_none_vals) + " |"
                                                markdown_lines.append(row_text)
                        
                        markdown_lines.append("")
                
                markdown_lines.append("---")
                markdown_lines.append("")
    
    # Salvar markdown completo
    complete_markdown = '\n'.join(markdown_lines)
    output_file = Path("AutoCAD_Complete_Document.md")
    output_file.write_text(complete_markdown, encoding='utf-8')
    
    print(f"✅ MARKDOWN COMPLETO CRIADO: {output_file}")
    print(f"📏 Tamanho: {len(complete_markdown)} caracteres")
    print(f"📄 Linhas: {len(markdown_lines)}")
    
    return output_file

def extract_comparison_table_from_text(text: str) -> list:
    """
    Extrai tabelas de comparação de tempo do texto
    """
    lines = text.split('\n')
    table_data = []
    
    # Encontrar cabeçalho da tabela
    header_found = False
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Detectar diferentes tipos de cabeçalho
        if any(x in line for x in ["AutoCAD", "Architecture toolset"]) and not header_found:
            # Determinar o tipo de tabela baseado na primeira palavra
            first_word = lines[i-1].strip() if i > 0 else ""
            if first_word:
                table_data.append([first_word, "AutoCAD", "Architecture toolset"])
                header_found = True
                
                # Processar linhas seguintes
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("(Figures shown"):
                    current_line = lines[j].strip()
                    
                    if current_line and not current_line.startswith("•") and "Advantages" not in current_line:
                        # Extrair tempos
                        time_pattern = r'(\d+:\d+)'
                        times = re.findall(time_pattern, current_line)
                        
                        if len(times) >= 2:
                            # Extrair descrição (tudo antes do primeiro tempo)
                            desc_match = re.match(r'^(.+?)\s+\d+:\d+', current_line)
                            if desc_match:
                                description = desc_match.group(1).strip()
                                table_data.append([description, times[0], times[1]])
                        elif "Time savings" in current_line or "Time Savings" in current_line:
                            percent_match = re.search(r'(\d+%)', current_line)
                            if percent_match:
                                table_data.append(["Time Savings", "", percent_match.group(1)])
                    
                    j += 1
                break
    
    return table_data if len(table_data) > 1 else []

if __name__ == "__main__":
    # Primeiro mostrar a tabela da página 6 corrigida
    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[5]  # Página 6 (índice 5)
        text = page.extract_text()
        
        print("📊 TABELA CORRIGIDA DA PÁGINA 6:")
        print("=" * 60)
        
        table_data = extract_table_from_text(text)
        
        if table_data:
            # Mostrar tabela formatada
            for i, row in enumerate(table_data):
                if i == 0:
                    print(f"| {'Task':<35} | {'AutoCAD':<10} | {'Architecture toolset':<20} |")
                    print(f"|{'-'*37}|{'-'*12}|{'-'*22}|")
                else:
                    task = row[0][:35] if len(row[0]) > 35 else row[0]
                    autocad = row[1] if len(row) > 1 else ""
                    toolset = row[2] if len(row) > 2 else ""
                    print(f"| {task:<35} | {autocad:<10} | {toolset:<20} |")
        
        print("\n")
    
    # Criar documento completo
    create_complete_markdown()
