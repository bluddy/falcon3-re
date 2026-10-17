"""Record finding 59 in docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md, docs/open_items.md (CRLF) and the rebuild runbook (LF).

Idempotent + line-ending preserving (pattern of tools/_docs57.py).
Also repairs the (g) item head that finding 58's replacement clipped.
"""
import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 59 — The carve: `sub_2E2F0` becomes 258 functions + 3
sha256-pinned data holes, static edges 2,730 -> 4,013

Finding 58's plan, executed with the gate written FIRST: nothing was mutated
until `registry/subblock_split_expected.json` described exactly what the IDB
must look like afterwards.

### Step 1 -- the plan is a file, not a guess

`tools/carve_seeds.py` (372 seeds = 343 internal CALL targets + 22 external +
10 thunk + the blob start) -> `tools/seed_tests.py` (read-only backward sweep:
which instructions decode to END EXACTLY on each seed, and what the first three
instructions look like) -> `tools/plan_carve.py` writes the manifest: parent
span + sha256, **3 data holes with their own sha256 and why** (93 B object
table, 144 B RTLink name table `global.amo/local.amo/harpoon.dat/
FALCONCOLORADO`, 2 B pad), and every planned child `(key, ea, size)`.
**253 seeds accepted by the terminator-backwards rule + 7 forced** (blob start,
3 hole ends, 3 anchors); coverage validates EXACT: 51,405 B code + 239 B data
= 51,644 B.

### Step 2 -- the gate before the mutation

`verify_rebuild.py` gained a **CARVE** class: a shrunk/retired parent is
intentional only when (a) the manifest's `(key, ea, size)` list matches the
functions currently inside the old span *exactly* (missing or extra = fail),
(b) no function overlaps a hole, (c) the parent really shrank, and (d) every
hole's **live** sha256 -- read from `analysis/ida_falconcd/data_holes.json`,
which `verify_idb.py` now computes from the database and refuses to accept if
a hole is covered by a function or not flagged as data. Dry run before carving:
`INTACT` + `faithful` (and one mis-detection fixed: `carved` was inferred from
"any planned child exists", but child #1 shares the parent's EA, so it read the
pre-carve parent as carved -- now inferred from "parent no longer spans the old
range").

### Step 3 -- the backward rule lied twice, and the plan caught it

`tools/carve_probe.py` found **10 existing instructions crossing planned
boundaries**: 8 are zero padding (the old sweep turned the `00 00...` before a
module boundary into `add`) -> delete that item; **2 are real code**:
`0x32553` sits inside a `9A` call-far at `0x32552`, `0x3A2D8` inside `3D` at
`0x3A2D6`. Those two seeds are backward-decode artefacts -> **dropped (ranges
merged), 260 -> 258 functions**. Rule learned: a terminator that "lands on" an
address in a backward sweep is only a candidate; it must not contradict the
existing decode.

### Step 4 -- three aborts, one save

The mutator refused to save three times, each time leaving the IDB restorable:
(1) `idc.get_byte` does not exist in 9.1 (`ida_bytes.get_byte` does); (2) a
`%d` format was handed the string "ABORTED"; (3) **`create_insn` returned 0 at
`0x2EA6D`, `0x2F6D0`, `0x39AA9`** although a fresh `decode_insn` succeeded --
another item sat *inside* the entry's first instruction, so IDA would not
create it; fixed with a clear-blocking-item-then-retry loop (3 small items
cleared). Every attempt restored `FALCONCD.EXE.i64.bak_carve` and re-verified
**INTACT** before the next run. Final run: **258 functions registered, heads
17,547 -> 17,545, code refs 5,209 -> 5,209 (the blob's edges survived
byte-for-byte), holes byte-identical, SAVED.**

### Measured effect

| metric | before | after |
|---|---|---|
| functions | 1,678 | **1,935** (1,678 - 1 + 258) |
| static edges | 2,730 | **4,013 (+1,283)** |
| refs into the blob forming edges | 82 | **812** |
| ... landing on an exact function start | 0 | **572** |
| total code refs | 9,244 | 9,244 (nothing lost) |
| `static_unresolved` | 957 | 957 (the holes hold no refs) |
| new functions with >=1 incoming edge | - | **256 / 258** |
| overlay zero-indegree orphans | 224 | 226 (the 2 uncalled pieces) |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- CARVE 1,
ADDED 257 (all manifest-planned), LOST 0, CHANGED 0** . `verify_idb`
**INTACT (1,935, 0 span / 0 name / 0 data-hole problems)** . read-back
265/265 + 2/2. Backup `FALCONCD.EXE.i64.bak_carve`.

Impact: finding 58 predicted the 971 internal refs were invisible because
`sub_2E2F0 -> sub_2E2F0` self-edges are dropped -- **730 of the 812 edges now
come from exactly that class**, and 572 refs land on a real entry instead of
inside a 46 KB span. Remaining on this line of work: 112 rejected seeds stay
interior by design, 2 pieces have zero indegree, `0x3ACAC..0x669F0` still
holds 251 unregistered destinations (registration, not carving), and the
runbook must document the `verify_idb` -> `verify_rebuild` ordering the hole
export depends on.

---

"""

ROW = ("| 2026-10-18 (session 17y) | ~3 h | **Finding 59: carved `sub_2E2F0` "
       "into 258 functions + 3 sha256-pinned data holes, behind a gate written "
       "first.** Plan-then-mutate: `carve_seeds` (372) -> `seed_tests` "
       "(backward sweep: 253 terminator-proven + 7 forced) -> `plan_carve` -> "
       "**`registry/subblock_split_expected.json`** (parent span+sha, 3 holes "
       "with sha/why, 258 child (key,ea,size), coverage EXACT 51,405 + 239 = "
       "51,644). Gate: `verify_rebuild` **CARVE class** (exact planned set, no "
       "function may overlap a hole, parent must shrink, hole sha256 from the "
       "LIVE export) + `verify_idb` now hashes every hole from the DB and "
       "writes `data_holes.json`, failing if a hole is covered or not data "
       "(one pre-carve mis-detection fixed: `carved` inferred from parent "
       "span, not from a child that shares the parent EA). `carve_probe` "
       "found **10 instructions crossing boundaries: 8 zero-padding (delete), "
       "2 real code (`9A` at 0x32552, `3D` at 0x3A2D6) -> seeds DROPPED**, "
       "260 -> 258 fns. Mutator refused to save 3x (idc.get_byte missing in "
       "9.1; %d on a string; `create_insn` -> 0 when another item sits inside "
       "the entry's first instruction -> clear-and-retry) -- each time "
       "restored `.bak_carve` + verified INTACT. Final: **258 registered, "
       "refs 5,209 -> 5,209 (edges intact), SAVED**. Effect: fns "
       "**1,678 -> 1,935**, static **2,730 -> 4,013 (+1,283)**, refs into the "
       "blob forming edges **82 -> 812** (of which **572 land on an exact "
       "function start**), total refs unchanged 9,244, `static_unresolved` "
       "957 (holes hold no refs), new fns called **256/258**, orphans 224 -> "
       "226. Gates: check 267, verify_rebuild **faithful (CARVE 1, ADDED 257 "
       "all planned, LOST 0, CHANGED 0)**, verify_idb **INTACT 1,935 / 0 hole "
       "problems**, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**`sub_2E2F0` carved (finding 59), gate first:** the 46 KB blob is now "
    "**258 functions + 3 data holes (239 B) pinned by sha256**, planned in "
    "`registry/subblock_split_expected.json` *before* any mutation. "
    "`verify_rebuild` learned a **CARVE** class (exact planned `(key, ea, "
    "size)` set, no function may overlap a hole, parent must shrink, and each "
    "hole's sha256 must match the **live** export that `verify_idb.py` now "
    "writes to `data_holes.json`, failing if a hole is covered by a function "
    "or not flagged as data). Boundaries came from the terminator-backwards "
    "rule over 372 seeds, cross-checked against the existing decode: 10 "
    "crossing instructions split into 8 zero-padding items (deleted) and **2 "
    "real instructions -- `9A` at `0x32552`, `3D` at `0x3A2D6` -- whose seeds "
    "were dropped as backward-decode artefacts**. The mutator refused to save "
    "three times (missing `idc.get_byte`, a `%d` on a string, and "
    "`create_insn` returning 0 when another item sits inside an entry's first "
    "instruction) and each time the backup was restored and re-verified "
    "**INTACT**. Result: functions **1,678 -> 1,935**, static edges "
    "**2,730 -> 4,013 (+1,283)**, refs into the blob forming edges **82 -> "
    "812** with **572 at an exact function start**, code refs unchanged at "
    "9,244 (nothing lost), 256/258 new functions already called."
)

OPEN_NEW = [
    "   `0x3ACAC..0x669F0`; (f) **DONE (finding 59): `sub_2E2F0` is carved**",
    "   -- the map (6 anchors inside, not f57's 4 KB-bucket \"13\"; data = 3",
    "   holes / 239 B) drove a manifest-planned split into **258 functions +",
    "   3 sha256-pinned holes**, boundaries from the terminator-backwards rule",
    "   with 2 seeds dropped where a real `9A`/`3D` instruction crossed;",
    "   static edges **2,730 -> 4,013**, refs into the blob 82 -> **812",
    "   edges** (**572** at an exact function start), 256/258 new fns called;",
    "   the gate is `verify_rebuild`'s CARVE class + `verify_idb`'s live hole",
    "   export (`data_holes.json`) -- **still open here**: 112 rejected seeds",
    "   stay interior by design, 2 new pieces have zero indegree, and",
    "   `0x3ACAC..0x669F0` (251 unregistered dsts) is registration work;",
    "   (g) 138 functions had zero indegree at HEAD and now have an edge",
    "   (134 resident, 4 overlay), while the 226 remaining overlay orphans are",
    "   still never called by anything static.",
]

RUNBOOK_OLD = """`SPLIT` (old fn subdivided, full coverage), `RECODE` (size changed but
`(key, ea, old_size, new_size)` matches `registry/bitness_fix_expected.json`
exactly) and `PATCH` (same `key`/`ea`/`size`, and **both** the pre- and
post-change sha256 match `registry/subblock_fixups_expected.json`) are the
only intentional-change classes and none counts against the gate."""

RUNBOOK_NEW = """`SPLIT` (old fn subdivided, full coverage), `RECODE` (size changed but
`(key, ea, old_size, new_size)` matches `registry/bitness_fix_expected.json`
exactly), `PATCH` (same `key`/`ea`/`size`, and **both** the pre- and
post-change sha256 match `registry/subblock_fixups_expected.json`) and
`CARVE` (finding 59: the parent's planned children in
`registry/subblock_split_expected.json` match the live functions *exactly*,
no function touches a data hole, and each hole's sha256 matches the export
`verify_idb.py` writes to `analysis/ida_falconcd/data_holes.json`) are the
only intentional-change classes and none counts against the gate.
**Order matters after a carve:** run `verify_idb.py` before `verify_rebuild.py`
so the live hole export exists."""

OPEN_START = "(f) `sub_2E2F0` is **mapped, not guessed**"
OPEN_END = "their recorded sha256 (else it is `CHANGED`);"


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 59" in raw:
    print("findings_log: 59 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 59 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 17y" in raw:
    print("time_log: 17y already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 17y after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "carved (finding 59)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f59 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "DONE (finding 59)" in raw:
    print("open_items: already updated")
else:
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines) if OPEN_START in l)
    end = next(i for i in range(start, len(lines)) if OPEN_END in lines[i])
    # the old (g) line lost its head in finding 58's replacement; it follows
    tail_start = end + 1
    assert "HEAD and now have an edge" in lines[tail_start], lines[tail_start]
    cr = "\r" if lines[start].endswith("\r") else ""
    lines[start:tail_start + 2] = [x + cr for x in OPEN_NEW]
    save(p, "\n".join(lines))
    print("open_items: replaced (f) block + repaired (g) head (%d lines)"
          % len(OPEN_NEW))

# ---- docs/workflow/idb_regeneration.md (LF) ----
p = "docs/workflow/idb_regeneration.md"
raw = load(p)
if "CARVE" in raw:
    print("runbook: CARVE already documented")
else:
    assert RUNBOOK_OLD in raw, "runbook anchor not found"
    save(p, raw.replace(RUNBOOK_OLD, RUNBOOK_NEW))
    print("runbook: documented the CARVE class + gate ordering")
