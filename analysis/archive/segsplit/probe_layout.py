"""Read-only: for R05_1E10 / R29_1E10s / R30 / R53 / others with anchors,
list functions vs anchor lines (straddles), code/data bytes per anchor block,
and DS/ES paragraph targets that fall inside each segment."""
import json
import traceback

import ida_segment
import ida_funcs
import ida_bytes
import idautils
import idaapi

ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
OUT = ROOT + r"\probe_layout.json"
anchors = json.load(open(ROOT + r"\anchors.json"))
res = {}


def main():
    for idx, o in anchors.items():
        if len(o["anchors"]) < 2 and o["len"] <= 0x10000:
            continue
        lo, hi = o["ida_ea"], o["ida_ea"] + o["len"]
        cuts = sorted(set([a["ea"] for a in o["anchors"]] + [lo]))
        funcs = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions(lo, hi)]
        strad = []
        for c in cuts:
            for fs, fe in funcs:
                if fs < c < fe:
                    strad.append([c, fs, fe])
        blocks = []
        for i, c in enumerate(cuts):
            e = cuts[i + 1] if i + 1 < len(cuts) else hi
            code = data = unk = 0
            ea = c
            while ea < e:
                f = ida_bytes.get_flags(ea)
                n = max(1, ida_bytes.get_item_size(ea)) if ida_bytes.is_head(f) else 1
                n = min(n, e - ea)
                if ida_bytes.is_code(f):
                    code += n
                elif ida_bytes.is_data(f):
                    data += n
                else:
                    unk += n
                ea += n
            nf = sum(1 for fs, fe in funcs if c <= fs < e)
            blocks.append({"ea": c, "end": e, "size": e - c, "code": code, "data": data,
                           "unk": unk, "nfuncs": nf})
        res[o["name"]] = {"straddles": strad, "blocks": blocks}


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
