import idaapi
import idautils
import idc
import json

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Searching for view mode switching code...")
print("[*] Looking for code that changes r15_external_view_flag dynamically...\n")

flag_addr = 0x107762

# Strategy 1: Find conditional writes to the flag
print("="*60)
print("STRATEGY 1: Find functions with conditional flag writes")
print("="*60)

# Get all functions
found_conditional = []

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    func = idaapi.get_func(func_ea)
    
    if not func:
        continue
    
    # Check if function references the flag
    refs_flag = False
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.DataRefsFrom(head):
            if xref == flag_addr:
                refs_flag = True
                break
        if refs_flag:
            break
    
    if refs_flag:
        # Check for conditional writes
        for head in idautils.Heads(func.start_ea, func.end_ea):
            insn = idc.generate_disasm_line(head, 0)
            if 'r15_external_view_flag' in insn and 'mov' in insn:
                # Check if there's a jump before this
                prev_head = idc.prev_head(head)
                prev_insn = idc.generate_disasm_line(prev_head, 0) if prev_head != idc.BADADDR else ""
                
                if 'j' in prev_insn.lower()[:3]:  # jz, jnz, jmp, etc.
                    found_conditional.append({
                        'func': func_name,
                        'addr': head,
                        'insn': insn,
                        'context': prev_insn
                    })
                    print(f"\nFound in {func_name} @ 0x{head:X}")
                    print(f"  Context: {prev_insn}")
                    print(f"  Write: {insn}")

# Strategy 2: Look for functions that read keyboard state and reference the flag
print("\n" + "="*60)
print("STRATEGY 2: Functions with keyboard input + flag reference")
print("="*60)

keyboard_funcs = [
    'kb_record_key_event',
    'kb_field_get_22',
    'key_code_pending_drain',
    'flag_bits_dispatch',
    'input_poll_handler',
]

for kf_name in keyboard_funcs:
    # Find this function
    for func_ea in idautils.Functions():
        if idc.get_func_name(func_ea) == kf_name:
            print(f"\nSearching callers of {kf_name}...")
            
            # Get callers
            for xref in idautils.XrefsTo(func_ea):
                if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                    caller_func = idc.get_func_name(xref.frm)
                    caller_func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
                    
                    # Check if caller references the flag
                    if caller_func_ea != idc.BADADDR:
                        func = idaapi.get_func(caller_func_ea)
                        if func:
                            refs_flag = False
                            for head in idautils.Heads(func.start_ea, func.end_ea):
                                for dref in idautils.DataRefsFrom(head):
                                    if dref == flag_addr:
                                        refs_flag = True
                                        break
                                if refs_flag:
                                    break
                            
                            if refs_flag:
                                print(f"  Found: {caller_func} calls {kf_name} AND references flag!")

# Strategy 3: Search for ACMI-related functions
print("\n" + "="*60)
print("STRATEGY 3: ACMI-related functions")
print("="*60)

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if 'acmi' in func_name.lower():
        print(f"\nACMI function: {func_name} @ 0x{func_ea:X}")
        
        # Check if it references the flag
        func = idaapi.get_func(func_ea)
        if func:
            for head in idautils.Heads(func.start_ea, func.end_ea):
                for xref in idautils.DataRefsFrom(head):
                    if xref == flag_addr:
                        insn = idc.generate_disasm_line(head, 0)
                        print(f"  References flag at 0x{head:X}: {insn}")

# Strategy 4: Look for view mode or camera-related function names
print("\n" + "="*60)
print("STRATEGY 4: View/Camera-related function names")
print("="*60)

view_keywords = ['view', 'camera', 'external', 'cockpit', 'chase']

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea).lower()
    
    if any(kw in func_name for kw in view_keywords):
        # Check if it references the flag
        func = idaapi.get_func(func_ea)
        if func:
            refs_flag = False
            for head in idautils.Heads(func.start_ea, func.end_ea):
                for xref in idautils.DataRefsFrom(head):
                    if xref == flag_addr:
                        refs_flag = True
                        insn = idc.generate_disasm_line(head, 0)
                        print(f"\n{idc.get_func_name(func_ea)} @ 0x{func_ea:X}")
                        print(f"  0x{head:X}: {insn}")
                        break
                if refs_flag:
                    break

print("\n" + "="*60)
print("[+] Search complete!")

# Save results summary
import json

results = {
    'conditional_writes': found_conditional,
    'strategies_completed': 4,
    'flag_address': f'0x{flag_addr:X}',
    'search_timestamp': idaapi.get_inf_attr(idaapi.INF_VERSION_TEXT) if hasattr(idaapi, 'get_inf_attr') else 'unknown'
}

output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\view_mode_switches.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"[+] Results saved to view_mode_switches.json")

# Exit IDA
idc.qexit(0)
