p = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
s = open(p, newline="", encoding="utf-8").read().replace("\r\n", "\n")
a = s.index("**Not removed, on purpose.**")
b = s.index("**Still open:** 0x167449")
new = """**Not removed, on purpose.**  sub_105DA7 (2 B, `01 D0` = `add ax,dx`) sits in the middle of a word table (0x105D90..0x105EB5,
`01 D0 04 D0 04 ...`) but is not a clean case: IDA records xrefs to it from `call cs:funcs_106A17[bx]` at 0x106A4C and
0x106A7E (type 17, resolved through an indirect-call table), a data offset at 0x1069B4, and the fl_F flow from 0x105DA5.
sub_105D9D (0x105D9D..0x105DA7) before it is referenced the same way.  Whether those table entries are real function
pointers or a misread of the table needs the 0x106A17 dispatch table decoded first, so the region is left for its own
finding.

"""
s = s[:a] + new + s[b:]
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n"))
print("ok")
