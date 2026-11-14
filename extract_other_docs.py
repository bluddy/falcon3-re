#!/usr/bin/env python3
"""Extract other reference documents."""

import pypdf
from pathlib import Path

def extract_pdf(pdf_path, output_path):
    """Extract text from PDF."""
    reader = pypdf.PdfReader(pdf_path)
    text = []
    for page_num, page in enumerate(reader.pages):
        text.append(f"\n--- PAGE {page_num + 1} ---\n")
        text.append(page.extract_text())
    
    full_text = ''.join(text)
    output_path.write_text(full_text, encoding='utf-8')
    return len(full_text)

def main():
    output_dir = Path('manual/extracted')
    output_dir.mkdir(exist_ok=True)
    
    docs = [
        ('manual/Operation Fighting Tiger Flight Manual (Text).pdf', 'operation_fighting_tiger.txt'),
        ('manual/Falcon 3.0 Keyboard Shortcuts (Text).pdf', 'keyboard_shortcuts.txt'),
    ]
    
    print("Extracting additional documents:\n")
    for pdf_file, txt_file in docs:
        pdf_path = Path(pdf_file)
        if pdf_path.exists():
            output_path = output_dir / txt_file
            char_count = extract_pdf(pdf_path, output_path)
            print(f"  {pdf_path.name}")
            print(f"    -> {output_path}")
            print(f"    {char_count:,} chars\n")
        else:
            print(f"  SKIPPED: {pdf_file} (not found)\n")
    
    # Copy relevant text files from old_mods
    print("Copying reference text files from old_mods:\n")
    old_mods = Path('old_mods')
    txt_files = ['F3CTIP.TXT', 'F3CTP2.TXT', 'F3KEYS.TXT', 'F3TACT.TXT']
    
    for txt_file in txt_files:
        src_path = old_mods / txt_file
        if src_path.exists():
            content = src_path.read_text(encoding='latin-1', errors='replace')
            dst_path = output_dir / txt_file.lower()
            dst_path.write_text(content, encoding='utf-8')
            print(f"  {src_path}")
            print(f"    -> {dst_path}")
            print(f"    {len(content):,} chars\n")
        else:
            print(f"  SKIPPED: {src_path} (not found)\n")
    
    print(f"All documents extracted to: {output_dir}/")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
