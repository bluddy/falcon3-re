"""Resolve and dump indirect-dispatch tables (Level 2) — read-only.

Given one or more *named dispatcher* functions, this:
  1. finds the `call cs:off_XXXXX[bx]` table operand inside it,
  2. reads the table as an array of 16-bit near offsets (stride 2),
     resolving each entry against the dispatcher's own segment,
  3. prints, per target: table index, EA, ledger name, size, class,
     a linear disassembly with its outgoing `callees`, and direct callers,
  4. prints every static call site of the dispatcher together with the
     immediate that was loaded into BX just before it.

Why stride 2 and why BX is a *byte* offset (finding 48): 8086 16-bit
addressing has no scale field, so `call cs:off_XXXXX[bx]` adds BX as bytes.
The table is an array of 16-bit near pointers, hence opcode = BX / 2.
Entries terminate at the first zero word.

Usage:
  DT_FNS=op_dispatch,fn_table_dispatch cmd /c "tools\\run_idat.bat tools\\dump_dispatch_tables.py"
"""
import json
import os

import ida_bytes
import ida_funcs
import ida_name
import ida_segment
import idaapi
import idautils
import idc

OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\level2_dump.log"
FB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
MAX_ENTRIES = 40
MAX_INSNS = 60

fns = os.environ.get("DT_FNS", "op_dispatch,fn_table_dispatch").split(",")

cls = json.loads(open(CLS).read())
fb = json.loads(open(FB).read())
byname = {v.get("ea"): v.get("name") for v in fb.values() if v.get("name")}

log = []


def parse_imm(text):
    text = text.strip()
    try:
        return int(text[:-1], 16) if text.endswith("h") else int(text, 10)
    except ValueError:
        return None


def table_operand(feas, mnem_wanted="call"):
    """EA of the dispatcher's `call cs:<table>[bx]` + the table itself.

    Matches on the addressing form rather than a name prefix: renaming the
    table (finding 48) changed the operand from `cs:off_22060[bx]` to
    `cs:op_dispatch_table[bx]`, which is exactly what a name-based match
    would miss.
    """
    pos = feas
    for _ in range(40):
        if idc.print_insn_mnem(pos) == mnem_wanted:
            op = idc.print_operand(pos, 0)
            if "[bx]" in op and ":" in op:
                sym = op.split(":", 1)[1].split("[")[0].strip()
                ea = ida_name.get_name_ea(idaapi.BADADDR, sym)
                if ea != idaapi.BADADDR:
                    return pos, ea
        sz = ida_bytes.get_item_size(pos)
        if sz <= 0:
            return None, None
        pos += sz
    return None, None


def bx_usage(feas, fname):
    """(call-site ea, BX immediate) for each static call to fname.

    Walking backwards, the FIRST instruction that *writes* BX decides it and
    ends the search. Earlier versions kept walking after a `mov bx, ax` and
    reported a stale `mov bx, imm` several instructions above, which produced
    a bogus opcode histogram.
    """
    out = []
    for h in idautils.Heads(0, 0x2B000):
        if idc.print_insn_mnem(h) != "call" or idc.print_operand(h, 0) != fname:
            continue
        imm = None
        pos = h
        for _ in range(8):
            pos = idc.prev_head(pos, 0)
            if pos == idc.BADADDR:
                break
            m = idc.print_insn_mnem(pos)
            op0 = idc.print_operand(pos, 0).lower()
            if op0 != "bx":
                continue
            if m in ("cmp", "test", "push"):      # does not define BX
                continue
            if m == "mov":
                v = parse_imm(idc.print_operand(pos, 1))
                if v is not None:
                    imm = v
                break                               # BX defined here either way
            if m == "xor" and idc.print_operand(pos, 1).lower() == "bx":
                imm = 0
                break
            if m == "shl" and parse_imm(idc.print_operand(pos, 1)) == 1:
                # `shl bx,1` doubling an opcode into a byte offset
                imm = _resolve_shifted(pos, h)
                break
            break                                   # any other BX writer
        out.append((h, imm))
    return out


def _resolve_shifted(shl_ea, call_ea):
    """Immediate feeding a `shl bx,1` (returns the *final* BX if immediate)."""
    pos = shl_ea
    for _ in range(8):
        pos = idc.prev_head(pos, 0)
        if pos == idc.BADADDR:
            return None
        if idc.print_insn_mnem(pos) == "mov" and \
           idc.print_operand(pos, 0).lower() == "bx":
            v = parse_imm(idc.print_operand(pos, 1))
            return (v * 2) if v is not None else None
    return None


for fname in [f.strip() for f in fns if f.strip()]:
    feas = ida_name.get_name_ea(idaapi.BADADDR, fname)
    log.append("#" * 78)
    if feas == idaapi.BADADDR:
        log.append("# %s: DISPATCHER NOT FOUND" % fname)
        continue
    site, tbl = table_operand(feas)
    if tbl == idaapi.BADADDR or tbl is None:
        log.append("# %s ea=0x%X: no table operand found" % (fname, feas))
        continue
    seg = ida_segment.getseg(feas)
    log.append("# %s  ea=0x%X   table ea=0x%X   (stride 2, base 0x%X)"
               % (fname, feas, tbl, seg.start_ea))
    log.append("#" * 78)

    targets = []
    for k in range(MAX_ENTRIES):
        w = ida_bytes.get_word(tbl + k * 2)
        if w == 0:
            break
        targets.append((k, seg.start_ea + w))
    log.append("# resolved %d targets (index = BX/2)" % len(targets))
    log.append("")

    for h, imm in bx_usage(feas, fname):
        log.append("   call site 0x%X -> BX=%s%s" % (
            h, imm if imm is not None else "(computed)",
            "" if imm is None else "  => opcode k=%d" % (imm // 2)))
    log.append("")

    for k, a in targets:
        nm = byname.get(a) or idc.get_func_name(a) or "?"
        f = ida_funcs.get_func(a)
        size = (f.end_ea - f.start_ea) if f else 0
        log.append("=== [k=%d] BX=%d  0x%X  %s  (%dB, %s)  ledger=%s ==="
                   % (k, k * 2, a, nm, size,
                      cls.get(nm, {}).get("class", "?"), byname.get(a, "-")))
        if not f:
            log.append("  NO FUNC OBJECT")
            log.append("")
            continue
        pos, i = a, 0
        while pos < f.end_ea and i < MAX_INSNS:
            log.append("  0x%X: %-6s %s %s %s" % (
                pos, idc.print_insn_mnem(pos) or "??",
                idc.print_operand(pos, 0) or "",
                idc.print_operand(pos, 1) or "",
                idc.print_operand(pos, 2) or ""))
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                log.append("    <zero-size item>")
                break
            pos += sz
            i += 1
        callers = []
        for h in idautils.Heads(f.start_ea, f.end_ea):
            for fr in idautils.CodeRefsTo(h, 0):
                cf = ida_funcs.get_func(fr)
                if cf and cf.start_ea != f.start_ea:
                    callers.append(byname.get(cf.start_ea)
                                   or idc.get_func_name(cf.start_ea)
                                   or hex(cf.start_ea))
        uniq = sorted(set(callers))
        if uniq:
            log.append("  direct callers(%d): %s"
                       % (len(uniq), ", ".join(uniq[:14])))
        log.append("")

open(OUT, "w").write("\n".join(log))
idaapi.qexit(0)
