import sys, io, re
sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('registry/naming.yaml', encoding='utf-8').read()
blocks = re.split(r'\n  - ida: ', txt)
for b in blocks[1:]:
    nm = re.search(r'name:\s*(\S+)', b)
    notes = re.search(r'notes:\s*"([^"]*)"', b)
    sig = re.search(r'sig:\s*"([^"]*)"', b)
    name = nm.group(1) if nm else '?'
    n = notes.group(1) if notes else ''
    s = sig.group(1) if sig else ''
    if re.search(r'mouse|33h|cursor|sprite|farptr|joystick|input|keyboard|timer|tick|rand|seed|fixed|mul|div|screen|pixel|blit|draw', name + ' ' + n + ' ' + s, re.I):
        print('%-30s | %s' % (name, (s or n)[:85]))