#!/usr/bin/env python3
"""Consolidate Falcon 3.0 manual into major sections."""

import re
from pathlib import Path

def find_major_sections(text):
    """Find major section boundaries (consolidate by section number)."""
    lines = text.split('\n')
    sections = {}
    
    for i, line in enumerate(lines):
        # Match: "S E C T I O N   I :   I N T R O D U C T I O N"
        match = re.match(r'^S E C T I O N\s+([\w\s]+?):\s+(.+?)\s*\d*\s*$', line)
        if match:
            section_num = match.group(1).strip().replace(' ', '')
            section_name = match.group(2).strip()
            
            # Use section number as key to consolidate
            if section_num not in sections:
                sections[section_num] = {
                    'num': section_num,
                    'name': section_name,
                    'start_line': i,
                    'end_line': None
                }
    
    # Sort sections and set end_line for each
    sorted_keys = sorted(sections.keys(), key=lambda x: (
        {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 
         'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13}.get(x, 99)
    ))
    
    for i, key in enumerate(sorted_keys):
        if i + 1 < len(sorted_keys):
            next_key = sorted_keys[i + 1]
            sections[key]['end_line'] = sections[next_key]['start_line']
        else:
            sections[key]['end_line'] = len(lines)
    
    return sections, sorted_keys, lines

def extract_consolidated_chapters(sections, sorted_keys, lines):
    """Extract consolidated chapters."""
    chapters = []
    
    # Mapping for filenames
    roman_to_num = {
        'I': '01', 'II': '02', 'III': '03', 'IV': '04', 'V': '05', 'VI': '06',
        'VII': '07', 'VIII': '08', 'IX': '09', 'X': '10', 'XI': '11', 'XII': '12', 'XIII': '13'
    }
    
    for key in sorted_keys:
        sec = sections[key]
        num_part = roman_to_num.get(sec['num'], sec['num'])
        name_part = sec['name'].replace(' ', '_').replace(':', '').lower()
        filename = f"{num_part}_{name_part}.txt"
        
        # Extract text
        text_lines = lines[sec['start_line']:sec['end_line']]
        text = '\n'.join(text_lines)
        
        chapters.append({
            'filename': filename,
            'section_num': sec['num'],
            'section_name': sec['name'],
            'text': text,
            'line_count': len(text_lines),
            'char_count': len(text)
        })
    
    return chapters

def main():
    # Read the full extracted text
    text_file = Path('manual/falcon3_manual_full_text.txt')
    text = text_file.read_text(encoding='utf-8')
    
    # Find and consolidate sections
    sections, sorted_keys, lines = find_major_sections(text)
    print(f"Found {len(sections)} major sections:\n")
    
    for key in sorted_keys:
        sec = sections[key]
        print(f"  {sec['num']:5s} - {sec['name']}")
    
    # Extract consolidated chapters
    chapters = extract_consolidated_chapters(sections, sorted_keys, lines)
    
    # Create output directory
    output_dir = Path('manual/chapters_consolidated')
    output_dir.mkdir(exist_ok=True)
    
    # Write each chapter
    print(f"\nWriting {len(chapters)} consolidated chapter files to {output_dir}/\n")
    for ch in chapters:
        output_file = output_dir / ch['filename']
        output_file.write_text(ch['text'], encoding='utf-8')
        print(f"  {ch['filename']}")
        print(f"    Section {ch['section_num']}: {ch['section_name']}")
        print(f"    {ch['line_count']} lines, {ch['char_count']} chars\n")
    
    # Create comprehensive index
    index_file = output_dir / 'INDEX.md'
    index_content = "# FALCON 3.0 MANUAL - CHAPTER INDEX\n\n"
    index_content += "## Overview\n\n"
    index_content += "This manual has been organized into the following major sections:\n\n"
    
    # Priority guide
    index_content += "## Priority Guide for Code Analysis\n\n"
    index_content += "**CRITICAL** (essential for understanding game systems):\n"
    index_content += "- Section IX: FLIGHT - Complete aircraft systems, weapons, avionics\n"
    index_content += "- Section XIII: REFERENCE - Enemy aircraft, weapons data, game mechanics\n\n"
    index_content += "**HIGH** (helpful for context):\n"
    index_content += "- Section VI: AIR COMBAT SCHOOL - Flight maneuvers, tactics\n"
    index_content += "- Section VIII: CAMPAIGN - Mission objectives, scenarios\n\n"
    index_content += "**MEDIUM** (game flow understanding):\n"
    index_content += "- Section VII: RED FLAG - Mission editor\n"
    index_content += "- Section V: SQUADRON READY ROOM - Pilot management\n\n"
    index_content += "**LOW** (user interface, not relevant to code):\n"
    index_content += "- Section I-IV: Introduction, Instant Action, Installation, War Room\n"
    index_content += "- Section X-XII: Configuration, ACMI, Communications (multiplayer)\n\n"
    
    index_content += "## Sections\n\n"
    for i, ch in enumerate(chapters, 1):
        index_content += f"{i:2d}. **{ch['filename']}**\n"
        index_content += f"    - Section {ch['section_num']}: {ch['section_name']}\n"
        index_content += f"    - Size: {ch['line_count']} lines ({ch['char_count']:,} chars)\n\n"
    
    index_file.write_text(index_content, encoding='utf-8')
    print(f"Created index: {index_file}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
