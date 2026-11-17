"""
Find radar mode selection enum/switch logic.

Look for:
1. Functions with 3+ mode comparisons
2. Mode state variables
3. Text displayed on HUD based on mode
4. Keyboard bindings for mode cycling

Based on F-16 radar:
- Typical modes: All-Aspect (arcade), Boresight (arcade), RWS/TWS (realistic)
- Realistic mode likely has submodes
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\radar_mode_enum.json"

def find_mode_state_variables():
    """Find variables that store current mode (likely byte/word with values 0-4)."""
    
    candidates = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Look in data/bss segments
        if not any(x in seg_name.lower() for x in ["data", "bss"]):
            continue
        
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            name = idc.get_name(head)
            if name:
                name_lower = name.lower()
                
                # Look for mode-related variable names
                if any(kw in name_lower for kw in ["mode", "state", "radar", "track", "target", "aim"]):
                    # Count how many times it's written to (mode switches)
                    write_count = 0
                    read_count = 0
                    
                    for xref in idautils.XrefsTo(head, 0):
                        mnem = idc.print_insn_mnem(xref.frm)
                        if mnem in ["mov", "or", "and", "xor"]:
                            # Check if destination operand
                            op0_addr = idc.get_operand_value(xref.frm, 0)
                            if op0_addr == head:
                                write_count += 1
                        else:
                            read_count += 1
                    
                    if write_count >= 2 and read_count >= 3:  # Frequently read/written
                        candidates.append({
                            "name": name,
                            "address": hex(head),
                            "segment": seg_name,
                            "writes": write_count,
                            "reads": read_count,
                            "total_refs": write_count + read_count
                        })
    
    # Sort by total references
    candidates.sort(key=lambda x: x['total_refs'], reverse=True)
    
    return candidates[:20]

def analyze_comparison_patterns():
    """Find functions that compare a value to 0, 1, 2, 3 (likely mode selection)."""
    
    mode_functions = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        # Track comparisons to small integers (likely mode values)
        mode_compares = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == "cmp":
                # Check if comparing to small constant
                if idc.get_operand_type(ea, 1) == idc.o_imm:
                    value = idc.get_operand_value(ea, 1)
                    if value <= 5:  # Mode values typically 0-5
                        mode_compares.append({
                            "offset": hex(ea - func.start_ea),
                            "address": hex(ea),
                            "value": value,
                            "instruction": idc.GetDisasm(ea)
                        })
            
            ea = idc.next_head(ea, func.end_ea)
        
        # If function has 3+ mode comparisons, likely a mode handler
        if len(mode_compares) >= 3:
            func_name = idc.get_func_name(func_ea)
            
            # Check if mode values are sequential (0,1,2,3 or 1,2,3,4)
            values = sorted(set(c['value'] for c in mode_compares))
            sequential = all(values[i] + 1 == values[i+1] for i in range(len(values)-1))
            
            mode_functions.append({
                "function": func_name,
                "address": hex(func_ea),
                "mode_compares": mode_compares,
                "unique_values": values,
                "sequential": sequential,
                "count": len(mode_compares)
            })
    
    # Sort by compare count
    mode_functions.sort(key=lambda x: x['count'], reverse=True)
    
    return mode_functions[:15]

def find_hud_text_display_functions():
    """Find functions that display text on HUD (mode indicators)."""
    
    # Look for functions that:
    # 1. Take a string pointer as parameter
    # 2. Are called with different string addresses
    # 3. Are related to HUD/display
    
    text_displayers = []
    
    # Look for "text", "draw", "print", "display", "string" in function names
    keywords = ["text", "draw", "print", "display", "string", "label", "indicator"]
    
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    if not func:
                        continue
                    
                    # Count string references in callers
                    string_refs = []
                    for xref in idautils.XrefsTo(func_ea, 0):
                        # Look backwards for string pointer loads
                        caller_ea = xref.frm
                        func_caller = ida_funcs.get_func(caller_ea)
                        if func_caller:
                            # Check few instructions before call
                            check_ea = max(caller_ea - 20, func_caller.start_ea)
                            while check_ea < caller_ea:
                                # Look for mov with string address
                                if idc.print_insn_mnem(check_ea) in ["mov", "lea", "push"]:
                                    for i in range(2):
                                        if idc.get_operand_type(check_ea, i) == idc.o_imm:
                                            addr = idc.get_operand_value(check_ea, i)
                                            if idc.is_strlit(idc.get_full_flags(addr)):
                                                str_val = idc.get_strlit_contents(addr)
                                                if str_val:
                                                    string_refs.append({
                                                        "caller": idc.get_func_name(func_caller.start_ea),
                                                        "string": str_val.decode('ascii', errors='ignore')[:30]
                                                    })
                                check_ea = idc.next_head(check_ea, caller_ea)
                    
                    if string_refs:
                        text_displayers.append({
                            "function": name,
                            "address": hex(func_ea),
                            "size": func.end_ea - func.start_ea,
                            "string_refs": string_refs[:10],
                            "ref_count": len(string_refs)
                        })
                    
                    break
    
    return text_displayers[:20]

def extract_mode_switch_logic():
    """Extract key_mode_state_setup function (likely sets up mode display)."""
    
    func_name = "key_mode_state_setup"
    func_ea = idc.get_name_ea_simple(func_name)
    
    if func_ea == idc.BADADDR:
        return {"error": "key_mode_state_setup not found"}
    
    func = idaapi.get_func(func_ea)
    if not func:
        return {"error": "Not a function"}
    
    # Extract string references and mode values
    strings = []
    mode_values = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        # Look for string loads
        if mnem in ["mov", "lea"]:
            for i in range(2):
                if idc.get_operand_type(ea, i) == idc.o_imm:
                    addr = idc.get_operand_value(ea, i)
                    if idc.is_strlit(idc.get_full_flags(addr)):
                        str_val = idc.get_strlit_contents(addr)
                        if str_val:
                            strings.append({
                                "offset": hex(ea - func.start_ea),
                                "string": str_val.decode('ascii', errors='ignore'),
                                "address": hex(addr)
                            })
        
        # Look for mode comparisons
        if mnem == "cmp":
            if idc.get_operand_type(ea, 1) == idc.o_imm:
                value = idc.get_operand_value(ea, 1)
                if value <= 10:
                    mode_values.append({
                        "offset": hex(ea - func.start_ea),
                        "value": value,
                        "instruction": insn
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "function": func_name,
        "address": hex(func_ea),
        "size": func.end_ea - func.start_ea,
        "strings": strings,
        "mode_comparisons": mode_values
    }

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Finding mode state variables...")
        state_vars = find_mode_state_variables()
        print(f"Found {len(state_vars)} candidate variables")
        for var in state_vars[:5]:
            print(f"  {var['name']}: {var['writes']}W / {var['reads']}R")
        
        print("\n[2] Analyzing mode comparison patterns...")
        mode_funcs = analyze_comparison_patterns()
        print(f"Found {len(mode_funcs)} functions with mode comparisons")
        for func in mode_funcs[:5]:
            print(f"  {func['function']}: {func['count']} compares, values {func['unique_values']}")
        
        print("\n[3] Finding HUD text display functions...")
        text_funcs = find_hud_text_display_functions()
        print(f"Found {len(text_funcs)} text display functions")
        for func in text_funcs[:3]:
            print(f"  {func['function']}: {func['ref_count']} string refs")
        
        print("\n[4] Extracting key_mode_state_setup logic...")
        mode_setup = extract_mode_switch_logic()
        if "error" not in mode_setup:
            print(f"Function {mode_setup['function']}: {mode_setup['size']} bytes")
            print(f"  Strings: {len(mode_setup['strings'])}")
            print(f"  Mode compares: {len(mode_setup['mode_comparisons'])}")
        
        result = {
            "mode_state_variables": state_vars,
            "mode_comparison_functions": mode_funcs,
            "hud_text_display_functions": text_funcs,
            "mode_setup_function": mode_setup
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[5] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
