import yaml
cases = [
    ('bs',    'a: ' + chr(34) + 'x' + chr(92)*2 + 'y' + chr(34)),
    ('quote', 'a: ' + chr(34) + 'x' + chr(92) + chr(34) + 'y' + chr(34)),
    ('both',  'a: ' + chr(34) + 'x' + chr(92)*2 + 'y' + chr(92) + chr(34) + 'z' + chr(34)),
]
for name, s in cases:
    try:
        d = yaml.safe_load(s)
        print(name, 'OK', repr(d['a']))
    except Exception as e:
        print(name, 'FAIL:', str(e).splitlines()[0])
        print('  s =', repr(s))