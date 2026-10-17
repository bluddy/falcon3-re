# IDB Regeneration Runbook (canonical)

> **This is the single source of truth** for rebuilding
> `analysis/ida_falconcd/FALCONCD.EXE.i64` from scratch. `docs/pipeline.md`
> links here instead of carrying its own (previously divergent) copy.
> Audit: finding 40.

The IDB is **not committed** (`*.i64` ignored, binary). Everything else it
encodes *is* committed — so a faithful rebuild costs one runbook pass and
loses no knowledge. **The check that a rebuild is faithful is step V.**

---

## Prerequisites

| need | where | status |
|------|-------|--------|
| `FALCONCD.EXE` (md5 `2BDD74F4B50729B8583224CCE471805A`) | **NOT in git** (`game/`, `*.exe` ignored) — re-obtain from a legal install and verify against `registry/FALCONCD.EXE.yaml` | manual |
| IDA Pro 9.1 (headless `idat.exe`) | `C:\Program Files\IDA Professional 9.1\idat.exe` | local |
| python venv + pyyaml | `venv\` | local |
| committed analysis JSONs | `analysis/ida_falconcd/*.json`, `analysis/traces/*.json` | ✅ git |
| committed traces (for step 8/10) | `memdump/*_{fileio,fartrans}.jsonl` | ✅ git |

**Never open Falcon in interactive IDA** (it holds the Gunship DB). Always
`idat.exe` headless.

---

## Step 0 — stage the binary

```powershell
# verify provenance first!
Get-FileHash game\FALCONCD.EXE -Algorithm MD5   # must be 2BDD74F4B50729B8583224CCE471805A
Copy-Item game\FALCONCD.EXE analysis\ida_falconcd\ -Force
```

## Step 1 — create the IDB (verified: works from a bare .EXE)

```
idat -A -S tools\ida_snapshot.py analysis\ida_falconcd\FALCONCD.EXE
```
Creates `FALCONCD.EXE.i64` + `survey.json`/`functions.tsv`/`overlays.json`,
adding RTLink record groups as segments. Saves explicitly (finding 40).
*(If the `.i64` already exists you may pass the `.i64` path instead.)*

## Step 2 — IDA: structure, entries, fixups

```
idat -A -S tools\rebuild_overlay_segments.py analysis\ida_falconcd\FALCONCD.EXE.i64  # layout from committed placement
idat -A -S tools\_add_missed_fn.py            analysis\ida_falconcd\FALCONCD.EXE.i64  # sub_19D65 (finding 26)
idat -A -S tools\add_missed_functions.py      analysis\ida_falconcd\FALCONCD.EXE.i64  # 11 kb-unit gap fns (finding 28)
idat -A -S tools\add_gap_functions.py         analysis\ida_falconcd\FALCONCD.EXE.i64  # 59 gap-sweep fns (finding 28b)
idat -A -S tools\mark_overlay_entries.py      analysis\ida_falconcd\FALCONCD.EXE.i64  # 184 thunk entries -> ~192 fns
idat -A -S tools\apply_overlay_fixups.py      analysis\ida_falconcd\FALCONCD.EXE.i64  # 25,222 fixups
```

## Step 3 — IDA: trace-driven repair (finding 33, +135 fns)

Needs `analysis/traces/boundary_report.json` (committed).

```
idat -A -S tools\apply_trace_functions.py     analysis\ida_falconcd\FALCONCD.EXE.i64
```
*(3 iterations historically; the script is idempotent-ish — `get_func` guards
skip already-split/registered ranges.)*

## Step 4 — IDA: patch the .RTLink thunk table (finding 35)

Needs `analysis/traces/thunk_states.json` (committed).

```
idat -A -S tools\patch_thunks_ida.py          analysis\ida_falconcd\FALCONCD.EXE.i64
```
299/303 thunks at IDA EA **0x2BD9D**: E8 trap → NOPs at +0..+2 so IDA flows
into the JMP FAR at +3; segments converted (JSON seg + 0x0E5E = IDA seg).
Log: `analysis/ida_falconcd/patch_thunks.log`.

## Step 5 — IDA: register functions missed by auto-analysis

Needs `boundary_report.json` (committed). These four are the finding 37/38/39
registrations; all are guarded (skip if the fn already exists).

```
idat -A -S tools\add_boundary_functions.py   analysis\ida_falconcd\FALCONCD.EXE.i64  # 0x1018F dispatcher
idat -A -S tools\add_trace_functions.py      analysis\ida_falconcd\FALCONCD.EXE.i64  # 18 from UNKNOWN targets
idat -A -S tools\fix_trace_functions.py      analysis\ida_falconcd\FALCONCD.EXE.i64  # force 15 known-good ranges
idat -A -S tools\add_indirect_targets.py     analysis\ida_falconcd\FALCONCD.EXE.i64  # 0x17263, 0x286CE
idat -A -S tools\restore_level0.py           analysis\ida_falconcd\FALCONCD.EXE.i64  # 4 hot L0 leaves (finding 39)
```
> `restore_level0.py` is normally a no-op (skips existing fns); it exists
> because a diagnostic once destroyed those 4 via `del_items` (finding 39).

## Step 6 — IDA: regenerate ground truth (overwrites the file)

```
idat -A -S tools\extract_ida_bytes.py         analysis\ida_falconcd\FALCONCD.EXE.i64
```
Preserves stable keys + `name` fields from the previous extract.

## Step 7 — IDA: export last instructions, then host: classify

```
idat -A -S tools\export_epilogues.py           analysis\ida_falconcd\FALCONCD.EXE.i64
venv\Scripts\python tools\classify_routines.py
```

`export_epilogues.py` writes `analysis/ida_falconcd/last_insns.json`
({name: last mnemonic, callers, interior refs}) and is **committed**, so a
fresh clone classifies identically without an IDA run — `classify_routines.py`
falls back to byte-only heuristics if it is missing.

**Do not point it at `epilogues.json`** — that path belongs to
`extract_prologues.py` and holds a `{hex-pattern: count}` map for compiler
fingerprinting. A different schema, same word (finding 49).

Why the IDA pass is needed: classifying from raw bytes only tests for a
trailing `c3`/`cb`, which misses tail jumps, `ret imm16`, `iret` and any
range running a few bytes past its last `retn` — that mislabelled **128 real
routines as DATA** (finding 49).

## Step V — VERIFY (do this before committing anything)

```
venv\Scripts\python tools\verify_rebuild.py
```
Diffs the fresh `function_bytes.json` against **git HEAD** and reports
LOST / ADDED / SPLIT / RECODE / PATCH / CHANGED. Exit 1 = divergence → fix the
failing step; never commit a diverged ground truth.

`SPLIT` (old fn subdivided, full coverage), `RECODE` (size changed but
`(key, ea, old_size, new_size)` matches `registry/bitness_fix_expected.json`
exactly) and `PATCH` (same `key`/`ea`/`size`, and **both** the pre- and
post-change sha256 match `registry/subblock_fixups_expected.json`) are the
only intentional-change classes and none counts against the gate. Both
manifests are **exact-match on purpose** — a bulk re-derivation like finding
53's bitness fix or finding 57's sub-block fixups must list every function it
touches (byte patches additionally pin the bytes on both sides, so a rebuild
that patches the wrong word still fails as CHANGED), so neither can become
precedent for silent drift. If you deliberately change more, regenerate the
manifest with `tools\make_subblock_manifest.py` and commit it in the same
change.

```
venv\Scripts\python tools\naming.py check       # ledger/routines/structs consistency
venv\Scripts\python tools\naming.py push-ida    # re-sync semantic names into the IDB
```

After any IDB mutation, also run the **semantic integrity gate** (it reads the
live database, so it needs idat):

```
cmd /c "tools\run_idat.bat tools\verify_idb.py"
type analysis\ida_falconcd\integrity.log        # expect VERDICT: INTACT
```

Every recorded function must still exist at its recorded EA with its recorded
span and name. **Do not use MD5 for this** (finding 50): idat rewrites the
`.i64` on every invocation — including read-only runs — so a hash comparison
against a backup false-alarms after the very next run, and comparing a file
against its own fresh copy always "succeeds" while proving nothing.

Note `push-ida` resolves entries by their old `sub_*` name, so after a
**split or rename** it will report `MISSING` and skip them; use an EA-keyed
rename for entries whose IDA name no longer matches the ledger `ida` key
(finding 50).

## Step 8 — callgraph (optional, after any IDA change)

```
idat -A -S tools\export_callrefs.py            analysis\ida_falconcd\FALCONCD.EXE.i64
venv\Scripts\python tools\callgraph_bottomup.py
```
→ `analysis/traces/callgraph_partial.json`.

---

## If the EXE itself changed (not the common case)

Regenerate the committed JSONs first, then re-run steps 1–V:
`prep_overlay_placement.py` → `prep_overlay_entries.py` →
`validate_fixup_semantics.py`.

## Rules

1. **Every IDB-mutating script must call `ida_loader.save_database()`
   explicitly.** Never rely on idat's implicit exit-save — it silently
   persisted a destructive diagnostic change (finding 39) and several scripts
   once depended on it (finding 40).
2. **Any IDB-mutating step → re-run step 6 + 7 and commit both**, plus
   `verify_rebuild.py` green.
3. **Diagnostics must never `del_items` existing functions** — read existing
   item heads instead (`tools/dump_level0.py` is the pattern).
4. **Text-scan tools must prune `dosbox*` under `src/`** (two full DOSBox
   trees live there, 70 MB).
5. **The IDB is never the only copy** of a name/comment/hypothesis — canonical
   text belongs in `src/`, `registry/`, or `docs/`.
6. **Back up the `.i64` before any high-consequence mutation** (deleting or
   subdividing an existing function, bulk re-analysis): copy it to
   `<IDB>.bak_<reason>` first. The IDB is not in git, and idat *may* persist a
   dirty DB on exit even if your script refuses to save — so "I aborted" is not
   a rollback. Pattern used for the `sub_2E2D0` split (finding 42).
7. **`verify_rebuild.py` classifies a shrink as `SPLIT` (not `CHANGED`) when
   the old range is exactly tiled by the new functions** — so deliberate
   subdivisions pass the gate while accidental byte drift still fails it.
   If you see `CHANGED`, it is drift; if you see `SPLIT`, confirm it is yours.
