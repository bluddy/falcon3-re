"""
Comprehensive analysis of all .DAT/.IDX file loaders.
Find loading points, sizes, patterns.
"""

import idaapi
import idautils
import idc
import re

def find_all_file_strings():
    """Find all .IDX and .DAT file references."""
    print("="*80)
    print("FINDING ALL .IDX/.DAT FILE REFERENCES")
    print("="*80)
    
    idx_files = {}
    dat_files = {}
    
    # Iterate through all strings
    for string_ea in idautils.Strings():
        str_text = str(string_ea).upper()
        
        if '.IDX' in str_text:
            # Extract filename
            match = re.search(r'([A-Z0-9_]+\.IDX)', str_text)
            if match:
                filename = match.group(1)
                ea = string_ea.ea
                
                # Find xrefs
                xrefs = list(idautils.XrefsTo(ea))
                idx_files[filename] = {
                    'string_addr': ea,
                    'string_text': str(string_ea),
                    'xrefs': []
                }
                
                for xref in xrefs:
                    func = idaapi.get_func(xref.frm)
                    func_name = idc.get_func_name(func.start_ea) if func else "???"
                    func_addr = func.start_ea if func else 0
                    idx_files[filename]['xrefs'].append({
                        'addr': xref.frm,
                        'func': func_addr,
                        'func_name': func_name
                    })
        
        elif '.DAT' in str_text:
            match = re.search(r'([A-Z0-9_]+\.DAT)', str_text)
            if match:
                filename = match.group(1)
                ea = string_ea.ea
                
                xrefs = list(idautils.XrefsTo(ea))
                dat_files[filename] = {
                    'string_addr': ea,
                    'string_text': str(string_ea),
                    'xrefs': []
                }
                
                for xref in xrefs:
                    func = idaapi.get_func(xref.frm)
                    func_name = idc.get_func_name(func.start_ea) if func else "???"
                    func_addr = func.start_ea if func else 0
                    dat_files[filename]['xrefs'].append({
                        'addr': xref.frm,
                        'func': func_addr,
                        'func_name': func_name
                    })
    
    return idx_files, dat_files

def analyze_loader_function(func_addr, file_pair_name):
    """Analyze a single loader function to extract size constants."""
    print(f"\n  Analyzing {file_pair_name} loader at 0x{func_addr:X}...")
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"    ERROR: Cannot get function")
        return None
    
    # Look for PUSH instructions with size constants
    # Pattern: push <size_constant>; push <file_handle>; push <operation>; call file_io
    size_constants = []
    
    for ea in range(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(ea)
        
        # Look for PUSH with immediate value
        if mnem == 'push':
            op_type = idc.get_operand_type(ea, 0)
            if op_type == idc.o_imm:  # Immediate value
                value = idc.get_operand_value(ea, 0)
                # Size constants are typically in range 1-10000
                if 1 < value < 10000:
                    # Check if followed by more pushes (likely parameters)
                    next_ea = idc.next_head(ea)
                    next_mnem = idc.print_insn_mnem(next_ea)
                    if next_mnem == 'push':
                        disasm = idc.generate_disasm_line(ea, 0)
                        size_constants.append({
                            'addr': ea,
                            'value': value,
                            'hex': f"0x{value:X}",
                            'disasm': disasm
                        })
    
    if size_constants:
        print(f"    Found {len(size_constants)} potential size constants:")
        for sc in size_constants[:10]:  # Limit output
            print(f"      0x{sc['addr']:X}: {sc['disasm']} (decimal: {sc['value']})")
    
    # Get function size
    func_size = func.end_ea - func.start_ea
    
    return {
        'func_addr': func_addr,
        'func_size': func_size,
        'size_constants': size_constants
    }

def pair_idx_dat_files(idx_files, dat_files):
    """Pair .IDX and .DAT files by base name."""
    print("\n" + "="*80)
    print("PAIRING .IDX AND .DAT FILES")
    print("="*80)
    
    pairs = {}
    
    for idx_name in idx_files:
        base_name = idx_name.replace('.IDX', '')
        dat_name = base_name + '.DAT'
        
        if dat_name in dat_files:
            # Files are paired
            pairs[base_name] = {
                'idx': idx_files[idx_name],
                'dat': dat_files[dat_name],
                'idx_name': idx_name,
                'dat_name': dat_name
            }
            
            # Check if they share the same loader function
            idx_funcs = set(x['func'] for x in idx_files[idx_name]['xrefs'])
            dat_funcs = set(x['func'] for x in dat_files[dat_name]['xrefs'])
            shared_funcs = idx_funcs & dat_funcs
            
            pairs[base_name]['shared_loaders'] = list(shared_funcs)
            
            print(f"\n{base_name}:")
            print(f"  IDX at 0x{idx_files[idx_name]['string_addr']:X}: {idx_name}")
            print(f"    {len(idx_files[idx_name]['xrefs'])} references")
            print(f"  DAT at 0x{dat_files[dat_name]['string_addr']:X}: {dat_name}")
            print(f"    {len(dat_files[dat_name]['xrefs'])} references")
            
            if shared_funcs:
                print(f"  Shared loader functions: {len(shared_funcs)}")
                for func_addr in shared_funcs:
                    func_name = idc.get_func_name(func_addr)
                    print(f"    0x{func_addr:X}: {func_name}")
            else:
                print(f"  WARNING: No shared loader functions!")
    
    return pairs

def analyze_all_loaders(pairs):
    """Analyze all loader functions."""
    print("\n" + "="*80)
    print("ANALYZING ALL LOADER FUNCTIONS")
    print("="*80)
    
    loader_analysis = {}
    
    for base_name, pair_info in pairs.items():
        if pair_info['shared_loaders']:
            for func_addr in pair_info['shared_loaders']:
                if func_addr not in loader_analysis:
                    func_name = idc.get_func_name(func_addr)
                    print(f"\n{'='*80}")
                    print(f"LOADER: {func_name} at 0x{func_addr:X}")
                    print(f"{'='*80}")
                    
                    analysis = analyze_loader_function(func_addr, base_name)
                    if analysis:
                        loader_analysis[func_addr] = analysis
                        loader_analysis[func_addr]['files'] = [base_name]
                else:
                    loader_analysis[func_addr]['files'].append(base_name)

    return loader_analysis

def summarize_findings(pairs, loader_analysis):
    """Create summary tables."""
    print("\n" + "="*80)
    print("SUMMARY: ALL .IDX/.DAT FILE PAIRS")
    print("="*80)
    
    print(f"\nTotal pairs found: {len(pairs)}")
    print("\nPair Name               | Loader Function          | Size Constants")
    print("-" * 80)
    
    for base_name in sorted(pairs.keys()):
        pair = pairs[base_name]
        if pair['shared_loaders']:
            for func_addr in pair['shared_loaders']:
                func_name = idc.get_func_name(func_addr)
                
                sizes = "None"
                if func_addr in loader_analysis:
                    size_vals = [sc['value'] for sc in loader_analysis[func_addr]['size_constants']]
                    if size_vals:
                        # Show first 3 sizes
                        sizes = ", ".join([str(s) for s in size_vals[:3]])
                        if len(size_vals) > 3:
                            sizes += f" ... (+{len(size_vals)-3})"
                
                print(f"{base_name:23} | {func_name:24} | {sizes}")
    
    # Analyze patterns
    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80)
    
    # Group by loader function
    loaders_by_func = {}
    for base_name, pair in pairs.items():
        for func_addr in pair['shared_loaders']:
            func_name = idc.get_func_name(func_addr)
            if func_name not in loaders_by_func:
                loaders_by_func[func_name] = []
            loaders_by_func[func_name].append(base_name)
    
    print("\nLoader Functions by Usage:")
    for func_name in sorted(loaders_by_func.keys()):
        files = loaders_by_func[func_name]
        print(f"\n{func_name} ({len(files)} file pairs):")
        for f in sorted(files):
            print(f"  - {f}")
    
    # Look for common size patterns
    print("\n" + "="*80)
    print("COMMON SIZE PATTERNS")
    print("="*80)
    
    all_sizes = {}
    for func_addr, analysis in loader_analysis.items():
        func_name = idc.get_func_name(func_addr)
        for sc in analysis['size_constants']:
            size = sc['value']
            if size not in all_sizes:
                all_sizes[size] = []
            all_sizes[size].append(func_name)
    
    # Show most common sizes
    print("\nMost common size constants:")
    sorted_sizes = sorted(all_sizes.items(), key=lambda x: len(x[1]), reverse=True)
    for size, funcs in sorted_sizes[:20]:
        print(f"  {size:5} (0x{size:04X}): used by {len(funcs)} loader(s)")
        if len(funcs) <= 3:
            for f in funcs:
                print(f"    - {f}")

def export_results(pairs, loader_analysis):
    """Export results to file for further analysis."""
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)
    
    output = []
    output.append("="*80)
    output.append("COMPLETE .IDX/.DAT LOADER ANALYSIS")
    output.append("="*80)
    output.append("")
    
    for base_name in sorted(pairs.keys()):
        pair = pairs[base_name]
        output.append(f"\n{'='*80}")
        output.append(f"FILE PAIR: {base_name}")
        output.append(f"{'='*80}")
        output.append(f"IDX: {pair['idx_name']}")
        output.append(f"DAT: {pair['dat_name']}")
        output.append("")
        
        if pair['shared_loaders']:
            for func_addr in pair['shared_loaders']:
                func_name = idc.get_func_name(func_addr)
                output.append(f"Loader: {func_name} at 0x{func_addr:X}")
                
                if func_addr in loader_analysis:
                    analysis = loader_analysis[func_addr]
                    output.append(f"  Function size: {analysis['func_size']} bytes")
                    output.append(f"  Size constants found: {len(analysis['size_constants'])}")
                    for sc in analysis['size_constants']:
                        output.append(f"    0x{sc['addr']:X}: {sc['value']} (0x{sc['value']:X})")
        else:
            output.append("WARNING: No shared loader function!")
        
        output.append("")
    
    # Write to file
    output_text = "\n".join(output)
    print(output_text)
    
    return output_text

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("COMPREHENSIVE .IDX/.DAT LOADER ANALYSIS")
    print("="*80)
    print()
    
    # Find all file references
    idx_files, dat_files = find_all_file_strings()
    
    print(f"\nFound {len(idx_files)} .IDX files")
    print(f"Found {len(dat_files)} .DAT files")
    
    # Pair them up
    pairs = pair_idx_dat_files(idx_files, dat_files)
    
    # Analyze loaders
    loader_analysis = analyze_all_loaders(pairs)
    
    # Summarize
    summarize_findings(pairs, loader_analysis)
    
    # Export
    results = export_results(pairs, loader_analysis)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nAnalyzed {len(pairs)} file pairs")
    print(f"Found {len(loader_analysis)} unique loader functions")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
