import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\m67c_probe.txt", "w")
words = [ida_bytes.get_word(0x69209 + i) for i in range(0, 30, 2)]
out.write("table words: %s\n" % [hex(w) for w in words])
for a in (0x674C0, 0x674CF):
    pass
a = 0x674C0
while a < 0x67500:
    out.write("%X %s\n" % (a, idc.generate_disasm_line(a, 0))); a += max(idc.get_item_size(a), 1)
out.write("\nxrefs 157cc8 context:\n")
a = idc.prev_head(0x157CC8, 0x157C80)
for _ in range(8):
    out.write("%X %s\n" % (a, idc.generate_disasm_line(a, 0))); a += max(idc.get_item_size(a), 1)
# who references 69227 / 6930B
for t in (0x69227, 0x6930B, 0x6940B):
    out.write("xrefs to %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.close()
idc.qexit(0)
