import idc
import idaapi

idaapi.auto_wait()

ea = idc.get_name_ea_simple("farobj_entity_type_handlers")
out_lines = [f"Table farobj_entity_type_handlers at 0x{ea:X}:"]
for i in range(16):
    ptr = idc.get_wide_word(ea + i * 2)
    # Target address in 16-bit CS
    seg = ea & 0xF0000
    target_ea = seg | ptr
    tname = idc.get_name(target_ea)
    out_lines.append(f"  [{i:2d}] (offset 0x{i*2:02X}) -> 0x{target_ea:08X} ({tname})")

with open(r'analysis/viewer/farobj_handlers.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
