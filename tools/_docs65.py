"""Record finding 65 (callgraph audit + fix) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 65 — Call-Graph Audit: 4 anomalies in the Level-0 queue,
fixed (`function_bytes` ea-join + thunk exclusion); SCC/levels verified sound

Before starting Global Level-0 Batch 1 we audited the `f55a16b` call-graph
report. Four anomalies were flagged; the first two were real bugs in
`callgraph_bottomup.py`, the last two were correct-but-surprising behavior now
documented. All four are resolved.

### Anomaly 1 — already-named functions counted as "unnamed" (BUG, fixed)

The Top-30 "unnamed" list showed ranks #2/#5/#6/#7/#8 =
`sub_112A1`/`sub_2703F`/`sub_2228F`/`sub_22285`/`sub_1122A`, which Finding 39
named `input_status_pack`/`farptr_table_get`/`active_farptr_restore`/
`active_farptr_set`/`joystick_poll`. Root cause: the code decided "named" by
string-matching the function key against `^sub_|nullsub_|loc_|...` (`AUTO`
regex). That is wrong twice over:

* a ledger-named function keeps its **IDA key** (`sub_112A1`) as the
  `function_bytes`/`naming.yaml` identifier, so the `sub_*` prefix says
  nothing about whether it has a semantic name;
* RTLink entries (`r01_e01`, `r22_e57`, ...) do **not** match `^sub_`, so the
  old code counted them as "named" even though most are unnamed.

**Fix:** join on the **integer `ea`** through `function_bytes.json`, whose
`name` field is non-null exactly for the applied ledger names.
`function_bytes[k].name != null` ⇔ named. Verified: **265 named = 265
`naming.yaml` `kind:function` entries, zero drift** (the other 2 ledger symbols
are data globals `op_dispatch_table`, `fn_table_dispatch_table`).

### Anomaly 2 — Levels 20–22 looked ~100% named; Level 19 piled up 292 nodes

This was **also the string-match bug**: the "23/63, 19/23, 3/3 named" figure
counted RTLink `r##_e##` keys (which don't match `^sub_`) as named. After the
ea-join fix, **Levels 20/21/22 have 0 named functions** — they were never
named (Findings 39–48 only named Levels 0–2).

The Level-19 pile-up is **legitimate graph structure, not an inverted edge**:

* **a giant 216-node SCC (id 749) sits entirely at Level 19** — 216
  mutually-recursive functions condensed into one component whose longest
  external callee path bottoms out at 19. That single SCC is 216 of the 292
  Level-19 nodes; the other 76 are independent nodes that also bottom out at
  19.
* The `2,237 − 1,993 = 244` (recount: **254**) cyclic nodes are spread across
  77 SCCs at Level 19 plus smaller cycles elsewhere (largest next: 13, 6, 6).
* **No edge is inverted.** The giant SCC's 144 external callers sit at Levels
  **19 (76), 20 (50), 21 (16), 22 (2)** — **zero below 19**. Levels 20/21/22
  are exactly `1 + 19` (callers of the giant SCC): 50/16/2 of them call into
  it. The invariant (`callee strictly below caller` for cross-SCC edges) holds
  with **0 violations across 5,449 edges** (278 thunk edges exempt as
  pass-through, 795 same-SCC).

Level 22 (3 fns): `r22_e57`, `r37_e137`, `r53_e88` — all unnamed RTLink
overlay entries that call into the giant SCC.

### Anomaly 3 — thunk slots polluting the naming queue (fixed) + 24 unresolved JMP FAR

Rank #22 `sub_2BFC3` (8 B) is **Thunk Slot #055** (`(0x2BFC3−0x2BD9D)/10 = 55`).
It sat at Level 0 because it is one of the thunk slots whose `JMP FAR` target
did not resolve to a function. **148 thunk slots** were in the Level-0
unnamed queue.

**Fix:** `naming_queue = unnamed − thunk_slots` (range `0x2BD9D..0x2C973`, 302
slots). Thunks stay in the graph as pass-through bridges but are excluded from
anything we intend to *name*.

**Why the JMP FAR is unresolved:** every thunk is 8 B = `call near sub_2AFBD`
(3 B, the loader trap) + `jmp far <target>` (5 B). The **278** "trap+real"
thunks resolve their far target to a function and emit a real edge. The **24**
"trap-only" thunks (the count is 24, not the hypothesized 7) have a far target
that lands on a **data item or mid-object**, so IDA names it `word_*`/`unk_*`
and no function→function edge is emitted — leaving only the trap edge (which we
exclude), hence Level 0. The 24 slots: #003,#004,#007,#008,#010–#014,#019–#024,
#055,#063,#067,#071,#102,#103,#120,#126,#142. Example: slot #012 `sub_2BE15`
→ `jmp far 6E8Fh:6DAh` = `0x2D63A` (lands past a function); slot #005-style
`0x2BDC5` → `word_6E009` (a data word).

### Anomaly 4 — `in_deg==0` dynamic leaves + DATA-class leaves (correct, documented)

* **`sub_1018F` (120 B, 337K dyn) and `sub_22AFF` (40 B, 229K dyn)** both have
  `static_in_degree == 0` **and zero raw inbound refs** (`CodeRefsTo` and
  `DataRefsTo` both empty). They are **indirect far-call dispatch targets**:
  called via `call far cs:[table]` where the target is stored/computed at
  runtime, so no direct ref exists. They are **not** ISRs (no vector DataRef)
  and **not** fall-through tails (both have proper prologues — `sub_1018F`
  starts `55 8B EC`, the standard `push bp; mov bp,sp`; `sub_22AFF` starts
  `push ax; cmp cs:byte_2224B,1`) and are `is_far=True`. Their high `dyn_calls`
  is exactly why the dual-tier rank puts them at #1/#3.
* **`sub_22C91` (13 B) and `sub_22C62` (41 B)** are classified `DATA`
  (`confidence: low`, `reason: "no ret in N bytes"`) but are **genuine code**:
  both decode to a `retf` terminator. `sub_22C62` is clean
  (`mov/mov/mov/retf` @`0x22C70`). **`sub_22C91` is truncated** — its span ends
  at `0x22C9E` (where a 2-byte `nullsub_19` sits) but the real chain runs to
  `retf` @`0x22CD4`, i.e. the function should be ~66 B, split by a spurious
  `nullsub_19`. The 13-byte epilogue window found no `retf` → `DATA`. These are
  classifier issues (window/truncation), not call-graph errors — they stay in
  the naming queue as unnamed code. **92 functions are `DATA`-class** (91 in
  the queue), all `"no ret in N bytes"`/low-confidence, mostly the large
  RTLink dispatch functions in the giant SCC.

### The fix, applied

`tools/callgraph_bottomup.py` now: (1) loads `function_bytes.json` and marks a
function **named iff `name` is non-null** (integer-ea join, not `sub_*`); (2)
computes `naming_queue = unnamed − thunk_slots` and reports both `unnamed` and
`to_name` per level; (3) exports `named`/`naming_queue`/`thunk_keys` alongside
the existing `scc_of`/`node_levels`/`static_in_degree`. The SCC/level logic was
already correct (0 invariant violations) and is unchanged.

### Corrected Level Summary + audit totals

| level | total | named | unnamed | to_name |
|---|---|---|---|---|
| 0 | 940 | 74 | 866 | **718** |
| 1 | 281 | 81 | 200 | 188 |
| 2 | 135 | 30 | 105 | 102 |
| 3 | 81 | 18 | 63 | 56 |
| 4 | 98 | 22 | 76 | 58 |
| 5 | 75 | 4 | 71 | 71 |
| 6 | 98 | 10 | 88 | 77 |
| 7–18 | … | … | … | … |
| 19 | 292 | 3 | 289 | 206 |
| 20 | 63 | 0 | 63 | 51 |
| 21 | 23 | 0 | 23 | 21 |
| 22 | 3 | 0 | 3 | 3 |

**Totals: 2,237 functions · named (fb join) 265 · unnamed 1,972 · thunk slots
302 · naming_queue 1,676 · Level-0 queue 718.**

**Clean Top-30 unnamed Level-0 (naming queue, thunks excluded)** — top by
`(dyn DESC, in_degree DESC)`:

1. `sub_1018F` (dyn 337K) 2. `sub_24E5D` (243K) 3. `sub_22AFF` (229K)
4. `sub_22C91` (DATA) 5. `sub_263F0` 6. `sub_22C62` (DATA) 7. `sub_25EF4`
8. `sub_25F0D` 9. `sub_22841` 10. `sub_22EE8` … 30. `sub_22DFA`.
(The 5 Finding-39 names and all 148 thunk slots are gone; `sub_2BFC3` no
longer appears.)

---

"""

ROW = ("| 2026-10-18 (session 21) | ~2 h | **Finding 65: call-graph audit -- 4 "
       "anomalies, 2 were real bugs, fixed.** (1) **named detection was a "
       "`sub_*` string match** -- wrong: ledger names keep the `sub_` IDA key "
       "(so `sub_112A1`=`input_status_pack` read as unnamed) and RTLink "
       "`r##_e##` read as named. Fixed: join **integer `ea`** via "
       "`function_bytes[k].name != null` (265 = 265 ledger, zero drift). (2) "
       "**Levels 20-22 '100% named' was the same bug** -- after the fix they "
       "are **0 named** (only Levels 0-2 were ever named in f39-48). The "
       "**Level-19 pile-up (292) is legitimate**: a **giant 216-node SCC "
       "(id 749) sits at Level 19** (216 of the 292; other 76 independent); "
       "**no inverted edge** -- the SCC's 144 external callers are at L19/20/"
       "21/22 (76/50/16/2), **0 below 19**; invariant **0 violations / 5,449 "
       "edges**. (3) **thunk slots polluted the queue**: `sub_2BFC3`=slot #055; "
       "**148** slots in Level-0 queue. Fixed: `naming_queue = unnamed - "
       "302 thunk slots`. **24** (not 7) trap-only thunks have unresolved JMP "
       "FAR (far target lands on `word_*`/`unk_*` data, e.g. slot #005 "
       "->`word_6E009`) so only the excluded trap edge remains -> Level 0. (4) "
       "**`in_deg==0` dyn leaves are indirect far-call dispatch targets** "
       "(`sub_1018F` 337K/`sub_22AFF` 229K: 0 CodeRefs+0 DataRefs, proper "
       "prologues, is_far, not ISR/fall-through); **DATA leaves are genuine "
       "code** misclassified by the epilogue window -- `sub_22C91` **truncated "
       "by a spurious `nullsub_19`** (real chain to `retf`@0x22CD4, span ends "
       "0x22C9E), `sub_22C62` clean `retf`@0x22C70; 92 DATA-class total (91 in "
       "queue) all low-conf 'no ret in window'. **Corrected:** 2,237 fns, "
       "named 265, unnamed 1,972, thunks 302, **naming_queue 1,676**, "
       "**Level-0 queue 718** (was 855 incl. thunks + 5 miscounts). Top-30 "
       "clean. |")

STATUS_PARA = (
    "**Call-graph audit (finding 65):** four anomalies in the `f55a16b` Level-0 "
    "report — two were real bugs, fixed. (1) **Named detection used a `sub_*` "
    "string match**, which misread ledger-named functions (they keep the "
    "`sub_` IDA key) as unnamed and RTLink `r##_e##` as named; now joins the "
    "**integer `ea`** through `function_bytes[k].name` (265 = 265 ledger, zero "
    "drift). (2) The **'Levels 20–22 ~100% named'** reading was the same bug — "
    "post-fix they are **0 named** (only Levels 0–2 were named in f39–48); the "
    "**Level-19 pile-up (292 nodes) is legitimate**: a **giant 216-node "
    "mutually-recursive SCC sits at Level 19**, with **no inverted edges** "
    "(its 144 external callers are all at Levels 19–22, **0 below 19**; "
    "invariant 0 violations / 5,449 edges). (3) **Thunk slots polluted the "
    "queue** (`sub_2BFC3` = slot #055; 148 slots in Level-0) — now excluded via "
    "`naming_queue = unnamed − 302 thunks`; **24 trap-only thunks** have "
    "unresolved `JMP FAR` (far target lands on `word_*`/`unk_*` data) leaving "
    "only the excluded trap edge. (4) **`in_deg==0` dynamic leaves** "
    "(`sub_1018F`, `sub_22AFF`) are indirect far-call dispatch targets (0 "
    "static refs, proper prologues, not ISR/fall-through); **DATA-class leaves** "
    "are genuine code misclassified by the epilogue window (`sub_22C91` "
    "truncated by a spurious `nullsub_19`). Corrected totals: **naming_queue "
    "1,676, Level-0 queue 718**."
)

OPEN_NEW = [
    "- **Call-graph audit done (finding 65):** named detection fixed (fb ea-join",
    "  = 265), thunk slots excluded (302), SCC/levels verified sound (giant",
    "  216-node SCC at L19, no inverted edges, 0 invariant violations).",
    "  **Corrected queue: 1,676 to-name, 718 at Level 0.** Top-30 clean (the",
    "  5 Finding-39 names + 148 thunks removed).",
    "- **Ready for Global Level-0 Batch 1:** name from the 718-entry Level-0",
    "  queue (dyn/in_degree ranked). Watch-outs from the audit: (a) 3",
    "  `in_deg==0` dyn leaves (`sub_1018F`, `sub_22AFF`, `sub_24D46`) are",
    "  indirect far-call targets -- name by body, no caller evidence; (b) 3",
    "  DATA-class leaves in the top-30 (`sub_22C91` [truncated by `nullsub_19`",
    "  -- real span to `retf`@0x22CD4], `sub_22C62`, `sub_25CCB`) need",
    "  epilogue-window reclassification before trusting their class; (c) 92",
    "  DATA-class fns total (91 queued), mostly large RTLink dispatch fns in",
    "  the giant SCC.",
    "- **Follow-ups:** reclassify the 92 low-confidence DATA fns (epilogue",
    "  window + the `nullsub_19` truncation of `sub_22C91`); consider whether",
    "  the 24 trap-only thunk far-targets deserve resolution (they point at",
    "  `word_*`/`unk_*` data -- possibly real targets behind data tables).",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 65" in raw:
    print("findings_log: 65 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 65 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 21" in raw:
    print("time_log: 21 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 20" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 21 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Call-graph audit (finding 65)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f65 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Call-graph audit done (finding 65)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f65 status (%d bytes)" % len(block))