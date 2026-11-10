import io
p = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
s = io.open(p, "r", newline="", encoding="utf-8").read()


def sub(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


sub("them are not clean function bodies: 0x106EE2 / 0x108430 start 3-4 bytes before an existing function",
    "them are not clean function bodies: 0x106EE2 / 0x108430 start 10 / 13 bytes before an existing function")
sub("bytes are inside a `mov dx,imm` operand, i.e. a misdecode, not an entry); 0x109445 is a self-modified `mov ax,0ABCDh`",
    "bytes are inside a `db 0BAh` / `mov dx,imm` operand, so the existing start looks like a mid-instruction entry); 0x109445 is a self-modified `mov ax,0ABCDh`")
sub("block that runs into the existing 0x109519; 0x10CE30 runs 373 B into the existing 0x10CFA6.  These need the",
    "block whose flow reaches the existing 0x109519; 0x10CE30 is 373 B ending right before the existing 0x10CFA6.  These need the")
io.open(p, "w", newline="", encoding="utf-8").write(s)
print("ok")
