import idaapi
import idautils
import idc
import json

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Extracting ranks 151-200...")

# Load top 200
with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\top_200_functions.json') as f:
    top_200 = json.load(f)

# Get ranks 151-200
batch = top_200[150:200]

for rank, func_data in enumerate(batch, 151):
    addr = int(func_data['address'], 16)
    name = func_data['name']
    
    print(f"{rank}. {name} @ 0x{addr:X} ({func_data['size']}B, {func_data['calls']} calls)")
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"  [!] No function!")
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
        f.write(f"# {name} @ 0x{addr:X}\n")
        f.write(f"# Rank #{rank}\n")
        f.write(f"# Size: {func_data['size']} bytes, Calls: {func_data['calls']}\n\n")
        f.write('\n'.join(insns))
    
    print(f"  [+] {len(insns)} instructions")

print("\n[+] Extraction complete!")

# Exit IDA
idc.qexit(0)
