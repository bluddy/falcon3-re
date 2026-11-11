import os
os.environ["DBFL_KILL"] = "1"
import ida_auto, ida_bytes, ida_funcs, idautils, idc

ida_auto.auto_wait()
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\txt_probe.txt", "w")
LO, HI = 0x105D90, 0x106280
a, rows = LO, []
while a < HI:
    fl = ida_bytes.get_flags(a)
    kind = "code" if ida_bytes.is_code(fl) else "data" if ida_bytes.is_data(fl) else "unk"
    sz = max(ida_bytes.get_item_size(a), 1)
    f = ida_funcs.get_func(a)
    rows.append((a, kind, sz, f.start_ea if f else 0))
    a += sz
runs = []
for a, k, s, f in rows:
    if runs and runs[-1][2] == k and runs[-1][3] == f and runs[-1][1] + runs[-1][4] == a:
        runs[-1][4] += s
    else:
        runs.append([a, a, k, f, s])
for r in runs:
    out.write("%X..%X %s fn=%X\n" % (r[0], r[0] + r[4], r[2], r[3]))
out.write("\nbytes 105EB5..1062A0:\n")
bs = ida_bytes.get_bytes(0x105EB5, 0x1062A0 - 0x105EB5)
for i in range(0, len(bs), 32):
    chunk = bs[i:i + 32]
    out.write("%X  %s  %s\n" % (0x105EB5 + i, chunk.hex(" "), "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))
out.write("\nxrefs into 105EB5..106280 from outside:\n")
for t in range(0x105EB5, 0x106280):
    for r in idautils.XrefsTo(t, 0):
        if not (0x105EB5 <= r.frm < 0x106280):
            out.write("%X -> %X type %d\n" % (r.frm, t, r.type))
out.close()
idc.qexit(0)
