"""
Find where dword_22084 gets written to (initialized)
This will show us what function gets assigned
"""
import idaapi
import idc
import idautils
import json

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        ptr_ea = idc.get_name_ea_simple('dword_22084')
        print(f"[+] Looking for writes to 0x{ptr_ea:X} (dword_22084)")
        
        # Find all cross-references (reads and writes)
        writes = []
        reads = []
        
        for xref in idautils.XrefsTo(ptr_ea):
            xref_func = idc.get_func_name(xref.frm)
            disasm = idc.GetDisasm(xref.frm)
            
            # Determine if it's a write or read
            mnem = idc.print_insn_mnem(xref.frm)
            
            entry = {
                'addr': xref.frm,
                'func': xref_func,
                'disasm': disasm,
                'mnem': mnem,
                'type': xref.type
            }
            
            # MOV to memory is a write
            if mnem == 'mov':
                # Check if dword_22084 is the destination (first operand)
                op0_type = idc.get_operand_type(xref.frm, 0)
                if op0_type == idc.o_mem:
                    op0_val = idc.get_operand_value(xref.frm, 0)
                    if op0_val == ptr_ea:
                        writes.append(entry)
                    else:
                        reads.append(entry)
                else:
                    reads.append(entry)
            elif mnem == 'call':
                reads.append(entry)
            else:
                # Could be write (lea, etc.)
                writes.append(entry)
        
        print(f"[+] Found {len(writes)} potential writes")
        print(f"[+] Found {len(reads)} reads")
        
        print("\n=== WRITES (Initializations) ===")
        for write in writes:
            print(f"  0x{write['addr']:X}: {write['func']}")
            print(f"    {write['disasm']}")
        
        print("\n=== READS (Uses) ===")
        for read in reads[:10]:
            print(f"  0x{read['addr']:X}: {read['func']}")
            print(f"    {read['disasm']}")
        if len(reads) > 10:
            print(f"    ... and {len(reads) - 10} more")
        
        # If we found writes, get more details about those functions
        if writes:
            print("\n[*] Analyzing write functions...")
            for write in writes:
                func = idaapi.get_func(write['addr'])
                if func:
                    func_size = func.end_ea - func.start_ea
                    print(f"\n[+] Function: {write['func']}")
                    print(f"    Address: 0x{func.start_ea:X}")
                    print(f"    Size: {func_size} bytes")
                    
                    # Get surrounding instructions
                    print(f"    Context around write:")
                    start = max(func.start_ea, write['addr'] - 20)
                    end = min(func.end_ea, write['addr'] + 20)
                    for head in idautils.Heads(start, end):
                        if idc.is_code(idc.get_full_flags(head)):
                            disasm = idc.GetDisasm(head)
                            marker = " <<<" if head == write['addr'] else ""
                            print(f"      0x{head:X}: {disasm}{marker}")
        
        # Save results
        result = {
            'pointer_address': ptr_ea,
            'writes': writes,
            'reads': reads[:20]  # Limit reads in output
        }
        
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\pointer_writers_22084.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[+] Saved to {output_file}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
