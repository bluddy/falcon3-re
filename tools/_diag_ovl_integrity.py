import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
ROOT = r"C:\Users\yotam\projects\falcon3"
man = json.load(open(os.path.join(ROOT, 'registry/overlays_register_expected.json'), encoding='utf-8'))
log = []
bad = []
for r in man['ranges']:
    for f in r['new_fns']:
        s, e = f['ea'], f['ea'] + f['size']
        cur = s
        ok = True
        reason = ''
        while cur < e:
            h = ida_bytes.get_item_head(cur)
            if h == cur and ida_bytes.is_code(ida_bytes.get_flags(cur)):
                cur += max(ida_bytes.get_item_size(cur), 1); continue
            if h != cur:
                cur = h + max(ida_bytes.get_item_size(h), 1); continue
            if ida_bytes.is_data(ida_bytes.get_flags(cur)):
                cur += max(ida_bytes.get_item_size(cur), 1); continue
            ins = ida_ua.insn_t()
            k = ida_ua.decode_insn(ins, cur)   # decode only, NO create_insn
            if k <= 0:
                ok = False; reason = 'decode_fail@0x%X' % cur; break
            if cur + k > e:
                ok = False; reason = 'crosses_end@0x%X' % cur; break
            cur += k
        if not ok:
            bad.append((f['key'], s, e, reason, f['size']))
n_total = sum(len(r['new_fns']) for r in man['ranges'])
log.append("scanned %d new_fns, %d have body-integrity problems (decode-only):" % (n_total, len(bad)))
for k, s, e, reason, sz in bad:
    log.append("  %s 0x%X..0x%X size=%d  %s" % (k, s, e, sz, reason))
with open(os.path.join(ROOT, 'analysis/ida_falconcd/diag_ovl_integrity.log'), 'w') as f:
    f.write("\n".join(log))
idaapi.qexit(0)