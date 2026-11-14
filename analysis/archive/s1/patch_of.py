import io
p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = io.open(p, "r", newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")

def sub(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

sub("import ida_loader\n", "import ida_loader\nimport ida_ua\n")
sub('''        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
''', '''        if "seeds" in it:
            decode_menu(it)
        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
''')
sub('''        must(chunks(it["ea"]) == [[it["ea"], it["end"]]], "chunks of 0x%X" % it["ea"])
''', '''        must(chunks(it["ea"]) == [[it["ea"], it["end"]]], "chunks of 0x%X" % it["ea"])
        if "seeds" in it:
            a = it["ea"]
            while a < it["end"]:
                must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                a += ida_bytes.get_item_size(a)
''')
sub('''        add_all(items)
        MANIFEST.write_text(json.dumps({"finding": 126, "step": "S1c-4 call-reached orphan code registered",
                                        "add_funcs": items}, indent=1).replace("\n", "\r\n"))
''', '''        for base, cf, end in MENUS:
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
            must(terminated(base, end), "0x%X..0x%X does not end in a terminator" % (base, end))
            items.append({"ea": base, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, base), 0),
                          "callers": sorted(x.frm for x in idautils.XrefsTo(base, 0) if x.iscode),
                          "redecode": cf, "seeds": menu_seeds(base, cf), "sha256": sha(base, end)})
        add_all(items)
        MANIFEST.write_text(json.dumps({"finding": 126, "step": "S1c-4 orphan code registered as functions",
                                        "add_funcs": items}, indent=1).replace("\n", "\r\n"))
''')
sub('''            must(not any(ida_funcs.get_func(a) for a in range(ea, end)), "0x%X..0x%X already owned" % (ea, end))
''', '''            if state({"ea": ea, "end": end, "sha256": ""}) != "applied":
                must(not any(ida_funcs.get_func(a) for a in range(ea, end)), "0x%X..0x%X already owned" % (ea, end))
''')
if crlf:
    s = s.replace("\n", "\r\n")
io.open(p, "w", newline="", encoding="utf-8").write(s)
print("ok")
