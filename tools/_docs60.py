"""Record finding 60 (upper-half plan P0+P1) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).

Idempotent + line-ending preserving (pattern of tools/_docs57.py).
"""
import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 60 — Upper half P0+P1: the block inventory, and the dynamic
CS->record gap root-caused (432 -> 28,264 events mapped, variant swap proven)

Records the first two steps of the plan appended to `docs/open_items.md` after
finding 59. No IDB mutation: analysis only.

### P0 -- inventory of 0x3ACAC..0x669F0 (`tools/map_upper.py`)

179,524 B in **18 anchor-delimited blocks**, only **38 functions / 4,304 B
(2.4%)** registered. Evidence is concentrated: `0x3B830..0x43AE0` 33,456 B
(89 dsts / 163 refs, 30 terminator-preceded), `0x43AE0..0x48DB0` 21,200 B
(50/93, 41 strong), `0x4F250..0x4FD20` (21/55), `0x54AF0..0x669F0` 73,472 B
(28/36 but only **1** strong -- and it is the UI/text module: `*** PAUSED ***`,
`SPEED = KNOTS`, `YOUR PLANE HAS BEEN DESTROYED!`). **Three blocks have zero
call evidence**: 1,552 B, 880 B and **18,992 B (`0x500C0..0x54AF0`)**. 263
printable runs -> **68 candidate holes / 6,278 B** (for later sha256 pinning).
8 RTLink `entry_ea`s land here (`0x3ACAC, 0x3ADAA, 0x40E54, 0x4185A, 0x4DAE0,
0x4DF94, 0x4F4A8, 0x4FD8E`). Unlike `0x2F640`, these anchors are **code-led**
-- no name tables -- so holes come from UI strings, not from block heads.
Everything lands in `analysis/ida_falconcd/upper_map.json`.

### P1 -- the missing CS->record map, root-caused

Finding 51 said dynamic `to_ida()` covered only 16 segments and 145,212 events
fell out. Two independent causes, both fixed:

1. **`tools/mine_traces.py` globbed `trace_*_{kind}.jsonl`**, so
   `debug_test_fileio.jsonl` (37 MB -- where most `indirect_far` events live)
   and its fartrans were never mined. Now `*_{kind}.jsonl`; re-mined: **5 runs,
   46 records (was 45), unstable offsets 0**.
2. **The address rule was record-relative and content-decidable**:
   `runtime CS = link-time seg + 0x1F5` (record bases *and* the `0x1F64 ->
   0x2F640` anchor both confirm it), so
   `IDA = record.ida_ea + ((cs - 0x1F5) - w0)*16 + ip`. The tempting global
   identity `IDA = (cs<<4)+ip+0xE0B0` holds for only **9 of 68** placements --
   the `s`-suffix records were re-placed by our rebuild at `0x100000+`, so the
   record-relative form is the general one.

**Variant swap:** `R05_1E10`, `R27_1E10s`, `R28_1E10s`, `R29_1E10s` all declare
`w0 = 0x1E10` -- mutually exclusive copies of one module claiming the same link
paragraphs, loaded according to scenario. Candidates are therefore disambiguated
**by content** (does a ret-like instruction END exactly at the target, checking
`ret imm16` too -- finding 59's boundary evidence reused), with loader
read-evidence as tie-break:

| CS | events | chosen | hits | alternatives |
|---|---|---|---|---|
| `0x3BEC` | 26,622 | **R29** `base 0x138230` | **2/2** | R05 0/2 |
| `0x2159` | 1,210 | **R05** `base 0x2F640` | **17/19** | R29 2/19, R28 0/19 |
| `0x2005` | 272 | **R27** (read-evidence) | 1/2 | R05/R28/R29 0/2 |
| `0x6000` | 142 | **R15** | 15/18 | R11/R12 0/18 (R14 out of range) |
| `0x5894` | 18 | **R31** | 3/3 | 28 records share this pool segment |

Re-mining independently shows **both R05 and R29 loaded at base `0x2005` in
different runs** (`record 5 segments=[0x2005, 0x2fed, ...]`, `record 29
segments=[0x2005, 0x2fb9, ...]`) -- the swap is real, not an inference.

`tools/map_runtime_segments.py` -> `analysis/traces/runtime_seg_map.json`:
**overlay events resolved 432 -> 28,264 (65x)**; unmapped **32,392 -> 4,560**,
whose residue is honest: `0188:0000` (4,469 far jumps below the image, in no
record arena) and `0x77A3` (91 calls into a 751-para heap MCB block).
`callgraph_bottomup` now consults that map first (content-proven, range-guarded
-- it refuses rather than guesses past a proved record) with the old segment
join as fallback: **dynamic_unresolved 122,263 -> 64,067**, dynamic edges
**17 -> 36**, union **4,016 -> 4,034**.

### The negative that matters for the plan

With everything mapped, **zero events (src or dst) land in
`0x3ACAC..0x669F0`**: the traced runs never exercised those modules. P1 buys
the machinery (a proven, reusable runtime->IDA map and finding 51's gap closed
for future traces), not upper-half call evidence -- so the upper half remains
a **static** job: P2's chain sweep, then P3 registration under a manifest.

Gates: `naming.py check` OK (267) . `verify_rebuild` faithful . `verify_idb`
**INTACT (0 span / 0 name / 0 data-hole problems)**. Analysis only -- the IDB
was not touched.

---

"""

ROW = ("| 2026-10-18 (session 17z) | ~2.5 h | **Finding 60: upper-half plan "
       "P0+P1 -- block inventory, and the dynamic CS->record gap root-caused "
       "(432 -> 28,264 overlay events mapped).** P0 `map_upper.py` -> "
       "`upper_map.json`: 179,524 B in **18 anchor blocks**, only 38 fns / "
       "4,304 B (2.4%); evidence concentrated (`0x3B830` 163 refs, `0x43AE0` "
       "93, `0x4F250` 55, UI block 73,472 B with 1 strong); **3 blocks with "
       "zero call evidence incl. 18,992 B**; 263 string runs -> **68 candidate "
       "holes / 6,278 B**; 8 RTLink entry_eas; anchors here are code-led (no "
       "name tables). P1: two causes -- (1) `mine_traces` globbed `trace_*` so "
       "**`debug_test_fileio.jsonl` was never mined** (now `*_{kind}`, 5 runs, "
       "**46 records**, unstable offsets 0); (2) the rule is record-relative: "
       "`runtime CS = link seg + 0x1F5`, `IDA = ida_ea + ((cs-0x1F5)-w0)*16 + "
       "ip` (the global `+0xE0B0` identity holds for only 9/68 placements "
       "because rebuild-placed `s` records sit at 0x100000+). **Variant swap "
       "found:** R05/R27/R28/R29 all declare w0=0x1E10 -- mutually exclusive "
       "copies; content (terminator-ends-at-target) disambiguates: 0x3BEC "
       "26,622 ev -> **R29** 2/2 (R05 0/2), 0x2159 1,210 -> **R05** 17/19 "
       "(R29 2/19), 0x2005 -> R27 (read tie-break), 0x6000 -> R15 15/18, "
       "0x5894 -> R31 3/3; re-mining shows **both R05 and R29 loaded at "
       "0x2005 in different runs** (corroborates the swap). `map_runtime_"
       "segments.py` -> `runtime_seg_map.json`: overlay resolved **432 -> "
       "28,264**, unmapped **32,392 -> 4,560** (residue: `0188:0000` x4469 "
       "below-image jumps + `0x77A3` x91 heap block). `callgraph_bottomup` "
       "uses it first (range-guarded, refuses to guess): **dynamic_unresolved "
       "122,263 -> 64,067**, dynamic edges 17 -> 36, union **4,016 -> 4,034**. "
       "**Negative result:** 0 events src/dst land in 0x3ACAC..0x669F0 -- no "
       "upper-half call evidence exists yet, so P2 (chain sweep) carries it. "
       "Gates green; analysis only. |")

STATUS_PARA = (
    "**Upper-half P0+P1 done (finding 60):** inventory of `0x3ACAC..0x669F0` "
    "in `upper_map.json` — 18 anchor blocks, 179,524 B, only **38 fns / 2.4%**, "
    "evidence concentrated in two blocks (163 and 93 refs) with **three blocks "
    "carrying zero call evidence (18,992 B the largest)**, 68 candidate data "
    "holes / 6,278 B from UI strings, 8 RTLink `entry_ea`s. The dynamic "
    "CS→record gap is **root-caused and closed**: `mine_traces` only ever "
    "globbed `trace_*` (the 37 MB `debug_test` dump was never mined — now 5 "
    "runs / 46 records), and the address rule is record-relative "
    "(`runtime CS = link seg + 0x1F5`, `IDA = ida_ea + ((cs−0x1F5)−w0)*16 + ip`) "
    "with **mutually exclusive variant records sharing `w0=0x1E10`** "
    "(R05/R27/R28/R29) disambiguated by terminator content — re-mining shows "
    "R05 and R29 both loaded at `0x2005` in different runs. Result: "
    "`runtime_seg_map.json` resolves **432 → 28,264** overlay events, "
    "`dynamic_unresolved` **122,263 → 64,067**, union **4,016 → 4,034**. "
    "**Honest negative: 0 dynamic events touch the upper half**, so that range "
    "still rests on P2's static chain sweep (P3 registration under a manifest, "
    "P4 measurement follow)."
)

OPEN_NEW = [
    "- **Upper-half P0+P1 DONE (finding 60):** `map_upper.py` ->",
    "  `upper_map.json` (18 blocks, 68 candidate holes / 6,278 B, 3 zero-evidence",
    "  blocks incl. 18,992 B, 8 RTLink entry_eas, anchors code-led). The dynamic",
    "  gap had two causes, both fixed: `mine_traces` globbed `trace_*` only (the",
    "  `debug_test` dump was never mined -> now 5 runs / **46 records** / unstable",
    "  offsets 0), and the mapping is **record-relative + content-decidable**",
    "  (`runtime CS = link seg + 0x1F5`; `IDA = ida_ea + ((cs-0x1F5)-w0)*16 + ip`;",
    "  the global `+0xE0B0` identity holds for only 9/68 placements). Found a",
    "  **variant swap**: R05/R27/R28/R29 all declare `w0=0x1E10`, so candidates",
    "  are decided by terminator content (0x3BEC 26,622 ev -> R29 2/2; 0x2159 ->",
    "  R05 17/19; loader read-evidence as tie-break) and re-mining independently",
    "  shows both R05 and R29 loaded at `0x2005` in different runs. Effects:",
    "  overlay events **432 -> 28,264**, unmapped **32,392 -> 4,560** (residue =",
    "  4,469 below-image `0188:0000` jumps + 91 heap-block calls),",
    "  `dynamic_unresolved` **122,263 -> 64,067**, union **4,016 -> 4,034**.",
    "  **Still open:** **0 dynamic events src-or-dst land in the upper half** --",
    "  no call evidence exists for it yet, so **P2 (chain sweep) is the",
    "  load-bearing step**, then P3 (manifest registration) and P4 (measure).",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 60" in raw:
    print("findings_log: 60 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 60 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 17z" in raw:
    print("time_log: 17z already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 17z after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Upper-half P0+P1 done (finding 60)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f60 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "P0+P1 DONE (finding 60)" in raw:
    print("open_items: already updated")
else:
    # correct the plan bullet's forward reference (P0+P1 turned out to be 60)
    raw = raw.replace("and record as\r\n  finding 60.",
                      "recorded incrementally\r\n  (P0+P1 = finding 60, P2-P4 next).")
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the P0+P1 status (%d bytes)" % len(block))
