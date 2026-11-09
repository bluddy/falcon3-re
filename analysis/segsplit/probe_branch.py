"""Read-only: for near CALL/JMP/Jcc in R05/R29 ranges, classify the IDA cref
target (fstart / head / mid-item / not-code) and count the crefs IDA made."""
import json, collections, os
import idaapi, idautils, ida_bytes, ida_funcs, ida_ua, ida_xref
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
OUT = ROOT + "\\" + os.environ.get("BOUT", "branch.json")
res = {}
for name, lo, hi in (("R05", 0x2E100, 0x669F0), ("R29", 0x11C3C0, 0x154CB0)):
    st = collections.Counter()
    for h in idautils.Heads(lo, hi):
        if not ida_bytes.is_code(ida_bytes.get_flags(h)):
            continue
        b = ida_bytes.get_byte(h); sz = ida_bytes.get_item_size(h)
        if b in (0xE8, 0xE9) and sz == 3: k = "call" if b == 0xE8 else "jmp"
        elif (b == 0xEB or 0x70 <= b <= 0x7F or 0xE0 <= b <= 0xE3) and sz == 2: k = "jcc"
        else: continue
        insn = ida_ua.insn_t(); ida_ua.decode_insn(insn, h)
        t = idaapi.to_ea(insn.cs, insn.ops[0].addr)
        f = ida_bytes.get_flags(t)
        if ida_bytes.is_code(f) and ida_bytes.is_head(f):
            fn = ida_funcs.get_func(t)
            c = "fstart" if fn and fn.start_ea == t else "head"
        elif ida_bytes.is_code(f):
            c = "mid-insn"
        else:
            c = "not-code"
        st[k + " " + c] += 1
        refs = [x for x in idautils.CodeRefsFrom(h, 0)]
        st[k + " cref-present"] += t in refs
    res[name] = dict(sorted(st.items()))
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
