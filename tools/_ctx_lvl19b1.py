import json, sys
sys.stdout.reconfigure(encoding='utf-8')
b = json.load(open('analysis/ida_falconcd/level19_batches.json'))
keys = b['1']
ctx = {c['key']: c for c in json.load(open('analysis/ida_falconcd/level19_context.json'))}
print('batch1 count:', len(keys))
for k in keys:
    c = ctx.get(k)
    if not c:
        print('%-12s NOT-IN-CTX' % k); continue
    cal = ','.join(c.get('callees') or []) or '-'
    calr = ','.join(c.get('callers') or []) or '-'
    print('%-12s size=%-5s in=%-3s dyn=%-3s | CAL: %s | CALR: %s' % (
        k, c.get('size'), c.get('in'), c.get('dyn'), cal[:300], calr[:200]))
