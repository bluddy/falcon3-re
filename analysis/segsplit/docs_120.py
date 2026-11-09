"""One-shot doc update for findings 120/121 (run from repo root)."""
from pathlib import Path

F120 = r'''
## 2026-11-09 120 - R05_1E10 / R29_1E10s split into their RTLink object segments; near-branch targets re-based
Status: CONFIRMED

**Problem.** R05_1E10 (`0x2E100..0x669F0`, 231 KB) and R29_1E10s (`0x11C3C0..0x154CB0`) were each one IDA
segment with base = record start. In real mode a near CALL/JMP/Jcc wraps IP inside the *runtime CS*, which
for these records is a different paragraph per linked object segment: the distinct `seg` words of the
record's fixup table (finding 56; same anchors finding 119 uses for R53). IDA therefore resolved branches
against the wrong base. In R05, ~4,300 of 7,700 near branches pointed at the wrong bytes (2,074 Jcc and 601
CALL landed in non-code). No other overlay is affected: every other record's anchors sit inside one 64 KB
window and give the same targets (measured, `analysis/segsplit/probe_quant.json`).

**Gemini proposal refuted.** The pasted transcript proposed splitting R69/DGROUP because "IDA can't track
DS/ES". That is wrong: IDA already tracks DS/ES after all 17,150 immediate segment loads and produces 17,106
correct ES drefs. Splitting R69 would be cosmetic only.

**Fix (`tools/split_overlay_segments.py`, manifest `registry/segsplit_expected.json`).** 47 segments:
- 23 R05 segments + 1 tail, 21 R29 segments + 1 tail. Each segment's base paragraph = its fixup frame
  `ida_ea + (seg - w0)*16`, so the IDA selector is the true CS.
- A segment may start at a non-zero offset in its frame. The start is pushed past the previous block's last
  fixup word and past any function the cut would split. Six cases:
  - R05: `0x43AEE`, `0x4F256`, `0x4FD8D`.
  - R29: `0x11EB7F`, `0x1230EB`, `0x1282A7`, `0x131615`, `0x132805`, `0x1365A2`.
  - The earlier "straddling functions" were the end of the previous object (retf) running a few bytes into
    the next frame's paragraph. They are not wrong function ends.
- Blocks reaching 64 KB past their base get a tail cut at base+0x10000. These are `R05_54AF` (`0x64AF0..`)
  and `R29_4FC2s` (`0x14DEE0..`), both data/unexplored only.
- After re-basing, every code head in the 47 segments is re-created (75,190 heads). Analysis xrefs are
  dropped first and re-derived (18,542). `XREF_USER` crefs from finding 119 are kept.
- Two 1-byte truncated heads (`0x2EFE5`, `0x2F593`) are skipped.
- 4 functions starting with `nop` were nudged +1 by IDA; their recorded starts are restored.
- Segment-register ranges are replayed and the default DS/ES/SS of each new segment is seeded from the value
  live at the cut.

**Measured effect** (near-branch target classes, `analysis/segsplit/branch_{base,split}.json`):

| R05 | before | after |
|---|---|---|
| CALL -> function start | 499 | **843** |
| CALL -> non-code | 601 | **81** |
| Jcc -> instruction head | 3,696 | **5,534** |
| Jcc -> non-code | 2,074 | **48** |
| JMP -> non-code | 94 | **8** |

R29: Jcc -> non-code 113 -> 2, JMP -> non-code 15 -> 1.

Sreg tracking after re-decode:
- ES unknown->known 3,957 (`mov ax,imm / mov es,ax` sequences previously hidden behind mis-targeted flow).
- DS/ES follow-CS 644 (`push cs / pop ds`).
- known->unknown 37 (below the gate's 0.1 % threshold).

**Gates.**
- Function table identical (3,354).
- `verify_idb` output **byte-identical to the pre-split baseline**. Note: the baseline itself is DAMAGED
  versus the committed `function_bytes.json`: 3 missing, 91 span, 49 name and 5 hole problems. That is
  pre-existing drift between the committed i64 (`61884c7`) and the 2026-11-08 ground truth, not caused by
  this change.
- `extract_ida_bytes` output **byte-identical to a pre-split extract** (bytes/spans untouched).
- Second run is a no-op ("already split").
- Backup: `analysis/ida_falconcd/FALCONCD.EXE.i64.bak_segsplit` (md5 `a313ca27...`).

**Runbook:** run after `fix_overlay_jumps_ida.py` (step 6b). Tooling note: idat persists a dirty database on
exit even without `save_database()`. The script now sets `DBFL_KILL` on any failure (verified to discard
in-memory changes).

## 2026-11-09 121 - DGROUP PROVEN = link para 0x6A32 (IDA 0x7A32, runtime 0x6C27 session A); SS = DS = DGROUP
Status: CONFIRMED (supersedes the HYPOTHESIS in findings 34/35; corrects finding 35's "Borland C0L" basis)

**Startup code.** The stub at EXE file `0x1FFEA` (R01_1CF6, IDA ~`0x2D31A`) is
`8C D0 BB 32 6A 2B C3 C1 E0 04 FA 8E D3 03 E0 FB 33 D2 8E DB`, i.e.
`mov ax,ss; mov bx,6A32h; sub ax,bx; shl ax,4; cli; mov ss,bx; add sp,ax; sti; ...; mov ds,bx`.
- It rebases the MZ stack `752C:0800` to `6A32:B7A0`, so SS = DS = DGROUP.
- The C startup it calls stores DS in `CS:[0084:0002]`. Memdumps hold `0x6C27` there in session A (load
  base 0x1F5) and `0x6BD4` in session B (0x1A2). Both equal 0x6A32 + load base.

**Byte check.** DGROUP initialized data = EXE file `0x1448A0..+0xAD47` = IDA `0x7A320..0x85067`, the tail
of R69_606E.
- Against MEMDUMP1 at runtime para 0x6C27 it matches **5,706 / 5,710** nonzero bytes. Shifted +-1 paragraph
  it matches ~1,325.
- The only `0x6A32` word inside DGROUP (`DGROUP:A2C4`, far ptr to "SAVECOM.TMP") is relocated to 0x6C27 /
  0x6BD4 in the dumps.
- BSS + stack span `AD47..B7A0` with no file bytes. IDA SS 0x852C:0800 = linear `0x85AC0` = DGROUP:B7A0.
- Scripts: `analysis/dgroup/cmp.py`, `mcb.py`.

**Other frequent segment immediates are not DGROUP.**
- `0x7894` (link 0x6894, runtime 0x6A89) is a far-data segment used through ES (7,034 `mov es` vs 13
  `mov ds`). Finding 20's "DGROUP pattern" label for `mov ax,6894h` was wrong.
- `0x46A4` (runtime) is the sim far-data segment that flight asm enters with as DS.
- `0x7772`, `0x7B0E` and `0x71C1` are secondary data segments.

**No Borland or Microsoft CRT strings exist in the EXE.** Startup is RTLink/Plus plus custom code, so the
"C0L startup" argument in finding 35 does not hold. Its conclusion (0x6C27) does.

**Consequence for IDA (not yet applied).** C code entered with DS = DGROUP can get default DS = `0x7A32`.
About 20k implicit-DS operands are currently BADSEL. The flight-asm paths entered with DS = 0x46A4 must be
excluded. Per-function DS from `memdump/trace_20261015_211031_fartrans.jsonl` is the right source.
'''

TIME = ("| 2026-11-09 (session 54) | ~4 h | **Finding 120: R05_1E10 / R29_1E10s split into 47 RTLink object "
        "segments** (`tools/split_overlay_segments.py`, manifest `registry/segsplit_expected.json`). Each IDA base "
        "is now the true runtime CS, so near-branch targets are fixed: R05 Jcc->non-code 2,074->48, "
        "CALL->fn-start 499->843. Gemini's R69/DS-tracking claim refuted (IDA already tracks 17,150 sreg loads). "
        "Gates: function table identical, verify_idb identical to the pre-split baseline (the baseline is itself "
        "DAMAGED vs committed ground truth: 3/91/49/5 pre-existing), extract identical, rerun is a no-op; backup "
        "`.bak_segsplit`. **Finding 121: DGROUP PROVEN = link 0x6A32 / IDA 0x7A32 / runtime 0x6C27**: startup "
        "stub at file 0x1FFEA sets SS=DS=DGROUP, memdump byte match 5,706/5,710, CS:[0002] relocation in both "
        "sessions; 0x7894 is far data, not DGROUP; finding 35's Borland C0L basis corrected. Default-DS "
        "application pending. |\n")

fl = Path("docs/findings_log.md")
s = fl.read_text(encoding="utf-8")
assert "## 2026-11-09 120" not in s
fl.write_text(s.rstrip("\n") + "\n" + F120, encoding="utf-8")

tl = Path("docs/time_log.yaml")
s = tl.read_text(encoding="utf-8")
tl.write_text(s.rstrip("\n") + "\n" + TIME, encoding="utf-8")

rb = Path("docs/workflow/idb_regeneration.md")
s = rb.read_text(encoding="utf-8")
old = "# 7. Verify IDB integrity (expect VERDICT: INTACT)"
assert s.count(old) == 1
s = s.replace(old, "# 6b. Split R05_1E10 / R29_1E10s into their RTLink object segments (finding 120)\n"
              "#     (manifest registry/segsplit_expected.json; DRYRUN=1 env regenerates it)\n"
              "cmd /c \"tools\\run_idat.bat tools\\split_overlay_segments.py\"\n\n" + old)
rb.write_text(s, encoding="utf-8")

cs = Path("docs/current_state.md")
s = cs.read_text(encoding="utf-8")
reps = [
    ("| Overlay IDB | 68 segments / 1,053,376 B (9 real + 59 synthetic, 2 skipped) | `overlay_placement.json` |",
     "| Overlay IDB | 68 records / 1,053,376 B (9 real + 59 synthetic, 2 skipped); **R05/R29 split into 47 CS-true "
     "object segments (finding 120)** | `overlay_placement.json`, `registry/segsplit_expected.json` |"),
    ("| Findings logged | 1–118 (append-only)", "| Findings logged | 1–121 (append-only)"),
    ("DGROUP 27687 HYPOTHESIS, resident base 0x1F5 PROVEN",
     "DGROUP **PROVEN** link 0x6A32 = IDA 0x7A32 = runtime 27687/0x6C27 (finding 121), SS=DS=DGROUP; "
     "resident base 0x1F5 PROVEN"),
]
for a, b in reps:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
cs.write_text(s, encoding="utf-8")
print("ok")
