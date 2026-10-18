import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C973
trap_only = [0x2BDBB,0x2BDC5,0x2BDE3,0x2BDED,0x2BE01,0x2BE0B,0x2BE15,0x2BE1F,
             0x2BE29,0x2BE5B,0x2BE65,0x2BE6F,0x2BE79,0x2BE83,0x2BE8D,0x2BFC3,
             0x2C013,0x2C03B,0x2C063,0x2C199,0x2C1A3,0x2C24D,0x2C289,0x2C329]
log = []
working = 0x2BD9D
for ea in [working] + trap_only[:8]:
    fn = ida_funcs.get_func(ea)
    sz = (fn.end_ea - fn.start_ea) if fn else 0
    raw = idc.get_bytes(ea, sz) or b""
    insns = []
    cur = ea
    end = ea + sz
    while cur < end:
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, cur)
        if k <= 0:
            insns.append("0x%X: UNDECODABLE byte=0x%02X" % (cur, ida_bytes.get_byte(cur)))
            break
        mn = idc.print_insn_mnem(cur)
        ops = idc.print_operand(cur, 0)
        crefs = [hex(x) for x in idautils.CodeRefsFrom(cur, 0)]
        drefs = [hex(x) for x in idautils.DataRefsFrom(cur)]
        insns.append("0x%X: %s %s  k=%d crefs=%s drefs=%s" % (cur, mn, ops, k, crefs, drefs))
        cur += k
    log.append("thunk ea=0x%X size=%d raw=%s" % (ea, sz, raw.hex()))
    for i in insns:
        log.append("   " + i)
    log.append("")
with open(os.path.join(ROOT, "analysis/ida_falconcd/diag_thunk.log"), "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)