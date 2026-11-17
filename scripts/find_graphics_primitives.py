#!/usr/bin/env python3
"""
Find graphics primitives in Falcon 3.0 disassembly.
Searches for:
- VGA memory access (segment 0xA000)
- BIOS interrupts (INT 10h for video)
- Coordinate math patterns (multiplication, shifts for X/Y coords)
- Screen dimension constants (320x200, 640x480, etc.)
- Pixel plotting and line drawing primitives
"""

import re
from pathlib import Path

def search_disassembly(disasm_file: Path, patterns: dict) -> dict:
    """Search disassembly file for patterns."""
    results = {}
    
    if not disasm_file.exists():
        print(f"Warning: {disasm_file} not found")
        return results
    
    with open(disasm_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    for pattern_name, pattern_info in patterns.items():
        pattern = pattern_info['pattern']
        matches = []
        
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                # Get context (previous 2 lines and next 2 lines)
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = ''.join(lines[start:end])
                
                matches.append({
                    'line_num': i + 1,
                    'line': line.strip(),
                    'context': context
                })
        
        if matches:
            results[pattern_name] = {
                'description': pattern_info['description'],
                'count': len(matches),
                'matches': matches[:10]  # First 10 matches
            }
    
    return results

def main():
    base_dir = Path('C:/Users/ybarnoy/projects/falcon3')
    disasm_dir = base_dir / 'analysis'
    
    # Define search patterns
    patterns = {
        'vga_segment': {
            'pattern': r'\b0?[aA]000h?\b',
            'description': 'VGA memory segment (0xA000)'
        },
        'video_interrupt': {
            'pattern': r'int\s+10h',
            'description': 'BIOS video interrupt (INT 10h)'
        },
        'screen_width_320': {
            'pattern': r'\b(140h|320d?)\b',
            'description': 'Screen width 320 (0x140)'
        },
        'screen_width_640': {
            'pattern': r'\b(280h|640d?)\b',
            'description': 'Screen width 640 (0x280)'
        },
        'screen_height_200': {
            'pattern': r'\b(0?c8h|200d?)\b',
            'description': 'Screen height 200 (0xC8)'
        },
        'screen_height_480': {
            'pattern': r'\b(1e0h|480d?)\b',
            'description': 'Screen height 480 (0x1E0)'
        },
        'coord_multiply': {
            'pattern': r'(imul|mul).*(320|640|200|480|0?c8h|140h|280h|1e0h)',
            'description': 'Coordinate multiplication (likely Y * width + X)'
        },
        'coord_shift': {
            'pattern': r'(shl|shr|sal|sar).*(ax|bx|cx|dx|si|di)',
            'description': 'Coordinate bit shifts (scaling/alignment)'
        },
        'pixel_write': {
            'pattern': r'mov\s+(byte|word)\s+ptr\s+(es:|ds:)?\[',
            'description': 'Memory write pattern (possible pixel plotting)'
        },
        'es_segment_load': {
            'pattern': r'mov\s+es,',
            'description': 'ES segment load (VGA setup)'
        }
    }
    
    # Search available disassembly files
    print("=" * 80)
    print("GRAPHICS PRIMITIVES SEARCH")
    print("=" * 80)
    print()
    
    # Search R53 and R57 which are most likely to have graphics code
    disasm_files = [
        'r53_main_disasm.txt',
        'r57_state_machine_full_disasm.txt',
        'flight_physics_disasm.txt'
    ]
    
    all_results = {}
    
    for disasm_file_name in disasm_files:
        disasm_file = disasm_dir / disasm_file_name
        if not disasm_file.exists():
            print(f"Skipping {disasm_file_name} (not found)")
            continue
            
        print(f"\nSearching: {disasm_file_name}")
        print("-" * 80)
        
        results = search_disassembly(disasm_file, patterns)
        
        # Accumulate results
        for pattern_name, result in results.items():
            if pattern_name not in all_results:
                all_results[pattern_name] = {
                    'description': result['description'],
                    'files': {}
                }
            all_results[pattern_name]['files'][disasm_file_name] = result['count']
            
        # Show top matches for this file
        for pattern_name, result in results.items():
            if result['count'] > 0:
                print(f"\n  {result['description']}: {result['count']} matches")
                for match in result['matches'][:2]:  # First 2 matches only
                    print(f"    Line {match['line_num']}: {match['line'][:80]}")
    
    # Summary across all files
    print(f"\n{'=' * 80}")
    print("CROSS-FILE SUMMARY")
    print(f"{'=' * 80}")
    for pattern_name, result in all_results.items():
        total = sum(result['files'].values())
        if total > 0:
            print(f"\n{result['description']}: {total} total matches")
            for file_name, count in result['files'].items():
                if count > 0:
                    print(f"  {file_name}: {count}")

if __name__ == '__main__':
    main()
