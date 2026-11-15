import idaapi
import idautils
import idc
import json

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Analyzing view mode setter function...")

addr = 0x1086EC
current_name = idc.get_func_name(addr)

print(f"Function: {current_name} @ 0x{addr:X}")

func = idaapi.get_func(addr)
if not func:
    print("[!] No function found!")
    idc.qexit(0)

print(f"Size: {func.end_ea - func.start_ea} bytes")

# Extract all instructions
instructions = []
for head in idautils.Heads(func.start_ea, func.end_ea):
    if idc.is_code(idc.get_full_flags(head)):
        disasm = idc.generate_disasm_line(head, 0)
        instructions.append({
            'addr': f'0x{head:X}',
            'disasm': disasm
        })

print(f"Instructions: {len(instructions)}")

# Get callers
callers = []
for xref in idautils.XrefsTo(addr):
    if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
        caller_name = idc.get_func_name(xref.frm)
        caller_addr = xref.frm
        callers.append({
            'addr': f'0x{caller_addr:X}',
            'name': caller_name
        })

print(f"Callers: {len(callers)}")

# Get callees
callees = []
for head in idautils.Heads(func.start_ea, func.end_ea):
    for xref in idautils.CodeRefsFrom(head, 0):
        if xref != head + idc.get_item_size(head):
            callee_name = idc.get_func_name(xref)
            if callee_name and callee_name != current_name:
                callees.append({
                    'addr': f'0x{xref:X}',
                    'name': callee_name
                })

# Remove duplicates
callees = list({c['name']: c for c in callees}.values())

print(f"Callees: {len(callees)}")

# Print the function
print("\nComplete disassembly:")
for insn in instructions:
    print(f"  {insn['addr']}: {insn['disasm']}")

print("\nCallers:")
for c in callers[:10]:
    print(f"  {c['addr']}: {c['name']}")

print("\nCallees:")
for c in callees:
    print(f"  {c['addr']}: {c['name']}")

# Look for any string or data references
print("\nData references:")
for head in idautils.Heads(func.start_ea, func.end_ea):
    for xref in idautils.DataRefsFrom(head):
        name = idc.get_name(xref)
        if name:
            print(f"  0x{xref:X}: {name}")

# Save analysis
result = {
    'function': current_name,
    'address': f'0x{addr:X}',
    'size': func.end_ea - func.start_ea,
    'instructions': instructions,
    'callers': callers,
    'callees': callees
}

with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\view_mode_setter_analysis.json', 'w') as f:
    json.dump(result, f, indent=2)

print("\n[+] Analysis saved to view_mode_setter_analysis.json")

# Rename the function
new_name = "view_mode_set"
if idc.set_name(addr, new_name, idc.SN_CHECK):
    print(f"[+] Renamed {current_name} -> {new_name}")

# Add comments
idc.set_func_cmt(addr, "Set external view mode flag - Controls Path A (cockpit) vs Path B (external view)", 1)

# Find the mov instruction and add inline comment
for head in idautils.Heads(func.start_ea, func.end_ea):
    insn = idc.generate_disasm_line(head, 0)
    if 'r15_external_view_flag' in insn and 'mov' in insn:
        idc.set_cmt(head, "Set view mode: 0=cockpit (Path A), 1=external (Path B)", 0)
        print(f"[+] Added inline comment at 0x{head:X}")

print("\n[+] Complete!")

# Exit IDA
idc.qexit(0)
