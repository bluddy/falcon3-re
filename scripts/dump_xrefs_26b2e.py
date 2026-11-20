import idc
import idaapi
import idautils

idaapi.auto_wait()

ea = 0x26B2E
xrefs = list(idautils.CodeRefsTo(ea, 0))
out_lines = [f"Xrefs to 0x{ea:X}:"]
for x in xrefs:
    out_lines.append(f"  Caller: 0x{x:X} in {idc.get_name(x)}")
    # dump 10 instructions before caller
    cur = idc.prev_head(x)
    for _ in range(5):
        cur = idc.prev_head(cur)
    for _ in range(10):
        dis = idc.generate_disasm_line(cur, 0)
        out_lines.append(f"    0x{cur:08X}: {dis}")
        cur = idc.next_head(cur)

with open(r'analysis/viewer/xrefs_to_26b2e.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
