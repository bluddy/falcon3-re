import ida_funcs, ida_bytes, idc
from pathlib import Path
LOG = Path("analysis/s1/check_4da3d.log")
log = []
# Check 0x4DA3D specifically
for ea in [0x4D9FC, 0x4DA3C, 0x4DA3D, 0x4DA46]:
    f = ida_funcs.get_func(ea)
    fl = ida_bytes.get_flags(ea)
    log.append("0x%X: func=%s fl=0x%X is_code=%s head=%X" % (
        ea, (hex(f.start_ea) + ".." + hex(f.end_ea)) if f else "None",
        fl, ida_bytes.is_code(fl), ida_bytes.get_item_head(ea)))
# Also check if add_func would work
r = ida_funcs.add_func(0x4DA3D, 0x4DA46)
log.append("add_func(0x4DA3D, 0x4DA46): %s" % r)
LOG.write_text("\n".join(log))
import idaapi; idaapi.qexit(0)
