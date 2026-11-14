def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


R = r"C:\Users\ybarnoy\projects\falcon3"
ENTRY = """
## 2026-11-10 141 - the 0x100457 switch function with its tail registered (S1c-4p)

The 153-byte run at 0x100505 (finding 139's largest leftover) was the middle of a function that nothing had registered.
Its prologue is `push bp / mov bp,sp / sub sp,14h` at 0x100457; it stores `les` pairs into the record at `[si+9A0h]`, then
switches on `ax - 400h / 400h / 800h` with three `jz` and one fall-through.  The targets are 0x1004CC, 0x1004D3 and 0x1004DA,
which all lie after the overlay stub `overlay_undecoded_body_1004bf` (0x1004BF..0x1004CA, a far-call stub reached from
0x2BFBC), so IDA saw the stub as the end of a function and left the rest as undefined bytes and orphan code.  The tail
runs to `retf 14h` at 0x10059B (the last instruction before the byte 0xC7 at 0x10059E and `sub_10059F`).  The
`jmp short` at 0x1004E2 returns to 0x1004B6 and the `jmp` at 0x1004BB reaches 0x100596, so both chunks are one flow.

It is the same shape as finding 131 (0x100CA8): a two-chunk function whose second chunk lies after a foreign function.  The
existing ADD / TAILS / ADD_CLEAR machinery takes it with no new code: main chunk 0x100457..0x1004BE (103 B, ending in the `jmp`
at 0x1004BB), tail 0x1004CC..0x10059E, seeds 0x100457, 0x1004CC, 0x1004D3, 0x1004E4 and 0x100502, and one pad byte
0x100501 (the 0xEA after the `jmp short` at 0x1004FF, which no flow reaches).  The data before it, the 0x100400..0x100456
word table, is left as bytes.  The stub, `sub_10007F`, `sub_10059F` and the stray bytes at 0x1004CB and 0x10059E are
unchanged.  The function has no callers in the IDB (it is reached through the overlay table at run time) and is unnamed
(`sub_100457`).

Applied: plan (3,586 -> 3,587, no other function changed), dry replay (1 fresh, 72 applied), backup
`FALCONCD.EXE.i64.bak_sw141`, apply.  Gates: integrity INTACT, `naming.py check` OK (2035), `verify_rebuild` faithful (ADDED
1, everything else 0), idempotent replay (73 applied).  `function_bytes.json` has the main chunk only (`sub_100457`, 103 B).

**Still open:** the longer leftover pieces 0x6E7C7, 0x12BF89 and 0x155F1A, the padding runs and the R30 menu state machine.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-140): the longer pieces 0x100505, 0x6E7C7, 0x12BF89 and 0x155F1A, the padding runs and the R30 menu state machine"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4p (finding 141):** the switch function at 0x100457 registered with its second chunk (0x1004CC..0x10059E, behind an
       overlay stub); functions 3,586 -> 3,587; backup `.bak_sw141`.
     - Left open (findings 126-141): the longer pieces 0x6E7C7, 0x12BF89 and 0x155F1A, the padding runs and the R30 menu state machine""")
    b = "     - commit S1c-4o;\n"
    assert s.count(b) == 1
    return s.replace(b, "     - commit S1c-4p;\n")


def rb(s):
    a = "and one function start rebased onto its prologue (finding 140)"
    assert s.count(a) == 1
    return s.replace(a, a + " and a two-chunk switch function added (finding 141)")


edit(R + r"\docs\findings_log.md", log)
edit(R + r"\status.md", status)
edit(R + r"\docs\workflow\idb_regeneration.md", rb)
