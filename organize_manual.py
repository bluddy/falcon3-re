#!/usr/bin/env python3
"""Organize Falcon 3.0 manual into separate chapter files."""

import re
from pathlib import Path

def find_sections(text):
    """Find all major section markers."""
    lines = text.split('\n')
    sections = []
    
    for i, line in enumerate(lines):
        # Look for SECTION markers like "S E C T I O N   I I :   I N S T A N T   A C T I O N"
        if re.match(r'^S E C T I O N\s+', line):
            sections.append({
                'line': i,
                'header': line.strip()
            })
    
    return sections

def extract_chapters(text, sections):
    """Extract text for each section."""
    lines = text.split('\n')
    chapters = []
    
    for i, section in enumerate(sections):
        start_line = section['line']
        # Find the next section or end of file
        end_line = sections[i + 1]['line'] if i + 1 < len(sections) else len(lines)
        
        chapter_text = '\n'.join(lines[start_line:end_line])
        
        # Create a clean filename from the section header
        # "S E C T I O N   I :   I N T R O D U C T I O N" -> "01_introduction"
        header = section['header']
        match = re.search(r'S E C T I O N\s+([\w\s]+?):(.*)', header)
        if match:
            section_num = match.group(1).strip().replace(' ', '')
            section_name = match.group(2).strip().replace(' ', '_').lower()
            
            # Convert roman numerals to numbers for sorting
            roman_to_num = {
                'I': '01', 'II': '02', 'III': '03', 'IV': '04', 
                'V': '05', 'VI': '06', 'VII': '07', 'VIII': '08',
                'IX': '09', 'X': '10', 'XI': '11', 'XII': '12'
            }
            num_part = roman_to_num.get(section_num, section_num)
            
            filename = f"{num_part}_{section_name}.txt"
        else:
            filename = f"section_{i:02d}.txt"
        
        chapters.append({
            'filename': filename,
            'header': header,
            'text': chapter_text,
            'line_count': len(chapter_text.split('\n'))
        })
    
    return chapters

def main():
    # Read the full extracted text
    text_file = Path('manual/falcon3_manual_full_text.txt')
    text = text_file.read_text(encoding='utf-8')
    
    # Find all sections
    sections = find_sections(text)
    print(f"Found {len(sections)} sections:")
    for i, sec in enumerate(sections):
        print(f"  {i+1}. {sec['header']}")
    
    # Extract chapters
    chapters = extract_chapters(text, sections)
    
    # Create output directory
    output_dir = Path('manual/chapters')
    output_dir.mkdir(exist_ok=True)
    
    # Write each chapter
    print(f"\nWriting {len(chapters)} chapter files to {output_dir}/")
    for ch in chapters:
        output_file = output_dir / ch['filename']
        output_file.write_text(ch['text'], encoding='utf-8')
        print(f"  {ch['filename']}: {ch['line_count']} lines")
    
    # Create index file
    index_file = output_dir / 'INDEX.txt'
    index_content = "FALCON 3.0 MANUAL - CHAPTER INDEX\n"
    index_content += "=" * 60 + "\n\n"
    for i, ch in enumerate(chapters, 1):
        index_content += f"{i:2d}. {ch['filename']}\n"
        index_content += f"    {ch['header']}\n"
        index_content += f"    ({ch['line_count']} lines)\n\n"
    
    index_file.write_text(index_content, encoding='utf-8')
    print(f"\nCreated index: {index_file}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
