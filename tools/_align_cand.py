import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
ROOT = r"C:\Users\yotam\projects\falcon3"
CAND = os.path.join(ROOT, 'analysis/ida_falconcd/resident_candidates.json')
OUT = os.path.join(ROOT, 'analysis/ida_falconcd/resident_candidates_aligned.json')
candidates = json.load(open(CAND, encoding='utf-8'))
log = []
aligned = []
issues = []
for c in candidates:
    ea = c['ea']
    size = c['fn_size']
    # Get the real item head containing ea
    h = ida_bytes.get_item_head(ea)
    flags_h = ida_bytes.get_flags(h)
    entry = ea
    mid = False
    if h < ea:
        # ea is mid-instruction; use the real head as entry IF it decodes
        mid = True
        entry = h
        # recompute size from new entry to original end (or decode to terminator)
        # decode forward to terminator from entry
        cur = entry
        term_ea = None
        for _ in range(1024):
            insn = ida_ua.insn_t()
            k = ida_ua.decode_insn(insn, cur)
            if k <= 0:
                break
            mnem = idc.print_insn_mnem(cur).lower()
            if mnem in ('retn','retf','ret','iret','jmp'):
                term_ea = cur
                # advance past terminator
                insn2 = ida_ua.insn_t()
                k2 = ida_ua.decode_insn(insn2, cur)
                if k2 > 0:
                    cur = cur + k2
                break
            cur += k
        if term_ea is None:
            issues.append((ea, 'no_terminator_from_aligned_entry'))
            continue
        new_size = cur - entry
    else:
        new_size = size
    # Check entry is a head or can be made one
    flags_e = ida_bytes.get_flags(entry)
    is_head = ida_bytes.is_head(flags_e)
    is_code = ida_bytes.is_code(flags_e)
    # Try decode
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, entry)
    # Try add_func dry
    ok = ida_funcs.add_func(entry)
    if ok:
        ida_funcs.del_func(entry)
    else:
        issues.append((ea, 'add_func_failed_at_entry_%X' % entry))
    aligned.append({
        **c,
        'orig_ea': ea, 'entry': entry, 'mid_instruction': mid,
        'aligned_size': new_size, 'item_head': h, 'add_func_ok': ok,
        'decode_k': k,
    })
    log.append("0x%X -> entry 0x%X mid=%s size=%d add_func=%s k=%d" % (
        ea, entry, mid, new_size, ok, k))
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(aligned, f, indent=1)
with open(os.path.join(ROOT, 'analysis/ida_falconcd/diag_align.log'), 'w') as f:
    f.write("\n".join(log) + "\n\nISSUES:\n" + "\n".join("%s %s" % (hex(a),b) for a,b in issues))
idaapi.qexit(0)