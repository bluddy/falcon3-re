import idc
import idautils
import idaapi
import json

def find_type_0x19_handlers():
    """Find functions handling weapon type 0x19 (AGM-88 HARM)"""
    results = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        has_type_19 = False
        type_19_locations = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'cmp':
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:
                    val = idc.get_operand_value(ea, 1)
                    if val == 0x19:
                        has_type_19 = True
                        type_19_locations.append(hex(ea))
            
            ea = idc.next_head(ea)
        
        if has_type_19:
            results.append({
                'function': func_name,
                'address': hex(func_ea),
                'type_0x19_checks': type_19_locations
            })
    
    return results

def search_radar_emitter_patterns():
    """Search for potential radar emitter entity fields"""
    results = []
    
    # Look for functions with "radar" or "emitter" or "sam" in name
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        if not any(kw in name_lower for kw in ['radar', 'emitter', 'sam', 'harm', 'radiation']):
            continue
        
        # Find entity field accesses (patterns like [di+XX] or [si+XX])
        entity_field_accesses = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            disasm_lower = disasm.lower()
            
            # Look for entity field accesses
            if ('[di+' in disasm_lower or '[si+' in disasm_lower or 
                '[bx+' in disasm_lower or 'es:[di+' in disasm_lower):
                entity_field_accesses.append({
                    'address': hex(ea),
                    'disasm': disasm
                })
            
            ea = idc.next_head(ea)
        
        if entity_field_accesses:
            results.append({
                'function': func_name,
                'address': hex(func_ea),
                'entity_accesses': entity_field_accesses[:10]  # First 10
            })
    
    return results

def analyze_weapon_spawn_gate_type_19():
    """Analyze weapon_spawn_gate_validate for type 0x19 handling"""
    func_ea = 0x3DC55  # weapon_spawn_gate_validate
    
    result = {
        'function': 'weapon_spawn_gate_validate',
        'address': hex(func_ea),
        'type_0x19_sections': []
    }
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    ea = func.start_ea
    in_type_19_section = False
    current_section = []
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Check for type 0x19 comparison
        mnem = idc.print_insn_mnem(ea)
        if mnem == 'cmp':
            op_type = idc.get_operand_type(ea, 1)
            if op_type == idc.o_imm and idc.get_operand_value(ea, 1) == 0x19:
                in_type_19_section = True
                current_section = [{'address': hex(ea), 'disasm': disasm}]
        elif in_type_19_section:
            current_section.append({'address': hex(ea), 'disasm': disasm})
            
            # Stop at next label or after 20 instructions
            if len(current_section) > 20 or mnem in ['jmp', 'retn', 'retf']:
                result['type_0x19_sections'].append(current_section)
                in_type_19_section = False
                current_section = []
        
        ea = idc.next_head(ea)
    
    return result

print("Finding HARM lock system (type 0x19)...")

type_19_handlers = find_type_0x19_handlers()
radar_emitter_funcs = search_radar_emitter_patterns()
spawn_gate_analysis = analyze_weapon_spawn_gate_type_19()

results = {
    'type_0x19_handlers': type_19_handlers,
    'radar_emitter_functions': radar_emitter_funcs,
    'weapon_spawn_gate_analysis': spawn_gate_analysis
}

with open('temp/harm_lock_search.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nFunctions handling type 0x19: {len(type_19_handlers)}")
for handler in type_19_handlers[:10]:
    print(f"  {handler['function']} - {len(handler['type_0x19_checks'])} checks")

print(f"\nFunctions with radar/emitter keywords: {len(radar_emitter_funcs)}")
for func in radar_emitter_funcs[:10]:
    print(f"  {func['function']} - {len(func['entity_accesses'])} entity accesses")

print(f"\nweapon_spawn_gate_validate type 0x19 sections: {len(spawn_gate_analysis['type_0x19_sections'])}")

idc.qexit(0)
