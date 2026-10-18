import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
ea = 0x28CAB
log = []
# What's the byte at ea-1? is it part of an instruction ending at ea?
log.append("byte @0x%X = 0x%02X" % (ea, ida_bytes.get_byte(ea)))
log.append("byte @0x%X = 0x%02X" % (ea - 1, ida_bytes.get_byte(ea - 1)))
fl = ida_bytes.get_flags(ea)
log.append("flags(0x%X)=0x%X head=%s code=%s" % (ea, fl, ida_bytes.is_head(fl), ida_bytes.is_code(fl)))
flm1 = ida_bytes.get_flags(ea - 1)
log.append("flags(0x%X)=0x%X head=%s code=%s" % (ea - 1, flm1, ida_bytes.is_head(flm1), ida_bytes.is_code(flm1)))
# find item head containing ea
h = ida_bytes.get_item_head(ea)
log.append("get_item_head(0x%X)=0x%X (item size=%d)" % (ea, h, ida_bytes.get_item_size(h)))
# decode at the real item head
insn = ida_ua.insn_t()
k = ida_ua.decode_insn(insn, h)
log.append("decode@head 0x%X -> k=%d mnem=%s" % (h, k, idc.print_insn_mnem(h)))
# Does ea fall inside an instruction?
if h < ea:
    log.append("ea 0x%X is INSIDE insn starting 0x%X (len %d)" % (ea, h, ida_bytes.get_item_size(h)))
# check segment
seg = idaapi.getseg(ea)
log.append("segment: %s start=0x%X end=0x%X perm=0x%X" % (
    idaapi.get_segm_name(seg), seg.start_ea, seg.end_ea, seg.perm) if seg else "no seg")
# try add_func with explicit end
ok = ida_funcs.add_func(ea, 0x28D06)
log.append("add_func(0x%X, 0x28D06) -> %s" % (ea, ok))
if ok:
    ida_funcs.del_func(ea)
    log.append("del_func (dry)")
# check the instruction at ea: is it a valid entry (can decode standalone)?
insn2 = ida_ua.insn_t()
k2 = ida_ua.decode_insn(insn2, ea)
log.append("decode@ea 0x%X -> k=%d mnem=%s" % (ea, k2, idc.print_insn_mnem(ea)))
# check if ea-1 is a code head (meaning ea is mid-instruction)
if ida_bytes.is_code(flm1):
    log.append("WARNING: ea-1 is code — ea may be mid-instruction")
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_28CAB.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)