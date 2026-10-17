"""Finding 59 step 1b (read-only IDA): test every carve seed against the
terminator-backwards rule.

For each seed address in analysis/ida_falconcd/carve_seeds.json records
  * prev[]  : instructions that DECODE TO END EXACTLY at the seed (the sweep
              walks back up to 8 bytes), each with mnemonic + whether it is a
              flow terminator (retn/retf/ret/iret/jmp);
  * first[] : the first 3 instructions decoded forward from the seed (the
              frameless-prologue evidence);
  * item[]  : IDA state (item head, code/data flag).

NO mutation: decode only, no create_insn, no del_items, no auto_wait, and it
always exits with idaapi.qexit(0) (finding 58's trap: a script that lets idat
finish auto-analysis rewrites the IDB).

Usage: cmd /c "tools\\run_idat.bat tools\\seed_tests.py"
"""
import json
import traceback

import ida_bytes
import ida_idp
import ida_ua
import idaapi
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
SEEDS = ROOT + r"\analysis\ida_falconcd\carve_seeds.json"
OUT = ROOT + r"\analysis\ida_falconcd\seed_tests.json"
LOG = ROOT + r"\analysis\ida_falconcd\seed_tests.log"

TERMS = {"retf", "retn", "ret", "iret", "jmp"}
MAX_BACK = 8

log = []
out = {}


def mnem_of(insn):
    return (insn.get_canon_mnem() or "").lower()


def main():
    seeds = json.load(open(SEEDS))["seeds"]
    log.append("seeds: %d" % len(seeds))
    for ea in seeds:
        r = {"prev": [], "first": [], "is_head": False,
             "is_code": False, "is_data": False}
        for back in range(1, MAX_BACK + 1):
            c = ea - back
            if c < 0:
                break
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, c)
            if n > 0 and c + n == ea:
                m = mnem_of(insn)
                r["prev"].append({
                    "back": back, "mnem": m,
                    "term": m in TERMS or bool(ida_idp.is_ret_insn(insn)),
                    "call": bool(ida_idp.is_call_insn(insn)),
                })
        cur = ea
        for _ in range(3):
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, cur)
            if n <= 0:
                r["first"].append({"mnem": "", "size": 0, "ea": cur})
                break
            r["first"].append({"mnem": mnem_of(insn), "size": n, "ea": cur})
            cur += n
        fl = ida_bytes.get_flags(ea)
        r["is_head"] = bool(ida_bytes.is_head(fl))
        r["is_code"] = bool(ida_bytes.is_code(fl))
        r["is_data"] = bool(ida_bytes.is_data(fl))
        out["0x%X" % ea] = r

    json.dump({"tests": out}, open(OUT, "w"))
    log.append("wrote %s (%d)" % (OUT, len(out)))


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
