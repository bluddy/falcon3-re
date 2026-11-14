#!/usr/bin/env python3
"""
Extract specific function disassembly from IDA analysis files.
Focus on finding the line vertex index resolution code.
"""

import re
import json
from pathlib import Path

def search_for_line_processing():
    """
    Search for code that processes line records and resolves vertex indices.
    
    Looking for patterns like:
    - lodsw (load word from SI register - typical for reading records)
    - Comparisons with 8000h or sign checks (for negative value handling)
    - Adding vertex count to negative indices
    - Multiplication by 6 (vertex stride = 3 int16s)
    """
    
    ida_dir = Path("ida_falconcd")
    
    results = []
    
    # Pattern 1: Sign test on loaded value
    # Pattern 2: Adding to convert negative to positive
    # Pattern 3: Multiplication by 6 or shift by 1 then add (for vertex access)
    
    patterns = [
        (r'test\s+\w+,\s*8000h', 'Sign bit test (checking if negative)'),
        (r'js\s+', 'Jump if sign (negative value branch)'),
        (r'add\s+\w+,\s*cx', 'Add vertex count (cx often holds count)'),
        (r'add\s+\w+,\s*\[.*vertex.*count.*\]', 'Add from vertex count variable'),
        (r'imul.*,\s*6', 'Multiply by 6 (vertex stride)'),
        (r'shl.*1.*shl.*1', 'Shift pattern for *6 (shift 1, shift 1, add original)'),
    ]
    
    disasm_files = list(ida_dir.glob("*disasm.txt"))
    print(f"Searching {len(disasm_files)} disassembly files...")
    
    for filepath in disasm_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Look for functions that match our patterns
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Get context around the match
                        start = max(0, match.start() - 500)
                        end = min(len(content), match.end() + 500)
                        context = content[start:end]
                        
                        # Extract the address if possible
                        addr_match = re.search(r'0x[0-9A-Fa-f]+:', context)
                        addr = addr_match.group() if addr_match else "unknown"
                        
                        results.append({
                            'file': filepath.name,
                            'pattern': description,
                            'address': addr,
                            'context': context[:200]  # First 200 chars of context
                        })
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    return results

def extract_line_loop_code():
    """
    Extract the complete disassembly of functions that process line data.
    
    Based on previous findings:
    - sub_26B2E calls the line processing loop
    - line_record_draw_loop @ 0x2978E processes line records
    - We need to find where vertex indices are loaded and resolved
    """
    
    ida_dir = Path("ida_falconcd")
    
    # Key addresses we want to examine
    target_ranges = [
        (0x26B86, 0x26C21, "sub_26B2E line processing section"),
        (0x2978E, 0x29920, "line_record_draw_loop complete"),
        (0x28B08, 0x28CA0, "line_draw_441e complete"),
    ]
    
    print("\n=== Extracting target function ranges ===\n")
    
    for start_addr, end_addr, description in target_ranges:
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"Range: 0x{start_addr:X} - 0x{end_addr:X}")
        print(f"{'='*60}\n")
        
        found = False
        
        for filepath in ida_dir.glob("*disasm.txt"):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                in_range = False
                output_lines = []
                
                for line in lines:
                    # Check if we're at a relevant address
                    addr_match = re.match(r'\s*0x([0-9A-Fa-f]+):', line)
                    if addr_match:
                        addr = int(addr_match.group(1), 16)
                        if start_addr <= addr <= end_addr:
                            in_range = True
                            found = True
                        elif in_range and addr > end_addr:
                            break
                    
                    if in_range:
                        output_lines.append(line.rstrip())
                
                if output_lines:
                    print(f"From file: {filepath.name}\n")
                    for line in output_lines[:100]:  # Limit output
                        print(line)
                    if len(output_lines) > 100:
                        print(f"\n... ({len(output_lines) - 100} more lines)")
                    print()
                    
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
        
        if not found:
            print(f"*** NOT FOUND in any file ***\n")

def main():
    print("="*70)
    print("ASSEMBLY CODE EXTRACTION - Line Vertex Index Resolution")
    print("="*70)
    print()
    print("Goal: Find assembly code that implements:")
    print("  if (index < 0) index = vertex_count + index")
    print()
    
    # First, search for patterns
    print("\n### PART 1: Pattern Search ###\n")
    results = search_for_line_processing()
    
    if results:
        print(f"\nFound {len(results)} potential matches:")
        # Group by pattern
        by_pattern = {}
        for r in results:
            pattern = r['pattern']
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(r)
        
        for pattern, matches in by_pattern.items():
            print(f"\n{pattern}: {len(matches)} occurrences")
            # Show first few
            for m in matches[:3]:
                print(f"  - {m['file']} @ {m['address']}")
    
    # Then extract the specific function ranges
    print("\n\n### PART 2: Full Function Extraction ###\n")
    extract_line_loop_code()

if __name__ == "__main__":
    main()
