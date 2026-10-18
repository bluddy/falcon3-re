import io, yaml
p = 'registry/routines.yaml'
t = io.open(p, encoding='utf-8', newline='').read()
old = r"('X:\')"
new = r"('X:\\')"
c = t.count(old)
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(t)
print('replaced', c)
d = yaml.safe_load(io.open(p, encoding='utf-8').read())
print('routines.yaml OK, top keys:', list(d.keys())[:6])