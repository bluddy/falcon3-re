import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
ea = 0x28CAB
log = []
log.append("0x%X flags=0x%X is_code=%s is_data=%s is_head=%s size=%d name=%s" % (
    ea, ida_bytes.get_flags(ea),
    ida_bytes.is_code(ida_bytes.get_flags(ea)),
    ida_bytes.is_data(ida_bytes.get_flags(ea)),
    ida_bytes.is_head(ida_bytes.get_flags(ea)),
    ida_bytes.get_item_size(ea), idc.get_name(ea)))
insn = ida_ua.insn_t()
k = ida_ua.decode_insn(insn, ea)
log.append("decode_insn -> %d, mnem=%s" % (k, idc.print_insn_mnem(ea)))
for pos in range(0x28CAB, 0x28D06):
    fl = ida_bytes.get_flags(pos)
    if ida_bytes.is_head(fl):
        log.append("  head at 0x%X size=%d is_code=%s is_data=%s name=%s" % (
            pos, ida_bytes.get_item_size(pos),
            ida_bytes.is_code(fl), ida_bytes.is_data(fl), idc.get_name(pos)))
fn = ida_funcs.get_func(ea)
log.append("get_func(0x%X)=%s" % (ea, fn))
prevfn = ida_funcs.get_func(ea - 1)
log.append("prev fn end: %s" % (hex(prevfn.end_ea) if prevfn else None))
# clear blocking head at entry, then try add_func
if ida_bytes.is_head(ida_bytes.get_flags(ea)) and not ida_bytes.is_code(ida_bytes.get_flags(ea)):
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, ida_bytes.get_item_size(ea))
    log.append("cleared non-code head at entry")
k2 = ida_ua.decode_insn(ida_ua.insn_t(), ea)
log.append("re-decode -> %d mnem=%s" % (k2, idc.print_insn_mnem(ea)))
if k2 > 0:
    ok = ida_funcs.add_func(ea)
    log.append("add_func -> %s" % ok)
    if ok:
        ida_funcs.del_func(ea)
        log.append("del_func (dry run)")
else:
    log.append("decode failed, cannot add_func")
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_28CAB.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)