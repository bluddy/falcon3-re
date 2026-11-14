import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142d.txt", "w")
# context before the gap
a = ida_bytes.get_item_head(0x6E640)
while a < 0x6E69E:
    out.write("  %X %-14s %s\n" % (a, ida_bytes.get_bytes(a, ida_bytes.get_item_size(a)).hex(), idc.generate_disasm_line(a, 0)[:70])); a += ida_bytes.get_item_size(a)
f = ida_funcs.get_func(0x6E581)
it = ida_funcs.func_tail_iterator_t(f); ok = it.main(); ch = []
while ok:
    ch.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea)); ok = it.next()
out.write("r69 %X..%X chunks %s\n--- linear sweep from 6E69E (no DB change)\n" % (f.start_ea, f.end_ea, ch))
a = 0x6E69E
while a < 0x6E8F0:
    insn = ida_ua.insn_t()
    n = ida_ua.decode_insn(insn, a)
    if n <= 0:
        out.write("%X ??\n" % a); a += 1; continue
    # render via a throwaway: print mnemonic + raw bytes only
    out.write("%X %-16s %s\n" % (a, ida_bytes.get_bytes(a, n).hex(), insn.get_canon_mnem()))
    a += n
out.close(); idc.qexit(0)
