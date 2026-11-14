def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


R = r"C:\Users\ybarnoy\projects\falcon3"
ENTRY = """
## 2026-11-10 140 - sub_16F4B5 rebased onto its real prologue (S1c-4o)

`sub_16F4B5` (far, unnamed, 82 B) started three bytes late: its first instructions `push bp / mov bp,sp / push si` sit
at 0x16F4B1..0x16F4B4 and were left as a 4-byte orphan run (finding 139 flagged it, the one no-xref-scan run with
eight callers).  All eight callers (far calls, from 0x16DC0B, 0x16DC79, 0x16DCE1, 0x16DD66 and four more) target
0x16F4B1; the only xrefs into 0x16F4B5 and 0x16F4B4 were the fall-through flow from the bytes before them.  The existing
REBASE mode moved the start to 0x16F4B1 (86 B, ends unchanged at 0x16F507; no stale code heads, no DS change, no name).
`function_bytes.json` keeps the key `sub_16F4B5` with ea 0x16F4B1, as `sub_4335A` does for 0x4334E.

Gates: integrity INTACT, `naming.py check` OK (2035), `verify_rebuild` faithful (REBASE 1, everything else 0), idempotent
replay (72 applied).  Functions stay at 3,586.  Backup `FALCONCD.EXE.i64.bak_reb140`.

**Still open:** the longer leftover pieces (0x100505, 0x6E7C7, 0x12BF89, 0x155F1A), the padding runs and the R30 menu
state machine.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-139): the 0x16F4B5 -> 0x16F4B1 rebase, the body pieces 0x100505 and 0x6E7C7, padding runs and the R30 menu state machine"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4o (finding 140):** `sub_16F4B5` rebased to its real prologue 0x16F4B1 (eight far callers land there); functions stay
       at 3,586; backup `.bak_reb140`.
     - Left open (findings 126-140): the longer pieces 0x100505, 0x6E7C7, 0x12BF89 and 0x155F1A, the padding runs and the R30 menu state machine""")
    b = "     - commit S1c-4n;\n"
    assert s.count(b) == 1
    return s.replace(b, "     - commit S1c-4o;\n")


def rb(s):
    a = "and 31 terminated no-xref runs registered (finding 139)"
    assert s.count(a) == 1
    return s.replace(a, a + " and one function start rebased onto its prologue (finding 140)")


edit(R + r"\docs\findings_log.md", log)
edit(R + r"\status.md", status)
edit(R + r"\docs\workflow\idb_regeneration.md", rb)
