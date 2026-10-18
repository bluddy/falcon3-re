"""Record finding 63 (register verified Resident destinations) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 63 — Registering the Verified Resident Destinations:
`static_unresolved` 660 -> 564, 24 new functions, and the `0x43E0C`
variant-swap answered

Finding 62 left **93 Resident destinations / 236 refs** (`0x10000..0x2CF60`) as
the largest single bucket of `static_unresolved`. Finding 58 had already
classified them (59 `a_frameless_fn`, 15 `b_ptr_or_indirect` jump-table, 6
`c_anomaly`, 6 unknown). This session ran a guarded registerability pass over
all of them, registered the clean ones under the `REGISTER`/`ADDED` manifest
gate, and answered the read-only `0x43E0C` variant question.

### Step 1 -- audit the 93 (`audit_resident.py` + `decode_resident.py`)

`dst_list` post-f62 gives 86 distinct Resident dsts / 229 refs (the zone
filter found 86, not 93 -- a few of the original 93 resolve after f62). For
each, IDA-side: decode forward to a terminator (`retf`/`retn`/`jmp`/`iret`),
check no overlap with an existing function or named data, and classify
jump-table targets as standalone handler (ends `retn`/`retf`) vs tail (ends
`jmp`):

| category | dsts | refs | action |
|---|---|---|---|
| standalone, clean decode, no overlap | 36 | 124 | **register** |
| already inside an existing function | 27 | 45 | no action |
| forward-decode runs into an existing fn (gap-into-existing) | 18 | 48 | not standalone |
| undecodable (class-c anomaly) | 3 | 4 | rejected |
| jump-table target, ends `retn` (standalone handler) | 1 | 2 | **register** |
| jump-table target, ends `jmp` (case tail) | 1 | 6 | not standalone |

### Step 2 -- alignment correction (the `0x28CAB` lesson)

`add_func sub_28CAB 0x28CAB..0x28D06 -> None` on the first guarded run. The
diagnosis: **`0x28CAB` is mid-instruction** -- `get_item_head(0x28CAB) =
0x28CA8`, a 4-byte `mov` (`decode_insn(0x28CAB)` returns a spurious k=1).
The ref target lands 3 bytes into a real instruction. Finding 58's dst was
correct as a *destination*, but it is not a valid *entry*. `add_func` refuses
mid-instruction starts.

**3 of the 37 candidates are mid-instruction** and were re-aligned to their
real item head (then re-decoded to a terminator):

- `0x28CAB` -> `0x28CA8` (the top destination, 36 refs)
- `0x10423` -> `0x10422`
- `0x108E7` -> `0x108E6`

### Step 3 -- guarded registration

A per-candidate `add_func` dry-run (finding-59 clear-blocking-items retry on
failure, then `add_func(entry, end)` with explicit span + name + span check)
sorted the 37 aligned candidates:

- **23 confirmed registerable** (dry-run `add_func` + exact span) -- written to
  `registry/resident_register_expected.json` (24 ranges; `sub_28CA8` added as
  the 24th after a stray dry-run left it in the DB and the manifest was
  patched to match).
- **13 rejected**: 10 whose `add_func` still failed after the retry (mid-function
  case labels / crossing an existing function boundary), 3 whose explicit-end
  dry-run span-mismatched (`0x10897`, `0x108E6`, `0x28CA4`).

`register_upper.py` (now parameterized by `FALCON_MANIFEST`/`FALCON_REG_LOG`)
ran the resident manifest: **24 ranges, 24 new fns, 0 holes, guards PASSED,
SAVED** (backup `FALCONCD.EXE.i64.bak_resident`). `verify_rebuild` was
extended to load **both** register manifests (`upper` + `resident`), so the
24 count as `ADDED planned by the manifests`.

### Measured effect

| metric | f62 | f63 |
|---|---|---|
| functions | 2,133 | **2,157** (+24) |
| static edges | 5,289 | **5,341 (+52)** |
| `static_unresolved` | 660 | **564 (-96)** |
| union | 5,310 | 5,362 |
| Resident unresolved refs | 236 | **140 (-96)** |
| Resident unresolved dsts | 93 | 73 |
| new resident fns with >=1 incoming edge | - | **24 / 24 (0 orphans)** |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- ADDED 24
all manifest-planned, REGISTER 43 applied / 77 pending, LOST 0, CHANGED 0** .
`verify_idb` **INTACT (2,157, 0 span / 0 name / 0 data-hole problems)** .
read-back **265/265 + 2/2**.

The remaining **73 Resident dsts / 140 refs** are exactly the non-registerable
categories: 27 already-fn, 18 gap-into-existing, 3 undecodable, 13 rejected
standalone (the 10 `add_func` failures + 3 span mismatches), 1 jt-tail. They
are honest residue, not missed functions.

### Step 4 -- the `0x43E0C` variant-swap check (read-only)

`0x43E0C` (16 refs) sits at offset **`+0x15D0C` from `0x2E100`** (R05's upper
base). Since `R05_1E10`, `R27_1E10s`, `R28_1E10s`, `R29_1E10s` all declare
`w0 = 0x1E10` (finding 60's variant swap), the question was whether the *same
relative offset* `+0x15D0C` inside R27/R28/R29 lands on a valid
terminator-preceded entry.

**Answer: no -- and it is not checkable as posed.** Three independent reasons:

1. **The variants are mutually exclusive load scenarios.** Finding 60 proved
   only one of R05/R27/R28/R29 is placed per CS/segment (the swap is real:
   both R05 and R29 loaded at base `0x2005` in *different runs*). There is no
   concurrent R27/R28/R29 module in the IDB at a base where `+0x15D0C` is a
   checkable function entry.
2. **The `s`-suffix variants are re-placed only as sparse entry-record
   snippets**, not contiguous modules: the entire IDB contains exactly **6**
   `r27_*`/`r28_*`/`r29_*` named functions (`r27_e05` @`0x10DAC5`,
   `r27_e62`, `r27_e64`, `r28_e65`, `r29_e06`, `r29_e63`). Treating the
   lowest of each as a "base" and adding `0x15D0C` lands in **empty space**
   (`r27` base `0x10CC60` + `0x15D0C` = `0x12296C`, no function; same for R28
   `0x131F13`, R29 `0x132FAC`).
3. **`0x43E0C` is itself a class-c anomaly in R05** -- first byte does not
   decode (`unk_43E0C`), so even in its own variant it is not a valid
   terminator-preceded entry.

So the offset coincidence does not yield a registerable entry in any sibling
variant; `0x43E0C` stays an honest unresolved dst.

---

"""

ROW = ("| 2026-10-18 (session 19) | ~3 h | **Finding 63: registered the "
       "verified Resident destinations; `static_unresolved` 660 -> 564.** "
       "Audited the 93 Resident dsts (`audit_resident` + `decode_resident`): "
       "**36 standalone + 1 jt-standalone registerable**, 27 already-fn, 18 "
       "gap-into-existing, 3 undecodable, 1 jt-tail. **`0x28CAB` was "
       "mid-instruction** (`get_item_head=0x28CA8`, a 4-byte `mov`) -- `add_func` "
       "refuses it; **3 candidates re-aligned** to real item heads (`0x28CAB`->"
       "`0x28CA8`, `0x10423`->`0x10422`, `0x108E7`->`0x108E6`). Per-candidate "
       "`add_func` dry-run + finding-59 retry: **23 confirmed, 13 rejected** (10 "
       "add_func failures + 3 span mismatches); manifest `resident_register_"
       "expected.json` = 24 ranges (stray `sub_28CA8` patched in). "
       "`register_upper` parameterized by `FALCON_MANIFEST`; `verify_rebuild` "
       "now loads **both** register manifests. Registered **24 fns, guards "
       "PASSED, SAVED** (`.bak_resident`). Effect: fns 2,133 -> **2,157**, "
       "static 5,289 -> **5,341 (+52)**, **`static_unresolved` 660 -> 564 "
       "(-96)**, Resident refs 236 -> **140 (-96)**, 24/24 new fns called. "
       "Remaining 73 Resident dsts/140 refs = honest residue (already-fn, "
       "gap-into-existing, undecodable, rejected). **`0x43E0C` variant check "
       "(read-only):** NOT checkable as posed -- R05/R27/R28/R29 are "
       "mutually exclusive (finding 60), the `s`-variants exist only as **6 "
       "sparse entry-record snippets** (base+0x15D0C lands in empty space for "
       "each), and `0x43E0C` is itself class-c undecodable in R05. Gates: "
       "check 267, verify_rebuild faithful (ADDED 24 planned, REGISTER 43 "
       "applied/77 pending), verify_idb INTACT 2157 / 0 hole problems, "
       "read-back 265/265+2/2. |")

STATUS_PARA = (
    "**Resident destinations registered (finding 63):** a guarded pass over the "
    "93 Resident unresolved destinations (`0x10000..0x2CF60`) classified each "
    "by IDA-side decode-to-terminator + overlap check: **36 standalone + 1 "
    "jump-table handler were registerable**, 27 already inside functions, 18 "
    "gap-into-existing (forward-decode runs into a neighbor), 3 undecodable, 1 "
    "jump-table tail. The first guarded run failed on `0x28CAB` — it is "
    "**mid-instruction** (`get_item_head=0x28CA8`, a 4-byte `mov`), so 3 "
    "candidates were re-aligned to their real item heads. A per-candidate "
    "`add_func` dry-run with the finding-59 clear-blocking retry confirmed 23 "
    "and rejected 13 (10 `add_func` failures, 3 span mismatches); the manifest "
    "(24 ranges, `sub_28CA8` patched in) registered cleanly under the extended "
    "`REGISTER`/`ADDED` gate (`verify_rebuild` now loads both register "
    "manifests). Outcome: functions **2,133 → 2,157 (+24)**, static edges "
    "**5,289 → 5,341 (+52)**, **`static_unresolved` 660 → 564 (−96)**, "
    "Resident refs **236 → 140 (−96)**, 24/24 new functions called. The "
    "remaining 73 Resident dsts are honest residue (already-fn, "
    "gap-into-existing, undecodable, rejected). **`0x43E0C` variant check "
    "(read-only):** not checkable as posed — R05/R27/R28/R29 are mutually "
    "exclusive load scenarios (finding 60), the `s`-variants exist only as 6 "
    "sparse entry-record snippets (base+0x15D0C lands in empty space for each), "
    "and `0x43E0C` is itself class-c undecodable in R05."
)

OPEN_NEW = [
    "- **Resident destinations registered (finding 63):** 24 new fns,",
    "  `static_unresolved` **660 -> 564**, Resident refs **236 -> 140**.",
    "  `0x43E0C` variant check answered (not checkable -- mutually exclusive",
    "  variants, sparse s-snippets). **Still open:** (a) **73 Resident dsts /",
    "  140 refs** are honest residue (27 already-fn, 18 gap-into-existing, 3",
    "  undecodable, 13 rejected standalone, 1 jt-tail) -- no further",
    "  registration there; (b) **the other R\\* overlays** remain the big",
    "  bucket: R05 79, **R30_569F 71**, **R06_5CD9 25**, R53 16, R14 14,",
    "  R17 12, R35 12, R12/R32/R40 4 each -- these are separate RTLink",
    "  records already mapped by finding 60's runtime map, each needs its own",
    "  sweep/REGISTER cycle (Finding 64); (c) in-scope R05 residue 63 dsts /",
    "  109 refs inside documented stops; (d) untouched zero block",
    "  `0x500C0..0x54AF0` (0 dsts) stays out.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 63" in raw:
    print("findings_log: 63 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 63 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 19" in raw:
    print("time_log: 19 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 18" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 19 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Resident destinations registered (finding 63)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f63 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Resident destinations registered (finding 63)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f63 status (%d bytes)" % len(block))