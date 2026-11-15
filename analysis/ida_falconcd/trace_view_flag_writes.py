import idaapi
import idautils
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Tracing writes to r15_external_view_flag (cs:0x107762)...")

# The flag we're looking for
flag_addr = 0x107762
flag_name = "r15_external_view_flag"

# Make sure it has the right name
current_name = idc.get_name(flag_addr)
if current_name != flag_name:
    print(f"  [*] Renaming 0x{flag_addr:X}: {current_name} -> {flag_name}")
    idc.set_name(flag_addr, flag_name, idc.SN_CHECK)

# Add comment
idc.set_cmt(flag_addr, "External view mode flag: 0=cockpit (Path A), 1=external (Path B)", 1)

print(f"\n[*] Finding all writes to {flag_name} @ 0x{flag_addr:X}...")

# Find all xrefs to this address
xrefs = list(idautils.XrefsTo(flag_addr))

print(f"[+] Found {len(xrefs)} total references")

write_refs = []

for xref in xrefs:
    # Get the instruction that references the flag
    insn = idc.generate_disasm_line(xref.frm, 0)
    
    # Check if it's a write (mov to this address)
    is_write = False
    if 'mov' in insn.lower() and flag_name in insn:
        # Parse the instruction to see if flag is destination
        if insn.split(',')[0].strip().endswith(flag_name):
            is_write = True
    
    # Get function containing this reference
    func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
    func_name = idc.get_func_name(xref.frm) if func_ea != idc.BADADDR else "???"
    
    result = {
        'addr': xref.frm,
        'func': func_name,
        'func_addr': func_ea,
        'insn': insn,
        'is_write': is_write,
        'type': 'WRITE' if is_write else 'READ'
    }
    
    if is_write:
        write_refs.append(result)
        print(f"\n[+] WRITE at 0x{xref.frm:X} in {func_name}")
        print(f"    {insn}")
        
        # Get context around the write
        print(f"    Context:")
        for i in range(-3, 4):
            addr = xref.frm + (i * idc.get_item_size(xref.frm + (i * 2)))
            if addr != xref.frm and idc.is_code(idc.get_full_flags(addr)):
                ctx_insn = idc.generate_disasm_line(addr, 0)
                marker = " >>>" if i == 0 else "    "
                print(f"    {marker} 0x{addr:X}: {ctx_insn}")

print(f"\n{'='*60}")
print(f"[+] Summary: {len(write_refs)} write locations found")

if write_refs:
    print("\nWrite locations by function:")
    func_groups = {}
    for ref in write_refs:
        func = ref['func']
        if func not in func_groups:
            func_groups[func] = []
        func_groups[func].append(ref)
    
    for func, refs in sorted(func_groups.items()):
        print(f"\n  {func} ({len(refs)} writes):")
        for ref in refs:
            print(f"    0x{ref['addr']:X}: {ref['insn']}")

# Also search for any string references to view modes
print(f"\n{'='*60}")
print("[*] Searching for view-related strings...")

for seg_ea in idautils.Segments():
    for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
        if idc.is_strlit(idc.get_full_flags(head)):
            str_val = idc.get_strlit_contents(head)
            if str_val:
                str_val = str_val.decode('ascii', errors='ignore').lower()
                if any(word in str_val for word in ['view', 'camera', 'external', 'cockpit', 'chase', 'acmi']):
                    print(f"  0x{head:X}: {str_val}")

print("\n[+] Trace complete!")

# Save results
import json
output = {
    'flag_address': f'0x{flag_addr:X}',
    'flag_name': flag_name,
    'total_refs': len(xrefs),
    'write_refs': write_refs
}

with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\view_flag_writes.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"[+] Results saved to view_flag_writes.json")

# Exit IDA
idc.qexit(0)
