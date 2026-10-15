# Findings Log (append-only)

The chronological record of everything we learn about Falcon 3.0's code, data and
toolchain. **Append-only**: when a hypothesis is disproved, do not delete the entry —
mark it `DISPROVEN` and add the correction. The registry YAMLs hold the *current*
state; this log holds the *history* so reasoning and dead ends are never lost.

Format: `## <date> <seq> - <title>` with a `Status:` line
(`CONFIRMED` / `HYPOTHESIS` / `DISPROVEN` / `SUPERSEDED`).

Entries cross-reference artifacts (`registry/`, `docs/structures.md`, `analysis/`, commits).

---

## 2026-10-10 01 - Toolchain: Microsoft C 5.1 + hand-written ASM (NOT MSC 6.0/Borland)
Status: CONFIRMED (for C modules; ASM is hand-written)

Evidence: 30 `ENTER` (opcode C8) prologues with MSC 5.1-style stack sizes; 84 manual
`55 8B EC` prologues with inconsistent register-save order (hand-tuned); **0** `83 EC`
(`sub sp`) standard-C frames; no `B4 30 CD 21` (MSC 6.0 signature); no CRT error
strings; no Borland strings in main EXEs. RESETALL.EXE separately = Borland C++ 1991.
Details: `docs/toolchain.md`.

## 2026-10-10 02 - Linker: RTLink/Plus, 70 overlay records, 9 segment groups
Status: CONFIRMED

Strings ("Internal error in .RTLink(R)/Plus run-time code.", eov000x, reload stack).
18-byte directory at file 0x1E24F; thunk table 10-byte stubs at file 0x1EBAF (86
thunks); 4-byte tail directory (51 entries) at file 0x1FB61. Structs in
`docs/structures.md`; group summary in registry `FALCONCD.EXE.yaml`.

## 2026-10-10 03 - Fixup tables: 1569 entries, 14 types, applied into IDA
Status: CONFIRMED (static decode); loader-code confirmation pending (Parser RE)

Parsed from record tails (`tools/extract_fixups.py` → `analysis/.../fixup_tables_*.json`),
applied via `tools/apply_fixups_ida.py` so overlay code sits at runtime paragraphs.
Types seen: 0x33ae, 0x400c, 0x39ab, 0x3e52, 0x393c, 0x3de4, 0x3f25, 0x3bdd, 0x3d81,
0x38db, 0x3dad, 0x3fd8, 0x3fd2, 0x06c7. Semantics per type: HYPOTHESIS (see
`docs/overlay_fixups.md`), proof = disassembling the applier.

## 2026-10-10 04 - Compression: PKWARE DCL; assets already unpacked
Status: SUPERSEDED (see finding 31 — nothing decompressed; `PK\x03\x04` claims false; only the linked DCL library + "already extracted in game/" observation survive)

PKWARE copyright + patent strings, `PK\x03\x04` in tail. Asset files already extracted
in `game/` (DISPLAY.DAT, ARMSDATA\*.DAT). Per-asset stream framing: NOT YET MAPPED.

## 2026-10-10 05 - Fresh IDA Pro 9.1 snapshot replaces DOSBox-dump IDBs
Status: CONFIRMED

Headless `idat.exe` on a copy of FALCONCD.EXE (never opened in interactive IDA — it
holds GS2.exe.i64). 839 functions (817 resident + 22 overlay), 83 KB code.
Artifacts: `analysis/ida_falconcd/`.

## 2026-10-11 06 - IDA bytes ≠ raw-EXE bytes (relocation trap)
Status: CONFIRMED — SUPERSEDES naive file-offset comparison

Raw reads at `hdr + (ea - 0x10000)` show **pre-relocation** bytes: DOS applies 2717 MZ
relocations at load (segments 0x1AA3, 0xE56, 0x80F, …) and IDA applies them too.
Ground truth = `analysis/ida_falconcd/function_bytes.json` (extracted from the IDB via
`tools/extract_ida_bytes.py`). `portcheck_falcon.py` now prefers it over raw reads.
Symptom if forgotten: portcheck "expected" bytes look like garbage at correct offsets.

## 2026-10-11 07 - Portcheck pipeline working (C → DOSBox-X MSC 5.1 → .cod → compare)
Status: CONFIRMED

Compile line: `rbin\cl /c /AL /Gs /Fc<NAME8> /Ic:\include <file.c>` in
`dos_compilers\msc5.1`. `.COD` lands in MSC root, **not** source dir. C function name
must equal IDA routine name (parser searches `_name PROC`); filename itself is 8.3
truncated (`sub_16FDD` → `sub_16FD.c` / `SUB_16FD.COD`) but the function name inside
can be 9 chars.

## 2026-10-11 08 - First verified game routines: sub_16FDD, sub_2CB6E
Status: CONFIRMED (byte-identical)

- `sub_16FDD` (seg 0x16FD, ofs 0xD, 4 B): `b8 01 00 cb` = `return 1;` ✅
- `sub_2CB6E` (seg 0x2CB6, ofs 0xE, 4 B): `b8 ff ff cb` = `return -1;` ✅
Key: `/AL` large model + `int far func(void)` (qualifier after return type; MSC 5.1 has
no `__far` — C2054; `far int` order — C2062). Without far, compiler emits `RET` (C3)
but originals use `RETF` (CB).
Registry: `registry/routines.yaml`. Sources: `src/sub_16FDD.c`, `src/sub_2CB6E.c`.

## 2026-10-11 09 - sub_10340 is hand-written ASM, not C
Status: CONFIRMED (disproves "small = C-compiled" assumption)

IDA bytes `d1 e3 2e 89 87 25 00 cb` = `sal bx,1; mov cs:[bx+25h],ax; retf` — ad-hoc
logic, no C prologue. (An earlier raw-read suggestion `a1 0c 00 ab…` was the
relocation trap from Finding 06.) Lesson: classify before porting; size alone proves
nothing.

## 2026-10-11 10 - mzdiff/mzmap reusable (not game-specific)
Status: CONFIRMED

WSL binaries v1.0.20 at `gunship_2000/tools/f19re/mzretools/debug/{mzdiff,mzmap}` (the
GS2000 doc's `build/` path is stale). Generic MZ tools; only `.map` files are per-EXE
(`mzmap` generates them, can ingest an IDA `.lst`). Both verified running.

## 2026-10-11 11 - Track 1 will be splice-in-place, not relink
Status: CONFIRMED (design decision)

No RTLink/Plus binary ⇒ classic relink impossible. Instead: original EXE = immutable
scaffold (header/relocs/RTLink tail verbatim), verified routine bytes patched at
`hdr + (ea - 0x10000)` under a byte-identity guard ⇒ relocations stay valid by
construction. Whole-image check via `mzdiff`. Design + gap analysis:
`docs/pipeline.md` "Convergence Model".

## 2026-10-11 12 - Manual extracted; game knowledge in registry
Status: CONFIRMED

`game/manual.pdf` (254 pp) → `manual_full.txt` → `registry/game_knowledge.yaml`
(379 lines): modes, campaign structure, pilot abilities, weapons, HUD/REO/DED, ACMI,
file mentions (TOPTEN, *.mis, replay tapes).

## 2026-10-11 13 - Classification pass over all 839 functions
Status: CONFIRMED (heuristic, confidence-tagged)

`tools/classify_routines.py` → `analysis/ida_falconcd/classification.json`.
Counts: **ASM 622 (74%), C 83 (9%), DATA 65 (7%), LEAF 62 (7%), NEARTHUNK 7**.
- `C` = ENTER prologue with proper encoding (`c8 NNNN 00`, level 0) or frame+LEAVE.
  65 resident C functions decode as genuine MSC 5.1 code (arg pushes `[bp+6]/[bp+8]`,
  `59 59` caller cleanup, `[bp-2]/[bp-4]` return-pair stores).
- Resident C smallest → first real port queue: `sub_1A6D4` (44 B, ea 0x1A6D4),
  then sub_19CB0 (55 B), sub_17AD4 (61 B)… full list in classification.json.

## 2026-10-11 14 - Frameless LEAF families dissected (capstone, 16-bit)
Status: CONFIRMED

Disassembled the frameless small functions; four distinct families:
1. `b8 xx xx cb` — **ret const → C-portable** (sub_16FDD, sub_2CB6E verified).
2. `2e a0/a1/a2/a3 xx xx cb` — `mov ax, cs:[X]` / `mov cs:[X], al` — **CS-relative
   near-data accessors** (hand-ASM: small data tables embedded in the code segment;
   MSC 5.1 large model emits DS-relative, so NOT C-portable as written). ~13 routines.
3. `2e ff 1e xx xx cb` — `lcall cs:[table]; retf` — **indirect far dispatch stubs**
   (call through CS function-pointer table, then far-return). ~15 routines.
4. `e8 01 00 cb` (7×) — `call next_func; retf` — **far→near trampoline**: a far entry
   stub that near-calls the *following* near function (which ends `c3`), then retf.
   Layout `[far stub][near function]`. Structural, NOT C. Classified `NEARTHUNK`.
Also seen: `sub_25741`-family `mov al, cs:[A]; mov cs:[B], al; retf` byte-copy pairs.
Note: IDA names/boundaries for these are placeholder — rename via registry.

## 2026-10-11 15 - Ground truth validated: IDA bytes = raw EXE + MZ relocations (+0x1000)
Status: CONFIRMED — hard proof of `function_bytes.json` correctness

Compared all 839 functions' IDA bytes vs raw file at `hdr + (ea - 0x10000)`:
- **434 identical, 405 differ — and every single difference is a relocated word
  (+0x1000 = load base paragraph) at a position covered by the 2717-entry MZ
  relocation table. 815/815 resident functions fully explained, 0 anomalies**
  (`tools/_validate_relocs.py`; diff dump in `raw_vs_ida_diffs.json`).
- Consequence: `function_bytes.json` = **runtime image at load base 0x10000**; raw EXE
  = link-time base 0. For a routine containing far-pointer words, the two differ by
  exactly +0x1000 at reloc positions.
- **Portcheck TODO**: when comparing compiled `.cod` bytes for routines containing far
  calls (e.g. `9a .. .. 64 1f`), normalize: allow word = raw±0x1000 at reloc positions,
  or compare against raw-EXE + applying relocs. Our two verified routines had no far
  pointers, so this hasn't bitten yet.
- **Splice rule**: patch *unrelocated* (file/link-time) bytes into the EXE copy —
  DOS applies relocations at load. Never splice IDA-relocated bytes.

## 2026-10-11 16 - Overlay layout in the IDB is WRONG; resident validated good
Status: CONFIRMED (superseded the "maybe garbage decode" phrasing) — remediation required

**Resident: 815/815 functions = raw EXE + MZ relocations (+0x1000/word at exactly the
2717 reloc positions). Zero unexplained. Resident bytes are trusted ground truth.**

Overlay investigation (artifacts: `ida_record_bytes.json`, `ida_overlay_dump.json`,
`tools/dump_record_bytes.py`, `tools/dump_overlay_ranges.py`, `tools/_compare_records.py`):

1. Raw record payloads (from `rtlink_records.json`) DO exist in the IDB — but at
   **cluster bases 0x2D7B4 / 0x660A4 / 0x2F492** (content = base + tail_off, records in
   tail-file order), **not** at runtime positions. E.g. record id=56 (seg 0x569F,
   tail 0x1174) found at 0x67218 = 0x660A4+0x1174, while the runtime formula gives
   0x67B64 — whose content is unrelated tail bytes.
2. Content AT runtime-correct positions comes from **wrong tail offsets**: the bytes at
   id=8's runtime spot (0x73271 = (0x1000+0x5CD9)<<4 + 0x64E1) are actually tail bytes
   at tail_off 0xD1CD (file 0x2CD1E), not record 8 (tail 0x64E1).
3. **~30 of 70 record payloads not found anywhere** in the dumped overlay ranges.
4. The placement formula itself is now suspect: applying it to seg-0x569F record id=32
   (tail 0xC5DB → 0x72FCB..0x73753) **overlaps** seg-0x5CD9's record id=8
   (0x73271..0x734DA). Either some group's offsets are group-relative (not
   tail-absolute), or a 64-bit wrap/group-origin rule exists — must re-derive from
   primary anchors (thunk `ljmp seg:off` targets + 4-byte tail directory), not from the
   earlier analysis scripts (game_knowledge ranges were derived from the same pipeline
   and may share its errors).
5. Fixup parse output is also suspect: `type_counts` contain values like 49757/64070,
   and implausible splits (record 55: code 47 B / fixup 1975 B) — the "1569 entries,
   14 types" decode needs re-derivation from primary data
   (`docs/overlay_fixups.md` hypotheses are NOT proven).
6. Old-content clusters also mean previous overlay function discoveries (22 functions,
   joystick strings placement) may sit at wrong addresses.

**Consequence**: overlay function bytes in `function_bytes.json`/classification are
untrusted (the 18 "C"-class overlay functions decode as nonsense: negative ENTER
levels, `lidt`, `hlt` — while the 65 resident C functions decode perfectly).

**Remediation plan (ordered)**:
1. Re-derive runtime placement from primary anchors: thunk table `ljmp seg:off`
   (stored segs are pre-relocation; runtime = stored + 0x1000), MZ relocation list,
   4-byte tail directory (51 entries), 18-byte dir `seg`+`tail_off`.
2. Rebuild IDB overlay segments: write raw tail record bytes at verified placements,
   discard all old overlay content, re-run analysis.
3. Re-decode fixup format from primary bytes; validate each applied word against
   expected far-pointer semantics before trusting it.
4. Re-run classification + function discovery on rebuilt overlays; only then trust
   overlay `function_bytes`.

## 2026-10-11 17 - RTLink record schema obtained from gunship_2000 + Falcon validation
Status: CONFIRMED (schema) / PARTIAL (per-row file base) — the breakthrough of this session

**Source**: `gunship_2000/logs/discovery_log.md` decoded the 9-word/18-byte RTLink
record header on GS.GS2 (same linker family). Schema:

| word | offset | meaning |
|------|--------|---------|
| w0 | +0 | load base (LINK para; runtime = w0 + 0x1000) |
| w1 | +2 | filename ptr (GS: 17D1:0DB8 → "GS.EXE"; Falcon: constant 0x12ED = "FALCONCD.EXE" region) |
| w2 | +4 | file para of fixup table (**w2 × 16 = file offset of fixup table**) |
| w3 | +6 | high byte = **flags**: 0x04 = transient, 0x01 = startup-load |
| w4 | +8 | allocated span |
| w5 | +10 | fixup count (DWORDS = (off,seg) pairs) |
| w6 | +12 | 0xFFFF |
| w7 | +14 | id (Falcon: 2..71) |
| w8 | +16 | actual data size (A2) |
| | | data_start = w2×16 + align16(w5×4) (fixups first, then data) |

**Falcon validations**:
- idx7 (w2=0x661C, B=43): fixup@0x661C0 = (off,seg) pairs all seg 0x5CD9 ✓,
  data@0x66270 = **sane code** (`push ds; push ax; mov ax,5BE0h; ... retf`, followed
  by `call 0x66270`) — layout formula **exact**.
- idx1 (w2=0x1FB6, B=50): fixup@0x1FB60 = pairs (010B,1CF6),(0110,1CF6),(00D2,1CF6)…
  = **exactly the previously-misdecoded "4-byte tail directory"** (structures.md entry
  was reading record idx1's fixup table 1 byte off!). data@0x1FC30 = string table
  (`\0MYTEMP\0DISPLAY.DAT\0FALCON3.\0`) — runtime filename records ✓ (matches GS w1).
- Flags decode: w3-high = 0x04 (transient) for rows 0..68; **row 69 has 0x01 =
  startup-load** (its @6 = 0x0101 — the earlier "anomaly" explained).
- Loader code: `sub_2AFBD` = thunk entry (reads record word at retaddr+5),
  `sub_2AC4C(ax)` = load/evict worker, dir lookup `0x2B040` = **ax × 18 + 0xC1F**
  (table at CS:0xC1F, count at CS:0xC19, resident IDA ~0x2B64F).
- **Thunk word field = 0-based table index** (values 1..68 fit rows 0..69; field-based
  id interpretation failed cross-checks): word6,7,8 → rows 6,7,8 (seg 5CD9 ✓ targets
  5CD9 ✓), word9,10→rows seg 5DFF ✓, word17,18→5E8F ✓, word19..26→5F6C ✓.
- Old `rtlink_records.json` field labels (A/B/C as sizes) misread: B = fixup dword
  count, A = span (semantics of A vs A2 still open — GS says paras, Falcon gaps don't
  yet fit — see open question).

**OPEN**: small w2 values (0x6D..0x39B0, the C=0x1D group) make w2×16 land inside the
MZ header — for those rows the earlier tail-relative read (0x1FB51 + w2) yielded sane
code (e.g. idx53 → file 0x1FDCB = `07 1f cb; push ds; push es;…`). Two candidate bases
per row; next step = script that validates each row's base via disasm-sanity +
thunk-target containment, then rebuild the IDB.

## 2026-10-11 18 - Runtime placement model SOLVED (validators + assignment solver)
Status: CONFIRMED (high confidence) — completes finding 17's open item

Artifacts: `tools/validate_record_bases.py`, `tools/locate_fixup_tables.py`,
`tools/solve_thunk_assignment.py`, `analysis/.../record_validation.json`,
`analysis/.../record_fixup_located.json`.

**Runtime model (all 63 thunk words self-consistent under `word == 0-based dir row`):**
- Record runtime block = `[(0x1000 + w0) << 4, + span(w4) × 16)`.
- Records sharing the same w0 **all load at the arena base (overlapping)** — transient
  records are alternate occupants; overlap in the IDB is *expected*, not corruption.
- Thunk word = 0-based dir row index (word ∈ own block for all 63 words; only-1-word
  anomalies under packing models vanish under overlap model).
- Parity check: packing spans in **paras** = 250/250 thunks contained (bytes: 195/55).

**File side:**
- `fixup_file = w2 × 16` (gunship formula) confirmed: base-scoring A=61/70; fixup
  scanner located tables ≥80% valid for 46/70 (mostly "fixups-first",
  data = base + align16(fixups×4)); rows 5/16/28/30 have valid tables at base but
  later entries' segs outside my OVSET — because fixup segs may be ANY paragraph
  within `[w0, w0+span)` (GS model), not just record w0s. Extend OVSET = w0+range.
- Diagnostic dumps prove rows 5/16/28/30/30 tables at base are genuine (16/16 first
  segs valid).
- Small-w2 rows (C=0x1D group, w2 < 0x1000): `w2×16` lands in MZ header (impossible);
  row50's window at `0x1FB50 + w2×16` = **strings data (data-first)** ✓, fixups at
  `base + span×16` (row50: 0x21BA0, ends 8 B before row51's window ✓✓).
  For these rows: layout = **data-first**; exact fixup pos needs one more pass
  (likely seg/word order variant or OVSET extension).

**Also learned:**
- Loader `sub_2AC4C` seek math: dx = (fixup-size-derived) high bits | [bx+4], cl=[bx+6]
  → 32-bit file offset — consistent with w2×16 para addressing.
- word2 minor note: its two targets straddle rows 1–2 under packing; benign under
  overlap model (both ∈ row1∪row2 blocks... row2 covers both ✓).

**Next (plan 1.2b final step)**: `rebuild_overlay_segments.py` — write each record's
data bytes into the IDB at its runtime block base (arena base), handle overlaps
(e.g. keep per-arena record sets separately / annotate), re-run analysis, re-classify.
Residual: ~15 rows' fixup exact positions (non-blocking for data placement).

## 2026-10-11 19 - Overlay IDB REBUILT: 48 segments, 141 overlay functions (was 22-wrong)
Status: CONFIRMED — plan 1.2b rebuild + discovery done

Pipeline executed (`prep_overlay_placement.py` → `rebuild_overlay_segments.py` →
`prep_overlay_entries.py` → `mark_overlay_entries.py` → `extract_ida_bytes.py`):

1. **Placement**: 70 rows → 8 real arena segments + 40 synthetic (first-per-arena
   keeps real address; transient overlap means others go to 0x100000+; cluster-B
   rows 50–69 = 20 rows *honestly unplaced*, file location still open) + 2
   zero-span placeholders skipped. **778,640 bytes written** from verified file
   bases. Cross-check tiling: row N data-end == row N+1 window start exactly
   (e.g. row5: 0x26180+257168 == row6 base 0x64E10 ✓).
2. **Entries**: 184 thunk entry points computed as
   `entry = record_ida_ea + (target − real_arena_base)` (validates model 18:
   records load at arena+0). Content-driven marking with candidate rows
   (index → id-field → any-containing): **145 created + 23 pre-covered,
   16 unresolvable** (bytes at those spots aren't decodable code — usually
   thunk→row mapping hits a data record; candidates: word4/7/9/10/12/17).
3. **Result: 956 functions total (815 resident + 141 overlay)** — vs 839 with
   22 wrong-overlay before. `function_bytes.json` re-extracted by live
   enumeration (survey.json now stale for overlay names — extract script
   no longer reads it).
4. **Classification on new IDB**: ASM 680 / C 98 / DATA 98 / LEAF 73 /
   NEARTHUNK 7. C rose 65→98: new overlay C functions found (`r48_e89` 11 B,
   `r36_e107` 13 B, `r35_e92` 30 B … ENTER prologues, e.g.
   `c8 020000; push 0x6894`) — first *overlay* port targets.
5. Row assignments from successful entries **confirm word==row-index** for the
   dominant cases (30→30 ×30, 12→12 ×21, 33→33 ×12, 36→36 ×12, 39→39 ×12,
   8→8 ×7, 6→6 ×6 …).

**Toolchain learnings (IDA 9 headless, worth remembering):**
- `ida_segment.add_segm(para, start, end, name, sclass, flags)` (6 args);
  `getnseg` not `getn_seg`; `ida_ua.create_insn`; `ida_bytes.set_cmt`;
  `segment_t.name` attr; **`ida_loader.get_idb_path()` does not exist** —
  hardcode the IDB path for `save_database`.
- Headless `-A` script stdout is swallowed → always write results to a log file.
- Headless sometimes auto-saves on exit even after script errors (observed) —
  but ALWAYS call `save_database` explicitly right after `auto_wait`, before
  any reporting code.
- Edit-tool multi-line replacements in Python scripts repeatedly corrupted
  indentation → always `ast.parse` the file after editing before running IDA.

**Open after this:** cluster-B (rows 50–69) file location; 16 unresolvable
entries; fixup application (raw bytes now, far ptrs still link-time segs);
segment display names show numbers (cosmetic).

## 2026-10-11 20 - Cluster-B records located (B0 = 0xFFFA0) — ALL 70 rows placed
Status: CONFIRMED

`tools/find_cluster_b.py`: scanned for row50's 466-pair fixup run →
**B0 = 0xFFFA0**: cluster-B window = `0xFFFA0 + w2*16`.
- rows 50–68: fixups-first at window, **fixup fractions 0.80–0.99** (chain tiles:
  window deltas exactly `(w2[i+1]-w2[i])*16`, content fits with slack).
- row69 (flags=0x01 **startup**): code-first at window (disassembles as real code:
  `mov ax,0x6894; mov es,ax` DGROUP pattern), fixup table at **window+0x60**
  (frac 1.00), data len = w8×16 = 84,368 B (fits to EOF with 0x1F7 slack).
- Placement regenerated: **9 real + 59 synthetic + 2 skipped, 1,053,376 B**;
  row69 owns the 606E arena (real at 0x706E0). Rebuilt IDB: 68 segments.
- Entries recomputed: **250 (was 184)** → marked → **192 overlay functions**
  (was 141); nomatch 16→10. Cluster-B rows now contribute (53:8, 54:7, 64:8, 67:3…).

## 2026-10-11 21 - Overlay fixups APPLIED (+0x1000): 25,222 patches, byte-verified
Status: CONFIRMED (dominant type) / CAVEAT (minor types)

Semantics validated host-side first: every in-block pair (off,seg) locates a word at
`(seg+0x1000)<<4 + off` whose BEFORE value is a **link-time paragraph** — resident
link segs (0x1AA3 ×936, 0x0F6C ×2068 ✓ matching the MZ-reloc histogram), overlay
w0s (0x569F ×550), record-internal paras (0x6894 ×4110, 0x502E ×2322 …) — each
needing **+0x1000 (L)** to become IDA runtime space (gunship's "runtime = link + L"
generalizes). Block-membership filter: 25,543 in-block / 677 out.

Applied via `tools/apply_overlay_fixups.py` (per-segment `RTFIX` marker,
word_before guard): **25,222 applied, 0 silent corruption**:
- 177 mismatches = **clip-shadow zones**: record A's block overlapped neighbor
  arena's real segment (e.g. row9 5DFF-block extends past 5E0B arena start), so
  the IDB content there belongs to the neighbor — skipped by guard (by design).
- 144 out-of-written-bounds (rel ≥ clipped ida_len) — same cause.
- Post-apply extraction proves correctness: `mov ax,0x6894`→`0x7894`,
  `0x502E`→`0x602E`, far-call seg `0x0F6C`→`0x1F6C`, word 0→0x1000 (link seg 0
  = image base ✓).

**Caveat**: ~14 fixup *types* exist (overlay_fixups.md); +L validated for the
dominant far-pointer type; a minority of before-words (e.g. 0xC08E, 0x26C0) may
belong to exotic types — re-verify when per-type semantics are decoded.

**Final state this session**: **1,007 functions (815 resident + 192 overlay)**,
97 C-class (with relocated DGROUP operands visible: `b8 94 78` etc.), 6 ret-const
(portable), fixups applied. plan 1.2b: **5/5 core items done** (fixup semantics
dominant-type caveat noted).

## 2026-10-11 22 - COMPILER REVISED: Borland C++ 2.0 (NOT MSC 5.1) — first 44B port verified
Status: CONFIRMED — supersedes the "MSC 5.1 for C modules" conclusion (finding 01)

**The C functions were compiled with Borland C++ 2.0**, recipe: **`bcc -c -ml -1 -O`**
(large model / 80186 target / optimize). User installed BC 2.0 in
`dos_compilers/bcc2.0`; Google-confirmed that BC was the enter/lead emitter —
empirically proven byte-for-byte:

- **`sub_1A6D4` (44 B): MATCH, all 44 bytes** via `tools/obj_extract.py` on BCC's
  native `.OBJ` (PUBDEF 0x90 + LEDATA 0xA0, TASM dialect) and via new portcheck
  `--cc bcc` mode end-to-end. C source: `src/sub_1A6D4.c`
  (`long far f(unsigned a, unsigned n){ long acc=0; while(n){acc+=a;n--;} return acc; }`)
- Codegen fingerprints now explained: `enter 4,0` / `leave;retf` / `mov word [bp-N],0`
  (imm-zero stores) / `adc hi,0` (unsigned) / `or si,si` zero-tests / SI-held loop
  counter — **all Borland**, all reproduced by `-ml -1`.
- **`-1` (80186) is mandatory for ENTER** — without it BC emits
  `push bp; mov bp,sp; sub sp,N` (v1/v6 probes). `-2` also works. Without `-O`
  BC emits a redundant `jmp short $+2` before `pop si` (the `eb 00` we hit even
  in native OBJs); **`-O` elides it** → byte-exact.
- MSC 5.1 (our rbin, C 5.10 Feb 1988 — version banner verified) and MSC 6.00ax
  (gunship's) both emit `push bp` and `mov sp,bp; pop bp`, never enter/leave,
  under every flag tried (grid: /O /Os /Ot /Ox /Od /Oa /Og /Oe /Oa combos).
  → **toolchain.md's "ENTER = MSC 5.1 hallmark" was WRONG** (findings_log 01
  partially DISPROVEN: C modules = BC++ 2.0; hand-ASM conclusion unaffected;
  the 2 earlier trivial leaf matches (`b8 xx cb`) are compiler-agnostic).
- "No Borland strings in main EXEs" was never probative: Falcon embeds no CRT
  (strings come from CRT) — classic reasoning error, now documented.
- Infrastructure added: `tools/obj_extract.py` (Borland OBJ byte extraction),
  portcheck `--cc bcc|msc` (default **bcc**; flags `-c -ml -1 -O`), `--cflags`
  passthrough, `_compare_with_original` (pad-tolerant).

**Consequences**: the 97 ENTER/C-class functions are now portable with BCC;
MSC 5.1 remains installed only for comparison runs (`--cc msc`).

## 2026-10-11 23 - Chained same-module port: sub_17A85 + sub_17AD4 (79B+61B) MATCH
Status: CONFIRMED — methodology + BC large-model codegen rules learned

**Both routines byte-match** (`portcheck --cc bcc`):
- `sub_17AD4` (61 B) MATCH — full body + call displacement reproduced
- `sub_17A85` (79 B) MATCH [4 fixup bytes masked] — far target `0x0761:057B` is
  link-resolved (MZ-relocated); placeholder masked, not compared

**Methodology: same-module chained ports.** `sub_17AD4` calls `sub_17A85`
adjacently (`push cs; call rel16 0xFF7B`). An EXTERNAL declaration compiles to
`call far 0000:0000` (5 B) instead of `push cs; call rel` (4 B) → both functions
must live in ONE translation unit, callee first, and the callee must compile to
exactly its original size (79 B) for the displacement to fall out right.
The original binary was built from exactly such a multi-function .c file.

**BC 2.0 large-model codegen rules (byte-exact recipe), all discovered by diffing:**
1. In `-ml`, **plain `char *` is a FAR pointer** — `(char *)(int_expr)` converts
   int→far with **segment 0** (`mov word [bp-N],0`). To get the DS-segmented
   conversion the original uses (`mov [bp-2],ds; mov [bp-4],ax`), the right side
   must be **explicitly NEAR**: `dst = (char near *)(expr);`.
2. A separate near-ptr *variable* either spills to stack (enter grows 4→8, +14 B)
   or, with `register`, hijacks SI/DI and reshuffles the whole allocation — do NOT
   introduce intermediate pointer variables; direct cast keeps BC's register
   choice identical to the original (idx→DI, loop counter→SI, result in AX).
3. `int i = 0;` at declaration emits `xor si,si` BEFORE later statements —
   matches original ordering; loop must then be `for (; i < n; i++)` (no re-init).
4. `*dst = (char)(flags &= 3);` as ONE expression → `and [bp+C],3; mov ax,[bp+C];
   les bx; mov es:[bx],al` (separate statements reorder the les vs load).
5. Fixup masking (obj_extract): BCC placeholders (`9a 00000000`, `e8 0000`) masked
   from FIXUPP locats + zero-pattern scan; portcheck compare also accepts
   `got+0x1000 == expected` words (MZ/RTLink reloc signature, finding 15 TODO — now implemented).

**Registry**: sub_17A85 hypothesis = `dgroup_record_writer` (copies 13 bytes +
flags&3 into a DGROUP[idx*14+0xAD52] 14-byte record, then notifies 0x0761:057B);
sub_17AD4 = `widen_and_forward` (byte-widening copy into local int[14] → forwards
to sub_17A85). Verified count: 5 routines.

## 2026-10-11 24 - sub_197EA (69B) MATCH: BC switch codegen + CS-relative table recovery
Status: CONFIRMED

`sub_197EA` = sparse 5-case **switch**; BC 2.0 emits search-loop over a case-value
table + parallel jump table, both emitted IMMEDIATELY AFTER the function.
Ported from `src/sub_197EA.c` → MATCH (69 B) [12 mask bytes: table ptr + trailing data].

Techniques locked in:
1. **CS recovery by jump-target matching**: function used `cs:[0x173F]` table refs;
   candidate CS bases (paragraphs of seg009) were tested by checking that the
   table's jump entries (CS-relative) reproduce the known case-block linears →
   **CS = 0x180F0, table at linear 0x1982F** (right after the retf — BC appends
   switch data to the function).
2. **Case values read from the EXE table**: `0x103→10, 0x108→11, 0x111→12,
   0x112→4, 0x113→3, default→key`. (Values look like extended key/scan codes —
   candidate for game knowledgebase: key-mapping routine.)
3. **Register allocation needs the intermediate var**: `switch{case: return N}`
   compiles with results in AX directly (key→SI, no push di); original uses
   `int r` (r→SI, key→DI, `push/pop di`, fallback `mov si,di; mov ax,si`).
   Writing `r = N; break; ... return r;` reproduced the original exactly.
4. **`mov bx, table_off` immediate is a linker fixup** (standalone obj has 0x0045,
   IDB has 0x173F) → covered by FIXUPP mask; compare rule now also tolerates
   arbitrary post-function trailing bytes (data tables), reporting them.

Hypothesis: `key-mapper` — maps extended keycodes to small action IDs
(returns 10/11/12/4/3; default passthrough). Registry updated.

## 2026-10-11 25 - sub_19CB0 (55B) MATCH: union far-ptr arithmetic + slot-order rule
Status: CONFIRMED

`sub_19CB0`: far-calls `0x0994:0x0D22` (fixup masked), treats returned long as a
far pointer, reads a word at +12, `-1L` early-out. Ported from `src/sub_19CB0.c`
→ MATCH (55 B) [4 fixup bytes masked = the external `lcall`].

BC 2.0 codegen rules learned (via two deliberate iterations):
1. **Declaration order drives stack-slot assignment**: `int w;` must be declared
   BEFORE the long (w → [bp-2], r → [bp-6] matches original; reversed order
   swaps slots and shifts every subsequent displacement).
2. **Pointer arithmetic must be written through a union to stay in-place**:
   `union { long l; char far *p; } u; ... u.p += 12;` → `add [slot],0Ch` +
   zero-displacement `es:[bx]` (original shape). The folded expression
   `*(int far *)((char far *)r + 12)` instead folds the +12 into the addressing
   mode (`es:[bx+0Ch]`) and is 3 bytes shorter — clean diff symptom.
3. Long→far-ptr reinterpretation idiom confirmed: BC stores long low/high as
   offset/segment in memory; `les` reads the same slot back.

Verified: **7 routines** (2 trivial leaves + sub_1A6D4 + sub_17A85 + sub_17AD4
+ sub_197EA + sub_19CB0), 382 verified bytes total.

## 2026-10-11 26 - Keyboard unit: 10/10 routines byte-exact (570B) + IDA-missed function found
Status: CONFIRMED

The contiguous block **0x19CB0-0x19EF9 is ONE translation unit** (verified via call
displacement arithmetic): `sub_19CB0 | CE7 | D25 | D65 | DA6 | DE6 | E27 | E3B | E7B |
EBA` — sizes 55+62+64+65+64+65+20+64+63+63 = 570 B, all calling `sub_19CB0`
intra-module (`push cs; call rel16`). Ported as `src/kb_unit_19CB0.c`;
**portcheck: 10/10 MATCH**.

Semantics (registry hypotheses): keyboard-state records — 14-byte structs in DGROUP
(base index at `idx_0020` @ DGROUP:0x20, records at link-off 0x22), fields +0x22..+0x25
read/written through DGROUP far externs (fixup-masked). `sub_19CB0` = far-ptr field
reader feeding all of them; `sub_19E27` = `sub_19DE6(a,b,0)` clear-wrapper.

**New codegen rule (spill-forcer)**: `int r = f();` decl-init keeps r in **SI**;
`if ((r = f()) == -1)` assignment-in-condition **spills r to the stack** (enter grows).
Original uses BOTH styles across sibling functions — match per function:
CE7=decl-init(SI), all others=assign-in-cond(stack). Local declaration order picks
the [bp-2] slot (first-declared wins).

**IDA-missed function**: 65 B at 0x19D65 (between D25 and DA6) was absent from IDA's
function list — found because the unit's contiguous call-displacement arithmetic
required it. Registered in the IDB (`add_func` + name, saved), re-extracted:
function_bytes 1007 → **1008**. Worth a future sweep for other gap-hidden functions.

**Totals: 16 verified routines / 846 bytes** (up from 7/382).

---

## 2026-10-13 28 - Keyboard unit COMPLETE: 38/38 ported, 37 MATCH + 1 known-diff (2270B)
Status: CONFIRMED

**Unit boundary**: 0x19BFF..0x1A4CA = 38 functions / 2270 B, one TU. The unit
starts with four tiny DGROUP accessors (kb_record_base/kb_index_get/kb_farptr_get/
kb_name_copy) and ends with four flag/long accessors (kb_flag_get_10, two flag
setters, dgroup_long_get_08). All 38 now live in `src/kb_unit_19CB0.c` (the old
`src/sub_19CB0.c` reader was folded in). **37/38 portcheck MATCH**; the 38th
(kb_record_name_get, 19C4C) is a documented 2-byte peephole diff (below).

**13 IDA-missed functions registered this session** (14 total in the unit incl.
sub_19D65 from finding 26): gap analysis of the unit's `push cs; call rel16`
displacement arithmetic exposed functions absent from IDA's function list.
Batch 1 (2 fns): sub_19F7A, sub_19F8E. Batch 2 (11 fns): 19BFF, 1A00F, 1A0BC,
1A123, 1A1D6, 1A2DE, 1A348, 1A3B3, 1A423, 1A4A2, 1A4B6 — all add_func'd + named
in the IDB (addfunc2/3.log). function_bytes.json 1008 → **1021**. The batch
registrar is now committed as `tools/add_missed_functions.py` so the regen
runbook is reproducible; `tools/gap_sweep.py` (resident-window gap detector,
242 candidate gaps logged) generalizes the technique beyond one unit.
Confirms finding 26's lesson: IDA under-counts small leaf functions;
unit-boundary arithmetic is the reliable detector.

**Codegen difference 1 — push-only param SI/DI caching (the unit's big trap)**:
our bcc caches multi-use push-only params into SI/DI under default `-r`; the
original compiler build does NOT (it only allocates registers for register-context
params/locals: 1A2DE's i→SI, 19C4C's i→DI, get_22's r→SI). Symptoms: get_2c-style
functions put a in SI and b in DI; the original leaves them memory-only. Global
`-r-` reproduces get_2c exactly but breaks SI-using functions in the same TU;
the `register` keyword is IGNORED under `-r-`. **`#pragma option -r-` / `-r`
(BC 2.0, byte-proven) is the working tool**: a scoped region disables register
allocation for get_2c..count_2c only; the pragma-restored region keeps SI-using
fns correct. All 6 field fns in that region MATCH.

**Codegen difference 2 — array fns: struct param workaround**: array_get/set_1/2
need i→SI with a,b memory-only (original). Plain `(int a, int b, int i)` gives
si/di to a,b (cached above). `(struct kb_ab ab, int i)` forces a,b into a 2-word
struct (memory, identical stack layout/pushes) leaving i the sole scalar → i→SI.
`register int i` alone still cached a→DI. All 4 array fns MATCH with the struct.

**Codegen difference 3 — count spill via assign-in-cond**: array_get_2/set_2 hold
both count (plain assign, 2 uses) and r (assign-in-cond). Original spills BOTH to
stack; our BC cached count in DI. Rewriting as `if ((count = kb_count_2c(...)) <= i)`
invokes finding 26's spill-forcer → both stack-resident → byte-exact.

**Known unfixable diff — NUL-test peephole (19C4C, kb_record_name_get)**:
`if (p[k] == 0)` char test: our BC emits `cmp byte ptr es:[bx],0` (4B); the
original emits `mov al,es:[bx]; cbw; or ax,ax` (6B) + dependent jmp displacement
shifts. Not suppressible via int cast, volatile, -Z, -O-, -r-. Accepted as a
known build difference; function stays port_status draft / verified MISMATCH
(98B vs 100B). All other bytes (i→DI, k→SI, the copy loop) match.

**Other notes**: word/long field access requires explicit `(int far *)` / `(long
far *)` casts off char pointers (get_31/set_31 at +0x31, get_28/set_28 at +0x28);
set_28 takes `long v` and stores only the low word. New DGROUP externs: lng_0008,
flag_0010, name_0012[], ptr_000c, rec_002d[]. DGROUP segment immediates masked
(b89478 vs b80000), plus the usual rec_* displacements and ±0x1000 fixup words.

**Totals: 43 verified routines / 2282 bytes** (up from 16/846); registry now 45
entries; keyboard unit fully ledgered in naming.yaml (44 entries) + routines.yaml.

---

## 2026-10-13 29 - BC 2.0 codegen constraint: intra-module call chains required for byte-exact ports
Status: CONFIRMED

Porting attempts on new resident C functions from gap sweep (`sub_1B631` 83B, `sub_1AAA4` 85B, `sub_1C12F` 87B, `sub_1C0E4` 75B) revealed a critical constraint: **BC 2.0 only produces byte-exact output for functions with ≤1 external far call + intra-module `push cs; call rel16` call chains**.

**The pattern that works** (keyboard unit `kb_unit_19CB0.c`, 38 functions, 2270B):
- 1 external far call (`fn_0994_0D22` at 0x0994:0D22, fixup masked)
- Multiple intra-module calls via `push cs; call rel16` (same TU, address-ordered)
- No local buffers larger than scalars; stack args passed directly

**The pattern that breaks** (new C functions):
- Multiple external far calls to different segments (e.g., `sub_1B631` calls `fn_1994_2CA`, `fn_1994_30C`, `fn_1994_3A7`, `fn_1994_4E7`, `fn_1994_57A`, `fn_1994_2A8` — all different fixup targets)
- Local array buffers (16+ bytes) + multiple external far calls passing buffer pointers
- BC 2.0 emits: extra frame bytes (ENTER 0x14 vs 0x10), spurious register saves (push di), indirect call sequences via stack slots instead of direct `lcall` operands, spurious calls to self/same-module

**IDB boundary reliability**: Gap-sweep functions and many resident C functions have **unreliable IDA boundaries** — overlapping ranges, missing RETs, rel16 calls to mid-function addresses. Only the keyboard unit (0x19BFF..0x1A4CA) and `sub_17A85`/`sub_17AD4` have verified-correct boundaries via call-displacement arithmetic.

**Implication**: Viable porting targets are **resident C functions forming verified intra-module call chains** (same segment, `push cs; call rel16` adjacency). No new clean TUs found beyond the two already ported. Overlay C functions and gap-sweep C functions are not tractable with current BC 2.0 setup due to boundary issues and multi-external-call codegen.

**Next step**: Track C (splice setup) — verified bytes patched into original scaffold keep all relocations/RTLink structures valid by construction; `mzdiff` is the verifier.

Artifacts: classification.json (107 C-class, 757 ASM), function_bytes.json (1080 fns), portcheck_falcon.py test runs on `sub_1B631`/`sub_1AAA4`/`sub_1C0E4`/`sub_1C12F`.

---

## 2026-10-13 30 - Dynamic trace harvester (DOSBox-Staging) to resolve IDB boundary unreliability
Status: IN PROGRESS (2026-10-14 session 16: instrumented build DONE — see progress note at end)

**Problem**: Finding 29 established that static IDA boundaries are unreliable for gap-sweep/overlay C functions — overlapping ranges, missing RETs, rel16 calls to mid-function. Only keyboard unit and sub_17A85/sub_17AD4 have verified boundaries via call-displacement arithmetic.

**Solution** (per advice.md §3): Build instrumented DOSBox-Staging (src/dosbox-staging) with debugger enabled. Hook CPU core to log at three boundaries (advice.md §3.3):
1. **Function entry** (CALL FAR/NEAR, RTLink thunk jumps): Record symbolic DS/ES (SEG_DGROUP, SEG_OVERLAY_ID(n), SEG_HEAP_ALLOC(callsite))
2. **Memory dereferences** (EA calculation with DS:/ES:): Record resolved segment + offset range per instruction
3. **Indirect CALL/JMP** (CALL DWORD PTR [bx]): Record resolved (Overlay_ID, Offset) pairs

Also log: RTLink overlay loads (segment ↔ overlay ID), INT 21h file I/O (filename ↔ function).

**Deliverables**:
- DOSBox-Staging build with debugger + trace hooks (output JSONL trace)
- Redumped menu/mission/sim memory (accurate addresses, replaces old DOSBox 0.74 dumps)
- Segment classification JSON (maps runtime segments → symbolic origins)
- Updated function_bytes.json with verified runtime boundaries

**Impact**: Turns unreliable static boundaries into ground-truth runtime mappings. Enables reliable porting of remaining C functions by identifying true intra-module call chains.

**Dependencies**: src/dosbox-staging (CMake, SDL3 via vcpkg), debugger build config.

**Progress 2026-10-14 (session 16)**:
- Built: `src/dosbox-staging/build/falcon/dosbox_with_debugger.exe`
  (0.84.0-alpha @ c1e7c24, `OPT_DEBUGGER=ON`, `OPT_TESTS=OFF`, Ninja + clang-cl
  + vcpkg x64-windows). Reproduce with `tools\build_dosbox_debugger.ps1`
  (vcpkg root `C:\Users\yotam\tools\vcpkg`, bootstrapped this session).
- Trace hooks landed in the staging tree (`src/misc/falcon_trace.{h,cpp}` +
  hooks in `dos.cpp` INT 21h 3D/3E/3F/42, `cpu.cpp` CPU_CALL/CPU_JMP real-mode
  far transfers, init/shutdown in `dosbox.cpp`). Enabled via env
  `FALCON_TRACE=<prefix>` → `<prefix>_fileio.jsonl` (chronological open/read/
  seek/close with filename, file offset, buffer seg:off; reads <512 B filtered)
  + `<prefix>_fartrans.jsonl` (aggregated far CALL/JMP targets with entry
  DS/ES histograms) + `<prefix>_meta.json`. Smoke-tested (empty-session run
  wrote all three files).
- Hooks 2/3 of advice.md §3.3 (far-transfer entry DS/ES; file I/O) implemented;
  memory-dereference and indirect-target logging NOT yet implemented.
- Memdump tracker `docs/memdump.md` created; first-pass inventory of the three
  1 MB dumps via `tools/memdump_inventory.py` (game PSP para 0x118, main PSP
  para 0x192 owning 482 KB block, menu-vs-sim 47 % paragraph diff).
- Remaining: finish segment classification (per-function DGROUP,
  SEG_OVERLAY_ID(n), heap call-sites), memory-deref + indirect-target hooks
  (advice.md §3.3 hooks 2-3). Throttle added: far-transfer aggregation is
  wall-clock sampled (`FALCON_TRACE_THROTTLE_MS`, default 1 ms per target;
  `elapsed_ms` in jsonl) so hot thunks cannot flood histograms; disabled-run
  cost is one flag check per far transfer.

---

## 2026-10-14 31 - PKWARE compression claims RETRACTED (finding 04 partly SUPERSEDED)
Status: CONFIRMED (retraction); earlier claims SUPERSEDED

We never found how to decompress the tail, and never decompressed anything ourselves.
Corrections, all byte-verified today against both copies of FALCONCD.EXE
(`game/` and `analysis/ida_falconcd/`, md5 `2BDD74F4B50729B8583224CCE471805A`,
size 1,373,671):

1. **`PK\x03\x04` count in the whole file: 0** (also 0 × `PK\x05\x06`). status.md,
   toolchain.md and game_knowledge.yaml used to claim "multiple `PK\x03\x04`
   signatures in tail" — false. The 10 `signatures_in_tail` offsets recorded in
   game_knowledge.yaml (0x67F, 0x6B6, 0x4DEBB, 0x6D67A, 0x6D8EE, 0x9FF54,
   0xA0DE2, 0xA179B, 0xA2031, 0xA27FB) contain ordinary code/data bytes; field
   removed from the YAML.
2. **What IS true**: 2 × "PKWARE Data Compression Library(tm)" copyright strings
   → the DCL runtime is linked in. That is the entire evidence.
3. **"assets already unpacked in `game/`"** — `game/` is a plain game install
   (1,181 files), not an extraction of the EXE tail; `DISPLAY.DAT` does not exist
   in it at all. Per-asset stream framing (finding 04) was, and remains, NOT MAPPED.
4. Per knowledge-protocol: certainty levels added — status.md Verified Facts
   gained a Certainty column (PROVEN/STRONG/HYPOTHESIS/UNKNOWN/DISPROVEN);
   game_knowledge.yaml `compression:` block now `certainty: UNKNOWN`.

**Method going forward** (per advice.md §2/§4): do not guess the algorithm —
carve tail blobs → try `blast` (zlib/contrib/blast); dump decompressed buffers
from RAM at runtime; find the in-EXE decompressor via its static Huffman tables
(ChBits/ChCode/LenBits/LenCode/ExLenBits) or via INT 21h read traces from the
instrumented dosbox-staging build (finding 30).

## 2026-10-14 32 - Dynamic ground truth from traces: session load base, seg020 hub, RTLink loads
Status: CONFIRMED (tool: `tools/mine_traces.py` → `analysis/traces/`)

First mining pass over the two committed FALCON_TRACE runs
(`memdump/trace_20261014_23{1428,2757}_*.jsonl`, 4.8 M far calls, 1,024 file
events, both runs from `dosbox_with_debugger.exe`):

1. **Session-A load base PROVEN = image paragraph `0x1F5` (PSP `0x1E5`)**,
   identical in both runs (DOSBox loads deterministically):
   - `runtime_seg = ida_seg - 0x1000 + 0x1F5` (= `ida_seg - 0xE0B`);
     `runtime_lin = ida_lin - 0xE0B0`
   - `file_off = ida_lin - 0xD400` (load-module file `0x2C00` ↔ ida `0x10000`)
   - Verified three independent ways: (a) entry `0x2B19C` ida → file `0x1DD9C`
     ↔ dump linear `0x1D0EC` matches byte-for-byte (tail bytes are relocated
     segments), (b) 30/33 RTLink records at `runtime = w0 + 0x1F5`, (c) three
     hot functions of runtime `0x1161` match EXE bytes at constant
     `file = runtime_lin + 0xCB0`.
   - Supersedes the session-B legacy guess `runtime = ida - 0xE5E` (session
     bases differ — always re-derive per session).
2. **Top far-call target `0x1161` = resident `seg020`** (main resident code,
   346 funcs / 28 KB, ida `0x1F6C0`): 1.44 M far calls, ≥7 hot entry IPs
   (`52C4`, `797F`, `151B`, `69EF`, `2BCF`, `2BC5`, `59C7` — all verified
   against file bytes). This segment is the call-graph hub; C-class ports
   should preferentially target it.
3. **RTLink overlay loads mapped (finding 30 deliverable (a))**: 41 distinct
   EXE-tail file offsets → buffer segments, **0 unstable across both runs**;
   joined to `overlay_placement.json` → **33 records loaded at runtime, 30 at
   a stable segment**, 3 transient (records 5, 29, 69 — pool reuse, consistent
   with finding 18's transient overlap); 0 unmatched reads.
   Artifacts: `analysis/traces/{rtlink_loads,overlay_load_map}.json`.
4. **VGA confirmed at entry hooks**: ES = `0xA000` / `0xA400` (+ `0xA800`
   rare) → SEG_VGA_VRAM classification live.
5. **DS is NOT single-valued across a run** (run1 dominant `0x6C27` 58 %,
   run2 dominant `0x46A4` 41 %; both present in both) → per-phase data
   segments; DGROUP must be classified per-function, not globally (open).
6. File I/O: `FALCONCD.EXE` reads dominate (3.7 MB / 2.1 MB per run —
   overlay swapping); plain asset files (`israel.map`, `cockpit`, `madbuff.tmp`,
   `button1`, ...) read directly, unencrypted.

Open: identity of per-phase data segs `0x6C27`/`0x46A4` vs DGROUP; pool
segments hosting code (5-6 per run) → SEG_OVERLAY_ID(n) naming; thunk-state
merge across dumps; memory-dereference + indirect-target hooks (advice §3.3
hooks 2-3) not yet implemented.

## 2026-10-14 33 - Trace-driven boundary repair: 106 functions recovered from far-call targets
Status: CONFIRMED

The 914 merged far-call/far-jump targets (finding 32) are TRUE runtime
function entries. Converted via `runtime = ida - 0xE0B` and diffed against
`function_bytes.json` (`tools/verify_boundaries.py`), then applied to the IDB
headless (`tools/apply_trace_functions.py`; 2 iterations of add/split +
`extract_ida_bytes.py` + `classify_routines.py` regen):

| Metric | Before | After |
|---|---|---|
| Functions in ground truth | 1,080 | **1,215** (+135) |
| Targets EXACT (on a fn start) | 204 | **340** |
| Targets UNKNOWN (missed fns) | 251 | 87 |
| Resident MID (boundary errors) | 27 | 37 (mostly dispatch labels — see below) |

Method notes:
- **Validation before registration**: 97 % of UNKNOWN resident candidates
  start with plausible entry bytes; 100/202 are preceded by `CB` (retf) —
  textbook boundaries; MID candidates 100 % prologue-valid, 24/27 retf-preceded.
- **Splits work but hit a floor**: 29 MID splits applied (top: `sub_25E0E`
  +0x34 with 14,684 calls); remaining MID cases are (a) **jump-table
  dispatch labels** — several targets sharing one call count (e.g. 5×1,328
  into `sub_222AA`) are case labels, not functions — and (b) splits IDA
  rejects because the remainder is < function size. Do not loop further.
- Classification shift: ASM 757→834, LEAF 80→89, DATA 129→145,
  NEARTHUNK 7→10, C 107→108.
- Highest-value still-missed: `01F5:018F` (132K calls, image-start area,
  IDA refuses — chunk not code); 124 resident + 31 overlay UNKNOWN remain
  (list in `analysis/traces/boundary_report.json`).
- Overlay targets joined via `rtlink_loads.json` record→ida_ea mapping;
  18 overlay fns registered (rec1/5/6 entries), 31 remain.
- **Iteration 3 (v2 `apply_trace_functions.py`)**: forcing chunk conversion
  (`del_items` + `create_insn` before `add_func`) recovered 29 more fns —
  many v2 failures were "not a code chunk" (seg000 startup, data-adjacent).
  Final: **1,215 functions**, EXACT **340**, UNKNOWN **87** (MID rose to 62
  — new fns revealed second-order merges; dispatch-label rule still applies,
  diminishing returns — further loops not worth DB churn).

Impact: finding 29's "unreliable IDB boundaries" problem is now *quantified
and partly repaired* from dynamic ground truth; remaining port-queue C
candidates should be re-checked against the new boundaries.

---

## 2026-10-14 34 - Segment classification emitted; thunk states merged (66/66 stable)
Status: CONFIRMED

Two advice.md deliverables from the committed traces:

**Segment classification** — `tools/classify_segments.py` →
`analysis/traces/segment_classification.json`. Per run: 116–119 observed
segments (47–48 `SEG_DATA`, 18 `SEG_STATIC`, 1 `SEG_DGROUP`, 3
`SEG_VGA_VRAM`, 15 `SEG_OVERLAY_ID(n)` pool slots + 80–90
`SEG_OVERLAY_DATA(n)` carved from them).

- **Multi-kind segments** (user choice over rank precedence): a segment
  carries `kinds[]` plus a highest-rank `kind`. Example: `27687` =
  `["SEG_DATA","SEG_OVERLAY_DATA(7)","SEG_DGROUP"]` — it is DS-anchored
  data *and* sits inside pool block 7. Consumers wanting one label use
  `kind`; the authoritative view is `kinds` with per-kind `evidence`.
- **DGROUP ranking**: by *distinct entry-IP coverage*, not raw observation
  count. The naive count disagreed across runs (27687 vs 18084) because it
  measures which module ran most; coverage measures how many call sites
  anchor DS there, and is stable → 27687. Certainty **HYPOTHESIS** until a
  dump-side pointer check confirms it.
- **Resident base = 0x1F5, PROVEN** (finding 32/33), not re-derived.
- Heap call-site tagging (`SEG_HEAP_ALLOC`) needs the new INT 21h AH=48h
  hook, which is in the source but **postdates both committed traces** — 0
  heap blocks observed so far. A fresh traced run will populate it.

**Thunk-state merge** — `tools/merge_thunk_states.py` →
`analysis/traces/thunk_states.json`. Locates the 10-byte thunk table
(`E8 disp16` `EA off seg` `word rec_id`) by signature in all 12 dumps
(303 thunks each), joins `rec_id` → `overlay_entries.json`.

- **Key trap**: the two capture sessions have different DOS load bases
  (table at `0x1D7BD` vs `0x1DCED`, Δ 0x530), so absolute `seg:off` targets
  do not compare across dumps — naive grouping gave `stable: 0`. Normalizing
  each dump's targets against the reference base (subtract the table delta)
  makes them comparable.
- Result: **66/66 record ids resolve to a stable target across all 12
  dumps**; 0 transient. Resolved targets are the live `seg:off` per record
  (e.g. rec 6 → `5E7B:001E`, `5E7B:00AA`, …).
- Remaining: patch the static thunk table in the analysis DB to these live
  targets so agents see the true call graph (advice.md "Patch the Thunks
  for Static Analysis").

Impact: the segment-classification JSON is the schema advice.md §2 asks
for, and thunk resolution is no longer blocked by the multi-session
load-base problem.

---

## 2026-10-15 35 - DGROUP identity + MCB owner correction + VGA Mode X confirmation
Status: CONFIRMED

**DGROUP identity clarified (external review):**
- **0x6C27 (27687) is the single true Borland C++ DGROUP**. This is
  provable in 5 seconds by checking C0L startup at the entry point, which
  executes `MOV AX, DGROUP / MOV DS, AX`.
- **0x46A4 is NOT a second DGROUP** -- it is the primary **Sim Far Data /
  Flight State Segment** used by the 3D flight loop's hand-crafted assembly
  and far-data routines. The two runs differed only in which module
  dominated CPU cycles: run 1 (menu-heavy) entered far calls with DS=DGROUP
  (0x6C27) 58% of the time; run 2 (flight-heavy) entered with DS=0x46A4
  (Sim Far Data) 41% of the time. Both runs share the same single DGROUP
  = 0x6C27. Marked HYPOTHESIS pending dump-side pointer check.

**MCB owner correction:**
- The legacy session B (Feb 2026 dumps) had PSP at para 0x192.
- The current session A (instrumented build, Oct 2026) has PSP at 0x1E5.
- Heap-block carving must filter for owner=0x1E5 (not 0x192).
- The INT 21h AH=48h/49h hooks (added in this session) capture call-site
  CS:IP; a fresh traced run will populate SEG_HEAP_ALLOC correctly.

**VGA Mode X / Page Flipping confirmed:**
- ES values 0xA000, 0xA400, 0xA800 at call entries correspond to VGA
  display pages 0, 1, 2 (classic 16-color planar EGA/VGA or unchained
  Mode X page-flipping). Any function entering with ES in {0xA000, 0xA400,
  0xA800} is a graphics rasterizer or blitter.

**Thunk table patched in IDA (299/303):**
- `tools/patch_thunks_ida.py` (rewritten after external review found 4
  critical bugs in the original: `ea` never advanced in scan loop; rec_id
  grouping clobbered per-thunk offsets; E8 trap left active blocking flow
  into JMP FAR; no runtime→IDA segment conversion).
- Thunk table located at IDA EA **0x2BD9D** (not file offset 0x1EBAF —
  the original script had the wrong address; 0x1EBAF is the file offset,
  IDA linear = file_off + 0xD400 = 0x2BFAB, but the actual table start
  verified by E8/EA signature is 0x2BD9D).
- For each of 303 thunks: matched by (rec_id, orig_off) against
  `thunk_states.json` resolved targets; segment converted
  (JSON_seg + 0x0E5E = IDA_seg, since JSON segs are normalized to
  load_base 0x01A2 and IDA loads MZ at 0x1000); E8 trap at +0..+2 replaced
  with NOPs so IDA flows into JMP FAR at +3; `del_items` + `create_insn`
  forces re-analysis.
- **299/303 matched cleanly**. 4 ambiguous (thunks #032, #053, #261, #262)
  had duplicate offset 0x000A within recs 1/53 — skipped; their IDA
  segments were already correct.
- Log: `analysis/ida_falconcd/patch_thunks.log`.

**Fresh traced run — SEG_HEAP_ALLOC populated:**
- `trace_20261015_211031` (thorough walkthrough): 3.97M far calls, 82
  target CS segments, 1,093 overlay reads, 16,297 fileio events.
- **674 mcb_alloc / 1,354 mcb_free events** → **655 unique SEG_HEAP_ALLOC
  segments** in `segment_classification.json`, each with call-site
  attribution (dominant site `1161:2F53` = main code hub).
- 806 segments classified total (75 data, 22 static, 4 VGA, 1 DGROUP,
  674 heap). DGROUP still 27687 (HYPOTHESIS), resident base 501 (PROVEN).
- `mine_traces.py` + `classify_segments.py` re-run over all 6 traces;
  overlay offsets: 53 tracked, 0 unstable across runs.

---

## 2026-10-16 36 — Advice §3.3 hooks 2+3 implemented (memderef + indirect far)
Status: CONFIRMED

**Hook 2 (memory dereference, DS:/ES: segment override):**
- `DO_PREFIX_SEG` in `core_normal.cpp` now calls `FalconTrace_MemDeref` for
  every segment-override prefix. Per-CS:IP histogram of seen symbolic
  segments (capped at 4, SS ignored per advice).
- Output: `<prefix>_memderef.jsonl` — **8,352 unique CS:IP sites** in the
  smoke test (`debug_test`).
- Initially hooked at SAVEIP after instruction execution — missed all
  control-flow instructions (JMP/Jcc use `continue` to skip SAVEIP). Moved
  to prefix-decode time; GETIP then points at the instruction after the
  prefix byte, which is the deref site.

**Hook 3 (indirect far CALL/JMP through memory):**
- `CALL Ep` (FF /3) and `JMP Ep` (FF /5) in `prefix_none.h` GRP5 handler
  call `FalconTrace_IndirectFar` before `CPU_CALL`/`CPU_JMP`.
- Output: `indirect_far` events in `<prefix>_fileio.jsonl` —
  **379,498 events** in the smoke test. Each records target, caller CS:IP,
  and entry DS/ES.

**Three bugs found and fixed during bring-up:**
1. **Dynamic core bypass**: `core = auto` on x86 selects the dynamic
   recompiler, which never runs `prefix_none.h`. `ConfigureCpuCore` now
   forces `CPU_Core_Normal_Run` when `FALCON_TRACE` is set. The
   `config -set cpu core=normal` runtime command does NOT re-run
   `Configure()` — only startup does.
2. **Duplicate `falcon_trace_enabled`**: defined both inside the anonymous
   namespace (internal linkage — what `FalconTrace_Init` set to `true`) and
   at file scope (external linkage — what `FalconTrace_Active()` read,
   staying `false`). Every hook silently no-opped. Fixed to a single
   file-scope definition.
3. **SAVEIP miss**: control-flow instructions `continue` back to the loop
   head, skipping SAVEIP. Deref hook moved into `DO_PREFIX_SEG`.

**Smoke test** (`memdump/debug_test*`, 2026-10-16 01:05): 385,637 fileio
events, 1,120 far targets, 8,352 deref sites, 379,498 indirect-far events.

Impact: advice.md §3.3 all three hooks now active. Next traced run will
emit `<prefix>_memderef.jsonl` alongside the existing outputs — ready for
struct-reconstruction agents (deref offset ranges) and dispatch-table
recovery (indirect far targets).

Impact: DGROUP correctly identified as 0x6C27 (HYPOTHESIS pending
dump-side pointer check); 0x46A4 confirmed as Sim Far Data segment, not a
second DGROUP. MCB owner for heap carving corrected to 0x1E5. VGA Mode X
page flipping confirmed -- graphics routines are immediately classifiable
by ES value.

---

(append new findings below)
