import sys, json, io, re
sys.stdout.reconfigure(encoding='utf-8')
batches = json.load(open('analysis/ida_falconcd/level19_batches.json'))
trunc = json.load(open('analysis/ida_falconcd/level19_trunc.json'))
tr = set(trunc['truncated']) if isinstance(trunc, dict) else set(trunc)
ctx = json.load(open('analysis/ida_falconcd/level19_context.json'))

def blocks(path):
    lines = io.open(path, encoding='utf-8', errors='replace').read().split('\n')
    offs = {}
    for i, l in enumerate(lines):
        m = re.match(r'^(?:#\d+\s+)?([A-Za-z_][\w@]+)\s+ea=0x', l)
        if m:
            offs[m.group(1)] = i
    keys = list(offs)
    out = {}
    for j, k in enumerate(keys):
        end = offs[keys[j + 1]] - 2 if j + 1 < len(keys) else len(lines)
        out[k] = lines[offs[k]:end]
    return out

full = blocks('analysis/ida_falconcd/level19_full.txt')
dis = blocks('analysis/ida_falconcd/level19_disasm.txt')
fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))

for bn in ['1', '2', '3', '4', '5', '6']:
    keys = batches[bn]
    out = []
    out.append('===== L19 BATCH %s (%d fns) =====' % (bn, len(keys)))
    for k in keys:
        src = full if k in tr else dis
        body = src.get(k)
        if body is None:
            body = ['; MISSING BLOCK %s' % k]
        # callers line from context if present
        cl = ''
        if isinstance(ctx, dict):
            e = ctx.get(k) or {}
            c = e.get('callers') or e.get('in') or []
            if isinstance(c, list) and c:
                cl = '  callers (%d): %s\n' % (len(c), ', '.join(str(x) for x in c[:30]))
        out.append('; ---- %s size=%d ----%s' % (k, fb[k]['size'], cl))
        out.extend(body)
        out.append('')
    p = 'analysis/ida_falconcd/level19_batch%s.txt' % bn
    io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    print('wrote %s: %d lines' % (p, len(out)))
