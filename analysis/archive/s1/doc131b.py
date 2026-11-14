P = r"C:\Users\ybarnoy\projects\falcon3"


def edit(path, pairs):
    s = open(path, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:50], s.count(a))
        s = s.replace(a, b)
    open(path, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)


edit(P + r"\status.md", [
    ("""     - Left open (findings 126-130): 7 tiny/misdecoded fl_F fragments, 0x105DA9 and the 0x100CC0..0x100DFA
       data-decoded body, remaining jmp-reached tails, no-xref runs.""",
     """     - **S1c-4f (finding 131):** the jmp-reached tails: 0x100CA8 added as a two-chunk far function (88 B + 236 B tail
       around sub_100D01), sub_4335A rebased to 0x4334E (59 -> 71 B, unnamed); functions 3,556 -> 3,557; backup
       `.bak_tails`. The apply tool gained `TAILS` and unnamed rebases.
     - Left open (findings 126-131): 7 tiny/misdecoded fl_F fragments, 0x105DA9 junk run, 0x12C4F2 / 0x12C9D0, no-xref runs."""),
    ("     - commit S1c-4e;\n", "     - commit S1c-4f;\n"),
])
edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("(finding 130: three function starts rebased, four orphans added)",
     "(finding 130: three function starts rebased, four orphans added) and the jmp-reached tails (finding 131: a two-chunk function added, one start rebased)"),
])
print("ok")
