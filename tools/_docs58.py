"""Record finding 58 in docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md and docs/open_items.md (CRLF).

Idempotent + line-ending preserving (same pattern as tools/_docs57.py).
"""
import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 58 — The unresolved destinations audited: 78% are frameless
code, zero are pointer variables — and `sub_2E2F0`'s carve map, with the
correction finding 57's anchor heuristic needed

Read-only inspection (no IDB mutation) of everything finding 57 left
unresolved, plus the boundary map required before any split.

### Step 1 — the worklist is 515 destinations, not 233

Finding 57's "449 refs -> 233 addresses" was only the *retargeted* subset.
Counting properly (`tools/dst_list.py`): **957 unresolved refs -> 515 distinct
destinations**, 87 resident / 428 overlay, of which **251 (446 refs) sit in
`R05_1E10`'s upper half `0x3ACAC..0x669F0`** — the region where most of the
"outside-any-function" fixups landed. Only 1 of the 515 lies inside
`sub_2E2F0`'s span... none do: every ref into that blob resolves, which is why
they never appeared in this backlog.

### Step 2 — fresh IDA decode, read-only, and one trap

`tools/audit_dsts.py` decodes each address with `ida_ua.decode_insn` and takes
the mnemonic from **`insn.get_canon_mnem()`** (the `idc` helper returns `""`
for addresses that have no IDB item — i.e. most of them — and
`ida_idp.get_insn_name` does not exist in 9.1), sweeps backwards up to 6 bytes
for an instruction that lands exactly on the target (a terminator there is a
strong entry signal), and records every source's mnemonic, operand type and
operand text. No items created, no `auto_wait`, no save.
**Trap:** a throwaway API probe was written *without* `idaapi.qexit(0)`, so IDA
finished its auto-analysis pass and rewrote the IDB (file +65 KB).
`verify_idb.py` was run immediately: **INTACT — 1,678 functions, 0 span
mismatch, 0 name mismatch**. Every diagnostic now quits explicitly.

### Step 3 — classification of the 515

| class | dsts | refs | verdict |
|---|---|---|---|
| **(a) frameless ASM / unregistered code** | **401** | **750 (78%)** | decodes from the address to `retf` 153 / `jmp` 188 / `retn` 60 |
| **(b) indexed jump-table case targets** | 30 | 36 (4%) | `jmp/call cs:off_X[bx]` (o_displ) — dispatch handlers, also code |
| **(c) anomaly / data / truncated** | 84 | 171 (18%) | 49 first-byte-undecodable, 28 code >512 B without terminator, 7 no segment |

**(a) — yes, the prologue filter is why they were rejected:** only **12/401**
start with `55 8B EC`/`C8`. First mnemonics are `push` 126, `mov` 79, `add` 33,
`cmp` 30, `call` 14, `enter` 7, `pusha` 4. **196/401 carry a strong entry
signal** (previous instruction is a terminator, or the previous function ends
exactly there); 100 start like a mid-body, 105 are weak. IDA holds a name for
371 of them (`unk_` 298, `loc_` 70) but only **70 are code items**.

**(b) the pointer-variable hypothesis is refuted:** **0 of 515** are `FF 1E` /
`FF 2E` pointer words. Every source is an indexed `jmp/call cs:off_X[bx]`, and
the mapping is exact — all 12 destinations of `jmp cs:off_149D2[bx]` @ `0x149CD`
are `table_word + 0x11BA0` (12/12, the paragraph base of that segment), and
29/30 decode to a terminator. They are switch **case handlers**.

**(c) the two hottest are genuinely data and are *not* finding 57's fault:**
`0x6E1EA` x24 sits **inside the ASCII string `"WRONG VERSION!"`**, `0x6DFF0` x23
is a **word table** (`9d 00 aa 00 c0 00…`); both were unresolved before finding
57. Of f57's 233 retargeted addresses: **209 -> (a), 24 -> (c), 0 -> (b)**.

### Step 4 — `sub_2E2F0` map (and a correction to finding 57)

`tools/map_sub2e2f0.py` reads the fixup tables straight out of
`FALCONCD.EXE` (same location logic as `_size57.py`), so the anchors are the
real `(seg-w0)*16` values, not buckets:

- **24 anchors in `R05_1E10` = 1 at the segment base `0x2E100` + 6 inside
  `sub_2E2F0` + 17 in the upper half.** In-blob: `0x2EA10` x58 fixups,
  `0x2EFE0` x18, `0x2F400` x19, `0x2F590` x4, **`0x2F640` x1,442**, `0x3AB90`
  x15. **Correction:** finding 57 reported "13 sub-block anchors" — that was a
  4 KB bucket heuristic; the true count inside the function is **6** (24 in the
  segment matches finding 56 exactly).
- **Refs: 1,053 -> 596 distinct destinations, 0 at a function start**: 696
  `CALL` from inside the blob, 275 `JMP` from inside, 71 `CALL` from other
  functions (**22 distinct addresses**), 10 `JMP` through a thunk slot, 1 `JMP`
  from a function. Today **all 971 internal refs collapse to
  `sub_2E2F0 -> sub_2E2F0` and are dropped by the `s != d` rule** — the graph
  currently has no internal structure at all.
- **Entry seeds for a carve: 371** (343 targets of internal `CALL`s + 22
  external + 10 thunk); the remaining 225 destinations are branch-only labels.
  Two of the thunk seeds (`0x2E380`, `0x2E6C6`) are exactly finding 42's "MID
  targets" that `docs/open_items.md` called unexplained.
- **Data is tiny: 3 holes / 239 B** — `0x2EA10..0x2EA6D` (93 B: `OBJECTS`,
  `FalcObj.Bin`, `FSXObj.Bin`), `0x2F640..0x2F6D0` (144 B: `global.amo`,
  `local.amo`, `harpoon.dat`, `FALCONCOLORADO`; the first code word after it,
  `0x2F6D0`, is a thunk target), `0x3AB90..0x3AB92` (2 B). All 7 NUL-terminated
  strings (72 B) live inside those holes.
- **7 anchor-delimited blocks:** 1,824 / 1,488 / 1,056 / 400 / 176 /
  **46,416** / 284 B — anchors are module-level, so the 46 KB block must be cut
  on the 371 seeds, not on anchors alone.
- **Upper half:** 251 of the 515 unresolved destinations and **1,934 of 3,529**
  R05 fixup pairs live in `0x3ACAC..0x669F0` — that is where registration work
  goes next, and it is a *registration* problem, not a split.

### The gate has to be built before the carve

`verify_rebuild`'s `SPLIT` requires the old range to be tiled 100% by
functions, which would force 239 bytes of tables to become functions. Proposed
`registry/subblock_split_expected.json`, per old key: `{ea, old_size,
old_sha256, data_holes[{ea, size, sha256, why}], new_fns[{key, ea, size}]}`.
Accept a shrunk key **only if** `new_fns ∪ data_holes` tiles the old span with
no gap and no overlap, **every hole's current bytes still hash to its recorded
sha256** (holes may never be edited), and each new function's `(ea, size)`
matches; everything else stays `CHANGED` -> exit 1. Class name: `SPLIT` with
holes, or `SPLITDATA`.

### Carve plan (ordered, boundaries not guessed)

1. Seed at the 371 candidates; accept a start only when it is preceded by a
   terminator or by nothing (finding 33's retf rule, extended for frameless
   bodies by walking back <=6 B); every one of the 596 destinations must end up
   either a function start or interior of a seeded block.
2. `create_data` on the 3 holes after a decode confirms they are not code.
3. Split the 46 KB block at the seeds; unseeded code attaches to the preceding
   block unless a terminator separates it.
4. Payoff to measure: up to **971 internal refs become visible edges** for the
   first time, and the 72 external ones gain precise callees.

Gates: `naming.py check` OK (267) . `verify_rebuild` faithful . `verify_idb`
**INTACT (1,678, 0 span / 0 name mismatch)** . read-back 265/265 + 2/2.
Analysis only — the IDB was not modified by this finding (the one auto-analysis
rewrite was verified byte-identical in span/name terms and is now prevented by
`qexit`).

---

"""

ROW = ("| 2026-10-18 (session 17x) | ~2 h | **Finding 58: audited every "
       "unresolved destination (read-only) and mapped `sub_2E2F0`'s carve "
       "boundaries.** Worklist **957 refs -> 515 distinct dsts** (f57's 233 "
       "was only the retargeted subset; 251 of them / 446 refs sit in R05's "
       "upper half 0x3ACAC..0x669F0, where 1,934/3,529 R05 fixup pairs land). "
       "IDA-side fresh decode (`audit_dsts.py`: `insn.get_canon_mnem` + "
       "backward terminator sweep + source operand types; no items created): "
       "**(a) 401 dsts / 750 refs (78%) = frameless code** ending retf 153 / "
       "jmp 188 / retn 60, only **12/401** have `55 8B EC`/`C8` (so a prologue "
       "filter rejects the rest), 196 preceded by a terminator; **(b) 30 dsts "
       "= indexed jump-table case targets** (`jmp/call cs:off_X[bx]` -- "
       "verified 12/12 as table_word + para base 0x11BA0) -- **0 "
       "FF 1E/FF 2E pointer variables**; **(c) 84 dsts = 49 undecodable + 28 "
       "long-code + 7 no-segment**, incl. `0x6E1EA` x24 inside the ASCII "
       "string `WRONG VERSION!` and `0x6DFF0` x23 = a word table (both "
       "pre-existing, not f57's). `map_sub2e2f0.py`: **24 anchors in R05 = 1 "
       "base + 6 inside the blob + 17 upper half** -- corrects f57's \"13 "
       "anchors\" (that was a 4KB bucket heuristic); blob refs 1,053 = 696 "
       "internal CALL + 275 internal JMP (**all dropped today by the `s != d` "
       "rule**) + 71 external calls (22 addrs) + 10 thunk, **0 at a function "
       "start**; **371 entry seeds**; data = **3 holes / 239 B** (object table "
       "93 B, name table 144 B, pad 2 B); 7 anchor blocks of "
       "1824/1488/1056/400/176/**46416**/284 B. **Trap:** a probe without "
       "`qexit(0)` let auto-analysis rewrite the IDB -> verified **INTACT** "
       "immediately, diagnostics now always quit. Gate designed before "
       "cutting: `registry/subblock_split_expected.json` = old span + data "
       "holes (sha256 pinned) + new fns, accepted only when they tile exactly. "
       "Analysis only; gates green. |")

STATUS_PARA = (
    "**Unresolved-destination audit (finding 58, read-only):** the "
    "`static_unresolved = 957` backlog is **515 distinct destinations**, "
    "each freshly decoded in IDA: **401 dsts / 750 refs (78%) are frameless "
    "16-bit code** ending `retf`/`jmp`/`retn` — only **12/401** carry the "
    "strict `55 8B EC`/`C8` prologue that the step-3 guards required, 196 sit "
    "right after a terminator; **30 are indexed jump-table case targets** "
    "(`jmp/call cs:off_X[bx]`, mapped 12/12 onto table words + paragraph base "
    "`0x11BA0`) — **zero `FF 1E`/`FF 2E` pointer-variable refs exist**; "
    "**84 are anomalies** (49 undecodable-first-byte — including `0x6E1EA` x24 "
    "which is *inside* the ASCII string `WRONG VERSION!` and `0x6DFF0` x23 "
    "which is a word table — 28 long code without a terminator, 7 with no "
    "segment). **`sub_2E2F0` is now mapped, not guessed:** 24 anchors in "
    "`R05_1E10` = 1 segment base + **6 inside the blob** + 17 in the upper "
    "half (correcting finding 57's `13 sub-block anchors`, which was a 4 KB "
    "bucket heuristic); 1,053 refs into the blob = **971 internal, all dropped "
    "today by the `s != d` rule**, + 71 external calls over 22 addresses + 10 "
    "thunk; **371 entry seeds**; data is only **3 holes / 239 B**; 7 blocks "
    "whose largest is 46,416 B. The split waits on a new `verify_rebuild` "
    "class: a manifest whose `new_fns ∪ data_holes` tiles the old span exactly "
    "and whose holes keep their sha256, or it is `CHANGED`."
)

OPEN_NEW = [
    "   **(e) RESOLVED BY CLASSIFICATION (finding 58):** the 957 unresolved",
    "   refs = **515 distinct dsts = 401 frameless-code (registerable; only",
    "   12/401 pass a strict prologue test, 196 are preceded by a terminator)",
    "   + 30 jump-table case targets + 84 anomalies** (49 undecodable incl. the",
    "   `WRONG VERSION!` string at `0x6E1EA` x24 and a word table at `0x6DFF0`",
    "   x23, 28 long-code-no-terminator, 7 no-segment); 251 of the 515 sit in",
    "   `0x3ACAC..0x669F0`; (f) `sub_2E2F0` is **mapped, not guessed**: **6**",
    "   anchors inside (not f57's 4 KB-bucket \"13\"), 7 blocks of",
    "   1824/1488/1056/400/176/**46,416**/284 B, **371 entry seeds** (343",
    "   internal-CALL + 22 external + 10 thunk), data = **3 holes / 239 B**;",
    "   **971 internal refs are invisible today** because `sub_2E2F0 ->",
    "   sub_2E2F0` self-edges are dropped — and the carve is **blocked on the",
    "   gate first**: `verify_rebuild` must accept a manifest whose",
    "   `new_fns ∪ data_holes` tiles the old span exactly and whose holes keep",
    "   their recorded sha256 (else it is `CHANGED`);",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 58" in raw:
    print("findings_log: 58 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 58 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 17x" in raw:
    print("time_log: 17x already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 17x after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Unresolved-destination audit (finding 58" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    raw = load(p)
    old = ("1,053 interior refs across 13 sub-block anchors, none at a "
           "function start")
    assert old in raw, "f57 anchor phrase not found"
    save(p, raw.replace(
        old,
        "1,053 interior refs across 13 4 KB buckets = exactly 6 sub-block "
        "anchors (finding 58), none at a function start"))
    print("status: inserted f58 para + corrected the f57 anchor count")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "RESOLVED BY CLASSIFICATION (finding 58)" in raw:
    print("open_items: already updated")
else:
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines) if "(e) `static_unresolved`" in l)
    end = next(i for i in range(start, len(lines))
               if "turn those into real edges;" in lines[i])
    cr = "\r" if lines[start].endswith("\r") else ""
    lines[start:end + 1] = [x + cr for x in OPEN_NEW]
    save(p, "\n".join(lines))
    print("open_items: replaced (e)/(f) with %d lines" % len(OPEN_NEW))
