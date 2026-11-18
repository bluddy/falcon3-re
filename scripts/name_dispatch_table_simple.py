import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\dispatch_naming_simple.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Naming entity dispatch system...")
idaapi.auto_wait()

table_addr = 0x57034
code_base = 0x3B830

print(f"Table at: 0x{table_addr:X}")
print(f"Code base: 0x{code_base:X}\n")

# Read and verify table entries
print("Reading table entries:\n")
for i in range(20):
    entry_addr = table_addr + (i * 2)
    offset = idc.get_wide_word(entry_addr)
    abs_addr = code_base + offset if offset != 0 else 0
    func_name = idc.get_func_name(abs_addr) if abs_addr != 0 else "NULL"
    
    print(f"[{i:2d}] @ 0x{entry_addr:05X}: offset=0x{offset:04X} -> 0x{abs_addr:05X} ({func_name})")

print("\nNaming dispatch table...")
result = idc.set_name(table_addr, "entity_dispatch_table", idc.SN_FORCE)
print(f"Set name result: {result}")

# Add comment
comment = "Entity dispatch table indexed by object_category (+0x0C). Offsets from code base 0x{:05X}".format(code_base)
idc.set_cmt(table_addr, comment, 1)
print("Added table comment")

# Add comments to dispatch instructions
dispatch_site = 0x3C25D
idc.set_cmt(dispatch_site, "Load function offset from entity_dispatch_table[object_category*2]", 0)
print(f"Added comment @ 0x{dispatch_site:X}")

dispatch_call = 0x3C261
idc.set_cmt(dispatch_call, "Call category-specific update function (polymorphic dispatch)", 0)
print(f"Added comment @ 0x{dispatch_call:X}")

print("\nDone.")
output_file.close()
idc.qexit(0)
