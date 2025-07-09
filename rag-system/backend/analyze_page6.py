#!/usr/bin/env python3
"""
Teste melhorado para extrair TUDO do PDF - tabelas completas, cabeçalhos, rodapés
"""

import pdfplumber
from pathlib import Path
import json

def extract_complete_page(pdf_path: str, page_num: int):
    """
    Extrai TODO o conteúdo de uma página específica
    """
    print(f"🔍 ANÁLISE COMPLETA DA PÁGINA {page_num}")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            print(f"❌ Página {page_num} não existe. PDF tem {len(pdf.pages)} páginas.")
            return
            
        page = pdf.pages[page_num - 1]
        
        # 1. Texto completo
        print("📝 TEXTO COMPLETO:")
        print("-" * 40)
        text = page.extract_text()
        if text:
            print(text)
        else:
            print("(Nenhum texto encontrado)")
        print("-" * 40)
        print()
        
        # 2. Tabelas detalhadas
        print("📊 TABELAS DETALHADAS:")
        print("-" * 40)
        tables = page.extract_tables()
        if tables:
            for i, table in enumerate(tables):
                print(f"Tabela {i+1}:")
                for row_idx, row in enumerate(table):
                    print(f"  Linha {row_idx+1}: {row}")
                print()
        else:
            print("(Nenhuma tabela encontrada)")
        print("-" * 40)
        print()
        
        # 3. Elementos gráficos
        print("🎨 ELEMENTOS GRÁFICOS:")
        print("-" * 40)
        
        # Linhas
        lines = page.lines
        print(f"Linhas encontradas: {len(lines)}")
        
        # Retângulos  
        rects = page.rects
        print(f"Retângulos encontrados: {len(rects)}")
        
        # Curvas
        curves = page.curves
        print(f"Curvas encontradas: {len(curves)}")
        
        # Caracteres (para análise de fontes)
        chars = page.chars
        if chars:
            fonts = {}
            for char in chars:
                font = char.get('fontname', 'Unknown')
                size = char.get('size', 0)
                key = f"{font} ({size}pt)"
                fonts[key] = fonts.get(key, 0) + 1
            
            print("Fontes encontradas:")
            for font, count in sorted(fonts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {font}: {count} caracteres")
        
        print("-" * 40)
        print()
        
        # 4. Coordenadas da página
        print("📐 DIMENSÕES DA PÁGINA:")
        print(f"Largura: {page.width}")
        print(f"Altura: {page.height}")
        print(f"Coordenadas: ({page.bbox})")
        
        return {
            'text': text,
            'tables': tables,
            'lines_count': len(lines),
            'rects_count': len(rects),
            'curves_count': len(curves),
            'page_width': page.width,
            'page_height': page.height
        }

if __name__ == "__main__":
    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ Arquivo não encontrado: {pdf_file}")
        exit(1)
    
    # Extrair página 6 (tabela principal)
    result = extract_complete_page(pdf_file, 6)
    
    print("\n" + "="*60)
    print("🎯 RESUMO DA EXTRAÇÃO:")
    print(f"✅ Texto extraído: {'Sim' if result['text'] else 'Não'}")
    print(f"📊 Tabelas encontradas: {len(result['tables'])}")
    print(f"🎨 Elementos gráficos: {result['lines_count']} linhas, {result['rects_count']} retângulos")
