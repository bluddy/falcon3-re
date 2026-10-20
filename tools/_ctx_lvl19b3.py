import json, sys
sys.stdout.reconfigure(encoding='utf-8')
batches = json.load(open('analysis/ida_falconcd/level19_batches.json', encoding='utf-8'))
ctx = json.load(open('analysis/ida_falconcd/level19_context.json', encoding='utf-8'))
ctxd = {c['key']: c for c in ctx}
order = batches['3']
print("batch3 count:", len(order))
for k in order:
    c = ctxd.get(k, {})
    print("%s ea=0x%X size=%d in=%d dyn=%d callees=%s callers=%s" % (
        k, c.get('ea',0), c.get('size',0), c.get('in',0), c.get('dyn',0),
        ','.join(c.get('callees',[])[:8]) if c.get('callees') else '-',
        ','.join(c.get('callers',[])[:10]) if c.get('callers') else '-'))
