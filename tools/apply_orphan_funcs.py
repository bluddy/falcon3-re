"""Register orphan code that is called but belongs to no function (finding 126, S1c-4).

Tier 1 only: a run of code heads that no function owns, entered by a call from code, that decodes from its
start to a terminator (ret/retf/iret or an unconditional jmp) without touching another function.  Runs that
end mid-flow (mov/add/popf ...) or look misdecoded are NOT registered; they are listed in finding 126.

Manifest registry/orphan_funcs_expected.json: {"add_funcs": [{"ea", "end", "last", "callers", "sha256"}]}
  OFMODE=plan   run on a COPY: registers every candidate in ADD (below) with an explicit end, checks each,
                records the result, never saves.
  (default)     replays the manifest: each [ea, end) must hold its recorded bytes and no function (or already be
                exactly the planned function); applies add_func(ea, end); post-check requires the old functions
                to be unchanged (start, end, name, chunks) and the new ones to be exactly the planned ones.
                A failure discards everything (DBFL_KILL).  Never runs auto_wait.
OFLOG overrides the log path, OFDRY=1 applies and checks without saving.

Usage: idat -A -S"tools\\apply_orphan_funcs.py" <idb>
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_ua
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "registry/orphan_funcs_expected.json"
LOG = Path(os.environ.get("OFLOG") or ROOT / "analysis/ida_falconcd/apply_orphan_funcs.log")
PLAN = os.environ.get("OFMODE") == "plan"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# (ea, end): chosen from analysis/s1/orphan_t1*.json; every end is the address after a terminator
ADD = [(0x1617C, 0x162DF), (0x162DF, 0x163AD), (0x16284E, 0x162878), (0x12C970, 0x12C9D0),
       (0x12CA0D, 0x12CAEF), (0x12CAEF, 0x12CB27)]
# jmp-reached menu bodies (R20/R21): (base, damaged `call far` head, end).  The key table is `mov bx, tab` with
# `mov cx, n` before the lookup loop; the handler table follows the keys, offsets relative to base.
MENUS = [(0x10B380, 0x10B4E8, 0x10B6DF), (0x10B720, 0x10B888, 0x10BA7B)]
log = []


def descend(seed, lo, hi, made):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made:
                    break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
                if ida_ua.create_insn(ea) <= 0:
                    raise RuntimeError("cannot decode 0x%X" % ea)
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += ida_bytes.get_item_size(ea)


def menu_seeds(base, cf):
    mov = cx = None
    a = base
    while a < base + 0x1C0 and mov is None:
        h = ida_bytes.get_item_head(a)
        if (idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "bx" and idc.get_operand_type(h, 1) == idc.o_imm
                and idc.get_operand_value(h, 1) > 0x300):
            mov = h
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(mov is not None, "table load in 0x%X" % base)
    h = mov
    while h > base and cx is None:
        h = idc.prev_head(h, base)
        if idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "cx" and idc.get_operand_type(h, 1) == idc.o_imm:
            cx = idc.get_operand_value(h, 1)
    must(cx, "loop count in 0x%X" % base)
    tab = idc.get_operand_value(mov, 1)
    hands = [ida_bytes.get_word(base + tab + 2 * cx + 2 * i) for i in range(cx)]
    return sorted({base + x for x in hands} | {cf + 5})


def decode_menu(item):
    lo, hi, cf = item["ea"], item["end"], item["redecode"]
    ida_bytes.del_items(cf, ida_bytes.DELIT_SIMPLE, 5)
    must(ida_ua.create_insn(cf) == 5, "re-decode call far at 0x%X" % cf)
    made = set()
    for sd in item["seeds"]:
        descend(sd, lo, hi, made)


def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)


def snapshot():
    return {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}


def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()


def must(ok, what):
    if not ok:
        raise RuntimeError(what + " failed")


def terminated(ea, end):
    last = idc.prev_head(end, ea)
    m = idc.print_insn_mnem(last)
    return m in RETS or (m == "jmp" and idc.get_operand_type(last, 0) in (idc.o_near, idc.o_far))


def callers(ea):
    return sorted(x.frm for x in idautils.XrefsTo(ea, 0)
                  if x.iscode and idc.print_insn_mnem(x.frm).startswith("call") and ida_funcs.get_func(x.frm))


def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"]:
        return "applied"
    if (not any(ida_funcs.get_func(a) for a in range(item["ea"], item["end"]))
            and sha(item["ea"], item["end"]) == item["sha256"]):
        return "fresh"
    return "mismatch"


def add_all(items):
    before = snapshot()
    for it in items:
        if state(it) == "applied":
            continue
        if "seeds" in it:
            decode_menu(it)
        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
        f = ida_funcs.get_func(it["ea"])
        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        must(chunks(it["ea"]) == [[it["ea"], it["end"]]], "chunks of 0x%X" % it["ea"])
        if "seeds" in it:
            a = it["ea"]
            while a < it["end"]:
                must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                a += ida_bytes.get_item_size(a)
    after = snapshot()
    new = {it["ea"] for it in items}
    changed = sorted(ea for ea in set(before) if before[ea] != after.get(ea))
    must(not changed, "existing functions changed %s" % [hex(c) for c in changed[:10]])
    must(set(after) - set(before) <= new, "unplanned new functions %s" % [hex(c) for c in sorted(set(after) - set(before) - new)][:10])
    log.append("functions added: %s; table %d -> %d, existing functions unchanged" % (
        ["0x%X..0x%X" % (it["ea"], it["end"]) for it in items], len(before), len(after)))


def main():
    if PLAN:
        items = []
        old = {x["ea"]: x for x in json.loads(MANIFEST.read_text())["add_funcs"]} if MANIFEST.exists() else {}
        for ea, end in ADD:
            if state({"ea": ea, "end": end, "sha256": ""}) == "applied" and ea in old:
                items.append(old[ea])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(ea, end)), "0x%X..0x%X already owned" % (ea, end))
            must(terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            items.append({"ea": ea, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, ea), 0),
                          "callers": callers(ea), "sha256": sha(ea, end)})
        for base, cf, end in MENUS:
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
            must(terminated(base, end), "0x%X..0x%X does not end in a terminator" % (base, end))
            items.append({"ea": base, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, base), 0),
                          "callers": sorted(x.frm for x in idautils.XrefsTo(base, 0) if x.iscode),
                          "redecode": cf, "seeds": menu_seeds(base, cf), "sha256": sha(base, end)})
        add_all(items)
        MANIFEST.write_text(json.dumps({"finding": 126, "step": "S1c-4 call-reached orphan code registered",
                                        "add_funcs": items}, indent=1).replace("\n", "\r\n"))
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("plan written: %s (not saved)" % MANIFEST.name)
        return
    doc = json.loads(MANIFEST.read_text())
    states = [state(it) for it in doc["add_funcs"]]
    log.append("manifest: %d functions; live: %d fresh, %d applied, %d mismatched" % (
        len(states), states.count("fresh"), states.count("applied"), states.count("mismatch")))
    if all(s == "applied" for s in states):
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if "mismatch" in states:
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    add_all(doc["add_funcs"])
    if os.environ.get("OFDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (OFDRY): not saved")
        return
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    main()
except Exception:
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)
    log.append("ERROR (not saved):\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.qexit(0)
