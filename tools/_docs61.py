"""Record finding 61 (P2 chain sweep + P3 manifest registration) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving.
Also bumps status.md's "Last updated" header (protocol)."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 61 — P2+P3: the upper-half chain sweep and manifest-backed
registration — 116 new functions, `static_unresolved` 957 -> 772

Executes finding 60's plan steps P2 and P3 on the evidence-rich blocks:
`0x3B830..0x43AE0` (163 refs), `0x43AE0..0x48DB0` (93), the `0x4E520..0x4FD20`
cluster (82) and the `0x54AF0..0x669F0` UI block (36). The three zero-evidence
blocks (1,552 / 880 / **18,992 B**) were left documented-unregistered -- no
chain from an adjacent verified entry reached them.

### Step 1 -- the gate first: `REGISTER` (parentless ranges)

`verify_rebuild.py` gained a **REGISTER** class for ranges that never had a
parent function (a plain ADDED wave would otherwise sail through, as finding
54's 45 entries did). A range validates only if
`new_fns | keep_fns | data_holes` tiles `[lo,hi)` **exactly** (no gap, no
overlap) and every hole's sha256 matches the **live** export that
`verify_idb.py` writes to `data_holes.json`; before anything is applied the
range reports `pending`, so the gate stays green pre-mutation. `verify_idb`
now exports three hole kinds: **3 split + 58 register + 10 standalone = 71**,
and enforces register/standalone holes are function-free always, data-flagged
once their range is registered.

### Step 2 -- P2: forward-chain + preceding-terminator sweep (`sweep_upper.py`)

The sweep walks each gap (range minus keep fns minus holes) with these rules,
each added because a run refused to give the coverage it promised:

1. **an existing IDA decode always wins**; fresh decode only fills undefined
   bytes;
2. **`00` does not decode in this IDB**, so zero runs are skipped only when
   what follows is entry-like (`ENTRY_AFTER_PAD`) -- and only 64 bytes of it;
   leading padding becomes uncovered, padding after a terminator is attributed
   to the previous instruction (so the next boundary still counts as
   terminator-preceded);
3. a **mid-item conflict adopts IDA's item and resyncs to its end** (never
   walks backwards, never contradicts) -- this alone took block i from 12.5 KB
   to 24 KB;
4. a **stale `<=15 B` data item** (a 2-byte `dw` was blocking 19 KB of block
   ii) is stepped over; **`>=16 B` stops** the sweep unless mid-body;
5. **mid-body island bridging**: on an undecodable byte or a real data blob,
   the sweep may jump at most 64 bytes to a position where a chain **re-closes
   on a terminator** within 160 instructions (this is what unblocked block ii
   past the `0F 3C` island and took block iii to 6,143/6,144 B);
6. **seeds** (the 197 in-scope unresolved destinations + RTLink `entry_ea`s)
   become boundaries only on a sweep boundary whose previous instruction is a
   terminator -- finding 59's rule, now exact because the stream is known;
7. **emission evidence**: a piece is registered only with an accepted seed
   inside, an existing IDA code item, a chain closed on an authoritative
   keep/hole/range boundary, or *any* referenced destination inside (an
   interior call still proves code);
8. **stage 2**: self-contained chains seeded at leftover destinations
   (terminator behind + chain closes, <=4 KB) -- 2 of 94 qualified (36 had no
   terminator behind, the rest could not close); **9 suspect holes** (a sweep
   overran into them) were dropped from tiling and the plan re-run 2x.

Result: **22,240 instructions walked, 59,641 B covered**, 77 contiguous
ranges, **116 planned functions** (block i 49 / ii 36 / iii 24 / iv 7), 167
spans left uncovered (74,631 B) with stop reasons recorded.

### Step 3 -- P3: manifest, then mutate

`tools/plan_register.py` -> `registry/upper_register_expected.json`
(77 ranges, 116 new + 24 keep fns, **68 pinned holes / 6,278 B** -- all of
them, including the 10 outside any range, so `YOUR PLANE HAS BEEN
DESTROYED!` and friends are protected). The generator refuses to write on any
tiling gap/overlap, duplicate key, drifted keep function or missing hash.
Then `tools/register_upper.py` (backup `FALCONCD.EXE.i64.bak_upper`):
preconditions checked (pre-state == keep for all 77 ranges, all 68 hashes
match) -> 58 holes converted to data (sha re-verified after conversion) ->
**116 functions registered, 19,289 instructions created** (only where no item
existed) -> guards: spans match plan, ranges still tile, holes byte-identical
and function-free, heads/code-refs never decreased -> **guards PASSED, SAVED**.

### Measured effect

| metric | f60 | f61 |
|---|---|---|
| functions | 1,935 | **2,051** (+116) |
| static edges | 4,013 | **4,907 (+894)** |
| `static_unresolved` | 957 | **772 (-185)** |
| union | 4,034 | 4,928 |
| code refs | 9,244 | 10,917 (**+1,673 revealed**) |
| new fns with >=1 incoming edge | - | **107 / 116** |
| overlay zero-indegree orphans | 226 | 234 (+8 uncalled pieces) |

The drop decomposes exactly: **957 - 291 (in-scope destinations now inside a
function: 153 of 197 dsts) + 106 (refs revealed by the new instructions whose
destination is still outside every function) = 772**. Per block: i 49 fns /
24,675 B, ii 36 / 19,028, iii 24 / 5,908, iv 7 / 1,262 plus 5,263 B of pinned
strings; 44 in-scope dsts (83 refs) remain unresolved inside the stops
(data, undecodable, chains that never close), and 318 dsts / 583 refs are
outside the four scope blocks.

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- REGISTER 18
applied / 59 pending (hole-only ranges), ADDED 116 all manifest-planned, LOST
0, CHANGED 0** . `verify_idb` **INTACT (2,051, 0 span / 0 name / 0 data-hole
problems)** . read-back **265/265 + 2/2**. Backup `FALCONCD.EXE.i64.bak_upper`.

Impact: the upper half went from **38 functions / 2.4% coverage to 154
functions / ~35% of its bytes inside registered ranges** (59,641 B covered +
3,505 B keep), the zero-evidence blocks were deliberately left alone, and the
REGISTER gate now makes any future parentless registration exact-match
instead of a free ADDED wave. Remaining: the 44 in-scope stragglers, the
`0x54AF0` UI block's data-dominated gaps, and 74,631 B of documented
uncovered scope.

---

"""

ROW = ("| 2026-10-18 (session 18) | ~4 h | **Finding 61: P2 chain sweep + P3 "
       "manifest registration in the R05 upper half -- 116 new functions, "
       "`static_unresolved` 957 -> 772.** Gate first: `verify_rebuild` gained "
       "**REGISTER** for parentless ranges (exact tiling of new_fns | keep | "
       "data_holes + live hole sha256 from `verify_idb`'s export; reports "
       "`pending` pre-mutation; export now covers 3 split + 58 register + 10 "
       "standalone = 71 holes). P2 `sweep_upper.py`: existing decode wins; "
       "`00` never decodes here so zero runs are skipped only before "
       "entry-like code; mid-item conflicts adopt IDA and resync (block i "
       "12.5 -> 24 KB); stale <=15B data items stepped over (a 2B `dw` had "
       "blocked 19 KB of block ii); **mid-body islands bridged <=64 B only "
       "when a chain re-closes on a terminator** (unblocked block ii past "
       "`0F 3C`, took iii to 6,143/6,144); seeds (197 in-scope dsts + RTLink "
       "entries) become boundaries only on terminator-preceded sweep "
       "boundaries; emission needs seed/IDA-item/closed-boundary/any-ref "
       "evidence; stage-2 self-contained chains added only 2 (36 lacked a "
       "terminator behind); 9 suspect holes dropped + plan re-run twice. "
       "Walked **22,240 insns / 59,641 B**, plan = 77 ranges / 116 fns. P3: "
       "`plan_register.py` -> `upper_register_expected.json` (116 new + 24 "
       "keep, **68 pinned holes / 6,278 B**, refuses on any tiling/hash "
       "problem) -> `register_upper.py`: preconditions (pre-state == keep, "
       "68/68 hashes) -> 58 holes converted (sha re-checked) -> 116 fns + "
       "**19,289 instructions created** -> guards PASSED -> **SAVED**. "
       "Effect: fns **1,935 -> 2,051**, static **4,013 -> 4,907 (+894)**, "
       "**`static_unresolved` 957 -> 772** (exact: -291 in-scope dsts now "
       "registered +106 new refs still outside), refs 9,244 -> 10,917 (+1,673 "
       "revealed), 107/116 new fns already called, orphans 226 -> 234, "
       "zero-evidence blocks untouched. Gates: check 267, verify_rebuild "
       "faithful (REGISTER 18 applied / 59 pending, ADDED 116 planned), "
       "verify_idb INTACT 2051 / 0 hole problems, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**Upper half registered (finding 61):** P2's chain sweep (`sweep_upper.py`) "
    "walked **22,240 instructions / 59,641 B** across the four evidence-rich "
    "blocks under strict rules -- existing IDA decodes always win, `00` runs "
    "only skip before entry-like code, mid-item conflicts resync instead of "
    "stopping, stale `<=15 B` data items step over, mid-body islands bridge "
    "only when a chain re-closes on a terminator, and no piece is emitted "
    "without evidence (seed / existing code item / closed boundary / any "
    "referenced dst). P3 then registered it behind the new **REGISTER** gate: "
    "`registry/upper_register_expected.json` pins **116 new functions + 24 "
    "kept + 68 data holes (6,278 B)** with exact tiling and live sha256, and "
    "the mutator (`register_upper.py`) converted the holes, created 19,289 "
    "instructions only where none existed, and saved only with every guard "
    "green. Outcome: functions **1,935 -> 2,051**, static edges **4,013 -> "
    "4,907**, **`static_unresolved` 957 -> 772** (957 - 291 in-scope "
    "destinations now registered + 106 newly revealed refs still outside), "
    "107/116 new functions already have callers. Zero-evidence blocks "
    "(1,552 / 880 / 18,992 B) deliberately untouched; 44 in-scope dsts (83 "
    "refs) remain inside documented stops."
)

OPEN_NEW = [
    "- **Upper-half P2+P3 DONE (finding 61):** 116 functions registered over",
    "  77 manifest ranges (i 49 fns/24,675 B, ii 36/19,028, iii 24/5,908, iv",
    "  7/1,262 + 5,263 B pinned strings), **68 holes / 6,278 B sha256-pinned**",
    "  (58 in-range + 10 standalone) via the new **REGISTER** gate (exact",
    "  tiling + live hole export; `pending` before, `applied` after). Sweep",
    "  walked 22,240 insns / 59,641 B; static **4,013 -> 4,907** and",
    "  **`static_unresolved` 957 -> 772** (exactly -291 in-scope dsts now",
    "  registered +106 newly revealed refs still outside); 107/116 new fns",
    "  called; zero-evidence blocks (1,552 / 880 / 18,992 B) untouched by",
    "  design. **Still open:** (a) 44 in-scope dsts / 83 refs sit in",
    "  documented stops (data, undecodable, chains that never close); (b) the",
    "  UI block `0x54AF0..0x669F0` is data-dominated: only 6,525 B of 73,472",
    "  covered, 7 fns -- its 67 string gaps are pinned but its code islands",
    "  mostly fail the entry-after-padding test; (c) 74,631 B of scope stays",
    "  uncovered with stop reasons in `upper_sweep.json`; (d) out-of-scope",
    "  residue: 318 dsts / 583 refs plus blocks `0x493C0..0x4E520`,",
    "  `0x4FD20..0x500C0`.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 61" in raw:
    print("findings_log: 61 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 61 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 18)" in raw:
    print("time_log: session 18 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted session 18 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Upper half registered (finding 61)" in raw:
    print("status: already updated")
else:
    hdr_old = "**Last updated**: 2026-10-17 (session 17 - see Time Log; always bump + append row)"
    hdr_new = "**Last updated**: 2026-10-18 (session 18 - see Time Log; always bump + append row)"
    if hdr_old in raw:
        raw = raw.replace(hdr_old, hdr_new, 1)
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: bumped header + inserted f61 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "P2+P3 DONE (finding 61)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the P2+P3 status (%d bytes)" % len(block))
