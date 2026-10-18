"""Record finding 62 (finish the R05_1E10 sweep + classify remaining
unresolved) in docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 62 — The R05_1E10 sweep is finished: 82 more functions,
`static_unresolved` 772 -> 660, and the block-iv anomaly diagnosed

Finding 61 left the four evidence-rich blocks registered and the rest of
`R05_1E10` (the lower `0x3ACAC..0x3B830` tail, the `0x48DB0..0x4FD20` run,
the `0x4FD20..0x500C0` tail, and the untouched `0x500C0..0x54AF0`) pending a
recount. This session ran that recount, swept every remaining evidence-bearing
block, registered the result, and diagnosed why the `0x54AF0` UI block yielded
only 7 functions.

### Step 1 -- the post-f61 recount

Re-running `dst_list.py` against the finding-61 refs: **415 destinations /
772 refs** (was 515/957). The **13 other anchor blocks** of `0x3ACAC..0x669F0`
carry **26,260 B / 83 dsts / 130 refs** now (the recount moved some evidence:
the previously zero-evidence `0x48DB0..0x493C0` gained **4 dsts / 10 refs**
from a newly revealed reference, so it enters scope per the standing rule;
`0x4DAD0..0x4DE40` and `0x500C0..0x54AF0` remain at 0 and stay out).

### Step 2 -- sweep + register the remaining evidence-bearing blocks

`register_scope.json` now lists **12 blocks / 26,260 B** (unioned with the
finding-61 four = 16 scope blocks total, 0x3ACAC..0x669F0 minus the two
untouched zero-evidence blocks). The same
`sweep_upper.py -> plan_register.py -> register_upper.py` pass ran, with two
findings:

1. **a gap may start on a small data item.** `blk_4FD20` starts on a 2-byte
   `word_4FD48`; the sweep's small-data skip advanced `cur` but not
   `gap_start`, so the planned function `0x4FD48..0x4FD80` began on a data
   byte and `add_func` refused the whole range. Fixed: when a gap *starts* on
   a `<=15 B` data item, move `gap_start` past it and record it as
   lead-padding (the range split cleanly into `0x4FD20..0x4FD38` keep +
   `0x4FD4A..0x4FD80` new).
2. **suspect holes must not be enforced.** The sweep dropped 10 holes it had
   overrun into (`0x4aca1`, `0x5a33b`, ... `0x5c04d`) from tiling, but they
   stayed in `all_holes` and flowed into `standalone_holes`, where the mutator
   required `sha256 + not in function`. A guard-failed attempt then left a
   dirty DB (idat persists on exit) that covered `0x4ACA1`. Fixed in
   `plan_register.py`: suspects are recorded (`suspect_holes_not_enforced`)
   but never enforced, and `register_upper.py` became **idempotent** (pre-state
   accepts `keep` *or* `keep+new`; already-converted holes and already-added
   functions are skipped), so the re-run after the guard was a no-op that
   passed and saved.

Result: **96 ranges, 82 new functions, 58 in-range holes converted, 8,727
instructions created; guards PASSED, SAVED** (backup `FALCONCD.EXE.i64.bak_upper2`).

### Measured effect

| metric | f61 | f62 |
|---|---|---|
| functions | 2,051 | **2,133** (+82) |
| static edges | 4,907 | **5,289 (+382)** |
| `static_unresolved` | 772 | **660 (-112)** |
| union | 4,928 | 5,310 |
| new fns with >=1 incoming edge | - | **76 / 82** |
| overlay zero-indegree orphans | 234 | 238 |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- REGISTER 19
applied / 77 pending, ADDED 82 all manifest-planned, LOST 0, CHANGED 0** .
`verify_idb` **INTACT (2,133, 0 span / 0 name / 0 data-hole problems)** .
read-back **265/265 + 2/2**.

### Step 3 -- diagnose the remaining 660 unresolved

**Block `iv` (`0x54AF0..0x669F0`, 73,472 B, only 7 fns):** 28 dsts / 36 refs
remain. The forward sweep from the anchor dies at `pad-then-nonentry` /
`undecodable` / `zero-run` ~40 times because between the 7 functions sit
**binary UI/struct tables**, not `00` padding. **Stage-2 (cap raised 4 KB ->
16 KB) rejects all 27 attempts: 26 have no terminator behind them**, and the
one that does (`0x5DF97`, `prev=jmp`) sits inside an already-covered range
whose piece was rejected for no other evidence. Finding-58's audit agrees:
**27 of 28 are class-c anomalies with no terminator behind** — so these are
*not* clean functions separated by tables; the destinations themselves are
mid-instruction / data points, and only a handful of genuine functions exist
in the block (which the 7 registered).

**Residency of the remaining 660 (347 dsts):**

| zone | dsts | refs |
|---|---|---|
| **Resident `0x10000..0x2CF60`** | **93** | **236** |
| **other `R*` overlays** | **254** | **424** |
| — `R05_1E10` (in-scope stops + carved region) | 79 | 109 |
| — `R30_569F` | 71 | - |
| — `R06_5CD9` | 25 | - |
| — `R53_569Fs` / `R14_5E0B` / `R17_5E8F` / `R35_569Fs` | 16/14/12/12 | - |
| carved region `0x2E2F0..0x3ACAC` | 4 | 12 |
| untouched zero block `0x500C0..0x54AF0` | **0** | **0** |

The **in-scope residue is 63 dsts / 109 refs** — all in the sweep's documented
stops (the 40 `pad-then-nonentry` / `undecodable` / `zero-run` in block iv,
plus anomalies like `0x43E0C` ×16 which is class-c undecodable in block ii).
The bulk of the remainder (**93 resident + 254 other-overlay**) is outside
`R05_1E10` entirely: resident needs the same treatment as finding 54's
registration pass, and the `R*` overlays (`R30_569F` 71 dsts, `R06_5CD9` 25,
etc.) are the next registration targets (they are separate RTLink records
already mapped by finding 60's runtime map).

---

"""

ROW = ("| 2026-10-18 (session 18b) | ~3 h | **Finding 62: finished the "
       "`R05_1E10` sweep + registered 82 more fns; `static_unresolved` 772 -> "
       "660.** Post-f61 recount: **415 dsts / 772 refs**; 13 remaining "
       "evidence blocks = 26,260 B / 83 dsts / 130 refs; the previously "
       "zero-evidence `0x48DB0..0x493C0` **gained 4 dsts / 10 refs** from a "
       "newly revealed ref (per rule: include; the other two zero blocks stay "
       "out). `register_scope.json` = 12 blocks unioned with f61's four = 16 "
       "scope blocks. Sweep -> plan -> register ran with two fixes: (1) a gap "
       "starting on a small data item now moves `gap_start` past it "
       "(`0x4FD48` word made `add_func` refuse `blk_4FD20` -> range split "
       "cleanly), (2) suspect holes are recorded but **not enforced** "
       "(`0x4aca1` was in standalone and a guard-failed run's dirty DB covered "
       "it; plan_register now excludes suspects, register_upper is "
       "**idempotent**: pre-state accepts keep OR keep+new, holes/fns skip if "
       "already done). Registered: **96 ranges, 82 fns, 58 holes, 8,727 "
       "insns, guards PASSED, SAVED** (`.bak_upper2`). Effect: fns "
       "**2,051 -> 2,133**, static **4,907 -> 5,289 (+382)**, "
       "**`static_unresolved` 772 -> 660 (-112)**, 76/82 new fns called, "
       "orphans 234 -> 238. **Block-iv diagnosis:** 73 KB / 7 fns; the 28 "
       "remaining dsts sit behind binary UI/struct tables (stops: "
       "pad-then-nonentry/undecodable/zero-run), **Stage-2 (cap now 16 KB) "
       "rejects 26/27 for no terminator behind** -- they are class-c "
       "anomalies, not clean functions. **Residency of the 660:** Resident "
       "**93 dsts / 236 refs**, other R\\* overlays **254 / 424** (R05 79, "
       "R30 71, R06 25, R53 16, R14 14, R17 12, R35 12), carved region 4/12, "
       "untouched zero block **0**. In-scope residue 63 dsts/109 refs = the "
       "documented stops. Gates: check 267, verify_rebuild faithful (REGISTER "
       "19 applied/77 pending, ADDED 82 planned), verify_idb INTACT 2133 / 0 "
       "hole problems, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**R05_1E10 sweep finished (finding 62):** the post-f61 recount (415 dsts "
    "/ 772 refs) brought **12 remaining evidence-bearing blocks (26,260 B)** "
    "into scope — including `0x48DB0..0x493C0`, which *gained* 4 dsts / 10 "
    "refs from a newly revealed reference — while the two truly zero-evidence "
    "blocks stayed out. The same sweep→plan→register pass registered **82 more "
    "functions** (96 ranges, 8,727 instructions) after two fixes: a gap that "
    "starts on a small data item now moves its start past it (a 2-byte "
    "`word_4FD48` had made `add_func` refuse a whole range), and suspect holes "
    "the sweep overran into are recorded but **not enforced** (a guard-failed "
    "run's dirty DB covered `0x4ACA1`); `register_upper` is now **idempotent** "
    "so the re-run after the guard was a clean no-op. Outcome: functions "
    "**2,051 → 2,133**, static edges **4,907 → 5,289**, "
    "**`static_unresolved` 772 → 660 (-112)**, 76/82 new functions already "
    "called. **Block-iv (`0x54AF0..0x669F0`, 73 KB, 7 fns) diagnosed:** its "
    "28 residual destinations sit behind binary UI/struct tables (sweep stops "
    "at `pad-then-nonentry`/`undecodable`/`zero-run`), and Stage-2 with a "
    "raised 16 KB cap still rejects 26/27 for **no terminator behind** — they "
    "are class-c anomalies, not clean functions. **Residency of the 660:** "
    "**93 resident dsts / 236 refs**, **254 other-overlay dsts / 424 refs** "
    "(R05 79, R30 71, R06 25, …), carved region 4/12, untouched zero block 0."
)

OPEN_NEW = [
    "- **R05_1E10 sweep DONE (finding 62):** 12 remaining evidence blocks",
    "  registered (82 fns, 96 ranges), `static_unresolved` **772 -> 660**;",
    "  block iv (73 KB / 7 fns) diagnosed: its 28 residual dsts sit behind",
    "  binary UI tables and **26/27 fail Stage-2 for no terminator behind**",
    "  (class-c anomalies, not clean functions). **Still open:** (a) **93",
    "  resident dsts / 236 refs** in `0x10000..0x2CF60` -- needs a",
    "  finding-54-style registration pass over resident gaps; (b) **254",
    "  other-overlay dsts / 424 refs** -- `R30_569F` 71, `R06_5CD9` 25,",
    "  `R53_569Fs` 16, `R14_5E0B` 14, `R17_5E8F` 12, `R35_569Fs` 12,",
    "  `R12/R32/R40_569Fs` 4 each -- separate RTLink records already mapped",
    "  by finding 60's runtime map, each needs its own sweep/REGISTER cycle;",
    "  (c) in-scope residue 63 dsts / 109 refs inside documented stops;",
    "  (d) untouched zero block `0x500C0..0x54AF0` (0 dsts) stays out.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 62" in raw:
    print("findings_log: 62 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 62 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 18b" in raw:
    print("time_log: 18b already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 18" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 18b after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "R05_1E10 sweep finished (finding 62)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f62 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "R05_1E10 sweep DONE (finding 62)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f62 status (%d bytes)" % len(block))