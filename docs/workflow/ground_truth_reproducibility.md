# Ground Truth & Reproducibility
## Ground Truth & Reproducibility

**Authoritative byte source: `analysis/ida_falconcd/function_bytes.json`** (committed,
text) — per-function bytes *as they exist at runtime* (raw EXE + MZ relocations +
RTLink fixups). `portcheck_falcon.py` compares C output against it. The IDB is the
*analysis* ground truth (boundaries, names, segments, fixups, comments) but is
**binary, local-only, and never committed** — everything that must survive lives in
committed JSON/C/YAML/markdown instead.

| Artifact | Role | In git? |
|---|---|---|
| `game/FALCONCD.EXE` (+variants) | primary raw input | ❌ local (`game/` ignored) |
| `FALCONCD.EXE.i64` (+.id0/.id1/…) | analysis DB: boundaries, names, fixup state, comments | ❌ local (binary, regenerable) |
| `function_bytes.json` | **byte ground truth for portcheck** | ✅ |
| `classification.json`, `overlay_placement.json`, `overlay_entries.json`, `fixups_to_apply.json`, `rtlink_records.json`, `record_fixup_located.json`… | derived analysis state | ✅ |
| `survey.json`, `functions.tsv`, `prologues.json`… | regenerable intermediates | ❌ (ignored, rerun scripts) |
| `src/*.c`, `src/asm/*.asm` | ported code + annotations (protocol sinks 5/6) | ✅ |
| `registry/*.yaml`, `docs/*`, `findings_log.md` | hypotheses + history (sinks 1–4) | ✅ |

### IDB regeneration runbook (fresh clone / lost IDB)

Prereqs: local `game/FALCONCD.EXE`, IDA Pro 9.1 at
`C:\Program Files\IDA Professional 9.1\idat.exe`. Committed JSONs make the host-side
steps unnecessary unless the EXE itself changed.

```
:: 1. fresh analysis (creates survey.json etc.; legacy overlay layout - will be replaced)
idat -A -S tools\ida_snapshot.py       analysis\ida_falconcd\FALCONCD.EXE.i64

:: 2. IDA: rebuild overlays from committed placement + mark entries + fixups + extract
idat -A -S tools\rebuild_overlay_segments.py    analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\_add_missed_fn.py              analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\mark_overlay_entries.py        analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\apply_overlay_fixups.py        analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\extract_ida_bytes.py           analysis\ida_falconcd\FALCONCD.EXE.i64

:: 3. host: classification + sanity portcheck
venv\Scripts\python tools\classify_routines.py
venv\Scripts\python tools\portcheck_falcon.py sub_16FDD --source src\sub_16FDD.c --segment 0x16FD --offset 0xD
```
(Host-side regen of the committed JSONs, only if the EXE changed:
`prep_overlay_placement.py` → `prep_overlay_entries.py` → `validate_fixup_semantics.py`,
then steps 2–3.)

**Rules**: any IDB-modifying step → re-run `extract_ida_bytes.py` + `classify_routines.py`
and commit both; names/comments set only in the IDB are conveniences — canonical text
belongs in `src/asm/`, `registry/`, or `docs/` (IDB is never the only copy).
**The IDB is not committed** (binary, `*.i64` ignored): losing it costs one runbook
pass (~6 headless IDA runs), not the knowledge.

### Can this rebuild the binary? (rebuild verdict)

- **YES — code, via splice (Track C).** Every routine is either C-ported
  (byte-verified by portcheck) or will be hand-ASM-transcribed; patched into a
  copy of the original EXE at its file offset. Because patched bytes are
  byte-identical by construction, all 2717 MZ relocations, the RTLink directory
  and the whole 1.2 MB tail remain valid unchanged → the spliced EXE is
  byte-identical over the regenerated fraction. As coverage grows → full image.
  `mzdiff` proves it instruction-by-instruction.
- **From-scratch rebuild (no original EXE)** additionally needs: all data
  (non-function bytes) regenerated, MZ relocation table recomputed, RTLink
  container (directory/thunks/fixup tables) re-emitted, tail assets re-packed
  (packing format still UNKNOWN, finding 31).
  Not required for the splice path; the RTLink linker itself does not exist as a
  binary, so a faithful relink is off the table either way.
- Current code coverage: 16 routines / 846 bytes verified out of ~83 KB resident
  code (≈1%) — the methodology is proven, the volume is the remaining work.

---