"""Extract function prologues/epilogues for compiler fingerprinting."""
import json
import ida_bytes
import ida_funcs
import idautils

prologues = {}
epilogues = {}

for ea in idautils.Functions():
    f = ida_funcs.get_func(ea)
    if not f:
        continue
    
    size = f.size()
    if size == 0:
        continue
    
    # Get first 16 bytes (prologue)
    prologue = ida_bytes.get_bytes(ea, min(16, size))
    # Get last 16 bytes (epilogue)
    epilogue = ida_bytes.get_bytes(ea + size - 16, 16) if size >= 16 else ida_bytes.get_bytes(ea, size)
    
    pro = prologue.hex() if prologue else ''
    epi = epilogue.hex() if epilogue else ''
    
    prologues[pro] = prologues.get(pro, 0) + 1
    epilogues[epi] = epilogues.get(epi, 0) + 1

# Save
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\prologues.json", "w") as f:
    json.dump(dict(sorted(prologues.items(), key=lambda x: -x[1])), f, indent=1)
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\epilogues.json", "w") as f:
    json.dump(dict(sorted(epilogues.items(), key=lambda x: -x[1])), f, indent=1)

print(f"Unique prologues: {len(prologues)}")
print(f"Unique epilogues: {len(epilogues)}")
print("Top 15 prologues:")
for k, v in sorted(prologues.items(), key=lambda x: -x[1])[:15]:
    print(f"  {v:4d}: {k}")
print("Top 15 epilogues:")
for k, v in sorted(epilogues.items(), key=lambda x: -x[1])[:15]:
    print(f"  {v:4d}: {k}")

import idaapi
idaapi.qexit(0)