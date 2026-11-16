"""
Examine word_79F16 which appears to be set by view handlers.

From dispatcher analysis, we see:
  0x18249A: mov es:word_79F16, 7
  0x1824A3: push 8
  
These might be setting view mode state!
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("EXAMINING STATE VARIABLE word_79F16")
    print("="*80)
    
    # Find the variable
    var_addr = idc.get_name_ea_simple("word_79F16")
    
    if var_addr == idc.BADADDR:
        print(f"\n[!] Variable word_79F16 not found")
        print(f"[*] Trying direct address 0x79F16...")
        var_addr = 0x79F16
    
    print(f"\n[*] Variable at: 0x{var_addr:X}")
    print()
    
    # Get all references
    writes = []
    reads = []
    
    for xref in idautils.XrefsTo(var_addr):
        addr = xref.frm
        insn = idc.GetDisasm(addr)
        mnem = idc.print_insn_mnem(addr)
        func = idc.get_func_name(addr)
        seg = idc.get_segm_name(addr)
        
        # Determine if read or write
        is_write = False
        if mnem in ['mov', 'xor', 'or', 'and', 'inc', 'dec']:
            op0_type = idc.get_operand_type(addr, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(addr, 0)
                if op0_addr == var_addr:
                    is_write = True
        
        ref = {
            'addr': f'0x{addr:X}',
            'func': func,
            'segment': seg,
            'insn': insn,
            'mnem': mnem
        }
        
        if is_write:
            writes.append(ref)
            print(f"  [WRITE] 0x{addr:X} in {seg}/{func}: {insn}")
        else:
            reads.append(ref)
            print(f"  [READ ] 0x{addr:X} in {seg}/{func}: {insn}")
    
    print(f"\n[*] Total: {len(writes)} writes, {len(reads)} reads")
    
    # Analyze write values
    print("\n" + "="*80)
    print("ANALYZING WRITE VALUES")
    print("="*80)
    print()
    
    for w in writes:
        addr_int = int(w['addr'], 16)
        # Try to extract the value being written
        if 'mov' in w['insn']:
            parts = w['insn'].split(',')
            if len(parts) == 2:
                value_str = parts[1].strip()
                print(f"  {w['addr']}: writes {value_str}")
                
                # Show context (5 instructions before and after)
                print(f"    Context:")
                context_start = addr_int - 10  # rough guess for 5 instructions back
                ea = context_start
                for i in range(10):
                    insn = idc.GetDisasm(ea)
                    marker = " >>>" if ea == addr_int else "    "
                    print(f"{marker} 0x{ea:X}: {insn}")
                    ea = idc.next_head(ea)
                print()
    
    # Save results
    output = {
        'variable': 'word_79F16',
        'address': f'0x{var_addr:X}',
        'writes': writes,
        'reads': reads
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\state_variable_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
