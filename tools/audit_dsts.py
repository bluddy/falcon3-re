"""Finding 58 (read-only IDA diagnostic): decode the unresolved call/jump
destinations collected by tools/dst_list.py.

For every address that a CALL/JMP references but no function covers, records:
  * IDA's view: segment, item flags, item size, any name, prev/next function,
    whether the previous item ends in a terminator (a real entry signal);
  * a forward decode from the address (mnemonics until a terminator, a gap, a
    decode failure, or the limit) -- this is what separates a frameless 16-bit
    routine from a table;
  * the source instructions: mnemonic, operand type and operand text, so
    `call dword_XXXX` (FF 1E, a pointer variable) is distinguishable from a
    direct `call off:seg`.

Writes analysis/ida_falconcd/dst_audit.json.

NO IDB mutation: decode only (ida_ua.decode_insn), no create_insn, no
del_items, no auto_wait, no save -- findings 37/40 rules.

Usage: cmd /c "tools\\run_idat.bat tools\\audit_dsts.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_idp
import ida_segment
import ida_ua
import idaapi
import idautils
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
SRCLIST = ROOT + r"\analysis\ida_falconcd\dst_list.json"
OUT = ROOT + r"\analysis\ida_falconcd\dst_audit.json"
LOG = ROOT + r"\analysis\ida_falconcd\dst_audit.log"

TERMS = {"retf", "retn", "ret", "iret", "jmp"}
MAX_INSNS = 64
MAX_BYTES = 512

log = []
rows = []


def decode_forward(ea):
    """Decode from ea without touching the IDB. Read-only."""
    out = {"mnems": [], "bytes": 0, "term": None, "ok": False, "why": ""}
    insn = ida_ua.insn_t()
    cur = ea
    for _ in range(MAX_INSNS):
        if out["bytes"] >= MAX_BYTES:
            out["why"] = "byte-limit"
            break
        if ida_segment.getseg(cur) is None:
            out["why"] = "gap/no-segment"
            break
        n = ida_ua.decode_insn(insn, cur)
        if n <= 0:
            out["why"] = "undecodable@0x%X" % cur
            break
        # canonical mnemonic from the decode -- get_canon_mnem works on
        # addresses that have no IDB item (which is most of these); the idc
        # helper only reports what IDA happens to have stored
        m = (insn.get_canon_mnem() or "").lower()
        out["mnems"].append(m)
        out["bytes"] += n
        if m in TERMS or ida_idp.is_ret_insn(insn):
            out["term"] = m
            out["ok"] = True
            break
        cur += n
    else:
        out["why"] = "limit"
    return out


def main():
    targets = json.load(open(SRCLIST))
    log.append("targets: %d" % len(targets))
    for t in targets:
        ea = t["ea"]
        r = {"ea": ea, "n": t["n"], "zone": t["zone"], "call": t["call"],
             "jmp": t["jmp"]}
        seg = ida_segment.getseg(ea)
        r["seg"] = seg.name if seg else None
        fl = ida_bytes.get_flags(ea)
        r["is_code"] = bool(ida_bytes.is_code(fl))
        r["is_data"] = bool(ida_bytes.is_data(fl))
        r["item_size"] = ida_bytes.get_item_size(ea)
        r["is_head"] = ida_bytes.is_head(fl)
        r["name"] = idc.get_name(ea) or ""
        r["bytes16"] = (idc.get_bytes(ea, 16) or b"").hex()

        # Is this address immediately preceded by a terminator? Most of these
        # bytes carry no IDB item, so sweep the few plausible instruction starts
        # before ea and keep any decode that lands exactly on ea.
        r["prev_mnem"] = ""
        r["prev_mnem_idb"] = ""
        r["prev_is_term"] = False
        for back in range(1, 7):
            c = ea - back
            if c < 0:
                break
            ins2 = ida_ua.insn_t()
            n = ida_ua.decode_insn(ins2, c)
            if n > 0 and c + n == ea:
                pm = (ins2.get_canon_mnem() or "").lower()
                if not r["prev_mnem"]:
                    r["prev_mnem"] = pm
                if pm in TERMS or ida_idp.is_ret_insn(ins2):
                    r["prev_mnem"] = pm
                    r["prev_is_term"] = True
                    break
        ph = ida_bytes.get_item_head(ea - 1) if ea > 0 else None
        if ph is not None:
            r["prev_mnem_idb"] = (idc.print_insn_mnem(ph) or "").lower()

        pf = ida_funcs.get_prev_func(ea)
        nf = ida_funcs.get_next_func(ea)
        r["prev_fn"] = ([idc.get_func_name(pf.start_ea), pf.start_ea, pf.end_ea]
                        if pf else None)
        r["next_fn"] = ([idc.get_func_name(nf.start_ea), nf.start_ea, nf.end_ea]
                        if nf else None)
        r["decode"] = decode_forward(ea)

        srcs = []
        for s in t["srcs"][:6]:
            sm = (idc.print_insn_mnem(s) or "").lower()
            ot = idc.get_operand_type(s, 0)
            txt = idc.print_operand(s, 0) or ""
            srcs.append({"ea": s, "mnem": sm, "op_type": int(ot), "op0": txt})
        r["srcs"] = srcs
        rows.append(r)

    json.dump({"targets": rows}, open(OUT, "w"))
    log.append("wrote %s (%d rows)" % (OUT, len(rows)))


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
