#!/usr/bin/env python3
"""Extract and organize Falcon 3.0 manual into chapters."""

import pypdf
import re
import sys
from pathlib import Path

def extract_pdf_text(pdf_path):
    """Extract full text from PDF."""
    reader = pypdf.PdfReader(pdf_path)
    text = []
    for page_num, page in enumerate(reader.pages):
        text.append(f"\n--- PAGE {page_num + 1} ---\n")
        text.append(page.extract_text())
    return ''.join(text)

def identify_chapters(text):
    """Identify chapter boundaries in the text."""
    # Look for common chapter patterns
    chapter_patterns = [
        r'^(CHAPTER|Chapter)\s+(\d+|[IVX]+)[:\s]+(.+)$',
        r'^(\d+)\.\s+([A-Z][A-Z\s]+)$',
        r'^([IVX]+)\.\s+([A-Z][A-Z\s]+)$',
    ]
    
    chapters = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        for pattern in chapter_patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                chapters.append({
                    'line_num': i,
                    'title': line,
                    'match': match.groups()
                })
                break
    
    return chapters

def main():
    manual_path = Path('manual/Falcon_3_-_Manual_-_PC.pdf')
    
    if not manual_path.exists():
        print(f"Error: {manual_path} not found")
        return 1
    
    print(f"Extracting text from {manual_path}...")
    text = extract_pdf_text(manual_path)
    
    # Save full text for reference
    output_path = Path('manual/falcon3_manual_full_text.txt')
    output_path.write_text(text, encoding='utf-8')
    print(f"Full text saved to {output_path} ({len(text)} chars)")
    
    # Identify chapters
    print("\nIdentifying chapters...")
    chapters = identify_chapters(text)
    
    if chapters:
        print(f"\nFound {len(chapters)} potential chapters:")
        for ch in chapters[:20]:  # Show first 20
            print(f"  Line {ch['line_num']}: {ch['title']}")
    else:
        print("No clear chapter structure found. Manual may need manual parsing.")
        print("\nShowing first 2000 characters to identify structure:")
        print(text[:2000])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
