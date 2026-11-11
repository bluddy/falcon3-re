# IDB stabilisation (S1-S4): state, procedure and work queue

Written 2026-11-11 after finding 144.  This is the document to start from if you are picking up the IDB cleanup
(`status.md` -> "IDB readiness").  Anything an agent needs to continue S1c-4 without the earlier chat is here:
the current numbers, the exact cycle every finding follows, the pitfalls we hit, and a prioritised queue with a
measurement and a gate for each item.  The runbook for rebuilding the IDB from scratch is
[idb_regeneration.md](idb_regeneration.md); the per-finding record is `docs/findings_log.md` (findings 120-144).

## 1. Where we are

- **The live repaired IDB is canonical** (finding 124).  `analysis/ida_falconcd/FALCONCD.EXE.i64` is committed on purpose
  (binary, for transfer between machines).  Old names, old guesses and the pre-repair `function_bytes.json` are not truth;
  the committed ground truth is re-derived from the live IDB after every change.
- Applied through finding 144.  Findings 126-142 are committed (HEAD 7345a5e).  **143 (DATAFIX) and 144 (GLUE) are applied
  and fully gated but not committed** - ask the user for the commit first (stage list in section 4, step 10).
- Numbers after finding 144 (re-measure with section 5 before relying on them):

| Measure | Value | Tool |
|---|---|---|
| functions in `function_bytes.json` | 3,590 | `extract_ida_bytes.py` |
| naming ledger entries | 2,034 | `python tools/naming.py check` |
| orphan code runs (code heads owned by no function) | 96 runs / 221 B; 92 are 1-2 B padding, left on purpose | `analysis/s1/orphan_scan_probe.py` |
| orphan runs >= 3 B | 0x67BA3 (3 B), 0x6E16E (8 B), 0x6E7C7 (66 B), 0x6E8BC (3 B) | same |
| calls into a function body: targets / sites | 529 / 1,299 (was 524 / 1,409 after 124) | `analysis/segsplit/survey_mid.py` |
| - merged functions (target follows a ret/jmp) | 407 targets / 1,031 sites | same, class `after_ret_or_jmp(merged_fn)` |
| - fall-in entries with a prologue | 26 / 48 | class `fallthrough_entry_proloque` |
| - fall-in secondary entries | 23 / 68 | class `fallthrough_secondary_entry` |
| - not on an instruction head (misdecode) | 64 / 125 | class `not_head` |
| - other | 9 / 27 | class `other` |
| split of the 407 merged targets | 394 pure splits (978 sites), 12 shared tails (21 sites), 1 multi-chunk (32 sites) | `analysis/s1/merged_split_probe.py` |

The 394 "pure splits" are the biggest block of remaining S1 work and are the first item of the queue (P1).

## 2. Ground rules (all of them have bitten us)

1. **Canonical = live IDB.**  Never push the IDB back towards HEAD.  Every difference against HEAD must be explained by
   a manifest entry (`verify_rebuild.py` enforces it).
2. **Back up the `.i64` before mutating**: `cp FALCONCD.EXE.i64 FALCONCD.EXE.i64.bak_<reason><finding>` (gitignored).
3. **Manifest first**: plan -> dry replay -> apply -> idempotent replay -> extract -> gates.  Never edit the IDB by hand
   in an interactive session and call it done; every change must be replayable from `registry/*.json`.
4. **Never `auto_wait`, never `plan_range` in an apply tool** (that would drain the 94-function auto queue as a side effect).
   Apply tools save explicitly with `ida_loader.save_database()`; read-only probes set `DBFL_KILL` so nothing is saved.
5. **Probe on copies**: `cp analysis/ida_falconcd/FALCONCD.EXE.i64 analysis/s1/probe.i64`.  Plan and dry runs use a fresh
   copy each time; only the apply touches the live IDB.  Delete probe copies when done (`*.i64` is gitignored).
6. **Machine paths.**  Many old `tools/*.py` hardcode `C:\Users\yotam\...` and `venv\Scripts\python`.  On the ybarnoy
   machine use system `python` (3.9) and the `C:/Users/ybarnoy/projects/falcon3` absolute paths in new probes
   (`tools/apply_orphan_funcs.py` and `tools/extract_ida_bytes.py` use `ROOT = Path(__file__)...` and are portable).
   idat: `"/c/Program Files/IDA Professional 9.1/idat.exe" -A -S"C:/Users/ybarnoy/projects/falcon3/<script>.py" <idb>`.
7. **Line endings.**  The working copies of `docs/*.md`, `status.md`, `registry/*.yaml|json`, `docs/time_log.yaml` and
   `tools/verify_rebuild.py` are **CRLF**; `tools/apply_orphan_funcs.py` is LF.  Git has `autocrlf=true`, so HEAD shows LF.
   Edit with scripts that read with `newline=""`, normalise, edit, and write back in the file's own ending
   (pattern: `analysis/s1/doc145.py`).  Open with `encoding="utf-8"`.  Afterwards check that every line still ends in CRLF.
8. **`docs/findings_log.md` is append-only**, UTF-8, CRLF, heading style `## 2026-11-11 NNN - Title`.  One entry per
   applied finding; the next number is **145**.
9. **Do not use long inline `python - <<'E'` heredocs with nested quotes** to edit files; write a script file in
   `analysis/s1/` and run it.
10. **Commit only when the user asks.**  Stage files by name.  Messages end with
    `Co-Authored-By: Claude Code <noreply@anthropic.com>`.  Do not stage `analysis/s1/orphan_scan_probe.py` (it shows as
    modified with an unreviewed change) and `git checkout --` the tracked probe outputs after a scan
    (`analysis/s1/orphan_scan138.json`, `analysis/segsplit/survey_mid.json`).
11. If a live-IDB apply is blocked by the permission classifier, stop and tell the user (they may need `/permissions`
    or to run it with `!`).  Do not look for a way around it.

## 3. What each mode does (`tools/apply_orphan_funcs.py`)

One tool, one manifest (`registry/orphan_funcs_expected.json`).  A finding adds entries to the module-level constants
at the top of the tool; `OFMODE=plan` turns them into manifest records (hashing the bytes involved), and the default
mode replays the manifest.  Every record pins the sha256 of the bytes it touches, so a replay on a differently built
IDB fails instead of guessing.

| Constant / manifest key | Use it when | Effect |
|---|---|---|
| `ADD` -> `add_funcs` | a run of code heads owned by no function ends in a terminator (retn/retf/iret/jmp out) | `add_func(ea, end)` |
| `ADD_CLEAR` | the run holds a misdecoded stretch | clear `[lo,hi)`, recursive descent from the seeds, then add_func |
| `ADD_WORDS` | table words sit inside the cleared range | words are made again after the clear (142) |
| `FALL` | the function legitimately ends by falling into the next entry | skips the terminator check |
| `TAILS` | the function has a second chunk after a foreign function | `append_func_tail` (131, 141) |
| `MENUS` | jmp-reached R20/R21 menu bodies with a damaged `call far` | special decode (127) |
| `EXTEND`, `EXTEND_RUNS` -> `extend_funcs` | a function's body continues in orphan code (jcc/jmp or fall-through) | `set_func_end` or a tail chunk (128, 129) |
| `REBASE` -> `rebase_funcs` | the function start is a mid-instruction byte; the real entry is in front | delete, clear, redecode from the new start, same name (130, 132, 140) |
| `REMOVE` -> `remove_funcs` | a "function" is the head of a word table | delete function, remake `[ea,end)` as words (134) |
| `TABLEFIX`, `TEXTFIX` -> `table_fix`, `text_fix` | offset table plus message text were code | words / offsets / strings (135, 136) |
| `TRIM` -> `trim_funcs` | a function's tail is really data | move the end up, words behind it, redecode the rest (137) |
| `ABSORB` -> `absorb_funcs` | a bogus fragment function holds pieces of an owner's body | delete fragment, redecode, extend owner (138) |
| `DATAFIX` -> `data_fix` | an orphan "code" run is table / key data | clear, make words (`w`) or bytes (`b`); refuses on outside code xrefs (143) |
| `GLUE` -> `glue_funcs` | misdecoded pieces of one function's body are orphan or owned by a bogus fragment | clear, redecode from seeds, `append_func_tail` onto the owner (144) |

`verify_rebuild.py` classifies every difference against HEAD: LOST, ADDED, SPLIT, CARVE, REGISTER, RECODE, PATCH,
EXTEND, REBASE, REMOVE, TRIM, CHANGED.  `glue_funcs` is folded into EXTEND and REMOVE.  A new mode needs a matching
loader in `verify_rebuild.py` (look at `load_extends` / `load_removes`) or its changes will show as CHANGED / LOST.

## 4. The cycle for one finding (copy this)

Replace `NNN` by the finding number, `<tag>` by a short reason.  Probe copies are `analysis/s1/probe.i64`.

1. **Find and read the candidate.**  Run a read-only probe (section 5) and read the disassembly around it; decide what it
   really is (function, table, misdecode).  Look at xrefs in both directions.  Write probes as `analysis/s1/*_probe.py`
   with `os.environ["DBFL_KILL"]="1"` first and `idc.qexit(0)` last; write results to a file, not stdout.
2. **Encode the decision** in the constants of `tools/apply_orphan_funcs.py` (new tuples in the right list, with a one-line
   comment naming the finding).  If no mode fits, extend the tool (plan, apply, replay state function, `main` wiring,
   the changed-functions allowlist in `add_all`) and `verify_rebuild.py`, and add the mode to the table above.
3. **Back up**: `cp analysis/ida_falconcd/FALCONCD.EXE.i64 analysis/ida_falconcd/FALCONCD.EXE.i64.bak_<tag>NNN`.
   Save the manifest and ground truth: `cp registry/orphan_funcs_expected.json analysis/s1/ofe_before_NNN.json`,
   `cp analysis/ida_falconcd/function_bytes.json analysis/s1/fb_before_NNN.json`.
4. **Plan** on a fresh probe copy: `OFMODE=plan OFLOG=analysis/s1/of_plan_NNN.log idat ... tools/apply_orphan_funcs.py probe.i64`.
   It writes `registry/orphan_funcs_expected.json` and never saves.  **Fix the doubled CRs** it leaves
   (`\r\r\n` -> `\r\n`; one binary-mode replace).  Read the log; every record needs `must(...)` to have passed.
5. **Dry replay** on another fresh copy: `OFDRY=1 OFLOG=analysis/s1/of_dry_NNN.log`.  It applies and post-checks without saving.
   The log must show every entry applied and no mismatch.
6. **Apply** on the live IDB (no `OFMODE`, no `OFDRY`): `OFLOG=analysis/s1/of_apply_NNN.log`.
7. **Idempotent replay** on a new probe copy of the live IDB: `OFDRY=1 OFLOG=analysis/s1/of_idem_NNN.log`.
   It must say "already applied: nothing to do".
8. **Gates**, in this order:
   - extract on a probe copy: `idat -A -S".../tools/extract_ida_bytes.py" probe.i64` (updates `function_bytes.json`);
   - `ILOG=C:/.../analysis/s1/integrity_NNN.log idat -A -S".../analysis/s1/verify_idb_s1.py" probe.i64` -> `VERDICT: INTACT`;
   - `python tools/naming.py check` -> OK.  If a deleted function had a ledger entry, remove its entries from
     `registry/naming.yaml` and `registry/routines.yaml` (finding 144 did this for `r38_e149`);
   - `python tools/verify_rebuild.py` -> "faithful".  Explain every category count it prints; an unexplained
     CHANGED / LOST is a bug in the manifest or the tool, not something to allowlist.
9. **Document**: append `## 2026-11-11 NNN - Title` to `docs/findings_log.md` (what was found, what was done, numbers,
   the gate results, what is still open); add a bullet to the S1c list in `status.md` and the new function count;
   append the finding to step 6g of `docs/workflow/idb_regeneration.md`; add a `docs/time_log.yaml` row if the session is new.
10. **Commit only when asked.**  Usual stage list: `analysis/ida_falconcd/FALCONCD.EXE.i64`,
    `analysis/ida_falconcd/function_bytes.json`, `docs/findings_log.md`, `docs/workflow/idb_regeneration.md`,
    `registry/orphan_funcs_expected.json`, `status.md`, `tools/apply_orphan_funcs.py`; plus `registry/naming.yaml`,
    `registry/routines.yaml`, `tools/verify_rebuild.py` when they changed.  Then `git status`.

Common IDA traps seen so far: a user name on a mid-instruction address blocks `create_insn` (`del_func` and
`set_name(ea, "", SN_NOWARN)` first); `function_bytes.json` records only the main chunk of a function; its key is the
previous extract's key for the same ea, else `sub_%X`; xref types `fl_CF=16, fl_CN=17, fl_JF=18, fl_JN=19, fl_F=21`;
the end of a word / jump table decoded as code usually hides a real function behind it.

## 5. Measuring (all read-only, on a probe copy)

| Question | Run | Output | Restore afterwards |
|---|---|---|---|
| unowned code runs | `analysis/s1/orphan_scan_probe.py` | `analysis/s1/orphan_scan138.json` | `git checkout -- analysis/s1/orphan_scan138.json` |
| calls into function bodies, by class | `analysis/segsplit/survey_mid.py` | `analysis/segsplit/survey_mid.json` | `git checkout --` it, or keep it if you are re-baselining the numbers in status.md |
| which merged targets are safe to split | `analysis/s1/merged_split_probe.py` | `analysis/s1/merged_split.json` | untracked; keep |
| overall coverage | `analysis/segsplit/survey_ready.py` | `analysis/segsplit/survey_ready.json` | - |

## 6. Work queue

Order is by value for the function-by-function reading.  Each item has a measure (how to see progress) and a gate.
Items P1-P4 are S1 proper; P5+ close S1 or belong to S2-S4.

**P0. Commit findings 143 and 144** (user decision).  Gate: `git status` clean apart from scratch.

**P1. Split the merged functions (new `SPLIT` mode).**  407 call targets (1,031 sites) land right after a `ret`/`jmp`
inside a function: two or more functions were registered as one.  `merged_split_probe.py` classifies them:
394 targets are *pure splits* (no jump or jcc from anywhere in the function reaches the target, so
`[start, t)` and `[t, end)` are independent), 12 are shared tails (a `jz`/`jmp`/`loop` inside the function reaches the target:
those are real tails of one function and must NOT be split; leave them or give them a tail-chunk treatment),
1 has several chunks (`segment_clip_test` 0x25F93, 32 sites; do by hand).
  - Design: `SPLIT = [(owner, at)]` -> manifest `split_funcs` {ea, at, end, name, far, sha256 of `[ea,at)` and `[at,end)`}.
    Apply: `set_func_end(owner, at)` then `add_func(at, end)`; the new function is unnamed, far flag and DS range copied from the owner;
    refuse if any code xref (other than a call) crosses `at` in either direction, if the tail does not end in a terminator,
    or if the owner has tail chunks.  `verify_rebuild.py`: fold `split_funcs` into the SPLIT category (exact children).
  - Do it in batches of ~40 (by segment, so a bad assumption shows up early), one finding per batch, and read 5-10 samples
    from each batch first.  The renamed owner keeps its name; its semantic name may now be partly wrong, so check the ledger
    entries of the owners you split and note any that need a rename.
  - Measure: `survey_mid.py` merged targets 407 -> about 13.  Gate: the cycle above; the function count grows by the batch size.
  - Risks: a "pure" tail that is really the body of an indirect-jump switch (jump-table target not yet an xref) - check for
    data xrefs into `[start, end)` and for `jmp cs:[bx+...]` in the owner; and tails that are data, not code (ends without a terminator).

**P2. Misdecodes (`not_head`: 64 targets / 125 sites).**  A call lands in the middle of an instruction.  Usually the caller's
target is right and the owner's decode is wrong (like 0x16F4B1, finding 140), or the caller is itself misdecoded data.
Per target: disassemble both alignments, decide, then `REBASE` / `GLUE` / `DATAFIX` / `ADD_CLEAR`.  Measure: `survey_mid.py`.

**P3. Fall-in entries (49 targets / 116 sites).**  A function falls into a second entry that other code calls.
Prologue-bearing ones (26) are two functions that should be split at the prologue (same mechanism as P1 but with a fall-through:
the first part needs `FALL`-style handling or an explicit `jmp`); secondary entries (23) are legitimate multi-entry functions
- IDA cannot express them, so record them (see P8) rather than split them.

**P4. `other` (9 targets / 27 sites)** and the **shared tails** from P1: read each by hand.

**P5. The 0x6E696..0x6E8B7 handler cluster / R30 menu state machine.**  One giant `[bp+6]` / `[bp-0Eh]` switch function now
split into about 25 named pieces (listed in status.md "Left open"), plus the orphan runs 0x6E7C7 (66 B), 0x6E8BC (3 B) and
0x67BA3 (3 B).  Needs a function-merge mechanism (the inverse of P1: delete the pieces, redecode as one body, move the
ledger names to a comment or a case-label list) and a decision on the owning function.  The 15-word switch table at 0x69209
(offsets from 0x669F0, `jmp cs:jpt_674CF[bx]` at 0x674CF) has 6 of 15 cases decoded; the others (0x68A18, 0x68A5E, 0x68AE2, 0x68C02,
0x68CC0, 0x68E49, 0x68F20, 0x69123) are undecoded.  0x6940B (`enter 6,0`) is the real start of r30_record_link; 0x69227 is a
real far entry.  Do it last in S1: it is the only place where ledger names are lost.

**P6. Remaining small orphans**: 0x6E16E (8 B of data with two far-call xrefs from 0x6EF5D and 0x6F60C - check what the callers
expect), the 1-2 B padding runs (leave).  Measure: `orphan_scan_probe.py`.

**P7. Drain the auto queue under a manifest.**  The queue holds about 94 functions that IDA would add when autoanalysis runs.  Export
the queue (read-only), review it, and register the good ones through `ADD` (the bad ones are data).  Only then may a later step run
`auto_wait`.  Gate: queue empty and integrity INTACT.

**P8. Housekeeping found on the way**: thunk anomalies (0x2BE1F, 0x2C153, 0x2C17B and the 34 no-variant thunks); the merge of
0x3F861 with 0x3FB22; the stale `counts:` block in `registry/routines.yaml`; a multi-entry-function list (P3 secondary entries) so
the deep dive knows them; the `step` text in the orphan manifest still says "findings 126-139"; delete the `analysis/s1/probe*.i64`
copies and old scratch; refresh `docs/workflow/next_steps_for_future_agents.md`.

**P9. S2 VGRAPH.**  About 1.0M of 10.7M traced far calls (9.4%) go to CS 0x77A3, a 12 KB runtime-loaded heap block holding
`game\VGRAPH` (40-word entry table at file offset 0 matches; the EXE names `vgraph`/`egraph1`/`egraph0` at file 0x1D518;
`VGRAPHH`/`VGRAPHM` are variants).  Add it as a segment with the entry table and xrefs; scan for other loaded drivers.

**P10. S3 trace edges.**  527 indirect call/jump sites have no target xref and 604 functions have no static caller.  Turn the traced
indirect targets into user xrefs, then rebuild the collapsed call graph (`tools/export_callrefs.py`, `tools/callgraph_bottomup.py`)
and its levels.

**P11. S4 deep dive** bottom-up through the DAG, re-checking existing names (some of the 1,994 old names rest on the old wrong xrefs).

S1 is done when `survey_mid.py` shows mid-body targets at or near zero (apart from documented multi-entry functions), the orphan scan
shows only padding, the auto queue is empty, and integrity, `naming.py check` and `verify_rebuild.py` are green.

## 7. Report format when you finish a finding

Findings entries should say: what the scan or probe showed (with addresses), what each address really is, which constants/manifest
keys were added, the before/after counts (functions, ledger, orphan bytes or mid-body targets), the gate results
(integrity, naming, verify_rebuild categories, idempotent replay), the backup name, and what is still open.  Keep them short;
the manifest holds the exact data.
