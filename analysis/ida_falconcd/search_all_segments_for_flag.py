#!/usr/bin/env python3
"""
Search ALL segments (including other overlays and resident code) for 
references to r15_external_view_flag (0x107762).
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    flag_addr = 0x107762
    
    print("[*] Searching ALL segments for references to 0x{:X}...".format(flag_addr))
    print()
    
    # Get all segments
    segments = []
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        seg_size = seg_end - seg_start
        
        segments.append({
            'name': seg_name,
            'start': seg_start,
            'end': seg_end,
            'size': seg_size
        })
        
        print("Segment: {:20s} 0x{:08X} - 0x{:08X} ({:8d} bytes)".format(
            seg_name, seg_start, seg_end, seg_size))
    
    print()
    print("="*80)
    print("SEARCHING FOR XREFS TO 0x{:X} IN ALL SEGMENTS".format(flag_addr))
    print("="*80)
    print()
    
    # Search all xrefs
    all_xrefs = []
    for xref in idautils.XrefsTo(flag_addr):
        addr = xref.frm
        
        # Find which segment this xref is in
        seg_name = idc.get_segm_name(addr)
        func_name = idc.get_func_name(addr)
        insn = idc.generate_disasm_line(addr, 0)
        mnem = idc.print_insn_mnem(addr).lower()
        
        # Determine if write or read
        is_write = False
        if 'mov' in mnem:
            op0 = idc.print_operand(addr, 0)
            if 'r15_external_view_flag' in op0 or '107762' in op0:
                is_write = True
        
        xref_type = "WRITE" if is_write else "READ"
        
        entry = {
            'addr': addr,
            'addr_hex': '0x{:X}'.format(addr),
            'segment': seg_name,
            'func': func_name,
            'type': xref_type,
            'insn': insn,
            'mnem': mnem
        }
        
        all_xrefs.append(entry)
        
        print("[{:5s}] 0x{:08X} {:20s} {:30s}".format(
            xref_type, addr, seg_name, func_name))
        print("        {}".format(insn))
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("Total references found: {}".format(len(all_xrefs)))
    
    # Group by segment
    by_segment = {}
    for xref in all_xrefs:
        seg = xref['segment']
        if seg not in by_segment:
            by_segment[seg] = []
        by_segment[seg].append(xref)
    
    print("\nReferences by segment:")
    for seg_name in sorted(by_segment.keys()):
        refs = by_segment[seg_name]
        writes = [r for r in refs if r['type'] == 'WRITE']
        reads = [r for r in refs if r['type'] == 'READ']
        print("  {:20s} {:2d} refs ({} writes, {} reads)".format(
            seg_name, len(refs), len(writes), len(reads)))
    
    # Group by type
    writes = [x for x in all_xrefs if x['type'] == 'WRITE']
    reads = [x for x in all_xrefs if x['type'] == 'READ']
    
    print("\nWrite locations:")
    if writes:
        for w in writes:
            print("  0x{:08X} {:20s} {}".format(w['addr'], w['segment'], w['func']))
    else:
        print("  (none found)")
    
    print("\nRead locations:")
    if reads:
        for r in reads:
            print("  0x{:08X} {:20s} {}".format(r['addr'], r['segment'], r['func']))
    else:
        print("  (none found)")
    
    # Save results
    output = {
        'flag_address': '0x{:X}'.format(flag_addr),
        'segments': segments,
        'xrefs': all_xrefs,
        'summary': {
            'total_refs': len(all_xrefs),
            'total_writes': len(writes),
            'total_reads': len(reads),
            'by_segment': {seg: len(refs) for seg, refs in by_segment.items()}
        }
    }
    
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\all_segments_flag_search.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("="*80)
    print("Results saved to: all_segments_flag_search.json")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
