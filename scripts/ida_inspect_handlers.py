import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_handlers.txt"
with open(out_path, "w") as f:
    f.write("=== farobj_entity_type_handlers ===\n")
    # Find farobj_entity_type_handlers
    ea = 0x264ff
    # see what address cs:farobj_entity_type_handlers is
    insn = idaapi.insn_t()
    idaapi.decode_insn(insn, ea)
    f.write(f"Insn at 0x{ea:x}: {idc.generate_disasm_line(ea, 0)}\n")
    # op1 is memory ref
    table_ea = insn.Op1.addr
    f.write(f"Table addr: 0x{table_ea:x}\n")
    for i in range(16):
        ptr = idc.get_wide_word(table_ea + i * 2)
        name = idaapi.get_func_name(ptr)
        f.write(f"  Handler {i} (0x{i*2:02x}): 0x{ptr:04x} -> {name}\n")

idc.qexit(0)
