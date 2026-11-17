"""
Investigate the drawing functions called from waypoint_display_helper.
Focuses on loc_68716+1 and loc_686FC+3 which appear to be symbol/text rendering.
"""

import idc
import idautils
import idaapi
import json
from pathlib import Path

def analyze_function(addr, name):
    """Analyze a function and return info."""
    func = idaapi.get_func(addr)
    if not func:
        return {
            'name': name,
            'address': hex(addr),
            'error': 'No function at address'
        }
    
    # Get function name
    fname = idc.get_func_name(func.start_ea)
    
    # Get size
    size = func.end_ea - func.start_ea
    
    # Count xrefs
    xrefs = list(idautils.XrefsTo(addr))
    
    # Get first 50 lines of disassembly
    disasm = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 50:
        line = idc.generate_disasm_line(ea, 0)
        disasm.append(f"{ea:08X}  {line}")
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    return {
        'name': fname,
        'address': hex(func.start_ea),
        'size': size,
        'xref_count': len(xrefs),
        'disasm_preview': disasm
    }

def find_symbol_tables():
    """Search for potential symbol/icon data tables."""
    
    # Look for arrays of small structs (symbol definitions)
    # Typically 2-10 bytes per symbol
    
    results = []
    
    # Search for references to small byte arrays
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        # Skip code segments
        if seg_name.startswith('R'):
            continue
            
        # Look for data references in this segment
        ea = seg_start
        while ea < seg_end:
            # Check if this looks like a pointer table
            refs = list(idautils.XrefsTo(ea))
            if len(refs) > 3:  # Multiple references = might be a table
                # Get some bytes
                bytes_here = [idc.get_wide_byte(ea + i) for i in range(min(32, seg_end - ea))]
                
                results.append({
                    'address': hex(ea),
                    'segment': seg_name,
                    'xref_count': len(refs),
                    'bytes_preview': ' '.join(f'{b:02X}' for b in bytes_here)
                })
                
                if len(results) >= 20:  # Limit results
                    break
            
            ea = idc.next_head(ea, seg_end)
        
        if len(results) >= 20:
            break
    
    return results

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    results = {
        'drawing_functions': {},
        'symbol_tables': []
    }
    
    # Analyze the two drawing functions we found
    print("=== Analyzing Drawing Functions ===\n")
    
    # loc_68716+1 = 0x68717
    addr1 = 0x68717
    print(f"Analyzing 0x{addr1:X} (loc_68716+1)...")
    results['drawing_functions']['loc_68716_plus_1'] = analyze_function(addr1, 'loc_68716+1')
    
    # loc_686FC+3 = 0x686FF
    addr2 = 0x686FF
    print(f"Analyzing 0x{addr2:X} (loc_686FC+3)...")
    results['drawing_functions']['loc_686FC_plus_3'] = analyze_function(addr2, 'loc_686FC+3')
    
    # Also check if waypoint_display_helper calls anything else interesting
    print("\n=== Checking Waypoint Display Helper Calls ===\n")
    waypoint_func = 0x1A163A
    func = idaapi.get_func(waypoint_func)
    if func:
        calls = []
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == 'call':
                # Get call target
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target)
                if target_name and 'farobj_vec3' not in target_name:
                    calls.append({
                        'from': hex(ea),
                        'to': hex(target),
                        'name': target_name
                    })
            ea = idc.next_head(ea, func.end_ea)
        
        results['waypoint_helper_calls'] = calls
        print(f"Found {len(calls)} non-vec3 calls")
    
    # Search for symbol tables
    print("\n=== Searching for Symbol/Icon Tables ===\n")
    results['symbol_tables'] = find_symbol_tables()
    print(f"Found {len(results['symbol_tables'])} potential tables")
    
    # Save results
    output_path = Path(__file__).parent / "drawing_functions_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
