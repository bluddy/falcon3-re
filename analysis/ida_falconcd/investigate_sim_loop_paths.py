import idaapi
import idautils
import idc
import ida_funcs
import ida_bytes
import json

def analyze_function_brief(ea):
    """Get brief info about a function"""
    func = ida_funcs.get_func(ea)
    if not func:
        return None
    
    name = idc.get_func_name(ea) or f"sub_{ea:X}"
    size = func.end_ea - func.start_ea
    
    # Count string references
    strings = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if ida_bytes.is_strlit(ida_bytes.get_flags(xref.to)):
                s = idc.get_strlit_contents(xref.to)
                if s:
                    strings.append(s.decode('ascii', errors='ignore'))
    
    # Count calls
    call_count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.print_insn_mnem(head) == 'call':
            call_count += 1
    
    # Count xrefs to this function
    xref_count = len(list(idautils.XrefsTo(ea, 0)))
    
    return {
        'address': hex(ea),
        'name': name,
        'size': size,
        'calls': call_count,
        'xrefs_to': xref_count,
        'strings': strings[:5]  # First 5 strings
    }

# Path A unique functions
path_a_unique = [
    0x396B,    # near_fnptr_invoke
    0x34FE,    # entity_state_load
    0x3805,    # terrain_frame_update_driver
    0x0,       # viewlist_project_flagged (null?)
    0x7F,      # loc_2F05F
    0x1BA6,    # es_ptr_slots_init
    0x1C5C,    # farobj_sort_and_step
]

# Path B unique functions
path_b_unique = [
    0xEFF,     # unknown
    0x111D,    # unknown
    0xD2D,     # unknown
    0x2010,    # unknown
    0xD70,     # unknown
    0x7A8,     # unknown
    0x2BC5,    # unknown
    0x2BCF,    # unknown
    0x7AF,     # unknown
    0x211E,    # unknown
    0x1EFD,    # unknown
    0x2260,    # unknown
    0xF7E,     # unknown
]

result = {
    'analysis': 'R15 Simulation Loop Path Comparison',
    'path_a_unique_count': len([x for x in path_a_unique if x != 0]),
    'path_b_unique_count': len(path_b_unique),
    'path_a_unique': [],
    'path_b_unique': []
}

print("=== ANALYZING PATH A UNIQUE FUNCTIONS ===")
for ea in path_a_unique:
    if ea == 0:
        result['path_a_unique'].append({
            'address': '0x0',
            'name': 'NULL or special case',
            'note': 'viewlist_project_flagged - may be far call'
        })
        print(f"  0x0: NULL/special case")
        continue
    
    info = analyze_function_brief(ea)
    if info:
        result['path_a_unique'].append(info)
        print(f"  {info['address']}: {info['name']} ({info['size']}B, {info['calls']} calls, {info['xrefs_to']} refs)")
        if info['strings']:
            print(f"    Strings: {info['strings'][:2]}")

print("\n=== ANALYZING PATH B UNIQUE FUNCTIONS ===")
for ea in path_b_unique:
    info = analyze_function_brief(ea)
    if info:
        result['path_b_unique'].append(info)
        print(f"  {info['address']}: {info['name']} ({info['size']}B, {info['calls']} calls, {info['xrefs_to']} refs)")
        if info['strings']:
            print(f"    Strings: {info['strings'][:2]}")

# Save analysis
output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\sim_loop_path_comparison.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n✓ Analysis saved to: {output_file}")
print(f"\nSUMMARY:")
print(f"  Path A unique functions: {result['path_a_unique_count']}")
print(f"  Path B unique functions: {result['path_b_unique_count']}")
print(f"  Common functions: 30")
print(f"\nPath B is MORE COMPLEX with {result['path_b_unique_count'] - result['path_a_unique_count']} additional calls")

idc.qexit(0)
