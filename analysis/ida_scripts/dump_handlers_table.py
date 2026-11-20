import idaapi
import idc

idaapi.auto_wait()

table_ea = 0x26426
with open("analysis/ida_scripts/entity_type_handlers_table.txt", "w") as f:
    for i in range(28):
        ea = table_ea + i * 4
        off = idc.get_wide_word(ea)
        seg = idc.get_wide_word(ea + 2)
        linear = (seg << 4) + off
        name = idc.get_func_name(linear) or idc.get_name(linear, idaapi.GN_VISIBLE)
        f.write(f"Handler[{i:2d}] (offset 0x{i*4:02X}) -> 0x{seg:04X}:0x{off:04X} (linear 0x{linear:05X}) {name}\n")

idc.qexit(0)
