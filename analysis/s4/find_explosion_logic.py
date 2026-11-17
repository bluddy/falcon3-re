"""
Find when/how aircraft explode - search for destruction/explosion logic.

Questions to answer:
1. At what damage accumulator value does a plane explode?
2. Is there instant-kill logic (direct missile hit)?
3. How does damage differ between F-16 and other aircraft (MiGs, bombers)?
4. Are there different aircraft damage threshold tables?
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\explosion_logic.json"

def find_explosion_functions():
    """Find functions related to explosion/destruction."""
    keywords = ["explo", "destroy", "kill", "death", "debris", "wreck"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": kw
                    })
                    break
    
    return funcs

def analyze_damage_threshold_checks():
    """Find where damage accumulator [di+0xC9] is compared to thresholds."""
    
    threshold_checks = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.GetDisasm(ea)
            
            # Look for comparisons with [di+0xC9] or [si+0xC9]
            if ("+0C9h]" in disasm or "+0C9]" in disasm):
                mnem = idc.print_insn_mnem(ea)
                
                if mnem in ["cmp", "test"]:
                    # Get context - what happens after the comparison?
                    next_ea = idc.next_head(ea, func.end_ea)
                    next_insn = idc.GetDisasm(next_ea)
                    next_mnem = idc.print_insn_mnem(next_ea)
                    
                    # Look for threshold value
                    threshold = None
                    if idc.get_operand_type(ea, 1) == idc.o_imm:
                        threshold = idc.get_operand_value(ea, 1)
                    
                    # Get surrounding context
                    context = []
                    ctx_ea = max(ea - 10, func.start_ea)
                    ctx_end = min(ea + 10, func.end_ea)
                    
                    while ctx_ea < ctx_end:
                        context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                        ctx_ea = idc.next_head(ctx_ea, ctx_end)
                    
                    threshold_checks.append({
                        "function": idc.get_func_name(func_ea),
                        "address": hex(ea),
                        "instruction": disasm,
                        "threshold": threshold,
                        "next_instruction": next_insn,
                        "next_mnemonic": next_mnem,
                        "context": context
                    })
            
            ea = idc.next_head(ea, func.end_ea)
    
    return threshold_checks

def find_aircraft_type_data():
    """Find aircraft type data structures (damage thresholds per aircraft type)."""
    
    # From flight_physics.md, we know aircraft templates are at 0x22CF0
    # Look for byte at offset 0x56 (damage threshold)
    
    aircraft_data = []
    
    # Known aircraft template addresses from flight_physics.md
    known_templates = [
        ("F-16", 0x22CF0),
        ("Heavy Aircraft", 0x22D0A),
        ("Light Aircraft", 0x22D24),
    ]
    
    for name, addr in known_templates:
        # Read damage threshold at +0x56
        threshold_addr = addr + 0x56
        threshold = idc.get_wide_byte(threshold_addr)
        
        # Get surrounding data
        data_bytes = []
        for offset in range(0x50, 0x60):
            data_bytes.append(idc.get_wide_byte(addr + offset))
        
        aircraft_data.append({
            "aircraft_type": name,
            "template_address": hex(addr),
            "threshold_offset": "0x56",
            "damage_threshold": threshold,
            "surrounding_data": [hex(b) for b in data_bytes]
        })
    
    # Search for other templates nearby
    search_start = 0x22CF0
    search_end = 0x22D50
    
    ea = search_start
    template_candidates = []
    
    while ea < search_end:
        # Aircraft templates are ~26 bytes (0x1A) each
        # Look for patterns
        b0 = idc.get_wide_byte(ea)
        if b0 != 0 and b0 < 100:  # Reasonable threshold value
            template_candidates.append({
                "address": hex(ea),
                "threshold": b0
            })
        ea += 0x1A  # Template size
    
    aircraft_data.append({
        "note": "Template candidates found nearby",
        "candidates": template_candidates
    })
    
    return aircraft_data

def find_instant_kill_logic():
    """Find if there's instant-kill logic (e.g., direct missile hit)."""
    
    # Look for code that sets damage to 0xFF (maximum)
    # or directly sets critical/death flags
    
    instant_kills = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.GetDisasm(ea)
            
            # Look for mov [di+0xC9], 0xFF or similar max values
            if ("+0C9h]" in disasm or "+0C9]" in disasm):
                mnem = idc.print_insn_mnem(ea)
                
                if mnem == "mov":
                    # Check if setting to max value
                    if idc.get_operand_type(ea, 1) == idc.o_imm:
                        value = idc.get_operand_value(ea, 1)
                        if value >= 0xF0:  # Near maximum
                            instant_kills.append({
                                "function": idc.get_func_name(func_ea),
                                "address": hex(ea),
                                "instruction": disasm,
                                "value": hex(value)
                            })
            
            # Look for setting all damage bits at once
            if ("+0CAh]" in disasm or "+0CA]" in disasm):
                mnem = idc.print_insn_mnem(ea)
                
                if mnem == "or":
                    if idc.get_operand_type(ea, 1) == idc.o_imm:
                        value = idc.get_operand_value(ea, 1)
                        # 0x3FFF = all subsystems, 0xC000 = critical severity
                        if value in [0x3FFF, 0xC000, 0xC200, 0xFFFF]:
                            instant_kills.append({
                                "function": idc.get_func_name(func_ea),
                                "address": hex(ea),
                                "instruction": disasm,
                                "mask": hex(value),
                                "type": "bitfield_set"
                            })
            
            ea = idc.next_head(ea, func.end_ea)
    
    return instant_kills

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Finding explosion/destruction functions...")
        explosion_funcs = find_explosion_functions()
        print(f"Found {len(explosion_funcs)} functions")
        for func in explosion_funcs[:5]:
            print(f"  {func['name']} @ {func['address']}")
        
        print("\n[2] Analyzing damage threshold checks...")
        thresholds = analyze_damage_threshold_checks()
        print(f"Found {len(thresholds)} threshold checks on damage accumulator")
        for check in thresholds[:3]:
            print(f"  {check['function']}: {check['instruction']}")
            if check['threshold']:
                print(f"    Threshold: {check['threshold']} (0x{check['threshold']:02X})")
        
        print("\n[3] Analyzing aircraft type damage thresholds...")
        aircraft_types = find_aircraft_type_data()
        print(f"Found data for {len([a for a in aircraft_types if 'aircraft_type' in a])} aircraft types")
        for ac in aircraft_types:
            if 'aircraft_type' in ac:
                print(f"  {ac['aircraft_type']}: threshold = {ac['damage_threshold']} @ offset 0x56")
        
        print("\n[4] Finding instant-kill logic...")
        instant_kills = find_instant_kill_logic()
        print(f"Found {len(instant_kills)} potential instant-kill operations")
        for kill in instant_kills[:5]:
            print(f"  {kill['function']} @ {kill['address']}: {kill['instruction']}")
        
        result = {
            "explosion_functions": explosion_funcs,
            "damage_threshold_checks": thresholds,
            "aircraft_type_data": aircraft_types,
            "instant_kill_operations": instant_kills,
            "summary": {
                "explosion_funcs": len(explosion_funcs),
                "threshold_checks": len(thresholds),
                "instant_kills": len(instant_kills)
            }
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
