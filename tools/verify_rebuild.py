import ida_segment
import ida_bytes
import idaapi

lines = []
segs = []
for i in range(ida_segment.get_segm_qty()):
    s = ida_segment.getnseg(i)
    if s.start_ea >= 0x2CF60:
        n = 0
        f = idaapi.get_func(s.start_ea)
        while f is not None and f.start_ea < s.end_ea:
            n += 1
            f = idaapi.get_next_func(f)
        segs.append((s.get_name(), s.start_ea, s.end_ea, n))

total_f = sum(s[3] for s in segs)
lines.append("overlay segments: %d, functions: %d" % (len(segs), total_f))
for name, a, b, n in sorted(segs, key=lambda x: x[1]):
    head = ida_bytes.get_bytes(a, 8)
    lines.append("  %-12s %08X-%08X funcs=%d head=%s" % (
        name, a, b, n, head.hex() if head else 'NONE'))

b = ida_bytes.get_bytes(0x669F0, 6)
lines.append("idx30 head at 0x669F0: %s" % (b.hex() if b else 'NONE'))

open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\verify_rebuild.out", "w").write(
    "\n".join(lines))
idaapi.qexit(0)

