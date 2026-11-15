"""
Round 2 expansion: Start from top 20 scoring functions from round 1.
Continue systematic expansion to find RLE decompressor.
"""
import idaapi
import idc
import idautils
import json
from collections import deque

def get_function_stats(addr):
    """Get detailed statistics about a function."""
    stats = {
        'bit_ops': 0,
        'buffer_writes': 0,
        'loops': 0,
        'calls': 0,
        'instructions': 0
    }
    
    func = idaapi.get_func(addr)
    if not func:
        return stats
    
    # Analyze instructions
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        if not idaapi.decode_insn(insn, ea):
            ea = idc.next_head(ea)
            continue
        
        stats['instructions'] += 1
        mnem = idc.print_insn_mnem(ea).lower()
        
        # Bit operations
        if mnem in ['shr', 'shl', 'sar', 'sal', 'ror', 'rol', 'and', 'or', 'xor', 'test']:
            stats['bit_ops'] += 1
        
        # Buffer writes
        if mnem in ['mov', 'stosb', 'stosw', 'rep', 'movsb', 'movsw']:
            # Check if writing to memory
            op1_type = idc.get_operand_type(ea, 0)
            if op1_type in [idc.o_mem, idc.o_phrase, idc.o_displ]:
                stats['buffer_writes'] += 1
        
        # Calls
        if mnem in ['call', 'callf']:
            stats['calls'] += 1
        
        # Loops (jumps backward)
        if mnem.startswith('j') and mnem not in ['jmp', 'jmpf']:
            target = idc.get_operand_value(ea, 0)
            if target < ea:
                stats['loops'] += 1
        
        ea = idc.next_head(ea)
    
    return stats

def get_all_callees(addr):
    """Get all functions called by this function."""
    callees = set()
    func = idaapi.get_func(addr)
    if not func:
        return callees
    
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        if not idaapi.decode_insn(insn, ea):
            ea = idc.next_head(ea)
            continue
        
        mnem = idc.print_insn_mnem(ea).lower()
        if mnem in ['call', 'callf']:
            target = idc.get_operand_value(ea, 0)
            if idc.get_func_attr(target, idc.FUNCATTR_START):
                callees.add(target)
        
        ea = idc.next_head(ea)
    
    return callees

def score_function(stats, size):
    """Score a function for RLE decompressor likelihood."""
    score = 0
    
    # RLE needs bit operations
    if stats['bit_ops'] >= 10:
        score += stats['bit_ops']
    
    # RLE writes to buffer
    if stats['buffer_writes'] >= 5:
        score += stats['buffer_writes'] * 2
    
    # RLE has loops
    if stats['loops'] >= 1:
        score += stats['loops'] * 3
    
    # Size: 100-500 bytes is ideal
    if 100 <= size <= 500:
        score += 5
    
    # Few external calls (should be self-contained)
    if stats['calls'] <= 5:
        score += 2
    
    return score

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("EXPANSION ROUND 2: Starting from top 20 candidates")
    print("=" * 80)
    
    # Top 20 seed addresses from round 1 results
    seeds = [
        0x0012DF6A,  # overlay_handler_large_1 (score 20)
        0x00015AFD,  # state_cursor_advance_11c94 (score 16)
        0x0002AC4C,  # overlay_segment_load (score 14)
        0x001820B0,  # r53_sbi_stream_dispatch (score 13)
        0x000163AD,  # terrain_pos_grid_build (score 13)
        0x00015903,  # fixed_matrix_scale_shift_7e900 (score 13)
        0x00130CE7,  # undoc_130CE7 (score 12)
        0x001031C0,  # r08_farptr_load_gate_entry (score 10)
        0x001297F0,  # picfont_idx_dat_loader (original seed)
        0x001397CE,  # madfont_idx_dat_loader (original seed)
    ]
    
    # Add dispatch-related functions
    seeds.extend([
        0x002257B,   # op_dispatch
        0x0220B0,    # dispatch_220b0_near (if it exists)
        0x022128,    # dispatch_22128_invoke_1arg (if it exists)
    ])
    
    print(f"\nStarting from {len(seeds)} seed functions")
    print("Depth limit: 8")
    
    # BFS expansion
    visited = set()
    queue = deque()
    depth_map = {}
    parent_map = {}
    
    for seed in seeds:
        if idc.get_func_attr(seed, idc.FUNCATTR_START):
            queue.append(seed)
            depth_map[seed] = 0
            parent_map[seed] = None
        else:
            print(f"  Warning: Seed 0x{seed:06X} is not a function")
    
    results = []
    potential_decompressors = []
    
    print("\nExpanding...")
    while queue:
        addr = queue.popleft()
        
        if addr in visited:
            continue
        
        visited.add(addr)
        depth = depth_map[addr]
        
        if depth > 8:
            continue
        
        # Analyze function
        func = idaapi.get_func(addr)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        name = idc.get_func_name(addr)
        stats = get_function_stats(addr)
        score = score_function(stats, size)
        
        result = {
            'address': f"0x{addr:08X}",
            'name': name,
            'depth': depth,
            'size': size,
            'stats': stats,
            'score': score,
            'parent': f"0x{parent_map[addr]:08X}" if parent_map[addr] else None
        }
        results.append(result)
        
        # High scoring functions
        if score >= 10:
            potential_decompressors.append(result)
        
        # Expand to callees
        callees = get_all_callees(addr)
        for callee in callees:
            if callee not in visited and callee not in depth_map:
                depth_map[callee] = depth + 1
                parent_map[callee] = addr
                queue.append(callee)
        
        if len(visited) % 100 == 0:
            print(f"  Analyzed {len(visited)} functions, depth {depth}, score {score}")
    
    print(f"\nTotal analyzed: {len(results)}")
    print(f"Potential decompressors (score >= 10): {len(potential_decompressors)}")
    
    # Sort by score
    potential_decompressors.sort(key=lambda x: x['score'], reverse=True)
    
    # Save results
    output = {
        'round': 2,
        'total_analyzed': len(results),
        'max_depth': 8,
        'seeds': len(seeds),
        'potential_decompressors': potential_decompressors[:50],  # Top 50
        'all_functions': results
    }
    
    with open('expansion_round2_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("TOP 20 POTENTIAL DECOMPRESSORS")
    print("=" * 80)
    for i, func in enumerate(potential_decompressors[:20], 1):
        print(f"{i:2}. 0x{int(func['address'], 16):06X} {func['name']:40} "
              f"score={func['score']:2} depth={func['depth']} size={func['size']:4}B "
              f"bit={func['stats']['bit_ops']:2} write={func['stats']['buffer_writes']:2} "
              f"loop={func['stats']['loops']:2}")
    
    print(f"\nResults saved to expansion_round2_results.json")
    print("Done!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
