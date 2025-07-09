#!/usr/bin/env python3
"""
Simple test to check basic system functionality
"""

import os
import sys

def test_basic_imports():
    """Test basic imports that should work"""
    print("Testing basic imports...")
    
    try:
        import json
        print("✓ json import successful")
    except ImportError as e:
        print(f"✗ json import failed: {e}")
        return False
    
    try:
        import pathlib
        print("✓ pathlib import successful")
    except ImportError as e:
        print(f"✗ pathlib import failed: {e}")
        return False
    
    try:
        import logging
        print("✓ logging import successful")
    except ImportError as e:
        print(f"✗ logging import failed: {e}")
        return False
    
    try:
        import uuid
        print("✓ uuid import successful")
    except ImportError as e:
        print(f"✗ uuid import failed: {e}")
        return False
    
    try:
        import datetime
        print("✓ datetime import successful")
    except ImportError as e:
        print(f"✗ datetime import failed: {e}")
        return False
    
    return True

def test_available_packages():
    """Test which packages are available"""
    print("\nTesting available packages...")
    
    packages_to_test = [
        'fastapi',
        'uvicorn', 
        'docling',
        'docling_core',
        'pdfplumber',
        'python_docx',
        'openpyxl',
        'pandas',
        'pytesseract',
        'easyocr',
        'opencv-python'
    ]
    
    available = []
    missing = []
    
    for package in packages_to_test:
        try:
            __import__(package.replace('-', '_'))
            available.append(package)
            print(f"✓ {package} available")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} missing")
    
    return available, missing

def test_file_structure():
    """Test if required files exist"""
    print("\nTesting file structure...")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_check = [
        'main.py',
        'rag_processor.py',
        'main_new.py',
        'requirements.txt'
    ]
    
    for filename in files_to_check:
        filepath = os.path.join(backend_dir, filename)
        if os.path.exists(filepath):
            print(f"✓ {filename} exists")
        else:
            print(f"✗ {filename} missing")

def main():
    print("=== RAG System Simple Test ===\n")
    
    # Test basic imports
    if not test_basic_imports():
        print("\n❌ Basic imports failed!")
        return False
    
    # Test available packages
    available, missing = test_available_packages()
    
    # Test file structure
    test_file_structure()
    
    print(f"\n=== Test Summary ===")
    print(f"Available packages: {len(available)}")
    print(f"Missing packages: {len(missing)}")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
    else:
        print("\n✅ All packages available!")
    
    return len(missing) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
