"""
Correlate bitmask values to subsystem names by analyzing fault panel display code.

STRATEGY:
1. Load the subsystem bit mapping data
2. For each fault/panel display function, trace which bits are tested
3. Find which subsystem strings are referenced nearby
4. Build correlation map: bit → subsystem name

Focus on functions that display damage status on the fault panel.
"""

import json
import sys

MAPPING_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\subsystem_bit_mapping.json"

def analyze_correlations():
    """Analyze correlations between bitmasks and subsystem names."""
    
    with open(MAPPING_FILE, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("SUBSYSTEM BIT CORRELATION ANALYSIS")
    print("=" * 80)
    
    # Get all bitmasks
    bitmasks = sorted([int(k, 16) for k in data['grouped_by_bitmask'].keys()])
    
    print(f"\nFound {len(bitmasks)} unique bitmasks:")
    for mask in bitmasks:
        refs = data['grouped_by_bitmask'][hex(mask)]
        functions = set(r['function'] for r in refs)
        print(f"  0x{mask:04X} (bit {mask.bit_length()-1 if mask else 0}): {len(refs)} refs in {len(functions)} functions")
        for func in sorted(functions)[:3]:
            print(f"    - {func}")
    
    # Subsystem strings
    print(f"\n{len(data['subsystem_strings'])} subsystem types found:")
    for subsys, occurrences in data['subsystem_strings'].items():
        print(f"  {subsys}: {len(occurrences)} occurrences")
        # Show which functions use this string
        used_by = set()
        for occ in occurrences:
            used_by.update(occ['used_by'])
        if used_by:
            for func in sorted(used_by)[:3]:
                if func:
                    print(f"    - {func}")
    
    # Fault panel functions
    print(f"\n{len(data['fault_panel_functions'])} fault/panel display functions:")
    for func in data['fault_panel_functions'][:10]:
        print(f"  {func['name']} @ {func['address']} ({func['size']} bytes)")
    
    # Known bit mappings (from previous analysis)
    known_bits = {
        0x0020: "NAV (Navigation)",
        0x0200: "CRITICAL (Critical damage flag)",
        0x2000: "FUEL",
        0xC000: "SEVERITY (Damage level 0-3)"
    }
    
    print("\nKnown bit mappings (from previous analysis):")
    for mask, name in sorted(known_bits.items()):
        print(f"  0x{mask:04X}: {name}")
    
    # Correlate by function co-occurrence
    print("\nCorrelation by function co-occurrence:")
    print("(Which subsystems appear in same functions as which bitmasks)")
    
    correlations = {}
    
    for mask_hex, refs in data['grouped_by_bitmask'].items():
        mask = int(mask_hex, 16)
        functions_using_mask = set(r['function'] for r in refs)
        
        correlations[mask] = {}
        
        for subsys, occurrences in data['subsystem_strings'].items():
            # Count how many functions use both this mask and this subsystem
            functions_with_subsys = set()
            for occ in occurrences:
                functions_with_subsys.update(occ['used_by'])
            
            overlap = functions_using_mask & functions_with_subsys
            if overlap:
                correlations[mask][subsys] = list(overlap)
    
    # Show correlations
    for mask in sorted(correlations.keys()):
        if correlations[mask]:
            print(f"\n  0x{mask:04X}:")
            for subsys, funcs in correlations[mask].items():
                print(f"    → {subsys}: {len(funcs)} shared functions")
                for func in funcs[:2]:
                    print(f"        - {func}")
    
    # Recommendations for next steps
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("\n1. Examine fault panel display functions in detail:")
    for func in data['fault_panel_functions'][:5]:
        print(f"   - {func['name']} @ {func['address']}")
    
    print("\n2. Look for switch statements or bit-checking sequences that map bits to text")
    print("\n3. Focus on functions with multiple subsystem string references")
    print("\n4. Search for arrays of subsystem abbreviations indexed by bit position")

if __name__ == "__main__":
    analyze_correlations()
