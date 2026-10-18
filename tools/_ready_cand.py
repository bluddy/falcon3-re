import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, ida_name, json, os, sys
ROOT = r"C:\Users\yotam\projects\falcon3"
ALIGNED = os.path.join(ROOT, 'analysis/ida_falconcd/resident_candidates_aligned.json')
OUT = os.path.join(ROOT, 'analysis/ida_falconcd/resident_manifest_ready.json')
cands = json.load(open(ALIGNED, encoding='utf-8'))
log = []
ready = []
failed = []
for c in cands:
    entry = c['entry']
    size = c['aligned_size']
    end = entry + size
    if not c['add_func_ok']:
        # try the finding-59 clear-blocked-items retry
        ok = False
        for _try in range(8):
            insn = ida_ua.insn_t()
            k = ida_ua.decode_insn(insn, entry)
            if k <= 0:
                break
            blocking = []
            for pos in range(entry + 1, min(entry + k, end)):
                hh = ida_bytes.get_item_head(pos)
                if hh != entry and ida_bytes.is_head(ida_bytes.get_flags(hh)):
                    blocking.append(hh)
            if not blocking:
                break
            for hh in sorted(set(blocking)):
                nn = max(ida_bytes.get_item_size(hh), 1)
                ida_bytes.del_items(hh, ida_bytes.DELIT_SIMPLE, nn)
                log.append("  cleared %dB item @0x%X blocking entry 0x%X" % (nn, hh, entry))
        if not ida_bytes.is_code(ida_bytes.get_flags(entry)):
            ida_ua.create_insn(entry)
        ok = ida_funcs.add_func(entry)
        if ok:
            ida_funcs.del_func(entry)
            c['add_func_ok'] = True
            c['cleared'] = True
        else:
            failed.append(c)
            log.append("0x%X STILL add_func=False after retry" % entry)
            continue
    # success or already ok — dry-run add with explicit end + name to confirm
    ok2 = ida_funcs.add_func(entry, end)
    if ok2:
        # set name + verify span
        key = 'sub_%X' % entry
        ida_name.set_name(entry, key, ida_name.SN_NOWARN)
        fn = ida_funcs.get_func(entry)
        span_ok = fn and fn.start_ea == entry and fn.end_ea == end
        ida_funcs.del_func(entry)
        if not span_ok:
            failed.append(c)
            log.append("0x%X span mismatch after add" % entry)
            continue
    else:
        failed.append(c)
        log.append("0x%X add_func(entry, end) FAILED" % entry)
        continue
    ready.append({
        'entry': entry, 'size': size, 'key': 'sub_%X' % entry,
        'orig_ea': c['orig_ea'], 'mid': c['mid_instruction'],
        'n_refs': c['n_refs'], 'cls': c['cls'],
    })
    log.append("0x%X READY size=%d refs=%d mid=%s" % (entry, size, c['n_refs'], c['mid_instruction']))
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(ready, f, indent=1)
with open(os.path.join(ROOT, 'analysis/ida_falconcd/diag_ready.log'), 'w') as f:
    f.write("READY: %d  FAILED: %d\n\n" % (len(ready), len(failed)) + "\n".join(log))
idaapi.qexit(0)