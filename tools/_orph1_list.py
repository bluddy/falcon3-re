import json, io
ctx = json.load(io.open('analysis/ida_falconcd/orph1_context.json', encoding='utf-8'))
print(len(ctx))
for e in ctx:
    cal = ', '.join(e['callees'][:6]) if e['callees'] else '-'
    print('%3d %-12s sz=%5d cls=%-4s callees=%s' % (e['rank'], e['key'], e['size'], e['class'], cal))
