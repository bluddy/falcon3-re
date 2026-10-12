from pathlib import Path

p = Path("docs/pipeline.md")
src = p.read_text(encoding="utf-8")
subs = [
    (
        "| 5 | C sources in `src/` | **Renames + comments**: meaningful function/variable/global names, `// why` comments | As part of porting; when a hypothesis renames a symbol, rename here too |",
        "| 5 | C sources in `src/` | **Renames + comments**: semantic names (via `naming.py apply`), disasm/args/logic annotation headers | As part of porting; renames go through registry/naming.yaml first |",
    ),
    (
        "| 2 | `registry/routines.yaml` | Per-routine convergence ledger: `{ea, class, hypothesis, port_status, port_file, verified}` | Classify / hypothesize / port / verify / disprove a routine |",
        "| 2 | `registry/routines.yaml` + `registry/naming.yaml` | Port ledger `{ea, class, port_status, ...}` + **rename ledger** (ida -> name) | Classify/port/verify a routine; rename via `naming.py` |",
    ),
    (
        "| 3 | `registry/game_knowledge.yaml`, `registry/FALCONCD.EXE.yaml` | Game systems & file-level facts (segments, thunks, strings, groups) | Discovered game mechanic or file-level structure |",
        "| 3 | `registry/game_knowledge.yaml`, `registry/structs.yaml`, `registry/FALCONCD.EXE.yaml` | Game systems, **struct definitions**, file-level facts | Game mechanic decoded / struct fields pinned down |",
    ),
    (
        "| 4 | `docs/structures.md` | Byte-level struct layouts of anything in files/memory | A format is decoded (even partially — mark what's unverified) |",
        "| 4 | `docs/structures.md` | Byte-level struct **narrative/history** (fields themselves go to registry/structs.yaml) | A format is decoded (even partially - mark what's unverified) |",
    ),
]
for old, new in subs:
    assert old in src, "NOT FOUND: " + old[:70]
    src = src.replace(old, new)
p.write_text(src, encoding="utf-8", newline="\n")
print("pipeline.md sinks updated:", len(subs))
