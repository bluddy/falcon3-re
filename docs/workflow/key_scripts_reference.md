# Key Scripts Reference
## Key Scripts Reference

| Script | Purpose | Track |
|--------|---------|-------|
| `tools/ida_snapshot.py` | IDA headless: full analysis → survey.json/functions.tsv | A |
| `tools/extract_fixups.py` | Parse RTLink fixup tables statically | A |
| `tools/analyze_all_records.py` | Record/segment-group analysis | A |
| `tools/rtlink_scan.py` | RTLink directory scanner | A |
| `tools/prep_overlay_placement.py` | Per-record file base + runtime block + addr assignment → `overlay_placement.json` | A |
| `tools/find_cluster_b.py` | Locate cluster-B rows (B0=0xFFFA0, finding 20) | A |
| `tools/rebuild_overlay_segments.py` | Rebuild IDB overlay segments from raw bytes (finding 19) | A |
| `tools/prep_overlay_entries.py` | Thunk targets → entry_ea map → `overlay_entries.json` | A |
| `tools/mark_overlay_entries.py` | Content-driven entry marking (fallback row candidates) | A |
| `tools/validate_fixup_semantics.py` | Host-side fixup semantics check → `fixups_to_apply.json` | A |
| `tools/apply_overlay_fixups.py` | Apply +0x1000 fixups in IDB (byte-guarded, RTFIX marker) | A |
| `tools/extract_ida_bytes.py` | Live IDA functions → function_bytes.json (ground truth) | A |
| `tools/classify_routines.py` | All functions → C/ASM/DATA/LEAF/NEARTHUNK + port queue | A |
| `tools/portcheck_falcon.py` | Single-routine C verify (Track B driver) | B |
| `tools/compile_msc51.py` | Standalone MSC 5.1 compile wrapper | B |
| `tools/libscan.py` | Library signature matching (needs MSC 5.1 libs) | A/B |
| `tools/mzhdr.py`, `mzparse.py` | MZ header/relocation tools | A |
| ~~`tools/apply_fixups_ida.py`~~ | SUPERSEDED (old mis-based fixups; segments rebuilt) | A |
| `scripts/extract_routines.py` | **TODO (copy gunship)** `.cod` → `.asm` + EXTRN | C |
| `scripts/replace_routines.py` | **TODO (copy gunship)** hybrid asm builder | C |
| `tools/splice.py` | **TODO** patch verified bytes into EXE copy (Track 1) | C |
| `mzdiff` / `mzmap` (WSL, shared w/ gunship) | Instruction-stream diff / segment map gen — generic, not game-specific | C |

---