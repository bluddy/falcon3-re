#!/usr/bin/env python3
"""
Find VGA mode 13h memory access patterns in Falcon 3.0.
Mode 13h uses segment 0xA000 with linear addressing.
320x200 = 64,000 pixels, 1 byte per pixel (256 colors).
"""

import re
from pathlib import Path
from collections import defaultdict

def find_vga_patterns(disasm_file: Path) -> dict:
    """Search for VGA segment 0xA000 access patterns."""
    
    if not disasm_file.exists():
        return {}
    
    with open(disasm_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    results = {
        'segment_loads': [],      # mov es, ax with ax=0xA000
        'direct_segment': [],     # mov es, 0xA000
        'segment_refs': [],       # any reference to 0xA000
        'pixel_writes': [],       # byte ptr es:[...] with potential VGA segment
        'linear_calc': [],        # y*320+x calculations
    }
    
    es_value = None  # Track ES segment value
    
    for i, line in enumerate(lines):
        # Track ES segment loads
        if re.search(r'mov\s+es,\s*ax', line, re.IGNORECASE):
            # Check previous lines for ax=0xA000
            for j in range(max(0, i-3), i):
                if re.search(r'mov\s+ax,\s*0?[aA]000h?', lines[j], re.IGNORECASE):
                    context_start = max(0, i-5)
                    context = ''.join(lines[context_start:i+3])
                    results['segment_loads'].append({
                        'line': i+1,
                        'context': context
                    })
                    es_value = 0xA000
                    break
        
        # Direct segment load
        if re.search(r'mov\s+es,\s*0?[aA]000h?', line, re.IGNORECASE):
            context_start = max(0, i-2)
            context = ''.join(lines[context_start:i+3])
            results['direct_segment'].append({
                'line': i+1,
                'context': context
            })
            es_value = 0xA000
        
        # Any reference to 0xA000
        if re.search(r'\b0?[aA]000h?\b', line, re.IGNORECASE):
            if 'mov' in line.lower() or 'cmp' in line.lower() or 'push' in line.lower():
                results['segment_refs'].append({
                    'line': i+1,
                    'text': line.strip()
                })
        
        # Pixel write patterns (byte write to ES segment)
        if re.search(r'mov\s+(byte|word)\s+ptr\s+es:\[', line, re.IGNORECASE):
            # Check if we think ES is 0xA000
            context_start = max(0, i-5)
            context = ''.join(lines[context_start:i+2])
            
            # Look for VGA segment load in context
            if re.search(r'(mov\s+es,.*[aA]000|0?[aA]000h)', context, re.IGNORECASE):
                results['pixel_writes'].append({
                    'line': i+1,
                    'instruction': line.strip(),
                    'context': context
                })
        
        # Linear offset calculation: y*320+x
        # Pattern: imul with 320 (0x140) or shifts equivalent to *320
        if re.search(r'(imul|mul).*0?140h', line, re.IGNORECASE):
            context_start = max(0, i-3)
            context = ''.join(lines[context_start:i+4])
            results['linear_calc'].append({
                'line': i+1,
                'context': context
            })
        
        # Also look for shift+add pattern: y*256 + y*64 = y*320
        # shl ax, 8 (y*256) followed by operations
        if re.search(r'shl\s+(ax|bx|cx|dx),\s*8', line, re.IGNORECASE):
            context_start = max(0, i-2)
            context = ''.join(lines[context_start:i+6])
            if '64' in context or '0x40' in context.lower():
                results['linear_calc'].append({
                    'line': i+1,
                    'context': context,
                    'note': 'Possible y*256+y*64=y*320 pattern'
                })
    
    return results

def main():
    base_dir = Path('C:/Users/ybarnoy/projects/falcon3')
    analysis_dir = base_dir / 'analysis'
    
    print("=" * 80)
    print("VGA MODE 13H ACCESS PATTERN SEARCH")
    print("=" * 80)
    print()
    print("Mode 13h: 320x200, 256 colors, segment 0xA000, linear framebuffer")
    print("Pixel offset = Y * 320 + X")
    print()
    
    # Search multiple disassembly files
    files_to_search = [
        'r53_main_disasm.txt',
        'r57_state_machine_full_disasm.txt',
        'flight_physics_disasm.txt',
    ]
    
    all_results = {}
    
    for filename in files_to_search:
        filepath = analysis_dir / filename
        if not filepath.exists():
            continue
        
        print(f"\nSearching: {filename}")
        print("-" * 80)
        
        results = find_vga_patterns(filepath)
        
        # Display results
        for pattern_name, matches in results.items():
            if matches:
                print(f"\n{pattern_name.replace('_', ' ').title()}: {len(matches)} matches")
                
                # Show first 3 matches
                for match in matches[:3]:
                    if 'context' in match:
                        print(f"\n  Line {match['line']}:")
                        # Show last 4 lines of context
                        context_lines = match['context'].strip().split('\n')[-4:]
                        for ctx_line in context_lines:
                            print(f"    {ctx_line.strip()}")
                    else:
                        print(f"  Line {match['line']}: {match.get('text', '')}")
        
        # Accumulate for summary
        for pattern_name, matches in results.items():
            if pattern_name not in all_results:
                all_results[pattern_name] = []
            all_results[pattern_name].extend([(filename, m) for m in matches])
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY ACROSS ALL FILES")
    print(f"{'=' * 80}")
    
    for pattern_name, matches in all_results.items():
        if matches:
            print(f"\n{pattern_name.replace('_', ' ').title()}: {len(matches)} total")
            
            # Group by file
            by_file = defaultdict(int)
            for filename, match in matches:
                by_file[filename] += 1
            
            for filename, count in by_file.items():
                print(f"  {filename}: {count}")
    
    # Analysis
    print(f"\n{'=' * 80}")
    print("ANALYSIS")
    print(f"{'=' * 80}")
    
    total_vga = sum(len(matches) for name, matches in all_results.items() 
                    if 'segment' in name or 'pixel' in name)
    
    if total_vga > 0:
        print(f"\n[+] Found {total_vga} VGA segment 0xA000 references")
        print("  Graphics likely write directly to VGA memory")
    else:
        print("\n[!] No direct VGA segment 0xA000 references found")
        print("  Possible reasons:")
        print("  1. VGA access is in different segment/overlay not yet disassembled")
        print("  2. Using off-screen buffer, then block copy to VGA")
        print("  3. Pattern not matching (need to adjust search)")
    
    linear_calcs = len(all_results.get('linear_calc', []))
    if linear_calcs > 0:
        print(f"\n[+] Found {linear_calcs} linear offset calculations (Y*320+X)")
        print("  Confirms mode 13h linear addressing")

if __name__ == '__main__':
    main()
