import idaapi
import idautils
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Starting extraction of ranks 101-110...")

addresses = [
    (101, 0x11C884, "sub_11C884"),
    (102, 0x11C90F, "sub_11C90F"),
    (103, 0x13536F, "sub_13536F"),
    (104, 0x22EE8, "fixed_abs_div4"),
    (105, 0x249D8, "trig_table_lookup"),
    (106, 0x13BCE5, "sub_13BCE5"),
    (107, 0x23C9B, "angle_xy_far"),
    (108, 0x24CF7, "cs_word_store"),
    (109, 0x25E22, "dispatch_220f4_stub"),
    (110, 0x11C642, "sub_11C642"),
]

for rank, addr, name in addresses:
    print(f"\n[*] Rank #{rank}: {name} @ 0x{addr:X}")
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"  [!] No function found!")
        continue
    
    # Extract instructions
    insns = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            disasm = idc.generate_disasm_line(head, 0)
            insns.append(f"0x{head:X}: {disasm}")
    
    # Save to file
    output_path = rf'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_{addr:x}_disasm.txt'
    with open(output_path, 'w') as f:
        f.write(f"# {name} @ 0x{addr:X}\n# Rank #{rank}\n# Size: {func.end_ea - func.start_ea} bytes\n\n")
        f.write('\n'.join(insns))
    
    print(f"  [+] Extracted {len(insns)} instructions to func_{addr:x}_disasm.txt")

print("\n[+] Extraction complete!")

# Exit IDA
idc.qexit(0)
