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
REBASE (finding 130) moves the start of an existing named function up to the call-reached entry in front of it (the
old start was a mid-instruction byte left by a misdecode): del_func, clear, recursive descent, add_func, same name and
far flag, DS range extended.  Manifest key "rebase_funcs".
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
import ida_nalt
import ida_name
import ida_segment
import ida_segregs
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
       (0x12CA0D, 0x12CAEF), (0x12CAEF, 0x12CB27), (0x12C683, 0x12C7C6), (0x12C951, 0x12C970),
       (0x12CCE9, 0x12CE9D), (0x10931E, 0x1093A8), (0x109445, 0x109519), (0x129F7, 0x12B12), (0x12B12, 0x12B62),
       (0x100CA8, 0x100D00), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF), (0x12CB27, 0x12CB2A), (0x22C89, 0x22C91)]
# finding 139: no-xref runs that end in a terminator (far stubs, wrappers, an ISR); scan analysis/s1/orphan_scan138.json
ADD += [(0x1002C, 0x1005A), (0x10473, 0x1047C), (0x105DC, 0x105E1), (0x10C7E, 0x10C83), (0x11B90, 0x11B96), (0x11D16, 0x11D2B), (0x13A53, 0x13A57), (0x205BA, 0x205BF), (0x20613, 0x2061B), (0x20889, 0x20897), (0x21ABA, 0x21ABE), (0x22564, 0x2256D), (0x229BB, 0x229C0), (0x229C8, 0x229D1), (0x229D1, 0x229DD), (0x22AEB, 0x22AFF), (0x23E25, 0x23E37), (0x23E37, 0x23E57), (0x23F5E, 0x23F62), (0x2408B, 0x2408F), (0x24963, 0x24970), (0x24970, 0x2497C), (0x2551C, 0x25522), (0x25562, 0x25567), (0x25893, 0x25899), (0x25899, 0x2589F), (0x2B131, 0x2B135), (0x2CA17, 0x2CA3F), (0x2CB72, 0x2CB76), (0x2CB76, 0x2CB7B), (0x12D15E, 0x12D16E)]
# finding 141: a switch function entered through an overlay stub that pushes its offset; its second chunk lies after the stub
ADD += [(0x100457, 0x1004BE)]
# ea -> (clear_lo, clear_hi, seeds): orphan run with a misdecoded stretch that must be cleared and redecoded first
ADD_CLEAR = {0x10931E: (0x109388, 0x1093A6, [0x10931E, 0x109388]), 0x109445: (0x109445, 0x109519, [0x109445]),
             0x129F7: (0x129F7, 0x12B12, [0x129F7]), 0x12B12: (0x12B12, 0x12B62, [0x12B12]), 0x100CA8: (0x100CA8, 0x100D00, [0x100CA8]),
             0x22C89: (0x22C89, 0x22C91, [0x22C89]), 0x100457: (0x100457, 0x1004BE, [0x100457])}
# ea -> (tail chunk, clear ranges, seeds, pad bytes): a function whose second chunk lies after a foreign function that sits
# inside its span (finding 131); pad bytes are single data bytes inside a chunk that no flow reaches
TAILS = {0x100CA8: ([(0x100D0E, 0x100DFA)], [(0x100CA8, 0x100D00), (0x100D0D, 0x100DFA)], [0x100CA8, 0x100D0E, 0x100DF4], [0x100DEC]),
         0x100457: ([(0x1004CC, 0x10059E)], [(0x100457, 0x1004BE), (0x1004CC, 0x10059E)],
                    [0x100457, 0x1004CC, 0x1004D3, 0x1004E4, 0x100502], [0x100501])}
# (old_start, new_start, end, clear_lo, ds_para[, clear_hi]): existing function whose real entry is new_start (finding 130).
# [clear_lo, clear_hi) (default end) is cleared and redecoded from new_start; ds_para (or None) extends the DS range
# down to new_start.  A narrow clear_hi (finding 132, an instruction boundary) leaves the rest of a long body alone.
REBASE = [(0x106EEC, 0x106EE2, 0x106F3A, 0x106EE2, 0x706E), (0x10843D, 0x108430, 0x1084A6, 0x10843C, None),
          (0x10CFA6, 0x10CE30, 0x10CFEC, 0x10CFA5, None),
          (0x4335A, 0x4334E, 0x43395, 0x4334E, None),
          (0x6EF31, 0x6EF30, 0x6F1CE, 0x6EF30, None, 0x6EF39), (0x69723, 0x69720, 0x69AC6, 0x69720, None, 0x6972B),
          (0x16F4B5, 0x16F4B1, 0x16F507, 0x16F4B1, None)]
# (ea, fn_end, data_end): a "function" that is really the head of a word table (finding 134).  The function is deleted,
# [ea, data_end) is cleared and re-made as words; nothing may jump or call into it from outside.
REMOVE = [(0x6EC14, 0x6EC17, 0x6EC2C), (0x6EF1C, 0x6EF1F, 0x6EF30), (0x2E1C2, 0x2E1E8, 0x2E20A)]
# Table repair (finding 135): functions that are misread table words are deleted, the table and the text behind it are
# remade as data, and the two dispatch tables that caused the misread are rebuilt.  funcs: (ea, end) to delete;
# clear: [lo, hi) cleared to bytes; words: [lo, hi) remade as plain words; offwords: (lo, hi, base) words that are
# offsets from base; plain: (lo, hi) words that are not pointers.
TABLEFIX = [{"funcs": [(0x105D9D, 0x105DA7), (0x105DA7, 0x105DA9)], "clear": (0x105D90, 0x105EB5),
             "words": (0x105D90, 0x105DE6), "offwords": (0x1069B4, 0x1069BE, 0x105D90), "plain": (0x1069BE, 0x1069C8)}]
# Text fix (finding 136): the message text behind the 0x105D90 offset table becomes strings.  table: (lo, hi, base) offset
# words; text: (lo, hi) typed as C strings and single control bytes (1..0x1f, bare NUL); keep: bytes that are variables
# inside the text (0x10614A is the patched player digit of "PLAYER #2 HAS") and stay one-byte items.
TEXTFIX = [{"table": (0x105D90, 0x105DE6, 0x105D90), "text": (0x105DE6, 0x10626E), "keep": [0x10614A]}]
# (ea, old_end, new_end, clear_hi): a function whose tail is really data (finding 137).  The end moves up to new_end,
# [new_end, clear_hi) is cleared and the words in [new_end, words_hi) are made 2-byte data; whatever is left up to
# clear_hi is re-decoded by the ADD entry that follows (so an ADD_CLEAR item must cover [words_hi, clear_hi)).
TRIM = [(0x22C62, 0x22C8B, 0x22C71, 0x22C89, 0x22C91)]
# (owner, frag, clear_lo, clear_hi, new_end): finding 138.  frag is a bogus function made of fragments of owner's own body;
# it is deleted, [clear_lo, clear_hi) is redecoded from clear_lo, owner's tail chunks inside [main_end, new_end) are dropped
# and owner's main chunk is extended to new_end.
ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A)]
# (ea, end): existing functions whose body continues in orphan code (jcc/jmp into it) -> set_func_end
EXTEND = [(0x12C518, 0x12C66A), (0x12C7C6, 0x12C951)]
# (func, run_lo, run_hi): fl_F continuations (finding 129).  If run_lo is the main-chunk end the function is
# lengthened (set_func_end, which also swallows an adjacent tail chunk), else the run is appended as a tail chunk.
EXTEND_RUNS = [(0x10CC60, 0x10CC8E, 0x10CE05), (0x2D31A, 0x2D353, 0x2D375), (0x3F6A9, 0x3F6C7, 0x3F6D6),
               (0x2142E, 0x215FE, 0x21631), (0x2520B, 0x25220, 0x25224)]
DOS_EXIT = {0x2D353}  # run ends in `mov ax,4C00h / int 21h` (terminates the process)
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
    lo, hi = item["ea"], item["end"]
    if "clear" in item or "clears" in item:
        regs = regions(item)
        orig = set()
        for clo, chi in item.get("clears") or [item["clear"]]:
            a = clo
            while a < chi:
                h = ida_bytes.get_item_head(a)
                if ida_bytes.is_code(ida_bytes.get_flags(h)):
                    orig.add(h)
                a = h + max(ida_bytes.get_item_size(h), 1)
            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        for sd in item["seeds"]:
            rlo, rhi = next((x, y) for x, y in regs if x <= sd < y)
            descend(sd, rlo, rhi, set())
        for h in sorted(orig):
            if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
                bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(x <= r.frm < y for x, y in regs)]
                must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
        return
    else:
        cf = item["redecode"]
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


def regions(item):
    return [[item["ea"], item["end"]]] + [list(t) for t in item.get("tails", [])]


def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"] and (not item.get("tails") or chunks(item["ea"]) == sorted(regions(item))):
        return "applied"
    if (not any(ida_funcs.get_func(a) for lo, hi in regions(item) for a in range(lo, hi))
            and sha(item["ea"], item["end"]) == item["sha256"]
            and all(sha(lo, hi) == t for (lo, hi), t in zip(item.get("tails", []), item.get("tails_sha256", [])))):
        return "fresh"
    return "mismatch"


def uname(ea):
    return idaapi.get_name(ea) if ida_bytes.has_user_name(ida_bytes.get_flags(ea)) else None


def norm(x):
    """Fill the fields the finding-128 entries lack (they were a single contiguous run appended to a one-chunk function)."""
    x.setdefault("run", [x["before_end"], x["end"]])
    x.setdefault("run_sha256", x["sha256"])
    x.setdefault("chunks_before", [[x["ea"], x["before_end"]]])
    x.setdefault("chunks_after", [[x["ea"], x["end"]]])
    return x


def ext_state(x):
    """Entry: ea, run [lo, hi) of orphan code, run_sha256, chunks_before/after (sorted chunk lists), before_end/end
    (main-chunk end, which is what function_bytes.json sees) and sha256 of the bytes appended to the main chunk."""
    f = ida_funcs.get_func(x["ea"])
    if not f or f.start_ea != x["ea"]:
        return "mismatch"
    if chunks(x["ea"]) == x["chunks_after"] and f.end_ea == x["end"]:
        return "applied"
    lo, hi = x["run"]
    if (chunks(x["ea"]) == x["chunks_before"] and f.end_ea == x["before_end"]
            and not any(ida_funcs.get_func(a) for a in range(lo, hi)) and sha(lo, hi) == x["run_sha256"]):
        return "fresh"
    return "mismatch"


def extend(x):
    lo, hi = x["run"]
    f = ida_funcs.get_func(x["ea"])
    if f.end_ea == lo:
        must(ida_funcs.set_func_end(x["ea"], hi), "set_func_end 0x%X -> 0x%X" % (x["ea"], hi))
    else:
        must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (x["ea"], lo, hi))
    if x["chunks_after"] is None:
        f = ida_funcs.get_func(x["ea"])
        x["end"], x["chunks_after"] = f.end_ea, chunks(x["ea"])
        x["sha256"] = sha(x["before_end"], x["end"]) if x["end"] > x["before_end"] else ""
    must(ext_state(x) == "applied", "extend 0x%X (state %s, chunks %s)" % (x["ea"], ext_state(x), chunks(x["ea"])))


def is_far(ea):
    return bool(ida_funcs.get_func(ea).flags & ida_funcs.FUNC_FAR)


def rb_state(x):
    old, new, end = x["old_ea"], x["ea"], x["end"]
    f = ida_funcs.get_func(new)
    if f and f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]] and uname(new) == x["name"]:
        return "applied"
    f = ida_funcs.get_func(old)
    if (f and f.start_ea == old and f.end_ea == end and chunks(old) == [[old, end]] and uname(old) == x["name"]
            and sha(new, end) == x["sha256"] and not any(ida_funcs.get_func(a) for a in range(new, old))):
        return "fresh"
    return "mismatch"


def rebase(x):
    old, new, end, clo = x["old_ea"], x["ea"], x["end"], x["clear_lo"]
    chi = x.get("clear_hi") or end
    far = is_far(old)
    must(far == x["far"], "far flag of 0x%X" % old)
    a, orig = clo, set()
    while a < chi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(old), "del_func 0x%X" % old)
    ida_name.set_name(old, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    if x.get("ds") is not None:
        s = ida_segment.setup_selector(x["ds"])
        must(ida_segment.sel2para(s) == x["ds"], "selector for para 0x%X" % x["ds"])
        must(ida_segregs.split_sreg_range(new, idaapi.str2reg("ds"), s, ida_segregs.SR_user), "DS split at 0x%X" % new)
    made = set()
    descend(new, new, chi, made)
    a = new
    while a < chi:
        must(ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a, "non-code head 0x%X in rebased 0x%X" % (a, new))
        a += ida_bytes.get_item_size(a)
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (new <= r.frm < end)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.add_func(new, end), "add_func 0x%X..0x%X" % (new, end))
    f = ida_funcs.get_func(new)
    must(f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]], "span of rebased 0x%X" % new)
    if far:
        f.flags |= ida_funcs.FUNC_FAR
        must(ida_funcs.update_func(f), "update_func 0x%X" % new)
    if x["name"]:
        must(ida_name.set_name(new, x["name"], ida_name.SN_NOWARN), "name of 0x%X" % new)
    must(is_far(new) == far, "far flag of rebased 0x%X" % new)
    if x.get("lost_heads") is None:
        x["lost_heads"] = lost
    must(x["lost_heads"] == lost, "stale code heads of 0x%X differ from the manifest: %s" % (new, [hex(h) for h in lost]))
    must(rb_state(x) == "applied", "rebase 0x%X" % new)


def rm_state(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if sha(ea, end) != x["data_sha256"]:
        return "mismatch"
    if not any(ida_funcs.get_func(a) for a in range(ea, end)):
        a = ea
        while a < end:
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
            a += 2
        return "applied"
    if (f and f.start_ea == ea and f.end_ea == fe and chunks(ea) == [[ea, fe]] and uname(ea) == x["name"]
            and not any(ida_funcs.get_func(a) for a in range(fe, end))):
        return "fresh"
    return "mismatch"


def remove(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    must((end - ea) % 2 == 0, "word table length 0x%X" % ea)
    a, orig = ea, set()
    while a < end:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ea <= r.frm < end)]
        must(not bad, "jump/call into table head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.del_func(ea), "del_func 0x%X" % ea)
    ida_name.set_name(ea, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, end - ea)
    for a in range(ea, end, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(rm_state(x) == "applied", "removal of 0x%X" % ea)


def tf_outside(x):
    lo, hi = x["clear"]
    return sorted((r.frm, t) for t in range(lo, hi) for r in idautils.XrefsTo(t, 0)
                  if r.type in (1, 16, 17, 18, 19) and not (lo <= r.frm < hi))


def tf_state(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    if (sha(lo, hi) != x["clear_sha256"] or sha(olo, ohi) != x["offwords_sha256"]
            or sha(plo, phi) != x["plain_sha256"]):
        return "mismatch"
    if all(ida_funcs.get_func(f["ea"]) and ida_funcs.get_func(f["ea"]).start_ea == f["ea"]
           and ida_funcs.get_func(f["ea"]).end_ea == f["fn_end"] and uname(f["ea"]) == f["name"] for f in x["funcs"]):
        return "fresh"
    if any(ida_funcs.get_func(a) for a in range(lo, hi)):
        return "mismatch"
    wlo, whi = x["words"]
    for a in list(range(wlo, whi, 2)) + list(range(olo, phi, 2)):
        fl = ida_bytes.get_flags(a)
        if not (ida_bytes.is_data(fl) and ida_bytes.get_item_size(a) == 2):
            return "mismatch"
    if any(ida_bytes.is_code(ida_bytes.get_flags(a)) for a in range(lo, hi)) or tf_outside(x):
        return "mismatch"
    return "applied"


def tablefix(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    for f in x["funcs"]:
        must(ida_funcs.del_func(f["ea"]), "del_func 0x%X" % f["ea"])
        ida_name.set_name(f["ea"], "", ida_name.SN_NOWARN)
    ida_bytes.del_items(olo, ida_bytes.DELIT_SIMPLE, phi - olo)
    for a in range(olo, ohi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a in range(plo, phi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    wlo, whi = x["words"]
    for a in range(wlo, whi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    for a in range(whi, hi):
        must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
    for frm, t in tf_outside(x):
        ida_xref.del_cref(frm, t, 0)
    left = tf_outside(x)
    must(not left, "references into the table remain %s" % [(hex(a), hex(b), ) for a, b in left][:6])
    must(tf_state(x) == "applied", "table fix 0x%X" % lo)


def text_segments(x):
    lo, hi = x["text"]
    keep = set(x["keep"])
    bs = ida_bytes.get_bytes(lo, hi - lo)
    out, a = [], lo
    while a < hi:
        b = bs[a - lo]
        if a in keep or b < 0x20:
            out.append((a, 1, "b"))
            a += 1
            continue
        e = a
        while e < hi and bs[e - lo] >= 0x20 and e not in keep:
            e += 1
        if e < hi and bs[e - lo] == 0 and e not in keep:
            e += 1
        out.append((a, e - a, "s"))
        a = e
    return out


def xt_state(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    if sha(lo, hi) != x["text_sha256"] or sha(tlo, thi) != x["table_sha256"]:
        return "mismatch"
    if any(ida_funcs.get_func(a) for a in range(tlo, hi)):
        return "mismatch"
    ok = all(ida_bytes.is_off0(ida_bytes.get_flags(a)) for a in range(tlo, thi, 2))
    for a, n, k in text_segments(x):
        fl = ida_bytes.get_flags(a)
        ok = ok and ida_bytes.get_item_size(a) == n and ida_bytes.is_head(fl) and (
            ida_bytes.is_strlit(fl) if k == "s" else ida_bytes.is_byte(fl))
    return "applied" if ok else "fresh"


def textfix(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    for a in range(tlo, thi, 2):
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a, n, k in text_segments(x):
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, n)
        if k == "b":
            must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
        else:
            must(ida_bytes.create_strlit(a, n, ida_nalt.STRTYPE_C), "create_strlit 0x%X" % a)
    must(xt_state(x) == "applied", "text fix 0x%X" % lo)


def trim_state(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or uname(ea) != x["name"] or sha(ea, ch) != x["sha256"]:
        return "mismatch"
    if f.end_ea == oe and chunks(ea) == [[ea, oe]]:
        return "fresh"
    if f.end_ea == ne and chunks(ea) == [[ea, ne]]:
        for a in range(ne, wh, 2):
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
        return "applied"
    return "mismatch"


def trim(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    must((wh - ne) % 2 == 0, "word run of 0x%X" % ea)
    a, orig = ne, set()
    while a < ch:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ne <= r.frm < ch) and h != wh]
        must(not bad, "jump/call into trimmed head 0x%X from %s" % (h, [hex(b) for b in bad][:5]))
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X" % ea)
    ida_bytes.del_items(ne, ida_bytes.DELIT_SIMPLE, ch - ne)
    for a in range(ne, wh, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(trim_state(x) == "applied", "trim of 0x%X" % ea)


def ab_state(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or sha(be, ne) != x["sha256"]:
        return "mismatch"
    g = ida_funcs.get_func(fr)
    if f.end_ea == ne and chunks(ea) == x["chunks_after"] and not (g and g.start_ea == fr):
        return "applied"
    if (f.end_ea == be and chunks(ea) == x["chunks_before"] and g and g.start_ea == fr and uname(fr) == x["frag_name"]
            and chunks(fr) == x["frag_chunks"] and sha(fr, x["frag_end"]) == x["frag_sha256"]):
        return "fresh"
    return "mismatch"


def absorb(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    clo, chi = x["clear"]
    far = is_far(ea)
    must(not is_far(fr) or far, "far flag of 0x%X" % fr)
    a, orig = clo, set()
    while a < chi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(fr), "del_func 0x%X" % fr)
    ida_name.set_name(fr, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    a = clo
    while a < chi:
        n = ida_ua.create_insn(a)
        must(n > 0, "create_insn 0x%X" % a)
        a += n
    must(a == chi, "redecode of 0x%X..0x%X ends at 0x%X" % (clo, chi, a))
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (clo <= r.frm < chi)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    f = ida_funcs.get_func(ea)
    for lo, hi in chunks(ea)[1:]:
        if be <= lo < ne:
            must(ida_funcs.remove_func_tail(ida_funcs.get_func(ea), lo), "remove_func_tail 0x%X" % lo)
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X -> 0x%X" % (ea, ne))
    must(is_far(ea) == far, "far flag of 0x%X" % ea)
    if x["chunks_after"] is None:
        x["chunks_after"] = chunks(ea)
    must(ab_state(x) == "applied", "absorb into 0x%X (state %s, chunks %s)" % (ea, ab_state(x), chunks(ea)))


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=(), abs_=()):
    before = snapshot()
    for x in abs_:
        if ab_state(x) != "applied":
            absorb(x)
    for x in trs:
        if trim_state(x) != "applied":
            trim(x)
    for x in xts:
        if xt_state(x) != "applied":
            textfix(x)
    for x in tfs:
        if tf_state(x) != "applied":
            tablefix(x)
    for x in rms:
        if rm_state(x) != "applied":
            remove(x)
    for x in exts:
        if ext_state(x) == "applied":
            continue
        extend(x)
    for x in rebs:
        if rb_state(x) != "applied":
            rebase(x)
    for it in items:
        if state(it) == "applied":
            continue
        if "seeds" in it:
            decode_menu(it)
        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
        f = ida_funcs.get_func(it["ea"])
        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        for lo, hi in it.get("tails", []):
            must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (it["ea"], lo, hi))
            f = ida_funcs.get_func(it["ea"])
        must(chunks(it["ea"]) == sorted(regions(it)), "chunks of 0x%X" % it["ea"])
        if "clear" in it or "clears" in it:
            for lo, hi in regions(it):
                must(terminated(lo, hi), "0x%X..0x%X does not end in a terminator" % (lo, hi))
            it["last"] = idc.generate_disasm_line(idc.prev_head(it["end"], it["ea"]), 0)
        if "seeds" in it:
            for lo, hi in regions(it):
                a = lo
                while a < hi:
                    if a in it.get("pad", []):
                        a += 1
                        continue
                    must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                    a += ida_bytes.get_item_size(a)
    after = snapshot()
    new = {it["ea"] for it in items} | {x["ea"] for x in rebs}
    changed = sorted(ea for ea in set(before) if before[ea] != after.get(ea))
    must(set(changed) <= {x["ea"] for x in exts} | {x["old_ea"] for x in rebs} | {x["ea"] for x in rms} | {f["ea"] for x in tfs for f in x["funcs"]} | {x["ea"] for x in trs} | {x["ea"] for x in abs_} | {x["frag"] for x in abs_},
         "unplanned existing functions changed %s" % [hex(c) for c in changed[:10]])
    for x in exts:
        must(after[x["ea"]][0] == before[x["ea"]][0], "name of 0x%X changed" % x["ea"])
    for x in rebs:
        must(x["old_ea"] not in after and (x["name"] is None or after[x["ea"]][0] == x["name"]), "rebase of 0x%X" % x["old_ea"])
    must(not any(x["frag"] in after for x in abs_), "absorbed function still present")
    must(not any(x["ea"] in after for x in rms) and not any(f["ea"] in after for x in tfs for f in x["funcs"]),
         "removed function still present")
    must(set(after) - set(before) <= new, "unplanned new functions %s" % [hex(c) for c in sorted(set(after) - set(before) - new)][:10])
    log.append("functions added: %s; extended: %s; rebased: %s; table %d -> %d, other existing functions unchanged" % (
        ["0x%X..0x%X" % (it["ea"], it["end"]) for it in items],
        ["0x%X -> 0x%X" % (x["ea"], x["end"]) for x in exts],
        ["0x%X -> 0x%X %s" % (x["old_ea"], x["ea"], x["name"]) for x in rebs], len(before), len(after)))
    if abs_:
        log.append("absorbed: %s" % ["0x%X into 0x%X (end 0x%X)" % (x["frag"], x["ea"], x["end"]) for x in abs_])
    if trs:
        log.append("trimmed: %s" % ["0x%X end 0x%X -> 0x%X" % (x["ea"], x["old_end"], x["end"]) for x in trs])
    if xts:
        log.append("text fix: %s" % ["0x%X..0x%X (%d items)" % (x["text"][0], x["text"][1], len(text_segments(x))) for x in xts])
    if tfs:
        log.append("table fix: %s" % ["0x%X..0x%X (%d functions deleted)" % (x["clear"][0], x["clear"][1], len(x["funcs"])) for x in tfs])
    if rms:
        log.append("removed (word tables): %s" % ["0x%X..0x%X %s" % (x["ea"], x["end"], x["name"]) for x in rms])


def main():
    if PLAN:
        items = []
        old = {x["ea"]: x for x in json.loads(MANIFEST.read_text())["add_funcs"]} if MANIFEST.exists() else {}
        for ea, end in ADD:
            if state({"ea": ea, "end": end, "sha256": ""}) == "applied" and ea in old:
                items.append(old[ea])
                continue
            tails = TAILS[ea][0] if ea in TAILS else []
            freed = {a for (tea, toe, tne, twh, tch) in TRIM for a in range(tne, toe)}
            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi) if a not in freed), "0x%X..0x%X already owned" % (ea, end))
            must(ea in ADD_CLEAR or terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            it = {"ea": ea, "end": end, "last": None, "callers": callers(ea), "sha256": sha(ea, end)}
            if ea in ADD_CLEAR:
                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
            if ea in TAILS:
                it["tails"], it["tails_sha256"] = [list(t) for t in tails], [sha(lo, hi) for lo, hi in tails]
                it["clears"], it["seeds"], it["pad"] = [list(c) for c in TAILS[ea][1]], TAILS[ea][2], TAILS[ea][3]
                del it["clear"]
            items.append(it)
        for base, cf, end in MENUS:
            if state({"ea": base, "end": end, "sha256": ""}) == "applied" and base in old:
                items.append(old[base])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
            must(terminated(base, end), "0x%X..0x%X does not end in a terminator" % (base, end))
            items.append({"ea": base, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, base), 0),
                          "callers": sorted(x.frm for x in idautils.XrefsTo(base, 0) if x.iscode),
                          "redecode": cf, "seeds": menu_seeds(base, cf), "sha256": sha(base, end)})
        oldx = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("extend_funcs", [])} if MANIFEST.exists() else {}
        exts = []
        for ea, end in EXTEND:
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            if f.end_ea == end and ea in oldx:
                exts.append(norm(oldx[ea]))
                continue
            must(terminated(f.end_ea, end), "0x%X..0x%X does not end in a terminator" % (f.end_ea, end))
            exts.append(norm({"ea": ea, "before_end": f.end_ea, "end": end, "sha256": sha(f.end_ea, end)}))
        for ea, lo, hi in EXTEND_RUNS:
            if ea in oldx and "run" in oldx[ea]:
                exts.append(oldx[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            must(not any(ida_funcs.get_func(a) for a in range(lo, hi)), "run 0x%X..0x%X already owned" % (lo, hi))
            must(terminated(lo, hi) or lo in DOS_EXIT, "run 0x%X..0x%X not terminated" % (lo, hi))
            exts.append({"ea": ea, "run": [lo, hi], "run_sha256": sha(lo, hi), "before_end": f.end_ea,
                         "chunks_before": chunks(ea), "end": None, "sha256": None, "chunks_after": None})
        oldr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("rebase_funcs", [])} if MANIFEST.exists() else {}
        rebs = []
        for old, new, end, clo, ds, *chi in REBASE:
            if new in oldr:
                rebs.append(oldr[new])
                continue
            f = ida_funcs.get_func(old)
            must(f and f.start_ea == old and f.end_ea == end, "0x%X is not the planned function" % old)
            rebs.append({"ea": new, "old_ea": old, "end": end, "clear_lo": clo, "ds": ds, "name": uname(old),
                         "far": is_far(old), "sha256": sha(new, end), "old_sha256": sha(old, end),
                         "prefix_sha256": sha(new, old), "lost_heads": None, **({"clear_hi": chi[0]} if chi else {})})
        oldm = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("remove_funcs", [])} if MANIFEST.exists() else {}
        rms = []
        for ea, fe, end in REMOVE:
            if ea in oldm:
                rms.append(oldm[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
            rms.append({"ea": ea, "fn_end": fe, "end": end, "name": uname(ea), "far": is_far(ea),
                        "fn_sha256": sha(ea, fe), "data_sha256": sha(ea, end)})
        oldt = {x["clear"][0]: x for x in json.loads(MANIFEST.read_text()).get("table_fix", [])} if MANIFEST.exists() else {}
        tfs = []
        for t in TABLEFIX:
            if t["clear"][0] in oldt:
                tfs.append(oldt[t["clear"][0]])
                continue
            fl = []
            for ea, fe in t["funcs"]:
                f = ida_funcs.get_func(ea)
                must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
                fl.append({"ea": ea, "fn_end": fe, "end": t["words"][1], "name": uname(ea), "far": is_far(ea),
                           "fn_sha256": sha(ea, fe)})
            tfs.append({"funcs": fl, "clear": list(t["clear"]), "clear_sha256": sha(*t["clear"]), "words": list(t["words"]),
                        "offwords": list(t["offwords"]), "offwords_sha256": sha(t["offwords"][0], t["offwords"][1]),
                        "plain": list(t["plain"]), "plain_sha256": sha(*t["plain"])})
        oldx2 = {x["text"][0]: x for x in json.loads(MANIFEST.read_text()).get("text_fix", [])} if MANIFEST.exists() else {}
        xts = []
        for t in TEXTFIX:
            if t["text"][0] in oldx2:
                xts.append(oldx2[t["text"][0]])
                continue
            xts.append({"table": list(t["table"]), "table_sha256": sha(t["table"][0], t["table"][1]), "text": list(t["text"]),
                        "text_sha256": sha(*t["text"]), "keep": list(t["keep"])})
        oldtr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("trim_funcs", [])} if MANIFEST.exists() else {}
        trs = []
        for ea, oe, ne, wh, ch in TRIM:
            if ea in oldtr:
                trs.append(oldtr[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == oe, "0x%X is not the planned function" % ea)
            trs.append({"ea": ea, "old_end": oe, "end": ne, "words_hi": wh, "clear_hi": ch, "name": uname(ea), "far": is_far(ea),
                        "sha256": sha(ea, ch), "kept_sha256": sha(ea, ne)})
        olda = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("absorb_funcs", [])} if MANIFEST.exists() else {}
        abs_ = []
        for ea, fr, clo, chi, ne in ABSORB:
            if ea in olda:
                abs_.append(olda[ea])
                continue
            f, g = ida_funcs.get_func(ea), ida_funcs.get_func(fr)
            must(f and f.start_ea == ea and g and g.start_ea == fr, "0x%X / 0x%X are not the planned functions" % (ea, fr))
            abs_.append({"ea": ea, "frag": fr, "frag_end": g.end_ea, "frag_name": uname(fr), "frag_far": is_far(fr),
                         "frag_chunks": chunks(fr), "frag_sha256": sha(fr, g.end_ea), "clear": [clo, chi],
                         "before_end": f.end_ea, "end": ne, "sha256": sha(f.end_ea, ne), "chunks_before": chunks(ea),
                         "chunks_after": None})
        add_all(items, exts, rebs, rms, tfs, xts, trs, abs_)
        MANIFEST.write_text(json.dumps({"finding": 139, "step": "S1c-4 orphan code registered as functions (findings 126-139)",
                                        "extend_funcs": exts, "rebase_funcs": rebs, "remove_funcs": rms, "table_fix": tfs, "text_fix": xts, "trim_funcs": trs, "absorb_funcs": abs_, "add_funcs": items},
                                       indent=1).replace("\n", "\r\n"))
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("plan written: %s (not saved)" % MANIFEST.name)
        return
    doc = json.loads(MANIFEST.read_text())
    exts = [norm(x) for x in doc.get("extend_funcs", [])]
    rebs = doc.get("rebase_funcs", [])
    rms = doc.get("remove_funcs", [])
    tfs = doc.get("table_fix", [])
    xts = doc.get("text_fix", [])
    trs = doc.get("trim_funcs", [])
    abs_ = doc.get("absorb_funcs", [])
    states = ([state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs]
              + [rm_state(x) for x in rms] + [tf_state(x) for x in tfs] + [xt_state(x) for x in xts] + [trim_state(x) for x in trs]
              + [ab_state(x) for x in abs_])
    fresh_trims = [x for x in trs if trim_state(x) == "fresh"]
    for i, it in enumerate(doc["add_funcs"]):
        if states[i] == "mismatch" and any(x["end"] <= it["ea"] < x["old_end"] for x in fresh_trims):
            states[i] = "fresh"
    log.append("manifest: %d entries (add + extend); live: %d fresh, %d applied, %d mismatched" % (
        len(states), states.count("fresh"), states.count("applied"), states.count("mismatch")))
    if all(s == "applied" for s in states):
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if "mismatch" in states:
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_)
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
