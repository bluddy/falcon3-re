import io
p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = io.open(p, "r", newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")


def sub(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


sub('''        for base, cf, end in MENUS:
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
''', '''        for base, cf, end in MENUS:
            if state({"ea": base, "end": end, "sha256": ""}) == "applied" and base in old:
                items.append(old[base])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
''')
sub('''        add_all(items)
        MANIFEST.write_text(json.dumps({"finding": 126, "step": "S1c-4 call-reached orphan code registered",
                                        "add_funcs": items}, indent=1).replace("\n", "\r\n"))
''', '''        oldx = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("extend_funcs", [])} if MANIFEST.exists() else {}
        exts = []
        for ea, end in EXTEND:
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            if f.end_ea == end and ea in oldx:
                exts.append(oldx[ea])
                continue
            must(terminated(f.end_ea, end), "0x%X..0x%X does not end in a terminator" % (f.end_ea, end))
            exts.append({"ea": ea, "before_end": f.end_ea, "end": end, "sha256": sha(f.end_ea, end)})
        add_all(items, exts)
        MANIFEST.write_text(json.dumps({"finding": 126, "step": "S1c-4 orphan code registered as functions (findings 126-128)",
                                        "extend_funcs": exts, "add_funcs": items}, indent=1).replace("\n", "\r\n"))
''')
sub('''    states = [state(it) for it in doc["add_funcs"]]
''', '''    exts = doc.get("extend_funcs", [])
    states = [state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts]
''')
sub('''    add_all(doc["add_funcs"])
''', '''    add_all(doc["add_funcs"], exts)
''')
sub('''    log.append("manifest: %d functions; live: %d fresh''', '''    log.append("manifest: %d entries (add + extend); live: %d fresh''')
if crlf:
    s = s.replace("\n", "\r\n")
io.open(p, "w", newline="", encoding="utf-8").write(s)
print("ok")
