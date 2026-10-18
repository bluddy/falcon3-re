import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, ida_name, json, os, sys
log = []
s, e = 0x6CD90, 0x6CDA8

def build_body(s, e):
    created = 0
    cur = s
    while cur < e:
        h = ida_bytes.get_item_head(cur)
        if h == cur and ida_bytes.is_code(ida_bytes.get_flags(cur)):
            cur += max(ida_bytes.get_item_size(cur), 1); continue
        if h != cur:
            cur = h + max(ida_bytes.get_item_size(h), 1); continue
        if ida_bytes.is_data(ida_bytes.get_flags(cur)):
            cur += max(ida_bytes.get_item_size(cur), 1); continue
        ins = ida_ua.insn_t()
        k = ida_ua.decode_insn(ins, cur)
        if k <= 0:
            log.append("  decode fail @0x%X (skipping)" % cur)
            cur += 1; continue
        if cur + k > e:
            log.append("  insn @0x%X k=%d crosses end 0x%X" % (cur, k, e))
            cur += 1; continue
        n = ida_ua.create_insn(cur)
        if n and cur + n <= e:
            created += 1; cur += n
        else:
            log.append("  create_insn @0x%X -> %s" % (cur, n))
            cur += 1
    return created

created = build_body(s, e)
log.append("built %d insns" % created)
# check code coverage
code_bytes = sum(1 for a in range(s, e) if ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.is_head(ida_bytes.get_flags(a)))
log.append("code heads in span: %d (span=%d)" % (code_bytes, e-s))
# add_func
ok = ida_funcs.add_func(s, e)
log.append("add_func(0x%X, 0x%X) -> %s" % (s, e, ok))
if ok:
    f = ida_funcs.get_func(s)
    log.append("  span 0x%X..0x%X" % (f.start_ea, f.end_ea))
    ida_funcs.del_func(s)
else:
    # try set_func_end after add_func(s)
    ok1 = ida_funcs.add_func(s)
    log.append("add_func(0x%X) no-end -> %s" % (s, ok1))
    if ok1:
        ok2 = ida_funcs.set_func_end(s, e)
        log.append("set_func_end -> %s" % ok2)
        f = ida_funcs.get_func(s)
        log.append("  span 0x%X..%X" % (f.start_ea, f.end_ea))
        ida_funcs.del_func(s)
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_ovl.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)