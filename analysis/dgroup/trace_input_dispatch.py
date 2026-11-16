"""
Trace dispatch of input_flag_pending_2 to find view switching code.

Strategy:
1. Find all READS of input_flag_pending_2 (not writes)
2. Look for conditional branches based on scan code values 0x02-0x0B
3. Find switch/jump tables indexed by scan code
4. Look for calls to view functions based on scan code
"""

import idaapi
import idautils
import idc
import json

def find_input_flag_reads():
    """Find all instructions that READ input_flag_pending_2."""
    
    # Search for the symbol first
    input_flag_addr = idc.get_name_ea_simple("input_flag_pending_2")
    
    if input_flag_addr == idc.BADADDR:
        print("ERROR: Cannot find input_flag_pending_2 symbol")
        return []
    
    print(f"[*] input_flag_pending_2 at: 0x{input_flag_addr:X}")
    
    reads = []
    
    # Get all xrefs to input_flag_pending_2
    for xref in idautils.XrefsTo(input_flag_addr):
        addr = xref.frm
        insn = idc.GetDisasm(addr)
        mnem = idc.print_insn_mnem(addr)
        
        # Skip writes (mov to input_flag_pending_2)
        if "mov" in mnem.lower():
            # Check if destination is input_flag_pending_2
            op0_type = idc.get_operand_type(addr, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(addr, 0)
                if op0_addr == input_flag_addr:
                    continue  # This is a WRITE
        
        # This is a READ
        func = idaapi.get_func(addr)
        func_name = idc.get_func_name(addr) if func else "NO_FUNC"
        
        reads.append({
            'addr': addr,
            'func': func_name,
            'func_start': func.start_ea if func else 0,
            'insn': insn,
            'mnem': mnem
        })
        
        print(f"[READ] 0x{addr:X} in {func_name}: {insn}")
    
    return reads

def analyze_read_context(read_addr, scan_codes_of_interest):
    """Analyze what happens after a READ of input_flag_pending_2."""
    
    print(f"\n[*] Analyzing context at 0x{read_addr:X}")
    
    # Look at next 20 instructions
    current = read_addr
    for i in range(20):
        insn = idc.GetDisasm(current)
        mnem = idc.print_insn_mnem(current)
        
        print(f"  0x{current:X}: {insn}")
        
        # Look for comparisons with our scan codes
        if mnem in ['cmp', 'test', 'sub']:
            op1_type = idc.get_operand_type(current, 1)
            if op1_type == idc.o_imm:
                imm_val = idc.get_operand_value(current, 1)
                if imm_val in scan_codes_of_interest:
                    print(f"  ^^^ INTERESTING: Comparing with scan code 0x{imm_val:X}")
        
        # Look for jump tables
        if mnem in ['jmp', 'call']:
            op0_type = idc.get_operand_type(current, 0)
            if op0_type == idc.o_phrase or op0_type == idc.o_displ:
                print(f"  ^^^ INTERESTING: Indirect jump/call (possible switch table)")
        
        # Look for calls to view-related functions
        if mnem == 'call':
            target = idc.get_operand_value(current, 0)
            if target != idc.BADADDR:
                target_name = idc.get_name(target)
                if target_name and ('view' in target_name.lower() or 'external' in target_name.lower()):
                    print(f"  ^^^ INTERESTING: Calls view function: {target_name}")
        
        current = idc.next_head(current)
    
    return

def main():
    print("=" * 80)
    print("TRACING INPUT_FLAG_PENDING_2 DISPATCH")
    print("=" * 80)
    
    # Number key scan codes (view switching keys 0-9)
    scan_codes = list(range(0x02, 0x0C))  # 0x02-0x0B
    print(f"[*] Looking for dispatch of scan codes: {[hex(x) for x in scan_codes]}")
    
    # Find all reads
    reads = find_input_flag_reads()
    
    print(f"\n[*] Found {len(reads)} READ operations")
    
    # Analyze context around each read
    for read in reads:
        analyze_read_context(read['addr'], scan_codes)
    
    # Save results
    output = {
        'scan_codes_of_interest': [hex(x) for x in scan_codes],
        'reads': reads
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\input_dispatch_trace.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_file}")
    print("[*] Done!")

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
