"""Read-only probe: for instructions following `mov ax,IMM; mov es|ds,ax`, which
memory operands use that sreg, and does IDA produce a data xref, to which EA?
Also: what does an implicit-DS operand resolve to (DS default is BADSEL)."""
import json
import collections
import traceback

import ida_segment
import ida_segregs
import ida_ua
import ida_idp
import ida_lines
import ida_xref
import idautils
import idaapi
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\probe_refs.json"
res = {"samples": [], "stats": {}}
DS = ida_idp.str2reg("ds")
ES = ida_idp.str2reg("es")
SS = ida_idp.str2reg("ss")
CS = ida_idp.str2reg("cs")


def drefs_from(ea):
    return [x.to for x in idautils.XrefsFrom(ea, ida_xref.XREF_DATA)]


def main():
    st = collections.Counter()
    nsamp = collections.Counter()
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        for ea in idautils.Heads(s.start_ea, s.end_ea):
            if not idc.is_code(idc.get_full_flags(ea)):
                continue
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, ea):
                continue
            for op in insn.ops:
                if op.type == ida_ua.o_void:
                    break
                if op.type not in (ida_ua.o_mem, ida_ua.o_displ):
                    continue
                if op.type == ida_ua.o_displ and op.addr == 0:
                    continue
                # effective segment register
                pfx = insn.segpref if hasattr(insn, "segpref") else 0
                sreg = op.specval >> 16 if (op.specval >> 16) else 0
                # IDA: specval high word = segment prefix reg+1? fall back on text
                txt = ida_lines.tag_remove(ida_ua.print_operand(ea, op.n) or "")
                if txt.startswith("es:"):
                    r = "es"
                elif txt.startswith("cs:"):
                    r = "cs"
                elif txt.startswith("ss:"):
                    r = "ss"
                elif txt.startswith("ds:"):
                    r = "ds+"
                else:
                    r = "ds"  # implicit (or bp-based -> ss, ignore below)
                if r == "ds" and op.type == ida_ua.o_displ and op.phrase in (2, 3, 6):  # bp-based
                    continue
                regno = {"es": ES, "cs": CS, "ss": SS}.get(r, DS)
                val = ida_segregs.get_sreg(ea, regno)
                known = val not in (idaapi.BADSEL, 0xFFFFFFFFFFFFFFFF, -1)
                d = drefs_from(ea)
                key = (r, "known" if known else "unknown", "dref" if d else "nodref", op.type)
                st[key] += 1
                if nsamp[key] < 6:
                    nsamp[key] += 1
                    res["samples"].append({
                        "ea": ea, "dis": ida_lines.tag_remove(idc.generate_disasm_line(ea, 0)),
                        "reg": r, "sreg": val if known else None, "addr": op.addr,
                        "drefs": d, "key": list(map(str, key)),
                    })
    res["stats"] = sorted([[list(map(str, k)), v] for k, v in st.items()], key=lambda x: -x[1])


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
