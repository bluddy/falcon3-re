"""
Expand analysis systematically from known font loaders.
Extract and analyze all callees, then their callees, until we find RLE code.
"""
import idaapi
import idautils
import idc
import json

def get_function_info(addr):
    """Get comprehensive function information."""
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return None
    
    func_size = func_end - addr
    func_name = idc.get_func_name(addr)
    
    # Analyze instructions
    ea = addr
    stats = {
        'bit_ops': 0,
        'buffer_writes': 0,
        'loops': 0,
        'calls': 0,
        'instructions': 0
    }
    
    while ea < func_end and ea != idc.BADADDR and stats['instructions'] < 2000:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ['shl', 'shr', 'rol', 'ror', 'rcl', 'rcr']:
            stats['bit_ops'] += 1
        elif mnem in ['stosb', 'movsb', 'rep']:
            stats['buffer_writes'] += 1
        elif 'loop' in mnem:
            stats['loops'] += 1
        elif mnem in ['call', 'lcall']:
            stats['calls'] += 1
        elif mnem == 'mov':
            op0 = idc.print_operand(ea, 0)
            if '[' in op0 and 'sp' not in op0.lower() and 'bp' not in op0.lower():
                stats['buffer_writes'] += 1
        
        stats['instructions'] += 1
        ea = idc.next_head(ea)
    
    return {
        'addr': addr,
        'name': func_name,
        'size': func_size,
        'stats': stats
    }

def get_callees(addr):
    """Get all functions called by this function."""
    callees = []
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return callees
    
    ea = addr
    while ea < func_end and ea != idc.BADADDR:
        if idc.print_insn_mnem(ea) in ['call', 'lcall']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target = xref.to
                    target_name = idc.get_func_name(target)
                    if target_name and target not in callees:
                        callees.append(target)
        ea = idc.next_head(ea)
    
    return callees

def score_as_decompressor(info):
    """Score function as potential RLE decompressor."""
    if not info:
        return 0
    
    stats = info['stats']
    size = info['size']
    
    score = 0
    
    # Bit operations
    if stats['bit_ops'] >= 20:
        score += 10
    elif stats['bit_ops'] >= 10:
        score += 6
    elif stats['bit_ops'] >= 5:
        score += 3
    elif stats['bit_ops'] >= 1:
        score += 1
    
    # Buffer writes
    if stats['buffer_writes'] >= 20:
        score += 10
    elif stats['buffer_writes'] >= 10:
        score += 6
    elif stats['buffer_writes'] >= 5:
        score += 3
    elif stats['buffer_writes'] >= 1:
        score += 1
    
    # Loops
    if stats['loops'] >= 3:
        score += 5
    elif stats['loops'] >= 1:
        score += 3
    
    # Size (not too small, not too large)
    if 100 <= size <= 500:
        score += 3
    elif 50 <= size <= 1000:
        score += 1
    
    # Penalty for too many calls
    if stats['calls'] > 10:
        score -= 3
    
    return score

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("SYSTEMATIC ANALYSIS EXPANSION FROM FONT LOADERS")
    print("=" * 80)
    
    # Starting points
    seeds = [
        (0x1297F0, "picfont_idx_dat_loader"),
        (0x1397CE, "madfont_idx_dat_loader"),
    ]
    
    analyzed = set()
    to_analyze = list(seeds)
    
    all_functions = {}
    potential_decompressors = []
    
    depth = 0
    max_depth = 5
    
    while to_analyze and depth < max_depth:
        print(f"\n{'#' * 80}")
        print(f"DEPTH {depth} - Analyzing {len(to_analyze)} functions")
        print('#' * 80)
        
        next_level = []
        
        for addr, name in to_analyze:
            if addr in analyzed:
                continue
            
            analyzed.add(addr)
            
            print(f"\n{name} @ 0x{addr:08X}")
            
            # Get function info
            info = get_function_info(addr)
            if not info:
                print(f"  ERROR: Could not analyze")
                continue
            
            # Score it
            score = score_as_decompressor(info)
            info['score'] = score
            info['depth'] = depth
            
            all_functions[addr] = info
            
            print(f"  Size: {info['size']}B")
            print(f"  Instructions: {info['stats']['instructions']}")
            print(f"  Bit ops: {info['stats']['bit_ops']}")
            print(f"  Buffer writes: {info['stats']['buffer_writes']}")
            print(f"  Loops: {info['stats']['loops']}")
            print(f"  Calls: {info['stats']['calls']}")
            print(f"  Decompressor score: {score}/30")
            
            if score >= 10:
                print(f"  *** POTENTIAL DECOMPRESSOR ***")
                potential_decompressors.append(info)
            
            # Get callees
            callees = get_callees(addr)
            print(f"  Callees: {len(callees)}")
            
            for callee_addr in callees:
                callee_name = idc.get_func_name(callee_addr)
                if callee_addr not in analyzed:
                    next_level.append((callee_addr, callee_name))
                    print(f"    -> {callee_name} @ 0x{callee_addr:08X}")
        
        to_analyze = next_level
        depth += 1
        
        print(f"\nNext level has {len(next_level)} functions to analyze")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total functions analyzed: {len(analyzed)}")
    print(f"Depths reached: {depth}")
    print(f"Potential decompressors found: {len(potential_decompressors)}")
    
    if potential_decompressors:
        print("\nTOP CANDIDATES (score >= 10):")
        potential_decompressors.sort(key=lambda x: x['score'], reverse=True)
        
        for i, info in enumerate(potential_decompressors[:10], 1):
            print(f"\n{i}. {info['name']} @ 0x{info['addr']:08X}")
            print(f"   Depth: {info['depth']}, Score: {info['score']}/30")
            print(f"   Size: {info['size']}B, Bit ops: {info['stats']['bit_ops']}, "
                  f"Buffer writes: {info['stats']['buffer_writes']}, "
                  f"Loops: {info['stats']['loops']}")
    
    # Save results
    results = {
        'total_analyzed': len(analyzed),
        'max_depth': depth,
        'potential_decompressors': [
            {
                'addr': f"0x{info['addr']:08X}",
                'name': info['name'],
                'score': info['score'],
                'depth': info['depth'],
                'size': info['size'],
                'stats': info['stats']
            }
            for info in potential_decompressors
        ],
        'all_functions': {
            f"0x{addr:08X}": {
                'name': info['name'],
                'size': info['size'],
                'score': info['score'],
                'depth': info['depth'],
                'stats': info['stats']
            }
            for addr, info in all_functions.items()
        }
    }
    
    with open('expansion_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nComplete results saved to expansion_analysis_results.json")
    
    # Also create text summary
    with open('expansion_analysis_summary.txt', 'w') as f:
        f.write("Function Expansion Analysis from Font Loaders\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total functions analyzed: {len(analyzed)}\n")
        f.write(f"Expansion depth: {depth}\n\n")
        
        f.write("All functions by depth:\n")
        for d in range(depth):
            funcs_at_depth = [info for info in all_functions.values() if info['depth'] == d]
            f.write(f"\nDepth {d}: {len(funcs_at_depth)} functions\n")
            for info in sorted(funcs_at_depth, key=lambda x: x['score'], reverse=True):
                f.write(f"  {info['name']} @ 0x{info['addr']:08X} (score: {info['score']})\n")
        
        if potential_decompressors:
            f.write(f"\n\nPotential RLE Decompressors ({len(potential_decompressors)} found):\n")
            f.write("-" * 80 + "\n")
            for info in potential_decompressors:
                f.write(f"\n{info['name']} @ 0x{info['addr']:08X}\n")
                f.write(f"  Depth: {info['depth']}, Score: {info['score']}/30\n")
                f.write(f"  Size: {info['size']}B\n")
                f.write(f"  Bit ops: {info['stats']['bit_ops']}, "
                       f"Buffer writes: {info['stats']['buffer_writes']}, "
                       f"Loops: {info['stats']['loops']}, "
                       f"Calls: {info['stats']['calls']}\n")
    
    print("Text summary saved to expansion_analysis_summary.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
