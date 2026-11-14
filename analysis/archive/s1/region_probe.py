"""Read-only (DBFL_KILL): every head in the regions holding orphan alias tails, with owning function
(entry ea), code/data class, disassembly, and code xrefs to/from each head.
Output: analysis/s1/region_probe.json  {region: [[ea, cls, size, owner, dis, [cref_from...], [cref_to...]]]}"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\region_probe.json"
REGIONS = [(0x11DA04, 0x11E1AB), (0x2E100, 0x2E2D0), (0x6E7A0, 0x6E8D0), (0x6CD60, 0x6CDB8)]
R = {}
try:
    for lo, hi in REGIONS:
        rows, ea = [], lo
        while ea < hi:
            fl = ida_bytes.get_flags(ea)
            h = ida_bytes.get_item_head(ea)
            sz = max(1, ida_bytes.get_item_size(h))
            f = ida_funcs.get_func(h)
            code = ida_bytes.is_code(fl)
            rows.append([h, "C" if code else "D" if ida_bytes.is_data(fl) else "U", sz,
                         f.start_ea if f else None, idc.generate_disasm_line(h, 0),
                         [[x.to, x.type] for x in idautils.XrefsFrom(h, 0) if x.iscode] if code else [],
                         [[x.frm, x.type] for x in idautils.XrefsTo(h, 0) if x.iscode]])
            ea = h + sz if h + sz > ea else ea + 1
        R["%X" % lo] = rows
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
