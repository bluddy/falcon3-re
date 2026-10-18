import io, yaml

# 1) fix routines.yaml drive_path_build sig (two bare-backslash spots)
p = 'registry/routines.yaml'
t = io.open(p, encoding='utf-8', newline='').read()
fixed = False
for old, new in ((r"store ':' + '\' (0x3A5C)", r"store ':' + '\\' (0x3A5C)"),
                 (r"'X:\' path prefix", r"'X:\\' path prefix")):
    if old in t:
        t = t.replace(old, new)
        fixed = True
if fixed:
    io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print('routines patched')
d = yaml.safe_load(io.open(p, encoding='utf-8').read())
print('routines.yaml OK')

# 2) patch append templates: YAML needs backslash doubled BEFORE quote escaping
for tp in ('tools/_append_naming66.py', 'tools/_append_routines66.py'):
    s = io.open(tp, encoding='utf-8').read()
    for var in ('sig', 'notes'):
        old = var + '.replace(\'"\', \'\\\\"\')'
        new = (var + '.replace(chr(92), chr(92)*2)'
               '.replace(\'"\', chr(92)*2 + \'"\')')
        if old in s:
            s = s.replace(old, new)
            print('patched', var, 'in', tp)
    io.open(tp, 'w', encoding='utf-8', newline='').write(s)