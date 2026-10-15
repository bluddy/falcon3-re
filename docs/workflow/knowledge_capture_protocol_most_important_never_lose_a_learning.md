# Knowledge Capture Protocol (MOST IMPORTANT — never lose a learning)
## Knowledge Capture Protocol (MOST IMPORTANT — never lose a learning)

Every finding has exactly one canonical sink. Fill them **as you learn**, and update
them **as you disprove**; the findings log is append-only history, the registries are
current state.

| # | Sink | Holds | Write when |
|---|------|-------|-----------|
| 1 | `docs/findings_log.md` | Chronological history: hypotheses, evidence, confirmations, **disprovals, dead ends** | Every session, append only. Mark disproved entries `DISPROVEN` — never delete |
| 2 | `registry/routines.yaml` + `registry/naming.yaml` | Port ledger `{ea, class, port_status, ...}` + **rename ledger** (ida -> name) | Classify/port/verify a routine; rename via `naming.py` |
| 3 | `registry/game_knowledge.yaml`, `registry/structs.yaml`, `registry/FALCONCD.EXE.yaml` | Game systems, **struct definitions**, file-level facts | Game mechanic decoded / struct fields pinned down |
| 4 | `docs/structures.md` | Byte-level struct **narrative/history** (fields themselves go to registry/structs.yaml) | A format is decoded (even partially - mark what's unverified) |
| 5 | C sources in `src/` | **Renames + comments**: semantic names (via `naming.py apply`), disasm/args/logic annotation headers | As part of porting; renames go through registry/naming.yaml first |
| 6 | ASM listings/transcriptions | **Comments** annotating hand-ASM routines (intent, register roles) | As routines are transcribed/classified |
| 7 | `status.md` | **Bump `Last updated` + append a Time Log row every status change** (so staleness is measurable) | Whenever project state changes meaningfully |

Rules of thumb:
- **Hypothesis made** → registry entry (`class`/`hypothesis`) + findings log line.
- **Hypothesis disproved** → flip the registry value, leave a `notes:` trail, append the
  disproval to the findings log (see Finding 09 for the pattern).
- **Routine verified** → `port_status: verified`, source file kept in `src/`,
  byte recipe noted (e.g. `/AL + int far`).
- **Rename** lands in three places consistently: registry `hypothesis`, the C/ASM file,
  and (if it changes understanding) a findings-log entry.
- Structures never overwrite — extend `structures.md` sections and mark decode status.

---