"""
Trace callees of font loader functions to find RLE decompressor.

The font loaders (picfont_idx_dat_loader, madfont_idx_dat_loader) must call
the actual decompression function. Let's find it.

Run in IDA: File > Script file > trace_font_loader_callees.py
"""

import idaapi
import idc
import idautils
import json

def get_all_callees(func_ea):
    """Get all functions called by this function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    callees = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near/Far call
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    name = idc.get_func_name(target_func.start_ea)
                    size = target_func.end_ea - target_func.start_ea
                    callees.append({
                        'address': f'0x{target_func.start_ea:x}',
                        'name': name,
                        'size': size,
                        'call_site': f'0x{head:x}'
                    })
    
    return callees

def analyze_for_decompression(func_ea):
    """Analyze a function to see if it looks like RLE decompression."""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    name = idc.get_func_name(func_ea)
    size = func.end_ea - func.start_ea
    
    # Count key patterns
    loops = 0
    rep_stosb = False
    rep_movsb = False
    buffer_writes = 0
    byte_reads = 0
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        
        if mnem in ['loop', 'loopz', 'loopnz']:
            loops += 1
        
        if mnem == 'rep':
            next_head = idc.next_head(head)
            if next_head != idaapi.BADADDR:
                next_mnem = idc.print_insn_mnem(next_head).lower()
                if next_mnem == 'stosb':
                    rep_stosb = True
                elif next_mnem == 'movsb':
                    rep_movsb = True
        
        if mnem in ['mov', 'stosb']:
            op0 = idc.print_operand(head, 0)
            if '[' in op0:  # Memory write
                buffer_writes += 1
        
        if mnem in ['mov', 'lodsb']:
            op1 = idc.print_operand(head, 1)
            if '[' in op1:  # Memory read
                byte_reads += 1
    
    # Calculate score
    score = 0
    if loops > 0:
        score += 2
    if rep_stosb:
        score += 5  # Very strong
    if rep_movsb:
        score += 3
    if buffer_writes > 10:
        score += 2
    if byte_reads > 5:
        score += 1
    
    return {
        'address': f'0x{func_ea:x}',
        'name': name,
        'size': size,
        'loops': loops,
        'rep_stosb': rep_stosb,
        'rep_movsb': rep_movsb,
        'buffer_writes': buffer_writes,
        'byte_reads': byte_reads,
        'score': score
    }

def main():
    print("="*80)
    print("TRACING FONT LOADER CALLEES TO FIND RLE DECOMPRESSOR")
    print("="*80)
    
    idaapi.auto_wait()
    
    # Font loaders
    loaders = [
        (0x1297F0, 'picfont_idx_dat_loader'),
        (0x1397CE, 'madfont_idx_dat_loader')
    ]
    
    all_callees = {}
    
    for loader_ea, loader_name in loaders:
        print(f"\n[1] Analyzing {loader_name} @ 0x{loader_ea:x}")
        print("-"*80)
        
        callees = get_all_callees(loader_ea)
        print(f"Found {len(callees)} callees\n")
        
        for callee in callees:
            addr = callee['address']
            if addr not in all_callees:
                all_callees[addr] = {
                    'info': callee,
                    'called_by': []
                }
            all_callees[addr]['called_by'].append(loader_name)
            
            print(f"  {callee['name']:40s} @ {addr} ({callee['size']:4d}B)")
    
    print(f"\n[2] Analyzing unique callees for decompression patterns")
    print("="*80)
    
    analyzed = []
    for addr_str, data in all_callees.items():
        addr = int(addr_str, 16)
        analysis = analyze_for_decompression(addr)
        if analysis:
            analysis['called_by'] = data['called_by']
            analyzed.append(analysis)
    
    # Sort by score
    analyzed.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nTop candidates for RLE decompressor (by score):\n")
    for i, item in enumerate(analyzed[:10], 1):
        print(f"{i}. {item['name']:40s} @ {item['address']}")
        print(f"   Size: {item['size']:4d}B  Score: {item['score']}/10")
        print(f"   Loops: {item['loops']}  REP STOSB: {item['rep_stosb']}  REP MOVSB: {item['rep_movsb']}")
        print(f"   Buffer writes: {item['buffer_writes']}  Byte reads: {item['byte_reads']}")
        print(f"   Called by: {', '.join(item['called_by'])}")
        print()
    
    # Save results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\font_loader_callees.json'
    result = {
        'loaders': [{'address': hex(ea), 'name': name} for ea, name in loaders],
        'callees': analyzed
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"{'='*80}")
    print(f"Analysis saved to: {output_file}")
    print(f"{'='*80}")
    
    if analyzed:
        top = analyzed[0]
        print(f"\n[RECOMMENDATION]")
        print(f"Most likely RLE decompressor: {top['name']}")
        print(f"Address: {top['address']}")
        print(f"Score: {top['score']}/10")
        
        if top['score'] >= 5:
            print("\n✓ HIGH CONFIDENCE - This is very likely the RLE decompressor!")
            print("  Examine this function's disassembly to understand the algorithm.")
        elif top['score'] >= 3:
            print("\n~ MEDIUM CONFIDENCE - This could be the RLE decompressor.")
            print("  Check if it's called after file I/O and before VGA upload.")
        else:
            print("\n✗ LOW CONFIDENCE - May need to trace deeper or try different approach.")

if __name__ == '__main__':
    main()
