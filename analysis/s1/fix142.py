p = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
s = open(p, newline="", encoding="utf-8").read().replace("\r\n", "\n")
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("""the real code starts at 0x12BF96: `add [bp+si+35Ch],cl` was in fact `06 00 8a 5c 03` = `push es / ... mov bl,[si+3]`
(`xor bh,bh / shl bx,1 / cmp bx,0Ch / ja / call cs:off_12BF2A[bx] / retn`), an 18-byte dispatcher that ends at the `retn`
0x12BFA7.""", """the real code starts at 0x12BF96: the word 0x0006 at 0x12BF94 is the last table entry, and `8a 5c 03` is `mov bl,[si+3]`
(then `xor bh,bh / shl bx,1 / cmp bx,0Ch / ja / call cs:off_12BF2A[bx] / retn`), an 18-byte dispatcher that ends at the `retn`
0x12BFA7 (the `ja` and the table entries 0x0DB7 point at it).""")
rep("""Both are orphan code with no xref in; the second is reached by the
`jz` fall-through of nothing, so it too is an entry nothing calls directly.""", """Both are orphan code with no xref to their first byte (they are reached through overlay or vector tables at run time).""")
rep("""The table of far pointers behind 0x155F00 left the last two bytes of table (`32 ff`, the end of a word) just before
the code; the real entry is 0x155F18 (`xor bh,bh` = `32 ff`, then `cmp bx,6 / jge / shl bx,1 / shl bx,1 / jmp dword ptr
cs:[bx+1240h]`, `retn`).  So the function starts two bytes earlier than the orphan run.""", """The orphan run began at `cmp bx,6` (0x155F1A), but the two bytes before it, `32 ff` = `xor bh,bh`, were left as data
bytes at the end of the far-pointer table behind 0x155F00; the real entry is 0x155F18 (`xor bh,bh / cmp bx,6 / jge / shl bx,1 /
shl bx,1 / jmp dword ptr cs:[bx+1240h]`, `retn`).  So the function starts two bytes earlier than the orphan run.""")
rep("""It ends in a `retn` at 0x155F4B, no call into it exists, and it is registered as
a plain ADD (the `FALL` set records that the end 0x155F4C is `nullsub_27`, not a terminator inside the run).""", """Its last instruction is `inc cs:word_155EFB` at 0x155F47, which falls into the one-byte `nullsub_27` (`retn`, 0x155F4C), so
the run does not end in a terminator; the new `FALL` set lets the plan accept that.  No call into it exists.""")
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n"))
