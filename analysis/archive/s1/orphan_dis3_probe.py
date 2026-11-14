"""Read-only (DBFL_KILL): disassembly (owner function, item kind) of selected ranges.
Output: analysis/s1/orphan_dis3.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_dis3.txt"
RUNS = [(0x12C4F0,0x12C540),(0x12C655,0x12C690),(0x12C7B8,0x12C840),(0x12C940,0x12C9E4),(0x12CB1C,0x12CB34),(0x12CCDC,0x12CCF8),(0x12CE90,0x12CEA4)]
L = []
try:
    for lo, hi in RUNS:
        L.append("=== %X..%X" % (lo, hi))
        a = ida_bytes.get_item_head(lo)
        while a < hi:
            g = ida_funcs.get_func(a)
            fl = ida_bytes.get_flags(a)
            k = "C" if ida_bytes.is_code(fl) else ("A" if ida_bytes.is_align(fl) else "D")
            xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
            L.append("%X [%s]%s %s %s" % (a, ("%X" % g.start_ea) if g else "-", k, idc.generate_disasm_line(a, 0),
                                          ("<- " + ",".join(xs[:4])) if xs else ""))
            a += ida_bytes.get_item_size(a)
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
