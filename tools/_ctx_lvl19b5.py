import io, json, sys
batches = json.load(open('analysis/ida_falconcd/level19_batches.json', encoding='utf-8'))
ctx = json.load(open('analysis/ida_falconcd/level19_context.json', encoding='utf-8'))
ctxd = {c['key']: c for c in ctx}
out = io.open('analysis/ida_falconcd/level19_batch5_ctx.txt', 'w', encoding='utf-8', newline='\n')
order = batches['5']
out.write("batch5 count: %d\n" % len(order))
for k in order:
    c = ctxd.get(k, {})
    out.write("%s ea=0x%X size=%d in=%d dyn=%d callees=%s callers=%s\n" % (
        k, c.get('ea',0), c.get('size',0), c.get('in',0), c.get('dyn',0),
        ','.join(c.get('callees',[])[:8]) if c.get('callees') else '-',
        ','.join(c.get('callers',[])[:10]) if c.get('callers') else '-'))
out.close()
print("wrote analysis/ida_falconcd/level19_batch5_ctx.txt", len(order))
