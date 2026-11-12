"""
Analyze DGROUP:0x4287 - Camera/view state structure.
This is the critical data structure passed to view_projection.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_dgroup_offset(offset):
    """Analyze a specific DGROUP offset."""
    
    dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
    if dgroup_base == idc.BADADDR:
        print("✗ DGROUP not found")
        return None
    
    addr = dgroup_base + offset
    
    print("="*80)
    print(f"ANALYZING DGROUP:0x{offset:X}")
    print("="*80)
    print(f"Linear address: {hex(addr)}")
    print(f"DGROUP base: {hex(dgroup_base)}")
    print(f"Offset: 0x{offset:X} ({offset} bytes)")
    
    # Get name and type
    name = idc.get_name(addr)
    type_str = idc.get_type(addr)
    
    print(f"\nName: {name if name else 'unnamed'}")
    print(f"Type: {type_str if type_str else 'unknown'}")
    
    # Get all xrefs
    xrefs = list(idautils.XrefsTo(addr, 0))
    print(f"\nTotal xrefs: {len(xrefs)}")
    
    # Group by function
    xref_funcs = {}
    for xref in xrefs:
        func_name = idc.get_func_name(xref.frm)
        if func_name:
            if func_name not in xref_funcs:
                xref_funcs[func_name] = []
            xref_funcs[func_name].append({
                "address": hex(xref.frm),
                "disasm": idc.GetDisasm(xref.frm),
                "type": xref.type
            })
    
    print(f"\nUsed by {len(xref_funcs)} functions:")
    for func_name in sorted(xref_funcs.keys()):
        refs = xref_funcs[func_name]
        print(f"\n  {func_name} ({len(refs)} refs):")
        for ref in refs[:5]:  # First 5
            print(f"    {ref['address']}: {ref['disasm']}")
        if len(refs) > 5:
            print(f"    ... and {len(refs) - 5} more")
    
    # Analyze access patterns to determine structure
    print(f"\n{'='*80}")
    print("STRUCTURE LAYOUT ANALYSIS")
    print("="*80)
    
    # Look for offset accesses like [DGROUP:4287+X]
    offsets_used = set()
    
    for func_name, refs in xref_funcs.items():
        for ref in refs:
            disasm = ref['disasm']
            ref_addr = int(ref['address'], 16)
            
            # Try to detect offset patterns
            # Common patterns: mov [di+offset], reg
            #                  mov reg, [di+offset]
            #                  lea reg, [di+offset]
            
            # Get the actual operand value
            for i in range(idc.get_operand_count(ref_addr)):
                op_type = idc.get_operand_type(ref_addr, i)
                if op_type == idc.o_displ:  # Displacement (base+offset)
                    # This is an offset access
                    op_val = idc.get_operand_value(ref_addr, i)
                    if op_val != addr:  # Not the base
                        offset_from_base = op_val - addr
                        if -100 < offset_from_base < 200:  # Reasonable range
                            offsets_used.add(offset_from_base)
    
    if offsets_used:
        print(f"\nDetected structure accesses at offsets:")
        for off in sorted(offsets_used):
            print(f"  +0x{off:04X} ({off:+d} bytes)")
        
        # Estimate structure size
        if offsets_used:
            max_offset = max(offsets_used)
            min_offset = min(offsets_used)
            print(f"\nEstimated structure:")
            print(f"  Lowest offset: {min_offset:+d}")
            print(f"  Highest offset: +{max_offset}")
            print(f"  Minimum size: {max_offset + 4} bytes (assuming int16/int32)")
    else:
        print("\nNo offset accesses detected - base address only")
    
    # Check for known patterns
    print(f"\n{'='*80}")
    print("ACCESS PATTERN ANALYSIS")
    print("="*80)
    
    read_count = 0
    write_count = 0
    
    for func_name, refs in xref_funcs.items():
        for ref in refs:
            disasm = ref['disasm'].lower()
            if 'mov' in disasm and any(r in disasm for r in ['[', 'ptr']):
                # Try to determine if read or write
                if disasm.split(',')[0].strip().startswith('mov ['):
                    write_count += 1
                else:
                    read_count += 1
    
    print(f"Read operations: ~{read_count}")
    print(f"Write operations: ~{write_count}")
    
    if read_count > write_count * 3:
        print("→ Mostly READ - likely state/configuration data")
    elif write_count > read_count * 3:
        print("→ Mostly WRITE - likely output/result buffer")
    else:
        print("→ Mixed READ/WRITE - likely working state")
    
    return {
        "offset": hex(offset),
        "address": hex(addr),
        "name": name,
        "type": type_str,
        "xref_count": len(xrefs),
        "used_by_functions": list(xref_funcs.keys()),
        "offsets_detected": sorted(list(offsets_used)) if offsets_used else [],
        "read_count": read_count,
        "write_count": write_count
    }

def find_nearby_structures():
    """Find other structures near 0x4287."""
    
    print("\n" + "="*80)
    print("NEARBY DGROUP STRUCTURES")
    print("="*80)
    
    dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
    if dgroup_base == idc.BADADDR:
        return []
    
    # Check offsets around 0x4287
    nearby_offsets = []
    for delta in range(-256, 256, 4):  # Check ±256 bytes, 4-byte aligned
        offset = 0x4287 + delta
        if offset < 0:
            continue
        
        addr = dgroup_base + offset
        name = idc.get_name(addr)
        
        if name and name != "":
            xrefs = list(idautils.XrefsTo(addr, 0))
            if len(xrefs) > 0:
                nearby_offsets.append({
                    "offset": hex(offset),
                    "delta": delta,
                    "name": name,
                    "xref_count": len(xrefs)
                })
    
    if nearby_offsets:
        print(f"\nFound {len(nearby_offsets)} named structures nearby:")
        for item in sorted(nearby_offsets, key=lambda x: x['delta']):
            print(f"  DGROUP:0x{int(item['offset'], 16):04X} ({item['delta']:+5d}): {item['name']} ({item['xref_count']} xrefs)")
    else:
        print("\nNo named structures found nearby")
    
    return nearby_offsets

def main():
    print("="*80)
    print("DGROUP:0x4287 ANALYSIS")
    print("Camera/View State Structure")
    print("="*80)
    
    # Analyze the main offset
    analysis = analyze_dgroup_offset(0x4287)
    
    # Find nearby structures
    nearby = find_nearby_structures()
    
    # Save results
    results = {
        "dgroup_4287": analysis,
        "nearby_structures": nearby
    }
    
    output_file = Path(__file__).parent / "dgroup_4287_detailed.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    # Provide recommendations
    if analysis:
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        if analysis['offsets_detected']:
            max_off = max(analysis['offsets_detected'])
            print(f"\nStructure appears to be at least {max_off + 4} bytes")
            print("Suggested name: camera_view_state or view_matrix_data")
        
        if analysis['used_by_functions']:
            print(f"\nUsed by {len(analysis['used_by_functions'])} functions:")
            print("Key users:")
            for func in analysis['used_by_functions'][:5]:
                print(f"  - {func}")
    
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
