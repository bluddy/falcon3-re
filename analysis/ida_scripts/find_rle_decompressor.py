"""
Find the RLE decompression algorithm by tracing backward from VGA palette upload.

Strategy:
1. Start with vga_dac_palette_upload (0x4F271) - 11 callers
2. Find functions that prepare graphics data before calling it
3. Look for loops with byte-counting patterns (RLE decompression signature)
4. Find functions that read .DAT file headers (00 04 width height)

Run in IDA: File > Script file > find_rle_decompressor.py
"""

import idaapi
import idc
import idautils
import json

def get_function_callers(func_ea):
    """Get all functions that call this function."""
    callers = set()
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near/Far call
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    return callers

def analyze_function_for_rle_patterns(func_ea):
    """
    Analyze a function for RLE decompression patterns.
    
    RLE patterns to look for:
    - Loop that reads byte count
    - memset-style fill operations
    - Byte copy loops
    - Comparison with 0x00, 0x04 (header markers)
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return {}
    
    patterns = {
        'loops': 0,
        'memset_calls': 0,
        'byte_compares': 0,
        'header_checks': [],  # Check for 0x00, 0x04
        'has_rep_stosb': False,  # Fast fill instruction
        'has_rep_movsb': False,  # Fast copy instruction
        'buffer_writes': 0,
    }
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        
        # Loop detection
        if mnem in ['loop', 'loopz', 'loopnz', 'loope', 'loopne']:
            patterns['loops'] += 1
        
        # Fast fill/copy operations (typical in decompressors)
        if mnem == 'rep':
            next_head = idc.next_head(head)
            if next_head != idaapi.BADADDR:
                next_mnem = idc.print_insn_mnem(next_head).lower()
                if next_mnem == 'stosb':
                    patterns['has_rep_stosb'] = True
                elif next_mnem == 'movsb':
                    patterns['has_rep_movsb'] = True
        
        # Byte comparisons (checking run lengths or markers)
        if mnem in ['cmp', 'test']:
            op1 = idc.print_operand(head, 1)
            # Check for header markers 0x00, 0x04
            if '0' in op1 or '4' in op1:
                patterns['header_checks'].append({
                    'address': head,
                    'instruction': idc.GetDisasm(head)
                })
            patterns['byte_compares'] += 1
        
        # Buffer write operations
        if mnem in ['mov', 'stosb'] and '[' in idc.print_operand(head, 0):
            patterns['buffer_writes'] += 1
    
    # Score the function for RLE likelihood
    score = 0
    if patterns['loops'] > 0:
        score += 2
    if patterns['has_rep_stosb']:
        score += 3  # Strong indicator
    if patterns['has_rep_movsb']:
        score += 2
    if patterns['byte_compares'] > 5:
        score += 2
    if len(patterns['header_checks']) > 0:
        score += 3  # Very strong indicator
    if patterns['buffer_writes'] > 10:
        score += 1
    
    patterns['rle_likelihood_score'] = score
    
    return patterns

def find_dat_file_readers():
    """
    Find functions that reference .DAT file strings.
    """
    dat_refs = []
    
    # Search for string references containing ".DAT"
    for string_ea in idautils.Strings():
        s = str(string_ea)
        if '.DAT' in s.upper() or '.IDX' in s.upper():
            # Find xrefs to this string
            for xref in idautils.XrefsTo(string_ea.ea, 0):
                func = idaapi.get_func(xref.frm)
                if func:
                    dat_refs.append({
                        'function': func.start_ea,
                        'function_name': idc.get_func_name(func.start_ea),
                        'string': s,
                        'string_ea': string_ea.ea
                    })
    
    return dat_refs

def main():
    print("="*80)
    print("FINDING RLE DECOMPRESSION ALGORITHM")
    print("="*80)
    
    # Wait for auto-analysis
    idaapi.auto_wait()
    
    # Start with vga_dac_palette_upload
    vga_upload_ea = 0x4F271
    
    print(f"\n[1] Analyzing vga_dac_palette_upload @ 0x{vga_upload_ea:x}")
    print("-"*80)
    
    callers = get_function_callers(vga_upload_ea)
    print(f"Found {len(callers)} callers")
    
    # Analyze each caller for RLE patterns
    print(f"\n[2] Analyzing callers for RLE decompression patterns")
    print("-"*80)
    
    caller_analysis = []
    for caller_ea in sorted(callers):
        name = idc.get_func_name(caller_ea)
        func = idaapi.get_func(caller_ea)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        patterns = analyze_function_for_rle_patterns(caller_ea)
        
        caller_analysis.append({
            'address': f'0x{caller_ea:x}',
            'name': name,
            'size': size,
            'patterns': patterns
        })
        
        score = patterns['rle_likelihood_score']
        print(f"\n{name:40s} @ 0x{caller_ea:06x} ({size:4d}B)")
        print(f"  RLE Likelihood Score: {score}/10")
        print(f"  Loops: {patterns['loops']}")
        print(f"  REP STOSB (fill): {patterns['has_rep_stosb']}")
        print(f"  REP MOVSB (copy): {patterns['has_rep_movsb']}")
        print(f"  Byte compares: {patterns['byte_compares']}")
        print(f"  Header checks: {len(patterns['header_checks'])}")
        if patterns['header_checks']:
            for check in patterns['header_checks'][:3]:  # Show first 3
                print(f"    - 0x{check['address']:06x}: {check['instruction']}")
        print(f"  Buffer writes: {patterns['buffer_writes']}")
    
    # Sort by RLE likelihood score
    caller_analysis.sort(key=lambda x: x['patterns']['rle_likelihood_score'], reverse=True)
    
    print(f"\n[3] Top candidates for RLE decompressor (by score):")
    print("-"*80)
    for i, analysis in enumerate(caller_analysis[:5], 1):
        score = analysis['patterns']['rle_likelihood_score']
        print(f"{i}. {analysis['name']:40s} @ {analysis['address']} (score: {score}/10)")
    
    # Find functions that reference .DAT files
    print(f"\n[4] Finding functions that reference .DAT/.IDX files")
    print("-"*80)
    
    dat_refs = find_dat_file_readers()
    print(f"Found {len(dat_refs)} .DAT/.IDX file references")
    
    # Show unique functions
    unique_funcs = {}
    for ref in dat_refs:
        func_ea = ref['function']
        if func_ea not in unique_funcs:
            unique_funcs[func_ea] = ref
    
    print(f"\nUnique functions: {len(unique_funcs)}")
    for func_ea, ref in sorted(unique_funcs.items())[:10]:
        print(f"  {ref['function_name']:40s} @ 0x{func_ea:06x} - '{ref['string']}'")
    
    # Analyze .DAT file reader functions for RLE patterns
    print(f"\n[5] Analyzing .DAT file readers for RLE patterns")
    print("-"*80)
    
    dat_reader_analysis = []
    for func_ea in unique_funcs.keys():
        name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        patterns = analyze_function_for_rle_patterns(func_ea)
        score = patterns['rle_likelihood_score']
        
        if score >= 3:  # Only show promising candidates
            dat_reader_analysis.append({
                'address': f'0x{func_ea:x}',
                'name': name,
                'size': size,
                'score': score,
                'patterns': patterns
            })
    
    dat_reader_analysis.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nPromising .DAT file reader candidates (score >= 3):")
    for analysis in dat_reader_analysis[:10]:
        print(f"  {analysis['name']:40s} @ {analysis['address']} (score: {analysis['score']}/10)")
    
    # Save results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\rle_decompressor_analysis.json'
    result = {
        'vga_upload': {
            'address': f'0x{vga_upload_ea:x}',
            'callers': len(callers)
        },
        'caller_analysis': caller_analysis,
        'dat_file_readers': dat_reader_analysis,
        'summary': {
            'top_vga_caller': caller_analysis[0] if caller_analysis else None,
            'top_dat_reader': dat_reader_analysis[0] if dat_reader_analysis else None
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Analysis saved to: {output_file}")
    print(f"{'='*80}")
    
    print("\n[RECOMMENDATION]")
    if caller_analysis:
        top = caller_analysis[0]
        print(f"Most likely RLE decompressor: {top['name']}")
        print(f"Address: {top['address']}")
        print(f"Score: {top['patterns']['rle_likelihood_score']}/10")
        print(f"Analyze this function in detail to understand the RLE algorithm.")

if __name__ == '__main__':
    main()
