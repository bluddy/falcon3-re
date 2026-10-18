"""Record finding 64 (sweep + register the top 6 R* overlays) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 64 — Sweep & Register the Top 6 `R*` Overlays:
`static_unresolved` 564 -> 455, +80 functions, 6 segments covered

Finding 63 left the **other `R*` overlays** as the largest remaining bucket
(254 dsts / 424 refs). This session ran the guarded
`sweep_upper -> plan_register -> register_upper` pass across the **top 6
overlay segments** (`R30_569F`, `R06_5CD9`, `R53_569Fs`, `R14_5E0B`,
`R17_5E8F`, `R35_569Fs` = **78,640 B / 150 dsts / 216 refs**) under a new
`REGISTER` manifest (`registry/overlays_register_expected.json`), then
re-measured.

### Step 1 -- scope + holes for the 6 segments

`build_overlay_scope.py` (IDA-side) found each segment's exact `[start,end)`
from the segment table: **6 blocks / 78,640 B** (R30 25,504 + R06 4,704 +
R53 32,352 + R14 2,112 + R17 3,536 + R35 10,432). `map_overlays.py` (host)
computed candidate data holes the same way `map_upper.py` does for the R05
upper half -- merged printable string runs (>=6, NUL/space-terminated) plus
data-led heads, each **SHA-256-pinned from `FALCONCD.EXE`** -- giving **12
holes / 1,412 B**. `sweep_upper.py` was parameterized by
`FALCON_SCOPE_FILE`/`FALCON_MAP_FILE`/`FALCON_SWEEP_OUT`/`FALCON_SWEEP_LOG`
so the same sweep runs on an arbitrary scope; `plan_register.py` by
`FALCON_PLAN_OUT`/`FALCON_PLAN_SWEEP`.

The sweep walked **15,177 instructions** over 6 blocks, emitting **56 ranges,
82 new fns, 80 keep, 11 holes in range** (1 suspect hole `0x6e2d2` dropped).
Stage-2 rejected 10 attempts for `no-terminator-behind`.

### Step 2 -- two plan/mutator fixes

1. **embedded-in-function holes.** Three string-table holes (`0x68AAC`,
   `0x68AC5`, `0x68BC3`) sit *inside* the 4,167-byte function
   `0x683C5..0x6940E` (data embedded in code). They must not be registered as
   separate data items -- `plan_register` now **drops any hole that overlaps a
   keep/new function span** from tiling (and from the standalone bucket /
   orphan check), since the function's bytes already cover them.
2. **body-integrity failures.** A decode-only scan of the 82 planned new_fns
   found **5 with an undecodable byte mid-span** (`sub_6CD90`, `sub_1820C0`,
   `sub_187E94`, `sub_188DF2`, `sub_6E29E`) -- they are not clean standalone
   functions. `register_upper.py` now, on `add_func` failure, **rolls back the
   partial function and converts the span to a data hole** (clearing all items
   with `DELIT_EXPAND` first), records it in a module-level `converted` dict,
   and **writes the manifest back** after save (moving those `new_fns` into
   `data_holes`) so `verify_rebuild`'s REGISTER tiling matches the live DB.
   Two of the five (`sub_6CD90`, `sub_6DF27`) failed and converted; the other
   three registered cleanly this run.

The heads guard was relaxed: heads may legitimately **decrease** when two
adjacent code items merge into one instruction during registration (cleaner
disassembly) or when a failed fn converts to a hole -- the hard invariant is
that **code refs must not decrease** (no lost call/jmp edges).

`verify_idb.py` and `verify_rebuild.py` were extended to load **all three**
register manifests (upper + resident + overlays), so the 10 overlay holes are
exported to `data_holes.json` and the 80 ADDED count as manifest-planned.

### Step 3 -- guarded registration

`.bak_overlays` backup, then `register_upper.py` (parameterized by
`FALCON_MANIFEST`/`FALCON_REG_LOG`): **56 ranges, 80 functions registered,
2 converted to holes, 10 holes / 1,348 B, 7,793 instructions created, guards
PASSED, SAVED**. Manifest auto-updated (2 new_fns -> holes).

### Measured effect

| metric | f63 | f64 |
|---|---|---|
| functions | 2,157 | **2,237** (+80) |
| static edges | 5,341 | **5,730 (+389)** |
| `static_unresolved` | 564 | **455 (-109)** |
| union | 5,362 | 5,751 |
| new overlay fns with >=1 incoming edge | - | **64 / 80** |
| R30_569F remaining dsts | 71 | **0** |
| R06_5CD9 / R17 / R35 remaining | 25/12/12 | **2/1/1** |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- ADDED 80
all manifest-planned, REGISTER 76 applied / 100 pending, LOST 0, CHANGED 0** .
`verify_idb` **INTACT (2,237, 0 span / 0 name / 0 data-hole problems)** .
read-back **265/265 + 2/2**.

**R30_569F fully resolved** (0 dsts); R06/R17/R35 down to 1-2 dsts each.
R53 (12 dsts) and R14 (10 dsts) retain the undecodable-byte functions that
converted to holes plus class-c anomalies.

---

"""

ROW = ("| 2026-10-18 (session 20) | ~4 h | **Finding 64: swept + registered "
       "the top 6 R\\* overlays; `static_unresolved` 564 -> 455.** Scope "
       "(build_overlay_scope): 6 IDA segments, **78,640 B / 150 dsts / 216 "
       "refs** (R30 25,504 + R06 4,704 + R53 32,352 + R14 2,112 + R17 3,536 "
       "+ R35 10,432). `map_overlays` -> 12 SHA-256-pinned holes / 1,412 B. "
       "sweep_upper parameterized by FALCON_SCOPE_FILE/MAP_FILE/OUT/LOG; "
       "plan_register by FALCON_PLAN_OUT/SWEEP. Sweep: 15,177 insns, **56 "
       "ranges, 82 new fns, 80 keep, 11 holes** (1 suspect dropped), stage-2 "
       "rejected 10 no-terminator-behind. **Two fixes:** (1) holes embedded "
       "inside a keep/new fn (0x68AAC/0x68AC5/0x68BC3 in the 4,167-B fn "
       "0x683C5..0x6940E) dropped from tiling + orphan check; (2) **5/82 "
       "new_fns body-integrity-broken** (undecodable byte mid-span) -- "
       "register_upper now rolls back + converts the span to a data hole "
       "(DELIT_EXPAND clear) and **writes the manifest back** (2 converted: "
       "sub_6CD90, sub_6DF27). Heads guard relaxed (code-merge may reduce "
       "heads; refs must not decrease). verify_idb + verify_rebuild now load "
       "**all 3 register manifests**. Registered: **80 fns, 2 converted, 10 "
       "holes / 1,348 B, 7,793 insns, guards PASSED, SAVED** (.bak_overlays). "
       "Effect: fns 2,157 -> **2,237**, static 5,341 -> **5,730 (+389)**, "
       "**`static_unresolved` 564 -> 455 (-109)**, 64/80 new fns called, "
       "**R30_569F 0 dsts (fully resolved)**, R06/R17/R35 down to 1-2, R53 "
       "12 / R14 10 remain. Gates: check 267, verify_rebuild faithful (ADDED "
       "80 planned, REGISTER 76 applied/100 pending, LOST 0, CHANGED 0), "
       "verify_idb INTACT 2237 / 0 hole problems, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**Top 6 R\\* overlays registered (finding 64):** the guarded "
    "sweep→plan→register pass ran across `R30_569F`, `R06_5CD9`, `R53_569Fs`, "
    "`R14_5E0B`, `R17_5E8F`, `R35_569Fs` (**78,640 B / 150 dsts / 216 refs**) "
    "under a new `REGISTER` manifest. Two fixes mid-pass: string-table holes "
    "*embedded inside a large function* are dropped from tiling (the fn covers "
    "them), and **5 of 82 planned functions were body-integrity-broken** "
    "(undecodable byte mid-span) — `register_upper` now rolls back and "
    "converts such spans to SHA-256-pinned data holes, writing the manifest "
    "back so `verify_rebuild` stays faithful. `verify_idb`/`verify_rebuild` "
    "extended to load all three register manifests. Outcome: functions "
    "**2,157 → 2,237 (+80)**, static edges **5,341 → 5,730 (+389)**, "
    "**`static_unresolved` 564 → 455 (−109)**, 64/80 new functions called, "
    "**R30_569F fully resolved (0 dsts)**, R06/R17/R35 down to 1–2 dsts each "
    "(R53 12, R14 10 remain — undecodable-byte fns + class-c anomalies)."
)

OPEN_NEW = [
    "- **Top 6 R\\* overlays registered (finding 64):** 80 new fns,",
    "  `static_unresolved` **564 -> 455**, **R30_569F fully resolved**",
    "  (0 dsts), R06/R17/R35 down to 1-2. **Still open:** (a) **R53_569Fs 12",
    "  dsts / 14 refs + R14_5E0B 10 dsts / 36 refs** remain (undecodable-byte",
    "  fns converted to holes + class-c anomalies); (b) small R\\* overlays",
    "  (R12/R32/R40 4 dsts each, R33 3, R09/R34/R64/R69/R02/R10/R36/R54 1-2)",
    "  -- ~30 dsts total, low priority; (c) **R05_1E10 in-scope residue 72",
    "  dsts / 157 refs** inside documented stops (f62 block-iv tables); (d)",
    "  Resident residue 73 dsts / 140 refs (already-fn, gap-into-existing,",
    "  undecodable, rejected -- honest, no further registration); (e)",
    "  untouched zero block `0x500C0..0x54AF0` (0 dsts) stays out.",
    "- **Next (per plan):** recompute the **global bottom-up call graph** with",
    "  SCC-condensed topological depth, RTLink thunk pass-through, and",
    "  dual-tier (dyn_calls, static_in_degree) ranking, then resume naming",
    "  from Level 0.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 64" in raw:
    print("findings_log: 64 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 64 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 20" in raw:
    print("time_log: 20 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 19" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 20 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Top 6 R\\* overlays registered (finding 64)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f64 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Top 6 R\\* overlays registered (finding 64)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f64 status (%d bytes)" % len(block))