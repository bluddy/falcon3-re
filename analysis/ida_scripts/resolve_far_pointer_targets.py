"""
Resolve all the cs:dword_XXXXX far pointers we keep seeing.
These are the trampolines that are hiding the actual code.
"""
import idaapi
import idautils
import idc

def resolve_and_analyze_far_pointer(ptr_addr, ptr_name):
    """Resolve a far pointer and analyze the target."""
    # Read far pointer (offset + segment)
    offset = idc.get_wide_word(ptr_addr)
    segment = idc.get_wide_word(ptr_addr + 2)
    
    info = {
        'ptr_addr': ptr_addr,
        'ptr_name': ptr_name,
        'offset': offset,
        'segment': segment,
        'targets': []
    }
    
    # Try to find the target in IDA's address space
    # Method 1: Search all segments
    for seg_ea in idautils.Segments():
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        seg_name = idc.get_segm_name(seg_ea)
        
        # Try: segment base + offset
        test_addr = seg_start + offset
        if seg_start <= test_addr < seg_end:
            if idc.is_code(idc.get_full_flags(test_addr)):
                func_name = idc.get_func_name(test_addr)
                if func_name:
                    func_end = idc.get_func_attr(test_addr, idc.FUNCATTR_END)
                    func_size = func_end - test_addr if func_end != idc.BADADDR else 0
                    
                    info['targets'].append({
                        'addr': test_addr,
                        'name': func_name,
                        'size': func_size,
                        'segment': seg_name
                    })
    
    return info

def analyze_target_function(addr):
    """Quick analysis of target function."""
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return None
    
    size = func_end - addr
    
    ea = addr
    bit_ops = 0
    buffer_writes = 0
    loops = 0
    
    count = 0
    while ea < func_end and ea != idc.BADADDR and count < 1000:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ['shl', 'shr', 'rol', 'ror', 'rcl', 'rcr']:
            bit_ops += 1
        elif mnem in ['stosb', 'movsb', 'rep']:
            buffer_writes += 1
        elif 'loop' in mnem:
            loops += 1
        elif mnem == 'mov':
            op0 = idc.print_operand(ea, 0)
            if '[' in op0 and 'sp' not in op0.lower() and 'bp' not in op0.lower():
                buffer_writes += 1
        
        ea = idc.next_head(ea)
        count += 1
    
    return {
        'size': size,
        'bit_ops': bit_ops,
        'buffer_writes': buffer_writes,
        'loops': loops,
        'instructions': count
    }

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("RESOLVING FAR POINTER TRAMPOLINES")
    print("=" * 80)
    
    # Known far pointers from the disassembly
    far_pointers = [
        (0x0002000C, "opcode_handler_table"),
        (0x000220B0, "dword_220B0"),
        (0x000220F0, "dword_220F0"),
        (0x000220FC, "dword_220FC"),
        (0x00022100, "dword_22100"),
        (0x00022128, "dword_22128"),
    ]
    
    all_targets = {}
    
    for ptr_addr, ptr_name in far_pointers:
        print(f"\n{'-' * 80}")
        print(f"Pointer: {ptr_name} @ 0x{ptr_addr:08X}")
        print('-' * 80)
        
        info = resolve_and_analyze_far_pointer(ptr_addr, ptr_name)
        
        print(f"Far pointer: {info['segment']:04X}:{info['offset']:04X}")
        print(f"Targets found: {len(info['targets'])}")
        
        for target in info['targets']:
            print(f"\n  -> {target['name']} @ 0x{target['addr']:08X} (segment: {target['segment']})")
            print(f"     Size: {target['size']}B")
            
            # Analyze it
            stats = analyze_target_function(target['addr'])
            if stats:
                print(f"     Bit ops: {stats['bit_ops']}, Buffer writes: {stats['buffer_writes']}, Loops: {stats['loops']}")
                
                # Score it
                score = 0
                if stats['bit_ops'] >= 10:
                    score += 6
                elif stats['bit_ops'] >= 5:
                    score += 3
                elif stats['bit_ops'] >= 1:
                    score += 1
                
                if stats['buffer_writes'] >= 10:
                    score += 6
                elif stats['buffer_writes'] >= 5:
                    score += 3
                elif stats['buffer_writes'] >= 1:
                    score += 1
                
                if stats['loops'] >= 1:
                    score += 3
                
                if 100 <= stats['size'] <= 500:
                    score += 3
                
                print(f"     Decompressor score: {score}/18")
                
                if score >= 10:
                    print(f"     *** HIGH SCORE - POTENTIAL RLE DECOMPRESSOR ***")
                
                all_targets[target['addr']] = {
                    'name': target['name'],
                    'pointer': ptr_name,
                    'stats': stats,
                    'score': score
                }
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY - ALL TARGETS BY SCORE")
    print("=" * 80)
    
    sorted_targets = sorted(all_targets.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for addr, info in sorted_targets:
        if info['score'] >= 5:
            print(f"\n{info['name']} @ 0x{addr:08X} (via {info['pointer']})")
            print(f"  Score: {info['score']}/18")
            print(f"  Size: {info['stats']['size']}B, Bit ops: {info['stats']['bit_ops']}, "
                  f"Buffer writes: {info['stats']['buffer_writes']}, Loops: {info['stats']['loops']}")
    
    # Save results
    with open('far_pointer_resolution.txt', 'w') as f:
        f.write("Far Pointer Resolution Results\n")
        f.write("=" * 80 + "\n\n")
        
        for addr, info in sorted_targets:
            f.write(f"{info['name']} @ 0x{addr:08X}\n")
            f.write(f"  Via: {info['pointer']}\n")
            f.write(f"  Score: {info['score']}/18\n")
            f.write(f"  Stats: size={info['stats']['size']}B, bit_ops={info['stats']['bit_ops']}, "
                   f"buf_wr={info['stats']['buffer_writes']}, loops={info['stats']['loops']}\n\n")
    
    print(f"\n\nResults saved to far_pointer_resolution.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
