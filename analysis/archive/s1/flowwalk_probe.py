"""Read-only (DBFL_KILL): decode forward from seeds WITHOUT changing the DB, following fall-through and
intra-segment jumps/branches (calls are not followed).  Reports per seed: reachable byte span, instruction count,
terminators, instructions whose bytes are not currently code in the DB (misdecode), collisions with existing
functions, and calls out.  Output: analysis/s1/flowwalk.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua, ida_segment, ida_idp
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\flowwalk.json"
SEEDS = [0x129F7, 0x106EE2, 0x108430, 0x10931E, 0x109445, 0x10CE30, 0x10B380, 0x10B720]
RETS = {"retn", "retf", "iret", "retnw", "retfw", "iretw"}
R = {"seeds": {}}


def walk(seed):
    seg = ida_segment.getseg(seed)
    todo, seen, insns = [seed], {}, {}
    term, calls, outside = [], [], []
    while todo:
        ea = todo.pop()
        while True:
            if ea in seen:
                break
            if ea < seg.start_ea or ea >= seg.end_ea:
                outside.append(ea)
                break
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, ea)
            if n <= 0:
                term.append([ea, "undecodable"])
                break
            seen[ea] = n
            m = idc.print_insn_mnem(ea) or ""
            insns[ea] = m
            if m in RETS or m == "hlt":
                term.append([ea, m])
                break
            if m.startswith("call"):
                t = insn.ops[0]
                if t.type in (ida_ua.o_near, ida_ua.o_far):
                    calls.append([ea, t.addr if t.type == ida_ua.o_near else None])
                ea += n
                continue
            if m.startswith("j") or m.startswith("loop"):
                t = insn.ops[0]
                if t.type == ida_ua.o_near:
                    todo.append((ida_segment.sel2para(seg.sel) << 4) + t.addr)
                if m == "jmp":
                    term.append([ea, "jmp"])
                    break
                ea += n
                continue
            ea += n
    return seen, insns, term, calls, outside


try:
    for sd in SEEDS:
        seen, insns, term, calls, outside = walk(sd)
        lo, hi = min(seen), max(a + n for a, n in seen.items())
        mis, own = [], set()
        for a, n in seen.items():
            if not ida_bytes.is_code(ida_bytes.get_flags(a)) or ida_bytes.get_item_head(a) != a:
                mis.append(a)
            g = ida_funcs.get_func(a)
            if g:
                own.add(g.start_ea)
        gaps, a = [], lo
        while a < hi:
            if a in seen:
                a += seen[a]
            else:
                gaps.append(a)
                a += 1
        R["seeds"]["%X" % sd] = {"lo": lo, "hi": hi, "n": len(seen), "term": term, "calls": len(calls),
                                 "outside": [hex(x) for x in outside[:6]],
                                 "misdecoded": [hex(x) for x in sorted(mis)[:40]], "n_mis": len(mis),
                                 "owned_by": [hex(x) for x in sorted(own)],
                                 "gap_bytes": len(gaps), "gaps": [hex(x) for x in gaps[:20]]}
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
