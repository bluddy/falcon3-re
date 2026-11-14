p = "doc139.py"
s = open(p, encoding="utf-8").read()
a = s.index("**What was registered.**")
b = s.index("**Applied.**")
new = '''**What was registered.**  The no-xref runs that end in `retn` / `retf` / `iret` or a near `jmp` out of the run, split at each
such terminator (a `jmp` back into the run is not a terminator): 26 runs became 31 functions.  By kind: 0x1002C..0x1005A
(46 B, a handler that saves registers, calls `int 33h` fn 3 and two far stubs, ends `popf / retf`); one-line `cs:` getters
at 0x10473, 0x105DC, 0x10C7E, 0x205BA, 0x22564 and 0x229BB; far-return wrappers around a single call at 0x11B90, 0x13A53,
0x21ABA, 0x23F5E, 0x2408B, 0x2B131, 0x2551C, 0x25893 and 0x25899 (the last three call through cs: vectors); 0x11D16
(`lds si,[bp+6]` wrapper, 21 B); 0x20613, 0x20889 and 0x25562 (a cs: store, then a call or `retf`); 0x229C8 and 0x229D1
(two entries in one run); 0x22AEB (`push sp / pop ax` CPU check, `iret`); 0x23E25 and 0x23E37 (two vector-subtract entries
that tail-jump to `fixed_vec_normalize_7b0e`); 0x24963 and 0x24970 (div / mul by 5A0h); 0x2CA17 (40 B, restores the
vector words at es:0Ah / 0Ch under `cli`); 0x2CB72 and 0x2CB76 (`mov cx,-1; retf` and `xor ax,ax; mov dx,ax; retf`) and
0x12D15E (`repne scasb ... repe cmpsb`, 16 B).  All are unnamed (`sub_XXXX`) and plain `ADD` entries (no clear, no tails).

**Left alone, on purpose (116 runs, 663 B).**  92 are 1- or 2-byte pieces (43 x 1 B, 49 x 2 B): alignment padding and
`add [bx+si],al` filler, including the `retf` pairs at 0x170F9, 0x172DA, 0x10852 and 0x22269.  24 are 3 bytes or longer:
0x100505 (153 B, a body that ends in `retf 14h` with no prologue in the run), 0x6E7C7 (66 B, starts with misdecoded bytes,
so the real start is a byte or two earlier), 0x12BF89 (88 B, table data and misdecoded bytes before the code, four xrefs),
0x155f1a (50 B), 0x1982F (20 B), 0x1277CC (14 B), 0x6EA3B (14 B), 0x5DA68 (13 B) and 15 shorter ones (3-10 B) that look like
data or loose fragments.  0x67BA3 is a switch default `jmp` inside the R30 state machine, 0x67F77 its `add bx,ax`, 0x6E16E is
data, 0x6DFF0 is the `popf` the RTFIX patch writes (four far-call xrefs from 0x6Exxx).  0x16F4B1 (4 B, `push bp / mov bp,sp /
push si`) is the prologue of `sub_16F4B5`, which IDA started three bytes late; its eight far-call xrefs land on 0x16F4B1,
so it is a rebase, not an add.  Only five of the 142 runs have an xref (0x12BF89, 0x6E16E, 0x16F4B1, 0x67F77, 0x6DFF0).

'''
s = s[:a] + new + s[b:]
s = s.replace("the rebase of 0x16F4B5 to 0x16F4B1 and the two body pieces 0x100505 / 0x6E7C7, then the padding runs and\nthe R30 menu state machine.",
              "the rebase of 0x16F4B5 to 0x16F4B1, the longer pieces (0x100505, 0x6E7C7, 0x12BF89, 0x155F1A), the padding runs and\nthe R30 menu state machine.")
s = s.replace("142 unowned code runs (1,020 B) were\n       left before it; 105 are 1-2 byte padding.",
              "142 unowned code runs (1,020 B) were\n       found; 116 (663 B) remain, 92 of them 1-2 byte padding.")
open(p, "w", encoding="utf-8").write(s)
