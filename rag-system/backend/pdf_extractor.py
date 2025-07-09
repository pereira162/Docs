#!/usr/bin/env python3
"""
RAG PDF Extractor - VERSÃO DEFINITIVA E CORRETA
Extrai PDFs com tabelas perfeitas sem duplicação de conteúdo
"""

import os
import re
import json
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

class DefinitivePDFExtractor:
    """
    Extrator definitivo que separa corretamente texto de tabelas
    """
    
    def __init__(self, output_dir: str = "./rag_outputs"):
        self.output_dir = Path(output_dir)
        self.setup_directories()
        
    def setup_directories(self):
        """Configura estrutura de diretórios"""
        self.output_dir.mkdir(exist_ok=True)
        self.directories = {
            'markdown': self.output_dir / "markdown",
            'json': self.output_dir / "json",
            'chunks': self.output_dir / "chunks", 
            'metadata': self.output_dir / "metadata"
        }
        
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True)
    
    def identify_table_sections(self, text: str) -> List[Tuple[int, int]]:
        """
        Identifica seções que contêm tabelas para remover do texto normal
        """
        lines = text.split('\\n')
        table_sections = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detectar início de tabela
            if self.is_table_header(line, lines, i):
                start_idx = i
                
                # Encontrar fim da tabela
                end_idx = self.find_table_end(lines, i)
                
                table_sections.append((start_idx, end_idx))
                i = end_idx + 1
            else:
                i += 1
        
        return table_sections
    
    def is_table_header(self, line: str, lines: List[str], index: int) -> bool:
        """
        Detecta se uma linha é cabeçalho de tabela
        """
        # Padrão 1: Linha com "AutoCAD" e "Architecture toolset"
        if "AutoCAD" in line and "Architecture toolset" in line:
            return True
        
        # Padrão 2: Nome da tarefa seguido de linha com tempos
        task_names = [
            "Floor plans", "Elevations", "Reflected ceiling plans", 
            "Building sections", "Sheet layouts", "Details", 
            "Schedules", "Automatic project reports", "Coordination and publishing"
        ]
        
        if any(task in line for task in task_names):
            # Verificar se próximas linhas têm padrão de tempo
            for j in range(index + 1, min(index + 3, len(lines))):
                if re.search(r'\\d+:\\d+.*\\d+:\\d+', lines[j]):
                    return True
        
        # Padrão 3: Tabela de conclusão
        if "Project tasks" in line and index + 2 < len(lines):
            if re.search(r'\\d+.*\\d+:\\d+.*\\d+:\\d+.*\\d+%', lines[index + 2]):
                return True
        
        return False
    
    def find_table_end(self, lines: List[str], start_idx: int) -> int:
        """
        Encontra o fim de uma tabela
        """
        i = start_idx + 1
        while i < len(lines):
            line = lines[i].strip()
            
            # Indicadores de fim de tabela
            if any(indicator in line for indicator in [
                "(Figures shown", "Advantages", "The advantages", 
                "The benefits of using", "Based on these"
            ]):
                return i - 1
            
            # Se não tem mais tempos ou percentuais, provavelmente acabou
            if line and not re.search(r'\\d+:\\d+|\\d+%|N/A', line) and len(line) > 50:
                return i - 1
            
            i += 1
        
        return len(lines) - 1
    
    def extract_clean_text(self, text: str) -> str:
        """
        Extrai texto limpo removendo seções de tabelas
        """
        lines = text.split('\\n')
        table_sections = self.identify_table_sections(text)
        
        # Criar lista de linhas que NÃO são tabelas
        clean_lines = []
        excluded_ranges = set()
        
        # Marcar linhas de tabelas para exclusão
        for start, end in table_sections:
            for i in range(start, end + 1):
                excluded_ranges.add(i)
        
        # Adicionar apenas linhas que não são tabelas
        for i, line in enumerate(lines):
            if i not in excluded_ranges:
                clean_lines.append(line)
        
        return '\\n'.join(clean_lines)
    
    def extract_tables_from_text(self, text: str, page_num: int) -> List[List[List[str]]]:
        """
        Extrai APENAS as tabelas do texto
        """
        lines = text.split('\\n')
        tables = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if self.is_table_header(line, lines, i):
                table_data = self.parse_complete_table(lines, i, page_num)
                if table_data and len(table_data) > 1:
                    tables.append(table_data)
                
                # Pular para depois desta tabela
                end_idx = self.find_table_end(lines, i)
                i = end_idx + 1
            else:
                i += 1
        
        return tables
    
    def parse_complete_table(self, lines: List[str], start_idx: int, page_num: int) -> List[List[str]]:
        """
        Parseia uma tabela completa com todas as colunas corretas
        """
        table_data = []
        
        # Determinar cabeçalho baseado no contexto
        header_line = lines[start_idx].strip()
        
        if page_num == 23 and "Project tasks" in header_line:
            # Tabela de conclusão
            table_data.append(["Project Task", "AutoCAD", "Architecture toolset", "Time Savings"])
            
            # Processar dados da tabela de conclusão
            task_mapping = {
                "1": "Floor plans", "2": "Elevations", "3": "Reflected ceiling plans",
                "4": "Building sections", "5": "Sheet layouts", "6": "Details",
                "7": "Schedules", "8": "Project modifications", "9": "Coordination and publishing"
            }
            
            for i in range(start_idx + 1, min(start_idx + 15, len(lines))):
                line = lines[i].strip()
                
                # Padrão: número + nome + tempos + percentual
                pattern = r'^(\\d+)\\s+(.+?)\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)\\s+(\\d+%)$'
                match = re.match(pattern, line)
                if match:
                    task_num = match.group(1)
                    autocad_time = match.group(3)
                    toolset_time = match.group(4) 
                    savings = match.group(5)
                    task_name = task_mapping.get(task_num, f"Task {task_num}")
                    table_data.append([task_name, autocad_time, toolset_time, savings])
                
                # Linha de total
                elif "Total time" in line:
                    times = re.findall(r'\\d+:\\d+', line)
                    if len(times) >= 2:
                        table_data.append(["Total time", times[0], times[1], ""])
                
                # Economia geral
                elif any(phrase in line for phrase in ["Overall time savings", "overall productivity"]):
                    percent = re.search(r'(\\d+%)', line)
                    if percent:
                        table_data.append(["Overall time savings", "", "", percent.group(1)])
        
        else:
            # Tabelas normais de comparação
            # Determinar nome da tarefa
            task_name = self.extract_task_name(lines, start_idx)
            table_data.append([task_name, "AutoCAD", "Architecture toolset"])
            
            # Processar linhas de dados
            end_idx = self.find_table_end(lines, start_idx)
            
            for i in range(start_idx + 1, end_idx + 1):
                line = lines[i].strip()
                if not line:
                    continue
                
                # Parsear linha de dados
                row_data = self.parse_data_row(line)
                if row_data and len(row_data) == 3:
                    table_data.append(row_data)
        
        return table_data
    
    def extract_task_name(self, lines: List[str], current_idx: int) -> str:
        """
        Extrai o nome da tarefa do contexto
        """
        # Verificar linha atual
        current_line = lines[current_idx].strip()
        
        task_patterns = [
            r'(Floor plans)', r'(Elevations?)', r'(Reflected ceiling plans?)',
            r'(Building sections?)', r'(Sheet layouts?)', r'(Details?)',
            r'(Schedules?)', r'(Automatic project reports?)', r'(Coordination and publishing)'
        ]
        
        for pattern in task_patterns:
            if re.search(pattern, current_line, re.IGNORECASE):
                match = re.search(pattern, current_line, re.IGNORECASE)
                return match.group(1)
        
        # Procurar nas linhas anteriores
        for i in range(max(0, current_idx - 10), current_idx):
            line = lines[i].strip()
            for pattern in task_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    match = re.search(pattern, line, re.IGNORECASE)
                    return match.group(1)
        
        return "Task"
    
    def parse_data_row(self, line: str) -> Optional[List[str]]:
        """
        Parseia uma linha de dados da tabela
        """
        # Limpar linha
        line = re.sub(r'\\s+', ' ', line.strip())
        
        # Padrões de extração
        patterns = [
            # Padrão completo: descrição + tempo + tempo
            r'^(.+?)\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)$',
            # Padrão com N/A
            r'^(.+?)\\s+(N/A)\\s+(\\d+:\\d+)$',
            # Padrão com percentual
            r'^(.+?)\\s+(\\d+:\\d+)\\s+(\\d+%)$',
            # Time savings especial
            r'^(Time [Ss]avings.+?)\\s+(\\d+%)$',
            # Total time
            r'^(Total time.+?)\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) == 3:
                    desc = match.group(1).strip()
                    val1 = match.group(2).strip()
                    val2 = match.group(3).strip()
                    return [desc, val1, val2]
                elif len(match.groups()) == 2:  # Time savings
                    desc = match.group(1).strip()
                    return [desc, "", match.group(2).strip()]
        
        return None
    
    def process_page(self, page, page_num: int) -> Dict[str, Any]:
        """
        Processa uma página separando texto limpo de tabelas
        """
        content = {
            'page_number': page_num,
            'clean_text': '',
            'tables': [],
            'has_content': False
        }
        
        # Extrair texto completo
        full_text = page.extract_text()
        if not full_text or not full_text.strip():
            print(f"⚠️  Página {page_num}: Sem texto extraído")
            return content
        
        # Extrair tabelas PRIMEIRO
        tables = self.extract_tables_from_text(full_text, page_num)
        
        # Extrair texto LIMPO (sem seções de tabelas)
        clean_text = self.extract_clean_text(full_text)
        
        # Debug
        print(f"  Página {page_num}: Texto={len(clean_text)} chars, Tabelas={len(tables)}")
        
        content.update({
            'clean_text': clean_text.strip(),
            'tables': tables,
            'has_content': True  # Sempre tem conteúdo se extraiu texto
        })
        
        return content
    
    def create_markdown_table(self, table: List[List[str]]) -> str:
        """
        Cria tabela markdown bem formatada
        """
        if not table or len(table) < 1:
            return ""
        
        lines = []
        
        # Cabeçalho
        header = "| " + " | ".join(table[0]) + " |"
        separator = "|" + "|".join([" --- " for _ in table[0]]) + "|"
        
        lines.append(header)
        lines.append(separator)
        
        # Dados
        for row in table[1:]:
            if len(row) == len(table[0]):
                # Escapar pipes nos dados
                escaped_row = [cell.replace("|", "\\|") for cell in row]
                row_text = "| " + " | ".join(escaped_row) + " |"
                lines.append(row_text)
        
        return "\\n".join(lines)
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Processa PDF completo
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        print(f"📄 Processando: {pdf_path.name}")
        
        results = {
            'filename': pdf_path.name,
            'total_pages': 0,
            'pages_processed': 0,
            'tables_found': 0,
            'content': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            results['total_pages'] = len(pdf.pages)
            print(f"📖 Total de páginas: {len(pdf.pages)}")
            
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                page_content = self.process_page(page, page_num + 1)
                
                if page_content['has_content']:
                    results['content'].append(page_content)
                    results['pages_processed'] += 1
                    results['tables_found'] += len(page_content['tables'])
                    
                    tables_info = f"{len(page_content['tables'])} tabela(s)" if page_content['tables'] else "sem tabelas"
                    print(f"✅ Página {page_num + 1}: {tables_info}")
        
        # Salvar resultados
        self.save_all_results(results)
        return results
    
    def save_all_results(self, results: Dict[str, Any]):
        """
        Salva todos os resultados
        """
        filename_base = Path(results['filename']).stem
        
        # 1. Markdown completo
        markdown_content = self.create_final_markdown(results)
        markdown_file = self.directories['markdown'] / f"{filename_base}.md"
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        # 2. JSON estruturado
        json_data = {
            'metadata': {
                'filename': results['filename'],
                'total_pages': results['total_pages'],
                'pages_processed': results['pages_processed'],
                'tables_found': results['tables_found'],
                'processed_at': datetime.now().isoformat()
            },
            'content': results['content']
        }
        
        json_file = self.directories['json'] / f"{filename_base}.json"
        json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 3. Chunks para IA
        chunks = self.create_ai_chunks(results)
        chunks_file = self.directories['chunks'] / f"{filename_base}_chunks.json"
        chunks_file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 4. Metadata
        metadata_file = self.directories['metadata'] / f"{filename_base}_metadata.json"
        metadata_file.write_text(json.dumps(json_data['metadata'], indent=2, ensure_ascii=False), encoding='utf-8')
        
        print(f"\\n💾 Arquivos salvos:")
        print(f"  📄 {markdown_file.name}")
        print(f"  📊 {json_file.name}")
        print(f"  🧩 {chunks_file.name}")
        print(f"  📋 {metadata_file.name}")
    
    def create_final_markdown(self, results: Dict[str, Any]) -> str:
        """
        Cria markdown final sem duplicação
        """
        lines = [
            f"# {Path(results['filename']).stem}",
            "",
            "## 📋 Informações do Documento",
            f"- **Arquivo:** {results['filename']}",
            f"- **Páginas:** {results['total_pages']}",
            f"- **Páginas processadas:** {results['pages_processed']}",
            f"- **Tabelas encontradas:** {results['tables_found']}",
            f"- **Processado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        for page_content in results['content']:
            page_num = page_content['page_number']
            clean_text = page_content['clean_text']
            tables = page_content['tables']
            
            lines.append(f"## 📄 Página {page_num}")
            lines.append("")
            
            # Texto limpo (SEM tabelas duplicadas)
            if clean_text:
                text_lines = clean_text.split('\\n')
                
                for line in text_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Formatação especial
                    if self.is_section_title(line):
                        lines.append(f"### {line}")
                    elif line.startswith("•"):
                        lines.append(f"- {line[1:].strip()}")
                    elif self.is_page_footer(line):
                        lines.append(f"*{line}*")
                    else:
                        lines.append(line)
                    
                    lines.append("")
            
            # Tabelas separadas e corretas
            for i, table in enumerate(tables):
                lines.append(f"### 📊 {table[0][0] if table and table[0] else f'Tabela {i+1}'}")
                lines.append("")
                
                table_md = self.create_markdown_table(table)
                if table_md:
                    lines.append(table_md)
                    lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\\n".join(lines)
    
    def is_section_title(self, line: str) -> bool:
        """
        Identifica títulos de seção
        """
        titles = [
            "Introduction", "Executive summary", "Key findings", "The study", 
            "Conclusion", "Design task", "Steps:", "Advantages"
        ]
        return any(title in line for title in titles)
    
    def is_page_footer(self, line: str) -> bool:
        """
        Identifica rodapés
        """
        return (re.match(r'^The benefits of using.+\\d+$', line) or 
                "Autodesk" in line or "©" in line)
    
    def create_ai_chunks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Cria chunks otimizados para IA
        """
        chunks = []
        chunk_id = 0
        
        for page_content in results['content']:
            page_num = page_content['page_number']
            clean_text = page_content['clean_text']
            tables = page_content['tables']
            
            # Chunk de texto limpo
            if clean_text and len(clean_text.strip()) > 50:
                chunks.append({
                    'chunk_id': f"chunk_{chunk_id}",
                    'type': 'text',
                    'page': page_num,
                    'content': clean_text.strip(),
                    'char_count': len(clean_text),
                    'word_count': len(clean_text.split())
                })
                chunk_id += 1
            
            # Chunks de tabelas
            for i, table in enumerate(tables):
                if table and len(table) > 1:
                    table_text = self.table_to_structured_text(table)
                    
                    chunks.append({
                        'chunk_id': f"chunk_{chunk_id}",
                        'type': 'table',
                        'page': page_num,
                        'table_index': i,
                        'content': table_text,
                        'raw_table': table,
                        'rows': len(table),
                        'columns': len(table[0]) if table else 0
                    })
                    chunk_id += 1
        
        return chunks
    
    def table_to_structured_text(self, table: List[List[str]]) -> str:
        """
        Converte tabela para texto estruturado
        """
        if not table:
            return ""
        
        lines = []
        headers = table[0]
        
        lines.append(f"TABELA: {headers[0]}")
        lines.append(f"Colunas: {', '.join(headers)}")
        lines.append(f"Dados: {len(table)-1} linhas")
        lines.append("")
        
        for i, row in enumerate(table[1:], 1):
            if len(row) == len(headers):
                row_parts = []
                for header, value in zip(headers, row):
                    if value and value.strip():
                        row_parts.append(f"{header}: {value}")
                
                if row_parts:
                    lines.append(f"Linha {i} - {', '.join(row_parts)}")
        
        return "\\n".join(lines)

def main():
    """
    Função principal
    """
    print("🚀 RAG PDF EXTRACTOR - VERSÃO DEFINITIVA")
    print("=" * 60)
    
    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ Arquivo não encontrado: {pdf_file}")
        return False
    
    try:
        extractor = DefinitivePDFExtractor()
        results = extractor.process_pdf(pdf_file)
        
        print("\\n" + "="*60)
        print("✅ EXTRAÇÃO CONCLUÍDA!")
        print(f"📄 Páginas: {results['pages_processed']}/{results['total_pages']}")
        print(f"📊 Tabelas: {results['tables_found']}")
        print(f"📁 Pasta: rag_outputs/")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
    else:
        print("\\n❌ PROCESSO FALHOU")
