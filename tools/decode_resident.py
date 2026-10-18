#!/usr/bin/env python3
"""Finding 63: IDA-side validation of the 86 Resident destinations.
For each dst: decode forward to a terminator, check no overlap with existing
functions / named data, classify jump-table targets as standalone handler
(ends retn/retf) vs tail (ends jmp).  Writes analysis/ida_falconcd/resident_decode.json.
Run under idat via run_idat.bat."""
import json, os, sys
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, 'analysis/ida_falconcd/resident_audit.json')
OUT = os.path.join(ROOT, 'analysis/ida_falconcd/resident_decode.json')

audit = json.load(open(AUDIT, encoding='utf-8'))
records = audit['records']

TERMINATORS = {'ret', 'retf', 'retn', 'jmp', 'iret', 'iretf', 'loope', 'loopne', 'loop'}

# Existing function intervals
ivs = sorted((ida_funcs.get_func(s).start_ea, ida_funcs.get_func(s).end_ea)
             for s in idautils.Functions())
starts = [x[0] for x in ivs]

def overlaps_existing_fn(ea, end):
    import bisect
    i = bisect.bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][1] > ea:
        return True
    i = bisect.bisect_left(starts, ea)
    if i < len(ivs) and ivs[i][0] < end:
        return True
    return False

def decode_to_terminator(start, max_insns=512, max_bytes=4096):
    """Walk forward from start until a terminator or failure."""
    ea = start
    insns = 0
    bytes_walked = 0
    while insns < max_insns and bytes_walked < max_bytes:
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, ea)
        if k <= 0:
            return None, ea, 'undecodable', bytes_walked
        # Check if this insn is a terminator
        mnem = idc.print_insn_mnem(ea).lower()
        if mnem in TERMINATORS:
            # For jmp, check if it's a tail (not jmp to next fn start)
            return ea, ea, mnem, bytes_walked
        ea += k
        bytes_walked += k
        insns += 1
    return None, ea, 'no_terminator_in_window', bytes_walked

def is_data_item(ea):
    f = ida_bytes.get_flags(ea)
    return ida_bytes.is_data(f) and not ida_bytes.is_head(f) == False  # is data head

results = []
for rec in records:
    ea = rec['ea']
    n_refs = rec['n_refs']
    cls = rec['cls']
    is_jt = rec['jump_table']

    # Check if already in an existing function
    fn = ida_funcs.get_func(ea)
    if fn:
        results.append({**rec, 'already_fn': True, 'fn_start': fn.start_ea, 'fn_end': fn.end_ea})
        continue

    # Check if it's a named data item (not a function entry)
    flags = ida_bytes.get_flags(ea)
    if ida_bytes.is_data(flags):
        results.append({**rec, 'already_fn': False, 'is_data': True,
                        'name': idc.get_name(ea)})
        continue

    # Decode to terminator
    term_ea, last_ea, term_mnem, bytes_walked = decode_to_terminator(ea)

    if term_ea is None:
        results.append({**rec, 'already_fn': False, 'is_data': False,
                        'decode': 'FAIL', 'reason': term_mnem,
                        'bytes_walked': bytes_walked})
        continue

    # Check no overlap with existing functions
    fn_start = ea
    fn_end = term_ea  # inclusive of terminator insn
    # Advance fn_end past the terminator insn
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, term_ea)
    if k > 0:
        fn_end = term_ea + k

    overlaps = overlaps_existing_fn(fn_start, fn_end)

    # For jump-table targets: standalone (ends retn/retf) vs tail (ends jmp)
    action = 'standalone'
    if is_jt:
        if term_mnem in ('retn', 'retf', 'ret'):
            action = 'jt_standalone'   # ends in return = standalone handler
        elif term_mnem == 'jmp':
            action = 'jt_tail'         # ends in jmp = tail/case branch
        else:
            action = 'jt_other'

    results.append({
        **rec, 'already_fn': False, 'is_data': False,
        'decode': 'OK', 'term_mnem': term_mnem, 'term_ea': hex(term_ea),
        'fn_end': hex(fn_end), 'fn_size': fn_end - fn_start,
        'bytes_walked': bytes_walked, 'insns': None,
        'overlaps_existing': overlaps,
        'action': action,
    })

# Stats
ok = [r for r in results if r.get('decode') == 'OK' and not r.get('already_fn') and not r.get('is_data')]
fail = [r for r in results if r.get('decode') == 'FAIL']
already = [r for r in results if r.get('already_fn')]
is_data = [r for r in results if r.get('is_data')]
overlap = [r for r in ok if r.get('overlaps_existing')]
jt_sa = [r for r in ok if r.get('action') == 'jt_standalone']
jt_tail = [r for r in ok if r.get('action') == 'jt_tail']

out = {
    'range': audit['range'],
    'total': len(records),
    'ok_decode': len(ok),
    'fail_decode': len(fail),
    'already_fn': len(already),
    'is_data': len(is_data),
    'overlap_existing': len(overlap),
    'jt_standalone': len(jt_sa),
    'jt_tail': len(jt_tail),
    'standalone_registerable': len([r for r in ok if r['action'] == 'standalone' and not r['overlaps_existing']]),
    'results': results,
    'failures': fail,
    'overlaps': overlap,
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1)

print(f"Resident decode validation: {len(records)} dsts")
print(f"  OK decode (registerable path): {len(ok)}")
print(f"  FAIL decode: {len(fail)}")
print(f"  already in fn: {len(already)}")
print(f"  is data: {len(is_data)}")
print(f"  overlap existing: {len(overlap)}")
print(f"  jump-table standalone (retn/retf): {len(jt_sa)}")
print(f"  jump-table tail (jmp): {len(jt_tail)}")
print(f"  standalone_registerable (no overlap): {out['standalone_registerable']}")
print(f"wrote resident_decode.json")

# Exit cleanly
idaapi.qexit(0)