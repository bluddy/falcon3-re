"""
Analyze the largest and most complex functions.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\mega_functions_analysis.json"

def analyze_func(name, addr_hex):
    addr = int(addr_hex, 16)
    func = idaapi.get_func(addr)
    
    if not func:
        return {"error": "no function"}
    
    # Get calls (limit to avoid timeout)
    calls = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 100:
        if idc.print_insn_mnem(ea) == "call":
            disasm = idc.GetDisasm(ea)
            target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
            calls.append(target_name)
            count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(addr, 0))
    callers = {}
    for xref in xrefs[:20]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    # Sample disassembly (first 20 instructions)
    disasm = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 20:
        disasm.append({
            "address": hex(ea),
            "disasm": idc.GetDisasm(ea)
        })
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    return {
        "address": hex(addr),
        "name": name,
        "size": func.end_ea - func.start_ea,
        "calls_sampled": calls[:50],  # First 50
        "total_calls_sampled": len(calls),
        "callers": callers,
        "xref_count": len(xrefs),
        "disasm_sample": disasm
    }

def main():
    try:
        idaapi.auto_wait()
        
        # Analyze top 5 largest and top 5 most complex
        targets = [
            ("r53_sbi_stream_dispatch", "0x1820b0"),  # Largest: 12,693 bytes, 342 calls
            ("sub_1744B0", "0x1744b0"),              # Most calls: 360 calls, 9,061 bytes
            ("sub_18B912", "0x18b912"),              # 2nd largest: 9,641 bytes
            ("r53_script_opcode_interpreter", "0x186a7c"),  # Script interpreter: 5,048 bytes
            ("ui_loadout_menu_enter", "0x683c1"),    # UI: 4,170 bytes, 142 calls
        ]
        
        result = {}
        for name, addr in targets:
            print(f"Analyzing {name}...")
            result[name] = analyze_func(name, addr)
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        print("Done!")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
