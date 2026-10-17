"""Report per-segment code coverage: decoded instruction heads that fall inside
a registered function vs not (read-only).

Used by findings 51/52 to size how much of each segment has a function
registered. NOTE: coverage numbers for R* overlay segments are meaningless
until finding 52's bitness bug (32-bit decode of 16-bit code) is fixed --
decode fails/garbles there, so low coverage is often an artifact.

Usage: cmd /c "tools/run_idat.bat tools/coverage_report.py"
Output: analysis/ida_falconcd/coverage_gap.log
"""
import ida_funcs, idautils, idc, ida_bytes, ida_segment, idaapi, json
log = []
cls = json.loads(open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json").read())
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1)) for v in cls.values())
import bisect
def covered(ea):
    i = bisect.bisect_right(ivs, (ea, 10**9)) - 1
    return i >= 0 and ivs[i][0] <= ea < ivs[i][1]

RES_LO, RES_HI = 0x10000, 0x2CF60
gaps = []
seg_rows = []
for i in range(ida_segment.get_segm_qty()):
    s = ida_segment.getnseg(i)
    if s.start_ea >= 0x100000:      # high overlay copies, skip for now
        continue
    # count instruction heads covered vs not
    tot = cov = 0
    hole = None
    for h in idautils.Heads(s.start_ea, s.end_ea):
        m = idc.print_insn_mnem(h)
        if not m:
            continue
        tot += 1
        if covered(h):
            cov += 1
            if hole and h - hole[0] >= 64:
                gaps.append((hole[0], h, h - hole[0], ida_segment.get_segm_name(s)))
                hole = None
        else:
            if hole is None:
                hole = (h, idc.print_insn_mnem(h))
    seg_rows.append((ida_segment.get_segm_name(s), s.start_ea, s.end_ea, tot, cov))
log.append("decoded-instruction heads by segment (res + overlay < 0x100000):")
log.append("  %-12s %9s %9s  %8s %8s  %s" % ("seg", "start", "end", "heads", "covered", "cov%"))
for n, a, b, tot, cov in seg_rows:
    if tot == 0: continue
    log.append("  %-12s 0x%07X 0x%07X  %8d %8d  %d%%" % (n, a, b, tot, cov, 100*cov//max(tot,1)))
log.append("")
log.append("UNCOVERED RUNS >= 64 decoded heads: %d" % len(gaps))
gaps.sort(key=lambda g: -g[2])
for a, b, d, sn in gaps[:16]:
    log.append("   %-10s 0x%X..0x%X  %d heads uncovered  (first mnem %r)" % (sn, a, b, d, idc.print_insn_mnem(a)))
open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\coverage_gap.log", "w").write("\n".join(log))
idaapi.qexit(0)