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

Impact: DGROUP correctly identified as 0x6C27 (HYPOTHESIS pending
dump-side pointer check); 0x46A4 confirmed as Sim Far Data segment, not a
second DGROUP. MCB owner for heap carving corrected to 0x1E5. VGA Mode X
page flipping confirmed -- graphics routines are immediately classifiable
by ES value.

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

---

## 2026-10-16 37 — Step 4: port-queue C re-check + 19 missed fns registered
Status: CONFIRMED

**Port-queue C candidates (the step-4 ask) — all clean:**
- **108 C candidates, 0 defects**: no overlap with any function, none missing
  from `function_bytes.json`, no classif-vs-extracted size mismatch, and
  **108/108 carry the `c8` (ENTER)** Borland C++ prologue (finding 22).
- Boundary verification improved sharply against the new comprehensive
  trace: C candidates **EXACT 8 → 33**, `NO_FARCALL` 100 → 75. (Most C fns
  are reached by *near* calls/thunks, so NO_FARCALL is expected, not a
  defect — but the richer trace confirmed many more entry points.)
- **Clean reloc-free port targets: 4** — `r36_e115` (13B, overlay),
  `sub_1A6D4` (44B, already MATCH), `sub_17AD4` (61B, already MATCH),
  `sub_197EA` (69B, already MATCH).

**The 87 UNKNOWN — claim confirmed, and better:**
- **67 = `.RTLink` thunk-table entries** (exact 10-byte stride,
  ida_ea inside 0x2BD9D..0x2C973). Not functions — matches the documented
  "dispatch-table labels, not functions".
- **13 = data / dispatch labels** (zero-fill; far-pointer tables with the
  recurring `xx 9f 56` = segment 0x569F pattern).
- **4 = real code** → all registered (see below).

**New: comprehensive trace exposed far more missed functions (19 total):**
Re-running `verify_boundaries.py` over the hook-rich trace raised the
target set (EXACT 340→466, UNKNOWN 87→163 as the denominator grew).
Decomposing the new UNKNOWN: 120 thunk entries, 40 data labels, **21 real
code candidates**, of which 19 registered cleanly:

| ea | size | term | calls | note |
|----|------|------|-------|------|
| `0x22AFF` | 40B | iret | **174,766** | 2nd-hottest target; PIC EOI handler (`out 20h,al`) |
| `0x1018F` | 122B | retf | 132,401 | far dispatcher, 11 je converge to off 110 |
| `0x260F4` | 348B | retf | 2,587 | |
| `0x208E7` | 403B | retf | 498 | |
| `0x2100F` | 280B | retf | 18 | |
| `0x6DE83` | 164B | ret | 3,039 | |
| `0x211C9` | 157B | retf | 480 | |
| + 12 more | 6–41B | retf | ≤1,105 | |

Function count **1,215 → 1,234**; all newly registered targets resolve to
**EXACT** in `boundary_report.json`.

**Four toolchain gotchas (each cost a debugging round):**
1. **Naive terminator scan gives false positives** — `c3`/`cf` as the *second
   byte* of `3b c3` (`cmp bx,ax`) / `3b cf` (`cmp cx,di`) looked like `ret`/
   `iret`. Must disassemble to instruction boundaries (handled in
   `add_trace_functions.py`).
2. **`ida_bytes.next_head()` returns BADADDR after `del_items`** — it only
   finds *already-created* item heads. Advance with `get_item_size()` instead.
   Symptom: every candidate "SKIP (no terminator)".
3. **`idaapi.auto_wait()` re-decides bodies and shrinks explicitly-registered
   functions** (348B → 1B). Fix (`fix_trace_functions.py`): disable
   autoanalysis (`ida_auto.enable_auto(False)`), force-decode every
   instruction, `set_func_end`, and save **without** `auto_wait`.
4. **`file_off = ida_lin - 0xD400` is resident-only.** Host-side byte peeks
   at overlay addresses (≥ ~0x6xxxx) read zeros — always trust IDA's own
   disassembly for overlay code.

Tools added: `add_boundary_functions.py`, `add_trace_functions.py`,
`fix_trace_functions.py`.

Impact: port queue confirmed sound; 19 previously-invisible functions
(including the game's #2 hot path) now in the IDB; boundary EXACT coverage
340→466.

---

## 2026-10-16 38 — Partial call graph built; external claims verified (2 right, 4 wrong)
Status: CONFIRMED

**Deliverable: partial call graph + bottom-up traversal** (agreed method —
the dynamic trace is incomplete by nature, so we build a *partial* graph
and attack it leaves→roots instead of chasing full coverage):
- `tools/export_callrefs.py` — IDA explicit call/jump refs →
  **1,494 static fn→fn edges** (2,138 call + 1,309 jmp refs; fall-through
  refs excluded via `CodeRefsFrom(ea, flow=0)`).
- `tools/callgraph_bottomup.py` — edges = static ∪ runtime `indirect_far`
  (caller→target). Endpoints = called-but-calls-nothing; BFS upward.
- `analysis/traces/callgraph_partial.json`:
  **327 endpoints, 911/1,234 nodes, 6 levels.**
  Level 0 = hot 5–37B ASM leaves; Level 2 = hubs (`sub_251C3` 543K,
  `sub_14EAE` 397K); Levels 4–5 = C controllers (`sub_17AD4`, `sub_1B7CE`).

**Runtime hook sanity check (concern raised externally):**
`indirect_far` DOES log the dereferenced target — the hook reads
`LoadMw(eaa)`/`LoadMw(eaa+2)` (the pointer's contents), not the pointer's
own address. Confirmed empirically: **322,396/379,498 events resolve to a
registered function**. The narrowness (13 unique caller→target pairs, 4
callers, `sub_2142E` the dispatch hub) is real but *explained*: indirect
far-dispatch is rare and concentrated in tight loops; nearly all far calls
are direct (already in static xrefs).

**A reporting bug of my own, corrected:** my earlier "28 unresolved
targets" list **conflated caller-side and target-side addresses**. The
hook passes the *post-instruction* IP as caller, so caller IPs sit a few
bytes past the call — landing them in gaps. Filtering to genuine *call
targets* only leaves **15 leads**, of which the real ones are:
| ea | calls | status |
|----|-------|--------|
| `0x17263` | 22,178 | **registered** (27B retf) — VGA/port routine, caller `0883:0483` |
| `0x286CE` | 2,106 | **registered** (166B retf) — caller `1161:1EDC` (main hub) |
| `0x2E100`,`0x2E148` | 136 | already-known UNKNOWN |
| `0x6E3FD`,`0x6E3C0`,`0x67C5A`… | 4–47 | **null-pointer dispatch** (`00 00…` = data, called through uninitialized table slots) |

**External advice verified (advice3.md). Two claims right, four wrong:**

RIGHT:
1. **`FF 0E` is `DEC WORD PTR`, not an indirect far call** (`FF 1E` = `CALL FAR
   [mem]`, `/3=0x1E`). I had misread `ff 0e` as a far call. IDA confirms
   `dec word ptr` at `0x1755E`.
2. **Method**: naming Level-0 leaves first to propagate types upward is sound.

WRONG (each falsified against IDB/trace data):
1. *"Only resident root is disassembled; 191 thunks are overlay-called"* —
   overlays **are** disassembled: **199 functions ≥ 0x60000** (+ more at
   0x1xxxx–0x5xxxx). Also the metric I reported was **outgoing**
   (112/303); true **incoming is only 27/303** — a different and much
   larger gap: most thunk *targets* aren't registered functions.
2. *"`0x1755E` is 60B inside `sub_17522` (secondary entry); `get_func`
   returns `sub_17522`"* — **`get_func(0x1755E)` = None (gap)**;
   `sub_17522` = 0x17522..0x17537 (21B), `0x1755E` not inside it.
   (It's also a *caller-side* address, not a target.)
3. *"`0x103D2D` is above 1 MB / HMA wrap"* — it's an ordinary **IDA linear
   address in the tail/asset region** (`file = 0x103D2D-0xD400 = 0xF692D`,
   inside the 1.37 MB EXE). And it's caller-side, not a target.
4. *"Level-0 leaves are `F_LXMUL@`/`F_LDIV@`/`SCOPY` runtime helpers"* —
   disassembly says otherwise: `sub_2703F` = far-ptr table lookup
   (`mov di,500Ch … les di,es:[di]`), `sub_22285`/`sub_2228F` = paired
   store/load of a CS-resident 32-bit value, `sub_112A1` = bit-twiddle on
   a CS flag with `mov ah,0F0h`. Hand-written ASM state helpers, not
   Borland fixed-point math.

**Toolchain gotcha (new, #5):** `ida_bytes.DELIT_ALL` does not exist —
flags are `SIMPLE=0, EXPAND=1, DELNAMES=2, NOTRUNC=4, NOUNAME=8,
NOCMT=16, KEEPFUNC=32`. A defined data item inside code (e.g.
`word_28759`, a CS-relative var) blocks `create_insn`; clear it with
`DELIT_EXPAND` + retry.

Impact: partial call graph is a working artifact; method validated;
2 more hot missed functions registered (1,231→1,232); external advice
triaged so its good ideas (bottom-up naming, opcode literacy) are kept and
its wrong diagnoses don't mislead the next session.

---

## 2026-10-16 39 — Level-0 bottom-up naming pass (24 leaves identified)
Status: CONFIRMED

First pass of the agreed **Level-0-first naming** strategy: took the
`callgraph_partial.json` endpoints ranked by dynamic call count and
identified the top **24**, giving each a semantic name + a register-level
`sig` contract (they're hand-written ASM, so there is no C prototype —
`sig` records params/returns/clobbers instead).

**Identified (24)** — grouped by role:
- **input/hw**: `joystick_poll` (95K — `in al,201h` + `int 15h/84h`),
  `input_status_pack` (318K, hottest leaf, conf:low), `hw_reg_write_pair`
  (OPL/AdLib-style index/data port write w/ delay, conf:med)
- **far-ptr table / trampolines**: `farptr_table_get` (210K — index→far ptr,
  4B stride), `far_cb_0/1/2` (6B stubs → cs:220B8/220BC/220C4),
  `far_cb_with_args` (ES/BP primed → cs:220E0), `near_fnptr_invoke`
  (near-indirect, contrast with the far ones)
- **CS state/flag**: `active_farptr_set` (203K) / `active_farptr_restore`
  (206K) pair on cs:22210:22212, `flag_byte_get` (76K),
  `cs_byte_test_zero` (ZF-returning predicate), `flag_clear`,
  `flag_set_lowbit`, `cs_word_store`, `flag_bits_clear`
- **geometry**: `view_limits_load` (→ cs:2547C..25482 X/Y min/max),
  `segment_clip_test` (79K — rect clip vs those limits), `pos_clamp_40`
  (clamp to [-40,40]), `pos_diff_norm` (563B — 32b delta / (1<<scale))
- **init/irq**: `irq_unmask_and_query` (PIC port 21h &= ~3 → IRQ0+IRQ1),
  `es_ptr_slots_init`, `es_word_zero`

**Where they were written:** `registry/naming.yaml` (24 entries, new `sig`
field + `notes` with confidence: high/med/low) → `naming.py apply`
(24 `function_bytes` name fields + 6 text hits in `src/asm/frameless_families.asm`)
→ **`naming.py push-ida` (all 24 confirmed in the IDB)** →
`registry/routines.yaml` (+24 entries, `port_status: unported`,
`hypothesis` = ledger name; stale `counts` refreshed to 1,236/ASM 871).
`naming.py check` **green** (68 ledger entries, structs valid).

**Regression found & fixed — diagnostic destroyed 4 hot functions:**
`tools/_verify_claims.py` called `ida_bytes.del_items()` on *existing*
functions just to disassemble them; the deletion **persisted** (idat -A
saves a dirty DB), removing the 4 hottest Level-0 leaves — `sub_112A1`
(318K), `sub_2703F` (210K), `sub_2228F` (206K), `sub_22285` (203K) —
from the IDB. Detected as `KeyError` on `sub_112A1` when ranking Level 0.
Restored with `tools/restore_level0.py` (known-good boundaries,
autoanalysis disabled, save without `auto_wait`) → **1,232 → 1,236 fns**;
re-extracted, re-classified, callgraph rebuilt. **Rule: diagnostics must
never `del_items` existing functions** — read existing item heads instead
(`tools/dump_level0.py` does this).

**`naming.py check` was unusable (hung minutes → now 0.5 s):** `SRC_ROOTS`
is `src/`, which holds *two* full DOSBox checkouts (`dosbox-staging`,
`dosbox-x` — 4,747 `.c/.h/.asm` files, 70 MB). `check` scans every file ×
68 patterns. Fixed by pruning `dosbox*`/`build`/`.git` in
`_iter_text_files`. **Rule: never point text-scan tools at `src/` without
pruning third-party trees.**

Note: `push-ida` reported `MISSING` for 16 *previously verified* entries —
**benign**: they were renamed in the IDB by earlier sessions, so the lookup
by old `sub_*` ida name fails (idempotent). Verified by probing the IDB
directly: `always_true`, `long_accumulate`, `key_mapper`,
`farptr_field_reader`… all correct.

Impact: the bottom layer of the call graph now has semantic names +
recorded register contracts, so Level-1+ callers become readable next;
two toolchain footguns (del_items-in-diagnostics, unpruned text scans)
documented and one fixed.

---

## 2026-10-16 40 — Reproducibility audit: was the IDB rebuildable from git alone?
Status: AUDITED — 3 real gaps found and fixed

Questions asked: *(a)* can we regenerate the IDB from scratch with everything
tracked in git? *(b)* is the process documented well enough for another agent?
*(c)* are we missing tracking anything important?

### What was already sound (no change needed)
- **All 13 IDB-mutating scripts are committed** (git has no untracked `tools/`).
- **Every rebuild *input* is committed**: `overlay_placement.json`,
  `overlay_entries.json`, `fixups_to_apply.json`, `thunk_states.json`,
  `boundary_report.json`, `rtlink_loads.json`, `callgraph_refs.json`, 28
  `memdump/*` traces.
- `extract_ida_bytes.py` preserves **stable keys + `name` fields** across a
  re-extract, so ledger names survive a rebuild.
- `classify_routines.py` degrades gracefully if `survey.json` (ignored) is absent.
- `naming.py push-ida` re-syncs all 68 ledger names — in the runbook.
- `.gitignore` correctly covers IDA binaries/logs; IDA version + paths documented.

### GAP 1 — the runbook was STALE (worst finding)
**Two diverging runbooks existed** (`pipeline.md`: 6 IDA steps;
`workflow/idb_regeneration.md`: 8 steps). **Both omitted:**
- `apply_trace_functions.py` — finding 33, **+135 functions** (1,080→1,215),
- `patch_thunks_ida.py` — finding 35, 299/303 thunk patch (unblocks Track C),
- all finding 37–39 registrations (`add_boundary_functions`,
  `add_trace_functions`, `fix_trace_functions`, `add_indirect_targets`,
  `restore_level0`) — **+~26 fns**,
- `export_callrefs.py` + `callgraph_bottomup.py` (the callgraph artifact),
- **any verification step**, and **step 0** (EXE → `.i64` creation).

Reproducible-from-scratch implication: following either runbook yields an IDB
**~157 functions short (1,236 → ~1,079, ~13%) with an unpatched thunk table
and a stale callgraph — silently**, because nothing checked.

**Fixed:** `workflow/idb_regeneration.md` rewritten as the **single canonical**
runbook (step 0 → 6 → V, full order, prereq table, 5 rules); `pipeline.md`
now links to it instead of carrying its own copy.

### GAP 2 — nothing verified a rebuild
`extract_ida_bytes.py` **overwrites `function_bytes.json` unconditionally** —
the committed byte ground truth could be silently shrunk. Only the 68 *named*
functions would be caught (by `naming.py check`), not the other ~1,168.

**Fixed:** `tools/verify_rebuild.py` — diffs the fresh extract against **git
HEAD** and reports `LOST`/`ADDED`/`CHANGED` (ea/size/bytes drift); **exit 1 on
divergence** so it can gate commits. Tested: `faithful — 1236/1236`, exit 0.

### GAP 3 — provenance TODO + reliance on *implicit* IDB save
- `registry/FALCONCD.EXE.yaml` had **`md5: "TODO"`** while `game/` is gitignored
  — a fresh clone had no way to verify its input. **Fixed:** md5
  `2BDD74F4B50729B8583224CCE471805A` + sha256 + provenance note (both copies
  independently re-hashed and confirmed identical).
- **3 scripts mutated the IDB but never called `save_database()`** —
  `ida_snapshot.py`, `patch_thunks_ida.py`, `apply_fixups_ida.py` — relying on
  idat's implicit dirty-DB exit-save. **That is the same implicit save that
  silently persisted the finding-39 `del_items` destruction.** All three now
  save explicitly. Three further mutators remain save-less but are
  **unreferenced** by any doc (`analyze_overlays_ida.py`,
  `ida_snapshot_fixed.py`, `_diag_entries.py` — legacy/ephemeral); left alone
  deliberately, flagged here so nobody wires them into the runbook.

### Gap 4 (documented, not "fixed") — the EXE itself is not in git
`FALCONCD.EXE` (the rebuild's only binary input) is excluded by design
(`*.exe`, `game/`). Documented as an explicit prerequisite with an md5 gate in
step 0 of the runbook. This is the one thing git alone cannot supply.

### Verified empirically (not assumed)
- **Step 0 works from a bare `.EXE`**: `idat -A -S tools\ida_snapshot.py <EXE>`
  created `FALCONCD.EXE.i64` (2,434,305 B) + `survey.json`/`functions.tsv`/
  `overlays.json` in a clean temp dir (tested twice, once after the explicit-save
  edit — identical sizes, no regression).
- `verify_rebuild.py` returns exit 0 / "faithful" on the current tree.

Impact: the answer to (a) is now **yes, gated by a verification step**; to (b)
**yes, one canonical runbook covering the full 1,236-fn history**; to (c) the
two things that were missing (binary provenance, rebuild verification) are now
tracked. Remaining known non-reproducibility: the EXE (by design) and the
intentionally-unreferenced legacy scripts.

---

## 2026-10-16 41 — Level-0 batch 2 (23 named) + two YAML type bugs found
Status: CONFIRMED

**Level-0 naming batch 2** (endpoints 24..48 by dynamic call count): **23 new**
identifications — the 24th slot was `sub_1A6D4`, already the verified
`long_accumulate`. Ledger **68 → 91 symbols**; `registry/routines.yaml`
**45 → 92 entries**; all pushed into the IDB; `naming.py check` green.

Groups identified:
- **`far_cb_3..9`** — completes the CS callback-trampoline family: **10**
  6B stubs (`far_cb_0..9`) each bound to one far-fn-ptr slot in the table
  `cs:22088..22154`, plus `far_cb_with_args` / `far_cb_gated` variants that
  prime ES/BP/args first.
- **callback-argument block cluster** (cs:24BB8 word, 24BBA/24BBB bytes,
  24BBC flag, backup 24BC0..24BBF): `cs_word_store`, `cb_args_save`,
  `cb_args_restore` (exact inverse pair), `cb_args_table_set` (indexes table
  `cs:54F0`, returns seg 0x834A — the same ES the trampolines load).
- **tables/geometry**: `table_dword_get` (4B-stride read → DX:AX),
  `table_rec_load_scaled` (8B record copy with field4 `<<4`), `clip_flags_batch`
  (Cohen–Sutherland-like outcode bits into a 16B-record array, helper at
  0x28E17), `index_limit_check`, `list_node_unlink` (**doubly-linked word-array
  removal**, `664h`=next / `6ACh`=back, set to 0xFFFF — conf: high),
  `group_all_free_check` (8-slot release predicate).
- **state getters/setters**: `cs_word_get_25499`, `cs_word_get_10842`
  (IDA mis-labels it `byte_10842` but it's read as a word), `cs_byte_set_25488`,
  `cs_state_copy_es` (4 CS words → ES:DI), `flag2224a_clear`/`flag2224a_set`.

Address-encoding names (`cs_word_get_25499`) are deliberate: the access target
is certain, the meaning of the value is not yet known.

### Two YAML schema bugs — and why `naming.py check` stayed green

1. **Duplicate insert (116 → 92 entries).** The routines insert helper wrote
   `ea` as a quoted hex **string** (`ea: '0x11223'`) while YAML-native entries
   are **ints** (`ea: 0x16FDD`, YAML hex literal → int). Its own skip-check
   compared `int in {ints + strs}` → never matched → **24 entries inserted
   twice**. Fixed with a *text-level* dedupe (keeps first block per ea, drops
   later ones, preserves all inline comments — deliberately NOT a
   yaml.safe_load/dump round-trip, which would have destroyed them).

2. **Silent validation bypass (the dangerous one).** `naming.py check`'s
   hypothesis-sync does `fb[k]['ea'] == ent['ea']` — `fb` holds **ints**, my
   entries held **strings**, so the comparison *never matched* and the check
   **silently skipped every entry I had added** while still printing
   `check OK`. Detected only because I questioned why `inserted 47` when 23
   were new. Fixed by unquoting `ea`/`seg`/`ofs` (`ea: '0x…'` → `ea: 0x…`);
   now **91/91 hypothesis-sync resolvable** and `counts.tracked` refreshed
   116 → 92 (it had gone stale too).

Also self-inflicted: my first unquote regex anchored `^ea`, which never
matches the `  - ea:` / `    seg:` line prefixes — 47 entries stayed strings
after "the fix"; second pass used `^(  - |    )`.

**Rule: when adding to an existing YAML schema, match the native scalar types
exactly — a type mismatch turns a downstream key-join into a silent no-op, and
a green `check` is then evidence of nothing. Always assert the round-trip**
(`unique ea == count`, `types == {int}`, `resolvable == all`).

Impact: 47 Level-0 leaves now named (383K+ cumulative dynamic calls across
batch 1+2); the callback-trampoline family and its argument block are mapped;
two registry bugs that made validation vacuous are fixed and a regression
rule recorded.

---

## 2026-10-16 42 — Level-0 is done; the 51,676 B blob `sub_2E2D0` split
Status: CONFIRMED

**Q: have we found all Level-0 functions?** — *Identified*: yes, all **328**
(`has incoming edge, no outgoing resolvable edge`) are enumerated in
`callgraph_partial.json`. *Named*: 56. But **Level-0 is effectively
exhausted**, and the numbers say stop:

| remaining unnamed Level-0 (272) | count |
|---|---|
| ASM / LEAF / DATA / C | 216 / 40 / 13 / 3 |
| **dyn > 0** (any runtime evidence) | **69** (total 6,532 calls) |
| dyn == 0 (leaf only in the static graph) | 203 |

The 69 "valuable" remainder average ~95 dynamic calls each — versus batch 1's
318K/210K and batch 2's 10K→539. **Marginal value of further Level-0 batches
is ~0; the value has moved to Level 1.** Also: 13 of them are DATA-class
(dispatch labels registered as functions) and belong in graph cleanup, not
naming.

**Method soundness check:** scanned all 328 endpoints for register-indirect
calls (`FF /2`/`/3` with mod=11 — these leave *no* xref target and would make
false leaves). Result: **only 2 of 328** (`sub_2E2D0`, `sub_14040`). The
leaf definition holds.

**But that scan exposed `sub_2E2D0` — a 51,676 B "function"** (the next
largest is 4,169 B; it is 33× larger, classified `confidence: low`):
- range `0x2E2D0..0x3ACAC`, and it was **also a Level-0 node** → it
  corrupted the very graph being traversed;
- contains **5 far-call targets MID inside it**, two hot: `0x2E2E0`
  (**8,312 calls**) and `0x2E2F0` (**8,696 calls**), plus `0x2E2D0` itself
  (12,106);
- raw-byte mapping showed the real structure: 16-byte slots each ending in
  `retf` (`cb` at +0x0F, +0x1F), then real code from +0x20 with its `retf`
  at +0x79 → `0x2E34A` (IDA's independent probe agreed exactly);
- it is dense real code (`8b`×1589, `9a`=call far×1495, `2e`×1405), not data.

→ Classic **multi-entry assembly routine** whose secondary entries IDA never
registered (the same shape as the `0x1755E` case discussed in finding 38).

**Split performed** (`tools/split_blob_2E2D0.py`, guarded):
`[0x2E2D0,0x2E2E0)` 16B + `[0x2E2E0,0x2E2F0)` 16B + `[0x2E2F0,0x3ACAC)`
51,644B = **exact 51,676 B coverage, all ending `retf`, no gap/overlap**.
Before mutating, the `.i64` was copied to `FALCONCD.EXE.i64.bak_before_split`
(IDB is not in git; idat may persist a dirty DB on exit even when the script
refuses to save → **"I aborted" is not a rollback**).

Results: functions **1,236 → 1,238**; boundary report **EXACT 466 → 468,
MID 98 → 96**; `0x2E2D0`/`0x2E2E0`/`0x2E2F0` all **EXACT** now;
`naming.py check` green; callgraph rebuilt (1,505 edges, 328 endpoints).

**`verify_rebuild.py` taught to distinguish SPLIT from drift:** the gate
correctly failed the change (`exit 1`) as `CHANGED sub_2E2D0: bytes differ
103352->32`, but review showed it was an *intended* subdivision — a gate that
trips on every improvement gets ignored. Added a `SPLIT` classification: a
shrink counts as intentional only when the old range is **exactly tiled**
by contiguous new functions. Now reports `SPLIT 1 (tiled by 3 fns)` and passes
(`exit 0`) while real byte drift still fails. Runbook gained **rules 6**
(backup `.i64` before high-consequence mutation) and **7** (how to read
SPLIT vs CHANGED).

Impact: two hot far-call entries (8.3K + 8.7K) recovered as real functions;
the largest graph artifact removed; Level-0 declared complete with evidence
(2/328 false-leaf rate, value cliff quantified); the rebuild gate now survives
deliberate improvements instead of being ignorable.

---

## 2026-10-16 43 — Level-1 batch 1: 24 named; bottom-up payoff demonstrated
Status: CONFIRMED

Level-1 = the **callers of the named leaves** (351 nodes, 137 with dynamic
evidence). Named **24** → ledger **91 → 115**, `routines.yaml` **92 → 116**,
all pushed to the IDB, `check` green, `verify_rebuild` faithful (1,238/1,238).

**Identified (24), by group:**
- **input/control**: `mouse_buttons_get` (35B, **320K calls — hottest L1**:
  `INT 33h AX=0003` = mouse position+buttons, `BX&7`, falls back to the named
  `input_status_pack`), `control_axes_read` (button-dir bits → rate
  integration → **±0x800 clamp** with separate X/Y divisors).
- **geometry (a 4-member family + friends)**: `angle_xy_far` / `angle_xy_near`
  / `angle_aux_far` / `angle_aux_near` — siblings differing only in record
  segment (es: vs default) and field pair (+0/+2&+4/+6 vs +8/+0Ah), all
  returning a 1/16384-turn code (±0x1000/0x2000/0x3000) via a shared
  helper chain; `angle_wrap` (modular normalisation into ±0x2000);
  `point_xy_transform`, `fixed_matrix_mul` (chained `imul`+0x4000+shift =
  16.16 matrix chain), `view_projection` (1,076B, **283K calls**: delta×16/z
  divide with dispatch — perspective transform).
- **trampolines/wrappers**: `stub_to_24988` (**303K**), `stub_to_249d8`,
  `stub_to_24980`, `stub_to_248d1`, `stub_to_25777`, `stub_to_205c3`
  (the 4B far→near `NEARTHUNK` family), `arg_dispatch_wrap`,
  `view_limits_wrap`, `far_obj_field_call` (table→object→member→call).
- **dispatch/state**: `event_state_machine` (2,266B, jump table
  `jpt_1AB65[bx]` + tick counters, **14 callees incl. 4 C-class**),
  `record_queue_push`, `flag_bits_dispatch`, `current_item_check`.
- **formatting**: `int32_to_ascii` (`div 10` + `add al,30h` + sign `2Dh`/
  pad `20h` back-fill loop).

**The bottom-up method paid off exactly as intended:** `mouse_buttons_get`
became identifiable *because* its fallback callee was already named
(`input_status_pack`); `view_limits_wrap` because of `view_limits_load`;
`far_obj_field_call` because of `farptr_table_get`. Reading the callee first,
then the caller, turned opaque 35B/14B shells into definite functions.

**Four YAML/identifier bugs — three caught by `check`, one only by assertion:**
1. **Uppercase hex in identifiers**: `stub_to_249D8`/`_248D1`/`_205C3`
   violated the ledger's lowercase rule (`^[a-z_][a-z0-9_]*$`). Caught by
   `check`; renamed to lowercase hex (`stub_to_249d8` etc.) — same convention
   already used for `flag2224a_*`.
2. **`yaml.dump` folded long `sig` strings at width 80 and emitted
   *unindented* continuation lines → corrupted `registry/routines.yaml`**
   (ScannerError at line 1242). Caught only because the script re-parses to
   assert. Restored from git; emitter switched to **`json.dumps`** (single-line,
   escaped → valid YAML double-quoted scalar).
3. (from finding 41, avoided by construction here): ea compared as **int**
   both sides; hex written **unquoted** so it round-trips as int.
4. Added a hard **round-trip assertion block**: unique-ea, types=={int},
   hypothesis-resolvable — so a silent key-join failure or a broken document
   can never again present as success.

**New tool:** `tools/add_routines_l1.py` (idempotent; picks up any newly
`sig`-bearing ledger entry, splices before `counts:`, refreshes counts,
asserts). Reusable for later batches.

**Flagged, deferred (open items):**
- `sub_228BF` (`int32_to_ascii`) is **classified DATA but is unquestionably
  code** — concrete evidence for the graph-cleanup task.
- 3 merged trampoline/wrapper ranges need splitting:
  `sub_256BE` (4B `call;retf` tail at +0x0B), `sub_25F64` (6B
  `call cs:220E4` trampoline prefix), `sub_24F03` (4B tail at +0x2D).

Impact: the middle of the call graph now has names too, and — more
importantly — the *interpretation* method is proven: name callees first, then
callers become readable. Two more classes of silent-corruption (identifier
case, YAML folding) are now blocked by `check` + assertions rather than
discovered by accident.

---

## 2026-10-16 44 — Level-1 batch 2: 29 named; found the graph's hub node
Status: CONFIRMED

Level-1 batch 2 (next 28 by dynamic count, all disassembled) + `sub_121C2`
verified separately. Ledger **115 → 144**, `routines.yaml` **116 → 145**,
all pushed to IDB, `check` green, `verify_rebuild` faithful (1,238/1,238),
round-trip assertions pass (145 unique ea, all `int`, 144 hypothesis-resolvable).

**Identified (29) by group:**
- **Dispatch hubs** (the important finds):
  - `op_dispatch` (`sub_2257B`, 29B, 6.5K dyn) — `call cs:off_22060[BX]`
    indexed dispatcher with **39 callers and 17 table targets — the
    highest-fan-in node in the whole graph**; masks a flag in `cs:22248`
    around it. This is *the* parameterized-operation entry point
    (`param_table_init` calls it with field ids 6/0xA/0xE/8).
  - `fn_table_dispatch` (`sub_231F0`) — `call cs:off_22D2A[BX]`, 14+ targets,
    saves/restores a context around it.
  - `entity_setup_step` (`sub_121C2`, 415B, ≥8 stack args) — stores 5 args
    (2 far ptrs + coords + count) into an entity record `ds:7753C+1A1..1B1`,
    scales by `0x96` (×150), then runs **19 callees** (entity update, dispatch,
    clamp, load, zero).
- **entity/state**: `entity_state_load` (775B — the batch-1 `clip_flags_batch`
  consumer), `entity_counters_update` (per-entity countdown over an array),
  `entity_update_batch` (3 subsystem steps, DS=ES=71C1), `param_table_init`
  (repeated `op_dispatch` with field ids).
- **state plumbing**: `farptr_state_set` (3 far-ptr setters + an embedded 2D
  rotate), `state_farptr_get`, `stream_record_read` (10-byte record-stream
  cursor at `cs:11CF4:11CF6` + fixed-point coord unpack), `irq_unmask_with_ds`.
- **input/control**: `mouse_buttons_get_2` (`INT 33h` + `AND 3`, 2-button
  subset of the batch-1 `mouse_buttons_get`), `control_axis_value` (reads one
  clamped accumulator; sibling of `control_axes_read`), `flag22220_clear`,
  `pending_task_run` (`cli`/`sti` one-shot — deferred task drained in ISR
  context; called from startup).
- **object-table family** (siblings of `far_obj_field_call`): the same
  `farptr_table_get` + `sub_2647E` type-code pattern split three ways by type —
  `farobj_copy_cond` (types 1/2), `farobj_field_set` (type 3),
  `farobj_copy_block` (18B unconditional copy).
- **trampolines/wrappers**: `stub_to_239f2`, `stub_to_23dcd`,
  `farwrap_25a1c`, `overlay_tail_bridge` (sole caller = `view_projection`;
  `call sub_2AFBD; jmp r05_e19` = resident→overlay tail jump).
- **geometry**: `vec_transform_scale` (normalize/transform chain),
  `bbox_clamp` (clamped bounding rect from the `table_rec_load_scaled` record).
- **hw/audio**: `channel_release` (clears a channel and writes hardware via
  `hw_reg_write_pair`; 4 of 6 callers are C-class), `hw_seq_step`,
  `state_dispatch_cb`, `angle_adjusted_copy` (low conf — undecoded regions).

**Discipline applied (and one rename):** `sub_121C2` was first named
`entity_step_main` *from callee context alone*. Before pushing I disassembled
it (a 415B, ≥8-arg entry deserves it), found it stores args into an entity
record and scales ×150 before stepping, and **renamed it to
`entity_setup_step` with a verified sig**. Rule of thumb recorded: *callee
context suggests; disassembly confirms.*

**New boundary-error candidates (→ open items):** `sub_23036` (≥4 entries),
`sub_128A1` (4), `sub_22996` (2), `sub_127D4` (3 tail), `sub_25A06`
(trampoline+wrapper merged — same shape as `sub_25F64`), `sub_26FF4` (4),
`sub_1509E` (shares a prologue with `sub_128A1`+0x2C → possible duplicate),
`sub_23D85` (4B stub in a 72B range with ~64B trailing data), `sub_26FE4`
(possible 1B overrun), `sub_22DFF` (undecoded regions 0x22E18–0x22E93 —
possibly self-modifying; its name is conf:low until resolved).

Impact: 85 Level-0+Level-1 nodes now named (144 ledger entries total); the
graph's highest-fan-in node (`op_dispatch`, 39 callers) is identified, which
makes Level 2 tractable; six more IDA boundary errors found and tracked rather
than silently propagated; the "suggest then verify" rule keeps callee-derived
hypotheses from becoming unexamined names.

---

## 2026-10-16 45 — Level-1 batch 3: 30 named; IDAPython has no PyYAML
Status: CONFIRMED

Level-1 batch 3 (next 30 dyn>0, 2,369 → 86 calls). Ledger **144 → 174**,
`routines.yaml` **145 → 175**, pushed to IDB, `check` green, `verify_rebuild`
faithful (1,238/1,238), all assertions pass (175 unique ea, all `int`).

**Bug found: `import yaml` fails inside IDAPython.** `dump_level0.py` loaded
the ledger with `try: import yaml ... except: led = {}` — so `led` was
**always empty inside IDA**. Consequences that had been hiding in plain sight:
the unnamed-node **filter never applied** (batch indices drifted onto already-
named nodes) and every `callees(...)` annotation silently fell through to the
`(size, class)` branch — no `sub_X<=semantic_name` was ever printed. Detected
because the filter reported "351 UNNAMED" while listing `sub_1016C` (already
named `mouse_buttons_get`). **Fix: read `function_bytes.json`'s `name`
fields** — written by `naming.py apply`, always in sync, zero dependencies.
Rule: *never assume an optional import inside IDAPython; the except-path
must be visible, not silent.*

**Identified (30), by group:**
- **stubs/wrappers**: `stub_to_24a94`, `farwrap_24aef`, `farwrap_gated`,
  `farwrap_103db`, `overlay_tail_bridge_b` (8B code + 198B resident-tail data
  in range), `far_list_dispatch` (indexed `cs:off_274A2[BX]` + `retf 8`),
  `dual_step_wrap`.
- **flag/callback clusters**: `flag254a1_set` (**7 entries** in 57B — the
  worst merge seen since `sub_2E2D0`), `flag_block_build`, `mouse_buttons_test`
  (pairs the named `mouse_buttons_get` with an 11-byte flag-block scan),
  `flag1084c_get`, `draw_from_struct`, `cb22124_dispatch`,
  `farptr_table_invoke` (pushes a far-ptr pair from table `cs:7DF2/7DF4`).
- **entity/list/state**: `list_record_register` (C, record = `SI*60+6D6h`),
  `group_register_main` (**1,511 B — the largest unnamed C function**, calls
  `group_all_free_check`), `index_scroll_step` (counter wrap 0x157..0x2AE,
  called by `event_state_machine`), `irq_state_init`, `state_mode_check`
  (returns 1 iff `es:77B44+2 ∈ {2,3,4}` — **10 callers**, same predicate
  `irq_unmask_and_query` tests internally), `range_validate`,
  `table_iterate_loop`, `indexed_byte_get`,
  **`table_dword_set`** (exact setter twin of the already-named
  `table_dword_get` — the pair now closes).
- **input/mode**: `critical_section_wrap` (`pushf; cli; …; popf` —
  unambiguous), `scaled_hw_write` (C), `key_event_process` (C; `key_mapper`
  callee decisive), `dist_accumulate` (C; drives `long_accumulate`),
  `math_saturate_store`, `rect_arg_store`, `farobj_copy_invoke`.

**6 C-class functions named** (`list_record_register`, `group_register_main`,
`scaled_hw_write`, `key_event_process`, `dist_accumulate`) — these are now
concrete port candidates, and 4 of them sit under `event_state_machine`.

**New cleanup evidence:** `sub_10E03` classified **DATA but is code** (2nd
instance after `sub_228BF`), its callee `sub_224C2` likewise; new multi-entry
ranges `sub_254C0` (7), `sub_27697` (2), `sub_257B1` (2), `sub_10E03` (2),
plus `sub_2BFCD`'s 8B-of-code-in-210B-of-data.

Impact: **174 ledger entries / 300+ dynamic-call-weight of Level-0+L1 named**;
the silent `led={}` degradation is fixed so future batches filter and annotate
correctly; 5 more C port candidates surfaced; the merge-error list keeps
growing in a *systematic* way (multi-entry ranges are clearly a recurring
class of IDA limitation here, worth one bulk cleanup pass later).

---

## 2026-10-16 46 — Level-1 batch 4: 30 named; two tooling traps caught before they corrupted a batch
Status: CONFIRMED

Level-1 batch 4 (next 30 dyn>0, **dyn 84 → 9**). Ledger **174 → 204**,
`routines.yaml` **175 → 205**, `check` green, `verify_rebuild` faithful
(1,238/1,238), assertions pass (205 unique ea, all `int`, 204 resolvable).

**New gate added — positive IDA read-back.** `push-ida` reports `MISSING`
whenever an *old* `sub_XXXXX` name no longer resolves, which is the normal
sign that a *previous* push already renamed it — so its OK/MISSING counts
cannot prove correctness. Added an IDA script that walks all 204
`function_bytes.json` entries and compares `get_func_name(ea)` against the
ledger: **`match=204 mismatch=0`**. (`push-ida` output alone would have left
this unproven.)

**Trap 1 — `L0_START`/`L0_END` silently index the wrong list.** The batch
bounds name the *unnamed* node list, which **shrinks by N every batch**. I
first ran batch 4 as `[144:174]` (carrying the arithmetic from the ledger
count) and got back 30 plausible-looking disassemblies for *much* lower-dyn
functions — the script happily returns whatever slice it is handed. Caught
only because the header printed `batch [144:174] of 267 UNNAMED` while the
top of the log started at `dyn=84`. **Rule: every batch starts at
`L0_START=0`; the ledger size is never the slice index.**

**Trap 2 — PowerShell 5.1 writes a BOM that IDAPython refuses.**
`Set-Content -Encoding UTF8` emits U+FEFF, and IDAPython's `compile()` dies
with `invalid non-printable character U+FEFF` before running a line — the
IDA run exits 1 and *no log is produced*, which looks like a crash rather
than a one-character encoding bug. Fix: `[IO.File]::WriteAllText($p, $s,
(New-Object Text.UTF8Encoding($false)))`.

**Docs integrity fix:** an `Impact:` paragraph about DGROUP `0x6C27` /
`0x46A4` / MCB owner `0x1E5` / VGA Mode X was dangling at the very end of
`findings_log.md` with **no `##` header**, directly under finding 45 — it is
finding 35's Impact line, written to the wrong offset. Relocated beneath
finding 35, where its content already lives. (An append-only log that
accumulates orphaned fragments defeats its own purpose; worth a periodic
structural check.)

**Identified (30):**
- **Interrupt vectoring (highest confidence in batch)**: `int8_vector_hook`
  (`sub_174AB`, `AH=35h/AL=8` get + save + `AH=25h/AL=8` install `cs:0C57h`)
  and `int8_vector_unhook` (`sub_17501`, restore saved seg:off) — a matched
  pair around the system timer IRQ.
- **Hardware/sound**: `sound_device_init` (`sub_1740D`) dispatches on a
  device type; type 2 passes **`0x388`** (the AdLib/OPL2 base port) into the
  `hw_reg_write_pair` family — this is the first *port number* to confirm the
  sound path. `mem_unmap_all` releases three banks conditionally, third via
  `INT 67h`.
- **Key/mode pipeline**: `key_code_resolve` (dyn=83) and
  `key_action_execute` (411B) form the key-id translator + action driver;
  `mode_slot_select` / `mode_slot_setup` / `mode_slot_setup_wrap` /
  `mode_slot_masks` / `mode_flags_apply` / `mode_check_wrap` / `step_dir_apply`
  are the slot-state machine that repeatedly appears around
  `state_mode_check`. `kb_records_rebuild` drives 11 `kb_*` field accessors.
- **Far-stub thunks** (all `high`): `cb_args_table_set_wrap`,
  `cs_word_store_wrap`, `stub_to_1119c`, `farptr_lds_invoke`,
  `farptr_lds_bx_invoke`, `farptr_7075_pick`, `tail_bridge_r30_e66`.
- **`mouse_wait_click`** (`sub_25102`) closes the cluster begun by
  `mouse_buttons_get` / `mouse_buttons_test` / `flag_block_build`.

**New cleanup evidence:** `sub_10D8C` is **4 disjoint `retf` routines in one
58B range** (far-ptr getter, table looker-up, mouse poll, `AH=48h` mem-size
query) plus 9B of embedded data — a 5th multi-entry range, taking the list to
~17. **3 C-class port candidates** named: `mode_slot_masks` (492B),
`mode_slot_setup` (279B), `kb_record_load` (562B).

Impact: **204 ledger entries named** (83 → 113 of 351 Level-1 nodes across
batches 1–4); dyn-weight of the remaining unnamed Level-1 top has dropped to
9 per node; the push-verification gap is closed with a real read-back gate;
two tooling traps that would have silently produced a *wrong* batch and a
*crashed* script are now documented as rules; the findings log's structural
drift is repaired.

---

## 2026-10-16 47 — Level-1 batch 5: 30 named; **dynamic evidence for Level-1 is exhausted**
Status: CONFIRMED

Level-1 batch 5 (next 30 dyn>0, **dyn 8 → 0**). Ledger **204 → 234**,
`routines.yaml` **205 → 235**, `check` green, `verify_rebuild` faithful
(1,238/1,238), assertions pass, **read-back `match=234 / mismatch=0`**.

**The batch tail hit `dyn=0`, which ends a strategy.** Because nodes are
sorted by descending dynamic-call weight, reaching rank 25 at `dyn=0` means
**every Level-1 node with any dynamic evidence is now named** — 143 of them.
The remaining **207 have zero dynamic-call weight**, exactly mirroring Level-0
(203 of 328 endpoints). Sorting by dyn therefore no longer ranks anything, so
batch-by-dyn is finished; what's left needs static fan-in ordering, Level-2
target resolution, or the bulk cleanup pass. Recorded in Open Items rather
than discovered again next session.

**High-confidence system finds (these anchor subsystems):**
- **`ems_init` (`sub_1053A`)** — a textbook EMS/LIM bring-up: `INT 67h`
  `AH=40` status → `AH=41` page frame → `AH=42` unallocated pages →
  `AH=43` allocate → `AH=44` map, storing the handle at `cs:unk_1022B`.
  This **retroactively validates** batch 4's low-confidence `mem_unmap_all`,
  which reads the very same `unk_1022B` handle and issues the same `AH=44`.
  One function confirms another 30 lines earlier — the value of leaving
  confidence levels visible instead of upgrading them silently.
- **`program_terminate` (`sub_2224C`)** — five cleanup calls then
  `AH=4Ch int 21h`. Process exit, unambiguous.
- **`vec3_dot` (`sub_23F62`)** — three 16×16 products accumulated into
  DX:AX. Unambiguous geometry primitive.
- **`file_create` (`sub_22699`)** — `AH=3Ch int 21h` with error-flag
  side effects. Critically, its caller list is **`op_dispatch, sub_22699`**:
  this is a *confirmed `op_dispatch` dispatch target*, the first concrete
  evidence feeding Level 2 (alongside `sub_227D3`). ~15 targets remain.
- **`adlib_operator_write` (`sub_17D6C`)** — builds a register index from
  five per-channel byte arrays and calls `hw_reg_write_pair`, the same writer
  `sound_device_init` feeds with port `0x388`. The AdLib path now has two
  independent confirmations.

**Structural finds:**
- **`mode_slot_enter` (`sub_1950C`)** is the *active-mode setter*: two-stage
  lazy init on `es:[SI*2+43Ah]` (initialized) and `es:[SI*2+428h]`
  (activated), then writes `es:7753C+25Bh = SI`. It complements
  `mode_slot_select`/`mode_slot_setup` from batch 4 — together they are the
  slot state machine.
- **`state_flags_clear` (`sub_1D3DB`)** has **6 callers** — the highest
  fan-in in this batch.
- **`sub_10BE2` (`stack_reset_dispatch`)** resets SP, does
  `pushf/call far/popf`, and branches on CF — yet its *outgoing* edges reach
  all four `tail_bridge_*` thunks, `program_terminate`, `state_swap_far_call`
  and `mode_slot_setup_wrap`. It is a subsystem dispatcher; kept `conf: low`
  because the CF semantics aren't pinned down.
- **A 4-function buffer pair discovered by cross-reference**: `slot2_alloc`
  ↔ `slot2_copy_chunks` and `slot3_alloc` ↔ `slot3_copy_chunks` share the
  `cs:11BA6+6/+8` and `+0A/+0C` word pairs respectively, and the `_copy_`
  half is gated on `sub_10463(BX=2)` / `(BX=3)` — the same index predicate
  batch 4 named `slot_flag_query`. `conf: low-med`, but the pairing is
  evidence-based rather than name-guessed.

**New cleanup evidence:** `sub_13755` is **DATA-class yet called** by
`entity_seg_reset` — the 3rd DATA-but-code instance after `sub_228BF` and
`sub_10E03`. Worse, a post-batch audit of `classification.json` showed
**`sub_10BE2` itself is classed DATA** despite resetting SP and doing
`pushf / call far / popf` with CF-based branching — the 4th, and the most
damaging so far because it is a dispatcher with 8+ outgoing edges that had
been silently excluded from every DATA-based sweep. **A C-class audit also
corrected a status figure:** 42 C-class functions are now named (12 from
batches 1–5), not the 11 previously written in `status.md` — the earlier
number counted only what I had *explicitly annotated*, not what the
classification file says. Three more `call sub_2AFBD; jmp far` bridges
(`sub_2BDB1`, `sub_2BDF7`, `sub_2BE33`) confirm the `2BExx` thunk cluster as
a family of four-plus.

Impact: **234 ledger entries**; Level-1's dynamic half is complete and the
remaining 207 nodes are documented as evidence-free rather than quietly
batched; the EMS reading from finding 46 is confirmed by finding 47 rather
than left as a guess; **the first `op_dispatch` target (`file_create`) is
resolved**, which makes Level 2 a concrete, actionable next step instead of a
pending idea.

---

## 2026-10-16 48 — Level 2: both dispatch tables fully resolved (31 targets); `op_dispatch` is a DOS service shim
Status: CONFIRMED

Resolved and named **every target of both indirect-dispatch hubs**:
`op_dispatch` = **16/16**, `fn_table_dispatch` = **15/15**. Ledger
**234 → 266** (264 functions + **2 globals — the `kind: global` ledger path
exercised for the first time**), `routines.yaml` **235 → 265**, `check` green,
`verify_rebuild` faithful (1,238/1,238), read-back **functions 264/264,
globals 2/2, zero mismatches**.

**`op_dispatch` is a DOS API shim** — a 16-entry near-pointer table
(`off_22060`, 32 bytes) where each slot sets `AH` and issues `int 21h`:

| k | AH | | k | AH |
|---|---|---|---|---|
|0|48h alloc| |8|4Eh find first|
|1|49h free| |9|4Fh find next|
|2|3Ch create| |10|2Fh get DTA|
|3|3Dh open| |11|memcpy (MOVSW)|
|4|3Eh close| |12|memset (STOSW)|
|5|3Fh read| |13|9h print `$`|
|6|40h write| |14|41h delete|
|7|42h lseek| |15|file size (3x lseek)|

**The BX scale was the one real puzzle, and three independent lines of
evidence settle it: opcode = BX / 2 (BX is a byte offset).**
1. **CPU semantics, dispositive:** 8086 16-bit addressing has **no scale
   field** — `call cs:off_22060[bx]` adds BX as bytes, and `op_dispatch`
   itself does no scaling between `and cs:byte_22248,80h` and the call.
2. **Behavioural cross-checks:** `sub_165AE` passes `BX=14, CH=2` with
   `CX:DX=0` → k=7 = lseek origin 2 = *seek-to-end = file size*; `sub_13F00`
   passes `BX=10, CX=4, DX=0x212` → k=5 = *read* with count 4 into buffer
   0x212. Under the alternative reading those become "get DTA" and "delete",
   for which the CX/DX state is meaningless.
3. **Every one of the 87 static call sites loads an *even* BX immediate**
   ({0,2,6,8,10,12,14} ⇒ opcodes {0,1,3,4,5,6,7}); an odd BX would be
   mid-entry. The resulting set — alloc, free, open, close, read, write,
   lseek — is exactly the classic core.

**This retroactively confirms batch 5, which had named them from structure
alone:** `slot2_alloc` = `file_size` + `(len+0x3FFF)>>14` chunk arithmetic
storing to `cs:11BA6+6/+8`; `slot2_copy_chunks` = looped opcode-5 **reads**
over those same words. Finding 45's "callee context suggests, disassembly
confirms" loop now closes on itself — a later finding validating an earlier
one is exactly the point of keeping `sig:` contracts.

**`fn_table_dispatch` is a view/projection dispatcher** — 15 targets all
writing the 3-vector `es:3884/3886/3888` (unit scale `0x1000`) before
`sub_236B8`: 8 constant writers (`view_proj_default` + `presets 1..7`, where
4..7 are the ±X/±Y unit vectors and 1/2 are mirrored ±0x555 with shared
0x199), plus 7 transform modes — `view_proj_offset_accum` (32-bit accumulate
via `fixed_matrix_mul`), `view_proj_load_3896`, `view_proj_ring_push` (the
269 B largest: a 0x12-byte ring over 0x120), `view_angles_from_struct`
(`angle_xy_near`/`angle_aux_near` + `sub_24980/24988` wrapping),
`view_proj_preset_offset`, `view_matrix_build` (the only one turning the
triple into 3×3 matrices via `sub_24536`), `view_proj_preset_direct`.

**New tool `tools/dump_dispatch_tables.py`** (replaces three throwaway
scripts): finds the table operand inside a named dispatcher, walks the
stride-2 near-pointer array to its zero terminator, and emits per-target
disassembly + callers **plus a BX→opcode histogram**. Selectable via
`DT_FNS`, so the next dispatcher costs one env var.

**Two bugs caught while building it, both worth keeping:**
- It originally matched the operand on the literal prefix `off_`. It broke
  *on the very next run* — because that run was after the table had been
  renamed to `op_dispatch_table`, so the operand printed
  `cs:op_dispatch_table[bx]`. **A tool that identifies a structure by its
  auto-generated IDA name breaks on the first rename**; it now matches the
  *addressing form* (`[bx]` + segment override).
- The BX back-scan kept walking after a `mov bx, ax` and could report a
  stale `mov bx, imm` further up, corrupting the histogram. Fixed to stop at
  the first instruction that *writes* BX (ignoring `cmp/test/push`), with
  explicit `shl bx,1` handling. The histogram was unchanged after the fix —
  but that is now *evidence*, not luck.

**Open:** 9 of 16 opcodes ({2,8,9,10,11,12,13,14,15} = create, find
first/next, get DTA, memcpy, memset, print, delete, file size) have **no
static immediate-BX call site** — all 87 sites resolve to the other 7. Either
they are driven by a computed index static analysis can't see, or they are
reached through a second entry point. Also still unknown: who writes
`cs:word_22D28`, the `fn_table_dispatch` opcode source.

Impact: **both hubs are 100% resolved** (finding 44's "17 targets" for
`op_dispatch` was really 16 — the table terminates cleanly at word[16]=0).
The binary's OS-abstraction layer is now legible: every file and memory
operation the game performs routes through one 32-byte table, and every
view/projection change routes through a second 30-byte one. Naming these 31
plus the 2 tables accounts for all of Level 2's previously-unresolved core.

---

## 2026-10-16 49 — Graph cleanup pass 1: `class` was our own bug, not IDA's — DATA 153 → 24
Status: CONFIRMED

**Root cause of every "DATA-but-code" report so far.** `classification.json`'s
`class` is **our heuristic**, not IDA's opinion, and `tools/classify_routines.py`
decided DATA purely on the raw byte string: `has_ret = b.endswith("cb") or
b.endswith("c3")`. That misses tail jumps (`jmp`), `iret`, `hlt`, `int 21h`,
`ret imm16` (`c2`), `retf imm16` (`ca`), a trailing tail-call, and any range
that runs a few bytes past its final `retn`. So findings 45/47's
"`sub_10E03`/`sub_10BE2` classified DATA but is code" were never IDA
misclassifying anything — **it was our byte test**. Correcting the record:
the fix belongs in the classifier, not the IDB.

**Fix (host + one read-only IDA pass, zero IDB mutation):**
- `tools/export_epilogues.py` → `last_insns.json`: IDA's decoded **last
  instruction**, external caller count, and interior code refs per function.
- `classify_routines.py` consults it: `retn`/`retf`/`ret` set `has_ret`;
  a last instruction in `{jmp, iret, hlt, int, ret, retn, retf, call}` is a
  terminating tail → `ASM` (medium) instead of `DATA`. Byte-only fallback is
  preserved if the export is missing, so classification still works cold.

| | before | after |
|---|---|---|
| ASM | 871 | **992** |
| LEAF | 96 | **104** |
| C | 108 | 108 |
| DATA | 153 | **24** |
| NEARTHUNK | 10 | 10 |

**Two mistakes made and caught inside this same pass:**
1. **I clobbered an existing artifact.** I first wrote my output to
   `analysis/ida_falconcd/epilogues.json` — which `extract_prologues.py`
   already owns, holding a completely different schema (`{hex-pattern: count}`
   for compiler fingerprinting). Caught by noticing `.gitignore:21` already
   listed that path, which meant something else had claimed it. Renamed mine
   to `last_insns.json`, re-ran `extract_prologues.py` to restore theirs, and
   documented the ownership in the runbook. **Rule: before choosing an output
   path, grep for existing writers *and* read `.gitignore` — an ignore entry
   you didn't write is a message from your past self.**
   The restored file independently corroborated the classification work: its
   top pattern is `e80100cb` with count **10**, exactly the 10 NEARTHUNK
   4-byte far stubs.
2. **A silently-invisible bug in my first audit:** I tested single *characters*
   against 2-char hex strings (`b[-3] in ('c2','ca','e9')`), so nothing could
   ever match and the script reported "104 unresolved". Rewrote with proper
   hex slicing — the mismatch between "IDA says 102 end in `jmp`" and "bytes
   matched 29" was the tell.

**Correction to an earlier claim:** Open Items said the 10 NEARTHUNK are
"dispatch-table labels / 4-byte far stubs, **not callable routines**". They
are `E8 01 00 CB` = `call next-near-func; retf` — genuinely callable far entry
points (one is already named `stub_to_1119c`). They are not pollution; they
belong in the graph.

**What is genuinely wrong now (24 DATA, 12 of them graph nodes):** ranges that
stop **mid-stream** — last instruction `pop`/`mov`/`push`/`sub`/`nop`/`ud0`.
Notably `sub_233C0` (4 callers, ends `pop`), `sub_1406A` (3 callers *and* an
interior ref), `sub_228BF` (= our named `int32_to_ascii`), `r08_e46` (`ud0` =
data misdecoded). These are real boundary errors needing range fixes.

**10 multi-entry ranges found by a definitive signal** (external code refs to
interior addresses, unlike my earlier prologue-guessing which found 0):
`sub_2142E` (2 interiors), `sub_14EAE`, `sub_13640`, `sub_287A8`,
`sub_23962`, `r30_e77`, `sub_213E6`, `sub_1406A`, `sub_23AC4`, `sub_2A340`.

**Scope finding — reclassifying does not move the graph.**
`export_callrefs.py`/`callgraph_bottomup.py` consume `classification.json` for
its **ea/size intervals only**; `class` is display metadata (and a filter in
my own tooling). Re-deriving Step 8 confirms it: static edges 1494 → 1503,
endpoints **328**, 6 levels, **913 nodes** — structurally unchanged. So the
"graph pollution" framing in Open Items conflated two different problems, and
actually **removing junk function objects is an IDB mutation that this pass
deliberately did not attempt** (backup taken and MD5-verified at
`FALCONCD.EXE.i64.bak-graphcleanup` first).

Gates: `naming.py check` OK (266 entries), `verify_rebuild` faithful
1,238/1,238 (LOST/ADDED/SPLIT/CHANGED all 0), `read-back` unchanged.

Impact: **the classification layer is now trustworthy** — every downstream
consumer (port-candidate queues, endpoint lists, `dump_level0` filters, my own
`sig:` claims) was reading a bucket that was 84% mislabeled. Data-classes
dropped from 163 to 34 bad-class functions, the remaining ones are actionable
range errors rather than noise, and the 10 "NEARTHUNK polluters" are exonerated
as real stubs. Pass 2 (IDB range/truncation fixes, then junk-object removal)
is now scoped and backstopped by a verified backup.

---

## 2026-10-17 50 — Graph cleanup pass 2: 1 split performed; finding 49's "10 multi-entry" was an overclaim
Status: CONFIRMED

Pass 2 was supposed to split 10 multi-entry ranges, fix 24 truncated ranges
and drop junk objects. It delivered **1 split** — and the headline is why the
other nine were wrong.

**Correction of finding 49.** The "definitive signal" (external code refs to
interior addresses) found 11 interior-ref sites. That is a *signal*, not a
*diagnosis*. Two further conditions are required, and each one eliminated
most candidates:

1. **The instruction immediately before the interior must be a terminator.**
   My first test accepted a terminator *anywhere earlier in the function*,
   which is meaningless in a 470 B body — `sub_14EAE` "passed" while its
   interior sits right after a `mov`. Strictly applied: **4 pass / 7 reject.**
2. **A passing case must still be a callable entry, not a shared block.**
   Manual byte inspection disposed of the remaining three:
   - `sub_213E6` — *no error at all*. Bytes `E9 8E 00 | 07 1F C3` = `jmp
     loc_214B9` / `pop es / pop ds / retn` / next function. It is a **shared
     epilogue** correctly owned by `sub_213E6`, which `sub_2142E` branches
     back into.
   - `sub_2A340` — the tail is `sub cx,cx; retn` (3 B), a **shared exit stub**
     reached by four *branches* from `sub_2A30E`, not by calls.
   - `r30_e77` — garbled data (`cmp eax [eax]`), DATA-class overlay region.

**The one genuine split — `table_iterate_loop`.** Raw bytes at the range
head: **`E8 01 00 CB`** = `call next; retf`, i.e. *the same pattern as the 10
known NEARTHUNK stubs*, merged with its 136 B body. `sub_2394A` calls the body
directly, bypassing the stub.

- `0x23962..0x23966` (4 B) → `stub_to_23966`, last byte `CB`
- `0x23966..0x239EE` (136 B) → `table_iterate_loop`, last byte `C3`
- coverage **exact** (140 B), both ranges verified before `save_database()`

**Independent corroboration:** NEARTHUNK went **10 → 11**, and
`extract_prologues.py`'s fingerprint map (a separate tool, restored in finding
49) lists `e80100cb` with count 10 — so the 11th instance was always there,
hiding inside an over-long function. Three unrelated artifacts agreeing is
about as good as it gets.

**Ledger handling.** The semantic name belongs on the implementation, so
`table_iterate_loop` moved to `sub_23966` and the 4 B stub took
`stub_to_23966`, matching the **8 existing `stub_to_*` precedents** (finding
43–45). Note the original `sig` already recorded "+0: near call loc_23966;
retf … 2 entries" — **the analysis had found the split point in batch 3; this
pass just made it structural.** Gate 3 then caught the stale copy: `routines.yaml
ea=0x23962 hypothesis 'table_iterate_loop' != naming 'stub_to_23966'`, fixed
(size 140→4, class ASM→NEARTHUNK).

**Two new tooling facts.**
- **`push-ida` cannot handle a split.** It resolves each entry with
  `get_name_ea(ida_name_str)`; once a function is renamed, the old `sub_*` key
  no longer resolves, so it reports `MISSING` and *silently skips the rename*.
  Harmless for already-pushed entries (finding 46) but a **real failure** after
  a split. Worked around with an EA-keyed rename. A split therefore needs an
  EA-based push, not the name-based one.
- **MD5 is unusable as an IDB integrity check.** The `.i64` hash changed after
  a few purely-read-only `idat` runs, so (a) comparing against a backup
  false-alarms immediately, and (b) the Phase-0 "MD5 verified identical"
  test only ever proved the copy succeeded — a file always matches its own
  fresh copy. Added **`tools/verify_idb.py`**: semantic check that every
  recorded function still exists at its EA with its span and name.

**Gates (all green):** integrity `INTACT` (1,239/1,239, 0 span, 0 name) ·
`verify_rebuild` **SPLIT 1 + ADDED 1, LOST 0, CHANGED 0 → faithful** ·
`naming.py check` OK (267) · read-back **265/265, zero mismatch**.
Graph: functions 1,238→1,239, endpoints 328→329, nodes 913→914.

**Still open in pass 2 (deliberately not attempted):** the 24 truncated
ranges need a *true* end address, which is not derivable from the bytes —
guessing would violate byte-identity; and dropping junk function objects
would report `LOST`, which `verify_rebuild` rightly fails on, so that needs an
explicit intentional-removal policy first.

Impact: **function boundaries are now correct where they were provably wrong,
and nobody else is.** The more valuable result is negative: a signal that
sounds decisive (interior refs) still needs two more conditions before it
justifies mutating the IDB, and finding 49 shipped it as a list of ten. Both
the strict test and the precondition check are now *inside* `split_function.py`,
so the next split cannot skip them.

---

## 2026-10-17 54 — Overlay edge connectivity: 45 registered, but orphans barely moved — the gap is not where I assumed
Status: CONFIRMED (negative result is the finding)

Chased finding 53's remaining problem (189/210 overlay orphans) with the
pipeline it had just fixed. **Registration worked; connectivity did not follow.**

**What the 16-bit decode changed.** Re-running the entry-registration dry run
*after* the bitness fix moved the candidate pool from **18 (probed through a
32-bit decode, garbage ends) to 45** whose first bytes are textbook 16-bit
prologues — `55 8B EC` (`push bp; mov bp,sp`) and `C8 xx 00 00` (`enter`).
Finding 52's warning ("do not register until bitness is fixed") was not
caution for its own sake: the earlier list would have baked in wrong ranges.

**Registered 45 / 45 planned, guard passed.** Function count **1,239 → 1,284**;
classification **C 108 → 126** (the `enter` functions), ASM 977 → 1,001,
LEAF 98 → 101, DATA 45 unchanged.

**The `target_linear → entry_ea` remap was net-negative and is reverted.**
Measured honestly: only **15 refs** carry a `target_linear` destination, and
unconditional remapping *reduced* resolution from **11 → 8 of 15**, because
some `entry_ea`s have no function. Re-tried as a non-worsening *fallback*
(remap only when direct resolve fails): static edges moved **1,766 → 1,764**
i.e. the remap contributed nothing real. Reverted to the original resolve.

**The orphan number barely moved — and went up in absolute terms:**

| | orphan / total | % | with-edge |
|---|---|---|---|
| before bitness fix | 204 / 210 | 97% | 6 |
| after bitness fix (finding 53) | 189 / 210 | 90% | 21 |
| after registering 45 (this finding) | **232 / 255** | **91%** | **23** |

+45 nodes registered, only **+2 got an incoming edge**. Percentages are
meaningless here; the honest read is that entry registration does not create
edges, because **the refs that would create them do not exist in
`callgraph_refs.json`.**

**Where the gap actually is:** `edge_counts` shows **`static_unresolved` =
1,257**. These are refs whose *source* resolves but whose *destination* is in
no registered function — i.e. `export_callrefs` is faithfully reporting
calls/jumps into regions nothing has registered. That 1,257, not the 189
orphans, is the real backlog of missing overlay (and resident) edges, and it
is a different problem from "overlay entries have no function": many of these
destinations are *mid-region*, off the 16-byte entry grid, or in areas with
no entry record at all.

**Two methodological corrections again:**
- I measured with a host-side script that mixed a **static** counter
  (`load_static`'s unresolved) into a "dynamic" line and then crashed on an
  unused `import ida` — so the first orphan printout was untrustworthy and had
  to be re-measured. The stable figures above are the re-measure.
- An unconditional remap looked principled from finding 51's analysis but
  measured worse. **A remap that can only lose must be a fallback, and a
  fallback that gains nothing must be removed.**

Gates: `naming.py check` OK (267) · `verify_rebuild` **ADDED 45, CHANGED 0,
LOST 0 → faithful** · `RECODE 0`.

Impact: **the overlay-node problem is essentially solved (45 registered, all
gates green) but the overlay-*edge* problem is not, and it was never the same
problem.** The actionable next number is `static_unresolved = 1,257` refs
pointing into unregistered destinations — not the orphan percentage. Anyone
(including me) who next sees "91% orphaned" should read it as "the call graph
is missing 1,257 destination registrations", not as evidence that overlay
entries are unregistered (they now largely are).

---

## 2026-10-17 51 — Overlay edge provenance measured: nodes are dynamic, edges are static, cross-record edges don't exist
Status: CONFIRMED

Question asked: *"we only have cross-overlay code from the dynamic data, right?
the rest is static."* Measured instead of assumed — **the premise was wrong in
both directions.**

**Corpus:** 1,239 functions = 1,029 resident + **210 overlay** (`ea >= 0x2CF60`).
All 210 map to a resolvable RTLink record via `overlay_placement.json`.

**Static refs (3,454 total, `export_callrefs.py` → IDA `CodeRefsFrom`):**

| pair | resolved | unresolved |
|---|---|---|
| resident → resident | 3,283 | 110 |
| resident → **overlay** | **8** | 19 |
| overlay → overlay | **28** | 6 |

**Dynamic `indirect_far` (379,498 events):** resident→resident **234,280**
resolved, overlay→overlay **6**, **145,212 unresolved (38%)**.

**Overlay functions reached as a call *target*: static 28 / 210, dynamic
2 / 210.**

**1. Strict cross-overlay — record → a *different* record — is 0 from both
sources.** All 28 static overlay→overlay edges sit **within a single RTLink
record**; distinct record pairs = **0**. So cross-overlay code is not
"dynamic-only", it is *absent entirely*.

**2. Static reaches ~14× more overlay functions than dynamic (28 vs 2).**
Dynamic overlay resolution runs through `callgraph_bottomup.py` `to_ida()`,
which needs `rtlink_loads.json` **and** `overlay_placement.json` — those hold
only **45 records / 70 placements / 16 distinct overlay segments**. Any runtime
`CS` outside those 16 falls through to `None`, which is where 145,212 events
go.

**3. What the dynamic data actually contributed is the *nodes*, not the
edges.** The 210 overlay functions exist because of trace-driven repair
(finding 33, +135 fns) and the overlay registration work. Once registered,
IDA's `CodeRefsFrom` emits the edges, and the thunk-table patch (finding 35,
299/303) is what lets resident→overlay far calls resolve statically at all.
Dynamic's other real contribution stays `dyn_target_calls`, the frequency
ranking that has ordered every batch since Level 0.

**Accurate statement to carry forward:** *overlay nodes are dynamic-derived;
overlay edges are mostly static; cross-record overlay edges do not exist in
either channel.*

**Two concrete gaps if cross-record edges are wanted:**
- the **19 unresolved resident→overlay** refs — thunk targets landing inside
  overlay territory but inside no registered function (register them);
- the runtime **CS → record map covers only 16 segments**, so most dynamic
  overlay events vanish in `to_ida()` (widen `rtlink_loads`/placement
  coverage).

Impact: provenance settled with numbers rather than a plausible story. The gap
that matters (cross-record) turns out to be **zero, not partial**, so it belongs
as an explicit work item rather than something anyone assumes is already
covered — and "overlay edges" was self-consistent in earlier notes only because
it never said *which* source supplied them.

---

## 2026-10-17 52 — **All overlay segments are decoded as 32-bit** — the root cause behind every overlay oddity
Status: CONFIRMED (blocker)

Pursuing "fix overlay edge visibility" turned up something that invalidates
most of what we think we know about the overlay layer.

**Every `R*` segment has `bitness = 1` (32-bit); every loader-created resident
segment has `bitness = 0` (16-bit).** Falcon 3 is a real-mode program whose
overlays are far-called from 16-bit code — they cannot execute 32-bit.

**Empirically (not inferred from a field):**

| address | segment | bitness | IDA renders |
|---|---|---|---|
| `0x10BE2` | `seg002` | 0 | `mov sp, cs:byte_10842+4` / `pushf` / `call far ptr sub_2BE3D` ✅ |
| `0x6D0C9` | `R06_5CD9` | 1 | `call far ptr 0C033h:2F64B4E9h`, `stosd`, `[esi]` ❌ |
| `0x15AD22` | `R33_569Fs` | 1 | `push eax`, `push dword ptr` ❌ |
| `0x103087` | `R07_5CD9s` | 1 | `mov ebx 579A000Ch` / `add eax 0DA8E1084h` ❌ |

**The bytes are fine — only the bitness is wrong.** `0x103087` holds
`1E 06 BB 0C 00 9A …`, which in 16-bit is
`push ds / push es / mov bx,000Ch / call far …`; and a sampled `entry_ea`
holds `55 8B EC 06 56 57 8B 46 06 8B 5E 08 8B 4E 0A C4 7E 0C` =
`push bp / mov bp,sp / push es / push si / push di / mov ax,[bp+6] /
mov bx,[bp+8] / mov cx,[bp+0Ah] / les di,[bp+0Ch]` — a textbook 16-bit C
function. IDA is being fed correct code with the wrong word size.

**Root cause:** `tools/rebuild_overlay_segments.py:61` creates every overlay
segment with `ida_segment.add_segm(ea >> 4, ea, ea + ln, name, "CODE", 0)`
and **never sets `bitness`**. Loader-created segments get 16-bit from the MZ
header; runtime-created ones default to 32-bit. A one-line omission.

**What this invalidates:**
- All overlay disassembly, and therefore every `r*_e*` function's **size and
  end address** (they were derived by terminator-probing a 32-bit decode).
- The overlay coverage figures from this session (R05 13%, R14 5%, R19/R69
  0%) — largely decode artifacts, not "undisassembled code".
- The `ovl→ovl` edges in finding 51 (28 static / 6 dynamic) — computed from
  32-bit-decoded jumps.
- The residual 24 `DATA`-class functions that carry overlay oddities
  (`fcmovne`, `ud0`, `jecxz` last-instructions).
- **Finding 50's rejection of `r30_e77` as a "garbled data region"** — its
  garble was 32-bit decoding. (Not splitting it may still be right, but the
  stated *reason* was wrong.)
- **The 18-candidate registration dry run I was about to execute** — it
  probed terminators through a 32-bit decode, so every end address in that
  list was garbage. Caught before mutation.

**Also corrected:** `overlay_entries.json`'s `target_linear` is **not** a
second copy of `entry_ea`. Sampling 232 pairs: only 7 bytes match, and the low
`target_linear` addresses hold RTLink directory content (`MP DISP.DAT`,
`FALCON3`) or `FF` padding — while the high `s` segments hold file-derived
code written by `put_bytes`. So **`entry_ea` is the registration address** and
`target_linear` is a runtime location the IDB does not map as code.

**Fix path (not yet executed — high consequence):**
1. set `bitness = 0` on all `R*` segments;
2. redefine items in them (`del_items` + re-analysis) so instructions re-decode
   as 16-bit;
3. re-derive the ~210 overlay functions' ranges (current ends are 32-bit
   artifacts);
4. re-run Step 6/7/8;
5. expect `verify_rebuild` to report a large `CHANGED` set for overlay
   functions — that needs an explicit allowlist decision, exactly like `SPLIT`
   did in finding 42. Without it the gate will (correctly) fail.

Impact: **this is the single highest-leverage defect found in the whole
cleanup.** It explains, with one cause, why the overlay layer scored 0–56%
coverage, why 204/210 overlay functions look orphaned, why a dozen entries
carried impossible last-instructions, and why a signal as good as
`overlay_entries.json` still produced a candidate list of garbage. The
overlay layer cannot be trusted — and no overlay function can be registered or
split — until bitness is fixed.

---

## 2026-10-17 53 — Bitness fixed: 68 overlay segments → 16-bit; the gate needed a narrow allowlist, not a bypass
Status: CONFIRMED

Executed the finding-52 fix. All four gates green.

**What ran (two guarded passes + source patch):**
1. **`tools/rebuild_overlay_segments.py` patched** so any future rebuild pins
   `bitness = 0` immediately after `add_segm` — the one-line root cause.
2. **`tools/fix_overlay_bitness.py`** — recorded all 210 overlay functions
   (start/end/name), set `bitness = 0` on **68 `R*` segments**, cleared
   **1,053,376 bytes** of 32-bit items, re-decoded each start as 16-bit and
   re-probed ends: **115 ends kept** (already valid under 16-bit — zero churn),
   **53 re-probed** as 32-bit artifacts, **42 flagged** (no terminator; kept
   old end). Guard passed → saved.
3. **`tools/fix_overlay_bodies.py`** — pass 1 cleared whole segments but only
   re-created each function's *first* instruction, so every body read `??`.
   This walked all ranges: **77,315 of 77,654 bytes decoded**.

**Gate lesson (rule 1, now observed directly):** pass 2's guard *failed* on
464 positions (0.6%) and printed **`NOT SAVED`** — yet the very next IDA run
found the decode present. **`idat` persisted a dirty DB despite an explicit
refusal to save.** The "don't save" control is advisory, not preventive; only
a host-side backup actually protects. Those 464 sit inside two functions: the
`0x2CF6A` range (whose bytes are RTLink directory text — `"MP\0DISPLAY.DAT"`,
i.e. **a junk function registered on data**) and the known 51 KB `sub_2E2F0`
blob.

**Effect on ground truth: 82 spans changed — and the audit is clean:**

| | |
|---|---|
| overlay, `ea` unchanged (the intended recode) | **82** |
| resident functions changed | **0** |
| `ea` moved | **0** |
| hit the 4000-byte probe cap | **0** |
| grew / shrank | 76 / 6 (median size ×2.34; 11 grew >20× — review) |

**The gate needed a narrow allowlist, not a bypass.** `verify_rebuild` correctly
failed with `CHANGED 82 → do NOT commit`. Rather than relax it, added
**`registry/bitness_fix_expected.json`**: each entry is keyed by
`(key, ea, old_size, new_size)`. `verify_rebuild` now classifies an exact
manifest match as `RECODE` (intentional) and still fails on any change that is
*not* in the manifest — so this bulk re-derivation cannot become precedent for
silent drift. Result: **`RECODE 82, CHANGED 0, LOST 0 → faithful`.**

**Measured effect:**

| metric | before | after |
|---|---|---|
| static edges | 1,503 | **1,762** (+259) |
| graph nodes | 913 | **1,007** |
| endpoints | 328 | 346 |
| overlay coverage `R05_1E10` | 13% (40 heads) | **100% (17,655)** |
| overlay coverage `R01_1CF6` | 36% | **92%** |
| overlay coverage `R14_5E0B` | 5% | **100%** |
| overlay zero-indegree | **204/210 (97%)** | **189/210 (90%)** |
| `DATA` class | 24 | 45 |

**The honest headline:** correctness improved a lot, *connectivity* barely did
— orphans fell only 15 (97% → 90%). **Bitness was blocking correct
analysis of overlay code, but it was not the main source of missing overlay
edges.** The remaining 189 need the edge side: registering entry points (the
133 `overlay_entries` with no function, minus the ~113 that fail a
prologue/terminator test) and the bridge-stub → `entry_ea` remap from finding
51. The `DATA 24 → 45` rise is the 42 flagged no-terminator functions landing
where they belong rather than being silently labelled ASM.

Gates: `verify_idb` **INTACT** (1,239, 0 span/name mismatches) ·
`verify_rebuild` **faithful** (RECODE 82, CHANGED 0, LOST 0) ·
`naming.py check` OK (267) · read-back **265/265**.

Impact: **the overlay layer is now decoded correctly for the first time** —
1,053,376 bytes of instruction data that had been misread as 32-bit since
`rebuild_overlay_segments.py` first ran. Everything downstream that was
garbled by it (sizes, coverage, last-instruction classification, finding 51's
edge counts, finding 50's `r30_e77` reasoning) is now measured on real
disassembly. And the fix did *not* buy us a weaker gate: the allowlist is
exact-match, so the next divergent rebuild still fails.

---

## 2026-10-17 55 — Where the 1,257 unresolved refs actually go, and the two
things that keep Resident from reaching Thunk from Overlay
Status: CONFIRMED

Finding 54 left `edge_counts.static_unresolved = 1257` as "the real backlog".
This session classified it instead of guessing. New tool:
`tools/unresolved_dsts55.py` (re-runnable, host side only).

### The bucket: 1,257 refs, 445 distinct destinations

Every one has a registered SOURCE and an unregistered DESTINATION. By src
region (R* = overlay, Res = resident): **1,130 from R\*, 127 from Res**.

| dst category | refs | % |
|---|---|---|
| inside an R* overlay segment, but no function registered there | **611** | 49% |
| inside the resident image, but no function registered there | **442** | 35% |
| inside the .RTLink thunk table (`0x2BD9D..0x2C973`) | **204** | 16% |
| below the image (`<0x10000`) / other | 0 | 0% |

**So the "missing overlay edges" are not mostly cross-segment mysteries: 49%
are simply overlay bytes with no function registered on them, and another 35%
are resident bytes with no function on them.** The thunk table -- the bridge
itself -- accounts for 16%.

The fourth category asked for -- *dst at a low `target_linear` while the
function is registered at the high `entry_ea` of the `R*_s` synthetic copy* --
is measured at **4 refs total** (2 resolve after remapping `target_linear ->
entry_ea`, 2 still do not), plus **1** dst outside every known range. That is
0.4% of the 1,257, which independently corroborates finding 54: the
`target_linear -> entry_ea` remap was never going to move the needle.

### The shift hypothesis, with a control

For each of the 445 distinct dsts, test every candidate paragraph delta
(`+/-0x1000`, `+/-0x10000`, `+/-0xE0B0`, `+/-0xE5E0`, `+/-0xE0B`, `+/-0xE5E`)
and record the first delta whose result lands EXACTLY on a registered function
start. Then repeat with a random base (seeded, same spread) as the control:

| delta | real | CONTROL |
|---|---|---|
| **+0x10000** | **45** | **0** |
| all other deltas combined | 6 | 2 |

**`+0x10000` (= +0x1000 paragraphs, the image load paragraph) is signal; every
other delta is noise.** At ref level, 441 of the 1,257 resolve at `+0x10000`
(234 of them exact-at-start).

Cross-checked from IDA instead of from bytes: `tools/farops_export55.py`
exports all **3,478** direct `9A`/`EA` far operands inside registered
functions; `tools/_join55.py` classifies them:

| | n |
|---|---|
| destination already resolves | 2,327 (67%) |
| destination dead, and `+0x10000` does **not** fix it | 683 |
| destination dead, `+0x10000` fixes it -- **but rel is not in the record's fixup table at all** | **408** |
| destination dead, `+0x10000` fixes it -- rel listed but **dropped by the `seg != w0` filter** | **36** |
| destination dead, `+0x10000` fixes it -- listed AND kept, still not applied | 2 |
| inside a function but outside every overlay record | 22 |

**446 of 1,151 dead far-destinations are recoverable by adding the load
paragraph, and 408 of those are simply absent from the fixup tables we apply.**
433 of the 446 live in one record, `R05_1E10`. Root cause of the absence is
**not yet pinned** (see Flags).

### The concrete thunk at `0x2BD9D` (the question asked)

Bytes: `e8 1d f2 | ea 12 00 37 2d | 01 00`. Two instructions:

```
0x2BD9D  call near ptr sub_2AFBD      CodeRefsFrom -> 0x2AFBD   fn=sub_2AFBD  OK
0x2BDA0  jmp  far ptr 2D37:0012       CodeRefsFrom -> 0x2D382   fn=None      <-- NO FUNCTION
```

So the JMP FAR is **`EA 12 00 37 2D` = seg:off `2D37:0012`**, IDA linear
**`0x2D382`**, and **IDA does NOT resolve it to a registered `r*_e*` function**
-- `0x2D382` is inside `R01_1CF6` but has no function on it.

And the `entry_ea` we *do* have for row 1 -- `overlay_entries.json` row 1,
`entry_ea = 0x2D31A = r01_e01` -- **belongs to a different thunk slot.**

### Found while checking that: `prep_overlay_entries.py` starts 53 entries late

```
file 0x1E99D .. 0x1F573   303 E8/EA entries   <- IDA 0x2BD9D .. 0x2C973  (patch_thunks #000..#302)
file 0x1EBAF              = 0x1E99D + 53*10   = IDA 0x2BFAF = patch_thunks "Thunk #053"
```

`prep_overlay_entries.py`, `parse_thunks.py`, `solve_thunk_assignment.py` and
`validate_record_bases.py` all hard-code `THUNK = 0x1EBAF` -- i.e. **530 bytes
= 53 thunk slots into a 303-entry table.** Verified independently:
`patch_thunks.log` labels `0x2BFAF` as `#053`, and `0x2BFAF - 0x1EBAF = 0xD400`
which is exactly `0x10000 - hdrparas*16` (`hdr = 0x2C00`, from `MZ[8:10] = 704`).

Consequences, measured (`tools/_close55.py`):

| | |
|---|---|
| table slots | **303** |
| slots with an `overlay_entries.json` row | **248** |
| slots **MISSING** | **55** -- indices `0..52` (the offset) plus `95`, `99` |
| of those 53 offset slots, JMP target has NO registered function | **46** |
| missing slots whose target sits inside a placed record (registerable) | 43 (35 with no fn) |

**53 thunk slots were never offered as registration candidates in finding 54,
and 46 of their targets have no function.** Slot `#000` is the concrete case
above: correct address `0x2D382`, never registered, because its entry row was
never computed.

### The second break: `export_callrefs` never walks most of the table

`tools/export_callrefs.py` iterates `idautils.Functions()` and then `Heads()`
inside each. A thunk slot that is **not** a registered function therefore never
yields a ref -- so the JMP FAR half of `Resident -> Thunk -> Overlay` is never
emitted at all:

| | |
|---|---|
| thunk slots registered as functions | **49 / 303** |
| slots whose JMP FAR (`slot+3`) produced a ref | **27** |
| ... of those, JMP target registered | 8 |
| ... of those, JMP target **NOT** registered | **19** |
| **slots never traversed at all** | **276** |
| refs INTO the thunk table | 228 (24 resolve, **204 do not**) |

**The bridge is severed twice over**: 276/303 slots are invisible to the ref
exporter, and of the 27 that are visible, 19 jump to unregistered targets.

### Flags (not conclusions)

- **`R05_1E10` fixup offsets do not line up with its own payload at delta 0.**
  398/412 of its fixable-but-unlisted operand rels become listed after a
  constant **+5440-byte** shift (vs ~29 expected by chance; next-best delta
  scores 59). But the declared table run (`w5 = 3529`, all segs in-arena) and
  the payload base both check out independently -- `file[data_file+0x1F0]` is
  `57 56 1e`, exactly `sub_2E2F0`'s head. So the discrepancy is **unexplained**;
  do not "fix" the base off this number alone.
- `validate_fixup_semantics.py` drops pairs with `seg != w0`: **12,118 of
  37,661** across all records, **2,319** of which point at a link-time
  paragraph. For far operands alone the cost is only 36, so this is a real but
  secondary loss.
- `-0x10000` also resolves 431 refs, but **0** land exactly on a function start
  (control 0) -- treat as mid-function coincidence until proven otherwise.

Tools kept: `unresolved_dsts55.py`, `bridge55.py`, `farops_export55.py`,
`_join55.py`, `_close55.py`. Evidence: `bridge55.log`, `farops_export55.log`,
`callgraph_refs` (all regenerable).

Impact: **the 1,257 are now explained -- and 84% of them are ordinary
"no function registered here", not addressing bugs.** The bridge has two
independent, mechanical defects: (1) `overlay_entries.json` is computed from
`0x1EBAF` instead of `0x1E99D`, silently skipping 53 thunk slots, and (2)
`export_callrefs` only sees thunk slots that happen to be registered
functions (49/303), so 276 JMP FARs are never exported. Both are cheap to fix
and both are prerequisites before any further registration pass -- fixing only
one still leaves the resident graph unable to reach the overlay graph.

---

## 2026-10-17 56 — The bridge is built: 8 → 213 Resident→Overlay edges, and the `+0x1540` fixup anchor explained
Status: CONFIRMED

Four steps, all gates green throughout.

### Step 1 — thunk-table base `0x1EBAF` → `0x1E99D`

Four tools started **53 entries into** the 303-entry table (`0x1EBAF =
0x1E99D + 53*10`, which is IDA `0x2BFAF` — `patch_thunks.log` itself calls that
"Thunk #053"). Fixed in `prep_overlay_entries.py`, `parse_thunks.py`,
`solve_thunk_assignment.py`, `validate_record_bases.py`.

`overlay_entries.json` went **248 → 301 rows covering all 303 slots** (2 slots
share a target). The 3 whose own row does not reach them now carry
**`covered_seg`** — which record's *written* window contains the EA — instead of
being silently dropped: `#095`/`#099` land in `R17_5E8F`/`R19_5F6C`, `#013`
(`0x6FD06`) is covered by nobody. `register_overlay_entries.py` now gates on
`covered_seg` rather than trusting the list to be pre-filtered.

### Step 2 — make all 303 slots first-class functions

`export_callrefs.py` walks heads *inside functions only*, so 254 slots emitted
nothing at all. `register_thunk_slots.py`:

| | |
|---|---|
| free slots registered | **254 @ 8B** (E8 + EA; rec-id word is data, matching the 26 already correct) |
| `sub_2BFCD` / `overlay_tail_bridge_b` | 210B → **21 × 10B** |
| `sub_2BE83` | 20B → **2 × 10B** |
| slot #053 (`0x2BFAF`) | owned by a foreign chunk of `start` — `start` really does transfer control there, so `remove_func_tail` was used and the **xref was kept** |
| **slot #302 (`0x2C969`)** | **impossible**: it straddles the loader-created boundary `seg021 0x2AA30..0x2C970` \| `seg022 0x2C970..0x2CF60`, and `add_func` refuses a cross-segment range (the same constraint finding 37 recorded). It has **zero refs in or out**, so it costs no edge. **302/303 accepted.** |

The split pieces are **10B only** because `verify_rebuild`'s `SPLIT` class
requires the old range to *tile exactly* — 8B pieces leave 2B holes and would
have been reported as `CHANGED`. Result: `SPLIT 2 (21 fns / 210B, 2 fns / 20B),
ADDED 274, CHANGED 0, LOST 0`.

**A decode bug hid the whole point.** The registration loop advanced with
`next_head(slot, slot+8)`; after the 3-byte `call` there is no head yet, so it
jumped to the limit and never created the 5-byte `jmp far` at `slot+3`. That
left `last_insns` recording `call`, and (what matters) `export_callrefs` seeing
no `jmp` mnemonic — so the `slot → overlay` half would still not be exported.
`decode_thunk_jmps.py` re-walks **by instruction size**: 276 instructions
created, `last_mnem = jmp` went **58 → 334**, all 302 slots decode `call..jmp`.

`export_epilogues.py` was reading `classification.json` (the *derived* file), so
any function added after the last classify pass got no epilogue facts and fell
through to the byte-only heuristic that labels tail-jumpers `DATA` (finding 49).
It now iterates `function_bytes.json`.

Ledger corrected: `overlay_tail_bridge_b` claimed *"8B of code in a 210B range —
the rest is resident-tail data/directory"*. **The bytes say all 210B are 21
consecutive 10B thunks** (21/21 `E8`+`EA`+rec-id); the old note was read off
IDA's partial decode. `notes` rewritten, `class: DATA → ASM`, `updated:
2026-10-17`.

### Step 3 — register the exposed targets (guarded, exhaustive)

`register_bridge_targets.py` — 624 candidates (514 unresolved destinations +
130 thunk JMP targets + 125 overlay entries), **617 on written bytes, 7 in no
segment at all** (`0x2D50D`, `0x2D650`, `0x2DFD6`, `0x2D63A`, `0x6FD06`,
`0x2E048`, `0x2DC61`). Rejections on the final pass: **no 16-bit prologue 274
(65%)**, no reachable terminator 106, already covered 27, decode failed 8, too
small 7. **120 registered; the final run found 0 candidates left** — the guarded
criteria are now exhausted, not merely interrupted.

### Step 4 — the `+0x1540` sub-segment hypothesis: **CONFIRMED, and the reason found**

Your arithmetic reproduces exactly: the fixup pair's `seg` field names a
**paragraph anchor inside the record's arena**, so

    absolute offset = (seg - w0) * 16 + off

For `R05_1E10` the dominant anchor is `seg = 0x1F64 = w0 + 0x154` → **`+0x1540`
bytes → IDA `0x2F640`** — precisely `0x2106 − 0x1FB2 = 0x0154 paras`. Measured:

| anchor (seg) | entries | `base = off` word-ok | `base = anchor` word-ok |
|---|---|---|---|
| `0x1F64` (=w0+0x154) | 1442 | 819 | **1442 (100%)** |
| `0x400C` (=w0+0x21FC) | 571 | 320 | **571 (100%)** |
| `0x33AE` (=w0+0x159E) | 394 | 237 | **394 (100%)** |
| `0x2B83` (=w0+0xD73) | 387 | 236 | **387 (100%)** |
| all non-zero anchors | 12,118 | 2,042 | **3,488** |

Far-call cross-check agrees: `(seg−w0)*16 + off` lands on a FAR segment word
for **10,094** pairs vs **5,926** for plain `off` — and for `R05_1E10`,
125 → **2,463 of 2,798 (88%)** where chance is ~43.

**Header or split?** Both — but not as a fixup base offset:

* **No IDA segment split**: `R05_1E10 0x2E100..0x669F0` is one segment; no
  function boundary or comment at `0x2F640` (it sits mid-`sub_2E2F0`).
* **A real record does begin exactly at the anchor**: file `0x276C0` =
  IDA `0x2F640` holds a **name table** — `0600 1100 1b00` (three u16 offsets,
  all pointing inside) followed by `global.amo\0local.amo\0harpoon.dat\0`.
* **And it is a split, not a single header**: `R05_1E10` carries **24 distinct
  paragraph anchors** (top 6 shown above) — the record is addressed as multiple
  paragraph-anchored sub-blocks, the largest being `w0+0x154`.
* The name table is *not* collided with: the dominant anchor's `off` values start
  at **`0xA7`**, i.e. the first fixup lands **167 bytes past** the ~64B table, and
  **0 of 1,442** fall inside it.

**Not applied.** Correcting `validate_fixup_semantics.py`/`apply_overlay_fixups`
to the anchor formula would add the **12,118** currently-filtered fixups →
overlay bytes change → `verify_rebuild` reports mass `CHANGED` → needs an
exact-match manifest in the finding-53 style plus its own backup/gate cycle.
That is a separate, high-consequence mutation; the bytes are now verified, the
edit is deliberately left for a dedicated pass.

### Measured effect (rev `73c4e03` → now, same script both sides)

| metric | before (f55) | after (f56) |
|---|---|---|
| functions | 1,284 | **1,678** |
| static edges | 1,764 | **2,493** |
| `static_unresolved` | 1,257 | **702** |
| overlay functions | 255 | **359** |
| **Resident→Overlay edges** | **8** | **213** |
| **overlay fns reachable from resident** | **5** | **73** |
| refs INTO the thunk table | 228 (204 unresolved) | 230 (**0 unresolved**) |
| slots emitting their JMP FAR | 27/303 | **296/303** |
| overlay zero-indegree orphans | 232 | 228 |

**The honest headline:** the Resident → Thunk → Overlay path now exists
(**8 → 213 edges, 5 → 73 overlay functions reachable**), and the thunk table is
fully resolved (**0 of 230**). But **overlay orphans only fell 232 → 228**:
the 104 newly registered overlay functions connect (they are ref
*destinations*), while the pre-existing orphans are functions nothing calls —
so registering *their* targets cannot rescue them. And **346 distinct
destinations remain unregistered although none passes the prologue/terminator
guards**, i.e. the residual `static_unresolved = 702` is no longer a
registration problem but a *diagnosis* problem: those addresses are not function
entries by any 16-bit test we trust.

Gates: `naming.py check` OK (267) · `verify_rebuild` **ADDED 120 / SPLIT 2 /
CHANGED 0 / LOST 0 → faithful** · `verify_idb` **INTACT (1,678, 0 span / 0 name
mismatch)** · name read-back **265/265 + 2/2**. Backup:
`FALCONCD.EXE.i64.bak_thunk303`, `.bak_targets`.

Impact: **the bridge that finding 54/55 showed to be missing is now built and
measured** — and the two causes were both mechanical, both invisible to a
percentage: a table read 53 entries late, and a function-boundary walk that
stopped one instruction short of the jump. The `+0x1540` mystery is resolved as
a paragraph-anchor addressing scheme (24 sub-blocks in `R05_1E10`), not a
relocation bug — and the fixup correction it implies is staged but deliberately
not executed.

---

## 2026-10-17 57 — The sub-block fixups are applied: 11,475 words corrected,
919 more call sites now hit a real function entry — and `static_unresolved`
rose because the targets finally tell the truth

Finding 56 verified `abs = (seg-w0)*16 + off` and deliberately did **not**
apply it ("12,118 fixups -> mass CHANGED -> needs a manifest"). This session
applied it with that manifest, and measured what actually moved.

### Step 1 — size the pass, freeze pass 1

`tools/_size57.py` over 38,001 candidate pairs, dropping the arena misses
(452), the pass-1 window repeat (681 — exactly pass 1's 321 failures: 177
mismatch + 144 out-of-bounds), non-paragraph offsets (5,458) and file-OOB
(0) leaves **31,410 word-ok**, of which **19,935 pass 1 had already applied**
and **11,475 are NEW**. 9,727 of the NEW sit outside any function; the rest
touch 59 functions. Pass 1's applied set was frozen to
`registry/fixups_pass1_applied.json` (25,543 entries / 67 rows) so
`validate_fixup_semantics.py` stays idempotent, and `fixups_to_apply.json`
regenerated twice to an identical hash: **36,697 entries over 68 records**
(25,222 reproduced + 11,475 NEW).

### Step 2 — the writer had to be made honest, and its first run was refused

`tools/apply_overlay_fixups.py` was rewritten: a **per-entry word guard**
(`applied` when the word still equals the recorded link value, `already_done`
when it already equals `+0x1000`, `mismatch` = never written) replaced the
blanket per-segment `RTFIX` skip, which would have blocked every record pass 1
had already touched. **Run 1 applied all 11,475 with 0 mismatches — and then
failed its own guard:** `sub_4DA46` grew `0x4DA46..0x4DA87` → `..0x4DA88`,
because re-decoding a byte IDA held as *data* let `create_insn` invent an
instruction and push the function end by one byte. NOT SAVED, IDB restored
from `.bak_f57_fixups`. **Run 2 re-decodes only heads that already had a
mnemonic** (5,359 pre-existing heads, 1,622 re-created) → **GUARD PASSED:
11,475 applied, 25,222 already present, 0 mismatch, 306 function spans
unchanged → SAVED.**

### Step 3 — exact-match manifest so the gate stays strict

`tools/make_subblock_manifest.py` → `registry/subblock_fixups_expected.json`
pins all 59 changed functions by `(key, ea, size)` **plus the sha256 of the
bytes before AND after**. Its first run refused `sub_3FD82`, which turned out
to be real: a fixup at `0x3FD81` writes a 2-byte word that *straddles* into
the function starting at `0x3FD82`, so attribution has to be by word overlap,
not owner-by-address. `verify_rebuild.py` gained a **PATCH** class — both
hashes must match exactly, so a rebuild that patches the wrong word still
fails as CHANGED. Result: **PATCH 59 / CHANGED 0 / LOST 0 / ADDED 0 →
faithful**.

### Measured effect

| metric | f56 | f57 |
|---|---|---|
| functions | 1,678 | 1,678 (0 lost, 0 added, 0 span change) |
| static edges | 2,493 | **2,730** |
| `static_unresolved` | 702 | **957** |
| overlay zero-indegree orphans | 228 | **224** |

Retargeted/new sites (`tools/measure_f57.py`): 1,369 sites moved, 103 new, 0
gone. **Exact function-entry hits 71 → 990** (resident 38 → 923, overlay 33
→ 67) — 72% of retargeted destinations now land on a registered entry instead
of somewhere inside one. Destinations that are data (outside every function):
**199 → 449**. Those 449 refs collapse to **233 distinct addresses**
(hottest: `0x28CAB` ×36, `0x15CCB` ×27, both resident). Functions with zero
indegree at HEAD: **719 → 138 now reached** (134 resident, 4 overlay);
pre-existing overlay orphans hit 7 times → **4 actually rescued** (the other 3
were self-edges, which the graph drops) → 228 → 224, 0 newly orphaned.

**Inside `sub_2E2F0` (0x2E2F0..0x3ACAC):** refs **985 → 1,053**, every one of
them **interior — 0 at a function start, 0 at `0x2F640`** — spread across
**13 distinct 4 KB blocks, i.e. 13 of that function's sub-block anchors**
(42..135 refs each), with 205 of them retargeted by this pass.

**Why `static_unresolved` rose 702 → 957: arithmetic, not a regression.**
Refs are only emitted from heads inside functions (0 sources ever fail to
resolve), so the count *is* "destination outside every function". The delta is
exact: 702 + 250 (retargeted dsts that moved onto data) + 5 (new sites) =
957; the remaining 503 are untouched pre-existing data destinations. Those
449 dsts used to be **interior** hits — resolved by luck, at the wrong address
— and now point at the true link-time targets, which for 449 sites are tables
and data with no registered function. The words themselves are certain: 0
mismatches in 36,697 guarded writes, and exact-entry hits 5% → 72%.

Gates: `naming.py check` OK (267) · `verify_rebuild` **PATCH 59 / CHANGED 0 /
LOST 0 → faithful** · `verify_idb` **INTACT (1,678, 0 span / 0 name
mismatch)** · read-back **265/265 + 2/2**. Classification unchanged
(ASM 1,370 / C 130 / LEAF 121 / DATA 46 / NEARTHUNK 11). Backup:
`FALCONCD.EXE.i64.bak_f57_fixups`.

Impact: the correction finding 56 staged is now **applied and allowlisted**,
and it bought ~919 provable call-to-entry edges — but it also *increased* the
unresolved backlog, because honest targets include tables. Two structural
items follow: register/classify the 233 data destinations (the residual is now
503 untouched + 449 new data dsts), and split `sub_2E2F0` along its 13 anchor
lines, since 1,053 call sites currently resolve into one 46 KB span.

---

## 2026-10-18 58 — The unresolved destinations audited: 78% are frameless
code, zero are pointer variables — and `sub_2E2F0`'s carve map, with the
correction finding 57's anchor heuristic needed

Read-only inspection (no IDB mutation) of everything finding 57 left
unresolved, plus the boundary map required before any split.

### Step 1 — the worklist is 515 destinations, not 233

Finding 57's "449 refs -> 233 addresses" was only the *retargeted* subset.
Counting properly (`tools/dst_list.py`): **957 unresolved refs -> 515 distinct
destinations**, 87 resident / 428 overlay, of which **251 (446 refs) sit in
`R05_1E10`'s upper half `0x3ACAC..0x669F0`** — the region where most of the
"outside-any-function" fixups landed. Only 1 of the 515 lies inside
`sub_2E2F0`'s span... none do: every ref into that blob resolves, which is why
they never appeared in this backlog.

### Step 2 — fresh IDA decode, read-only, and one trap

`tools/audit_dsts.py` decodes each address with `ida_ua.decode_insn` and takes
the mnemonic from **`insn.get_canon_mnem()`** (the `idc` helper returns `""`
for addresses that have no IDB item — i.e. most of them — and
`ida_idp.get_insn_name` does not exist in 9.1), sweeps backwards up to 6 bytes
for an instruction that lands exactly on the target (a terminator there is a
strong entry signal), and records every source's mnemonic, operand type and
operand text. No items created, no `auto_wait`, no save.
**Trap:** a throwaway API probe was written *without* `idaapi.qexit(0)`, so IDA
finished its auto-analysis pass and rewrote the IDB (file +65 KB).
`verify_idb.py` was run immediately: **INTACT — 1,678 functions, 0 span
mismatch, 0 name mismatch**. Every diagnostic now quits explicitly.

### Step 3 — classification of the 515

| class | dsts | refs | verdict |
|---|---|---|---|
| **(a) frameless ASM / unregistered code** | **401** | **750 (78%)** | decodes from the address to `retf` 153 / `jmp` 188 / `retn` 60 |
| **(b) indexed jump-table case targets** | 30 | 36 (4%) | `jmp/call cs:off_X[bx]` (o_displ) — dispatch handlers, also code |
| **(c) anomaly / data / truncated** | 84 | 171 (18%) | 49 first-byte-undecodable, 28 code >512 B without terminator, 7 no segment |

**(a) — yes, the prologue filter is why they were rejected:** only **12/401**
start with `55 8B EC`/`C8`. First mnemonics are `push` 126, `mov` 79, `add` 33,
`cmp` 30, `call` 14, `enter` 7, `pusha` 4. **196/401 carry a strong entry
signal** (previous instruction is a terminator, or the previous function ends
exactly there); 100 start like a mid-body, 105 are weak. IDA holds a name for
371 of them (`unk_` 298, `loc_` 70) but only **70 are code items**.

**(b) the pointer-variable hypothesis is refuted:** **0 of 515** are `FF 1E` /
`FF 2E` pointer words. Every source is an indexed `jmp/call cs:off_X[bx]`, and
the mapping is exact — all 12 destinations of `jmp cs:off_149D2[bx]` @ `0x149CD`
are `table_word + 0x11BA0` (12/12, the paragraph base of that segment), and
29/30 decode to a terminator. They are switch **case handlers**.

**(c) the two hottest are genuinely data and are *not* finding 57's fault:**
`0x6E1EA` x24 sits **inside the ASCII string `"WRONG VERSION!"`**, `0x6DFF0` x23
is a **word table** (`9d 00 aa 00 c0 00…`); both were unresolved before finding
57. Of f57's 233 retargeted addresses: **209 -> (a), 24 -> (c), 0 -> (b)**.

### Step 4 — `sub_2E2F0` map (and a correction to finding 57)

`tools/map_sub2e2f0.py` reads the fixup tables straight out of
`FALCONCD.EXE` (same location logic as `_size57.py`), so the anchors are the
real `(seg-w0)*16` values, not buckets:

- **24 anchors in `R05_1E10` = 1 at the segment base `0x2E100` + 6 inside
  `sub_2E2F0` + 17 in the upper half.** In-blob: `0x2EA10` x58 fixups,
  `0x2EFE0` x18, `0x2F400` x19, `0x2F590` x4, **`0x2F640` x1,442**, `0x3AB90`
  x15. **Correction:** finding 57 reported "13 sub-block anchors" — that was a
  4 KB bucket heuristic; the true count inside the function is **6** (24 in the
  segment matches finding 56 exactly).
- **Refs: 1,053 -> 596 distinct destinations, 0 at a function start**: 696
  `CALL` from inside the blob, 275 `JMP` from inside, 71 `CALL` from other
  functions (**22 distinct addresses**), 10 `JMP` through a thunk slot, 1 `JMP`
  from a function. Today **all 971 internal refs collapse to
  `sub_2E2F0 -> sub_2E2F0` and are dropped by the `s != d` rule** — the graph
  currently has no internal structure at all.
- **Entry seeds for a carve: 371** (343 targets of internal `CALL`s + 22
  external + 10 thunk); the remaining 225 destinations are branch-only labels.
  Two of the thunk seeds (`0x2E380`, `0x2E6C6`) are exactly finding 42's "MID
  targets" that `docs/open_items.md` called unexplained.
- **Data is tiny: 3 holes / 239 B** — `0x2EA10..0x2EA6D` (93 B: `OBJECTS`,
  `FalcObj.Bin`, `FSXObj.Bin`), `0x2F640..0x2F6D0` (144 B: `global.amo`,
  `local.amo`, `harpoon.dat`, `FALCONCOLORADO`; the first code word after it,
  `0x2F6D0`, is a thunk target), `0x3AB90..0x3AB92` (2 B). All 7 NUL-terminated
  strings (72 B) live inside those holes.
- **7 anchor-delimited blocks:** 1,824 / 1,488 / 1,056 / 400 / 176 /
  **46,416** / 284 B — anchors are module-level, so the 46 KB block must be cut
  on the 371 seeds, not on anchors alone.
- **Upper half:** 251 of the 515 unresolved destinations and **1,934 of 3,529**
  R05 fixup pairs live in `0x3ACAC..0x669F0` — that is where registration work
  goes next, and it is a *registration* problem, not a split.

### The gate has to be built before the carve

`verify_rebuild`'s `SPLIT` requires the old range to be tiled 100% by
functions, which would force 239 bytes of tables to become functions. Proposed
`registry/subblock_split_expected.json`, per old key: `{ea, old_size,
old_sha256, data_holes[{ea, size, sha256, why}], new_fns[{key, ea, size}]}`.
Accept a shrunk key **only if** `new_fns ∪ data_holes` tiles the old span with
no gap and no overlap, **every hole's current bytes still hash to its recorded
sha256** (holes may never be edited), and each new function's `(ea, size)`
matches; everything else stays `CHANGED` -> exit 1. Class name: `SPLIT` with
holes, or `SPLITDATA`.

### Carve plan (ordered, boundaries not guessed)

1. Seed at the 371 candidates; accept a start only when it is preceded by a
   terminator or by nothing (finding 33's retf rule, extended for frameless
   bodies by walking back <=6 B); every one of the 596 destinations must end up
   either a function start or interior of a seeded block.
2. `create_data` on the 3 holes after a decode confirms they are not code.
3. Split the 46 KB block at the seeds; unseeded code attaches to the preceding
   block unless a terminator separates it.
4. Payoff to measure: up to **971 internal refs become visible edges** for the
   first time, and the 72 external ones gain precise callees.

Gates: `naming.py check` OK (267) . `verify_rebuild` faithful . `verify_idb`
**INTACT (1,678, 0 span / 0 name mismatch)** . read-back 265/265 + 2/2.
Analysis only — the IDB was not modified by this finding (the one auto-analysis
rewrite was verified byte-identical in span/name terms and is now prevented by
`qexit`).

---

## 2026-10-18 59 — The carve: `sub_2E2F0` becomes 258 functions + 3
sha256-pinned data holes, static edges 2,730 -> 4,013

Finding 58's plan, executed with the gate written FIRST: nothing was mutated
until `registry/subblock_split_expected.json` described exactly what the IDB
must look like afterwards.

### Step 1 -- the plan is a file, not a guess

`tools/carve_seeds.py` (372 seeds = 343 internal CALL targets + 22 external +
10 thunk + the blob start) -> `tools/seed_tests.py` (read-only backward sweep:
which instructions decode to END EXACTLY on each seed, and what the first three
instructions look like) -> `tools/plan_carve.py` writes the manifest: parent
span + sha256, **3 data holes with their own sha256 and why** (93 B object
table, 144 B RTLink name table `global.amo/local.amo/harpoon.dat/
FALCONCOLORADO`, 2 B pad), and every planned child `(key, ea, size)`.
**253 seeds accepted by the terminator-backwards rule + 7 forced** (blob start,
3 hole ends, 3 anchors); coverage validates EXACT: 51,405 B code + 239 B data
= 51,644 B.

### Step 2 -- the gate before the mutation

`verify_rebuild.py` gained a **CARVE** class: a shrunk/retired parent is
intentional only when (a) the manifest's `(key, ea, size)` list matches the
functions currently inside the old span *exactly* (missing or extra = fail),
(b) no function overlaps a hole, (c) the parent really shrank, and (d) every
hole's **live** sha256 -- read from `analysis/ida_falconcd/data_holes.json`,
which `verify_idb.py` now computes from the database and refuses to accept if
a hole is covered by a function or not flagged as data. Dry run before carving:
`INTACT` + `faithful` (and one mis-detection fixed: `carved` was inferred from
"any planned child exists", but child #1 shares the parent's EA, so it read the
pre-carve parent as carved -- now inferred from "parent no longer spans the old
range").

### Step 3 -- the backward rule lied twice, and the plan caught it

`tools/carve_probe.py` found **10 existing instructions crossing planned
boundaries**: 8 are zero padding (the old sweep turned the `00 00...` before a
module boundary into `add`) -> delete that item; **2 are real code**:
`0x32553` sits inside a `9A` call-far at `0x32552`, `0x3A2D8` inside `3D` at
`0x3A2D6`. Those two seeds are backward-decode artefacts -> **dropped (ranges
merged), 260 -> 258 functions**. Rule learned: a terminator that "lands on" an
address in a backward sweep is only a candidate; it must not contradict the
existing decode.

### Step 4 -- three aborts, one save

The mutator refused to save three times, each time leaving the IDB restorable:
(1) `idc.get_byte` does not exist in 9.1 (`ida_bytes.get_byte` does); (2) a
`%d` format was handed the string "ABORTED"; (3) **`create_insn` returned 0 at
`0x2EA6D`, `0x2F6D0`, `0x39AA9`** although a fresh `decode_insn` succeeded --
another item sat *inside* the entry's first instruction, so IDA would not
create it; fixed with a clear-blocking-item-then-retry loop (3 small items
cleared). Every attempt restored `FALCONCD.EXE.i64.bak_carve` and re-verified
**INTACT** before the next run. Final run: **258 functions registered, heads
17,547 -> 17,545, code refs 5,209 -> 5,209 (the blob's edges survived
byte-for-byte), holes byte-identical, SAVED.**

### Measured effect

| metric | before | after |
|---|---|---|
| functions | 1,678 | **1,935** (1,678 - 1 + 258) |
| static edges | 2,730 | **4,013 (+1,283)** |
| refs into the blob forming edges | 82 | **812** |
| ... landing on an exact function start | 0 | **572** |
| total code refs | 9,244 | 9,244 (nothing lost) |
| `static_unresolved` | 957 | 957 (the holes hold no refs) |
| new functions with >=1 incoming edge | - | **256 / 258** |
| overlay zero-indegree orphans | 224 | 226 (the 2 uncalled pieces) |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- CARVE 1,
ADDED 257 (all manifest-planned), LOST 0, CHANGED 0** . `verify_idb`
**INTACT (1,935, 0 span / 0 name / 0 data-hole problems)** . read-back
265/265 + 2/2. Backup `FALCONCD.EXE.i64.bak_carve`.

Impact: finding 58 predicted the 971 internal refs were invisible because
`sub_2E2F0 -> sub_2E2F0` self-edges are dropped -- **730 of the 812 edges now
come from exactly that class**, and 572 refs land on a real entry instead of
inside a 46 KB span. Remaining on this line of work: 112 rejected seeds stay
interior by design, 2 pieces have zero indegree, `0x3ACAC..0x669F0` still
holds 251 unregistered destinations (registration, not carving), and the
runbook must document the `verify_idb` -> `verify_rebuild` ordering the hole
export depends on.

---

## 2026-10-18 60 — Upper half P0+P1: the block inventory, and the dynamic
CS->record gap root-caused (432 -> 28,264 events mapped, variant swap proven)

Records the first two steps of the plan appended to `docs/open_items.md` after
finding 59. No IDB mutation: analysis only.

### P0 -- inventory of 0x3ACAC..0x669F0 (`tools/map_upper.py`)

179,524 B in **18 anchor-delimited blocks**, only **38 functions / 4,304 B
(2.4%)** registered. Evidence is concentrated: `0x3B830..0x43AE0` 33,456 B
(89 dsts / 163 refs, 30 terminator-preceded), `0x43AE0..0x48DB0` 21,200 B
(50/93, 41 strong), `0x4F250..0x4FD20` (21/55), `0x54AF0..0x669F0` 73,472 B
(28/36 but only **1** strong -- and it is the UI/text module: `*** PAUSED ***`,
`SPEED = KNOTS`, `YOUR PLANE HAS BEEN DESTROYED!`). **Three blocks have zero
call evidence**: 1,552 B, 880 B and **18,992 B (`0x500C0..0x54AF0`)**. 263
printable runs -> **68 candidate holes / 6,278 B** (for later sha256 pinning).
8 RTLink `entry_ea`s land here (`0x3ACAC, 0x3ADAA, 0x40E54, 0x4185A, 0x4DAE0,
0x4DF94, 0x4F4A8, 0x4FD8E`). Unlike `0x2F640`, these anchors are **code-led**
-- no name tables -- so holes come from UI strings, not from block heads.
Everything lands in `analysis/ida_falconcd/upper_map.json`.

### P1 -- the missing CS->record map, root-caused

Finding 51 said dynamic `to_ida()` covered only 16 segments and 145,212 events
fell out. Two independent causes, both fixed:

1. **`tools/mine_traces.py` globbed `trace_*_{kind}.jsonl`**, so
   `debug_test_fileio.jsonl` (37 MB -- where most `indirect_far` events live)
   and its fartrans were never mined. Now `*_{kind}.jsonl`; re-mined: **5 runs,
   46 records (was 45), unstable offsets 0**.
2. **The address rule was record-relative and content-decidable**:
   `runtime CS = link-time seg + 0x1F5` (record bases *and* the `0x1F64 ->
   0x2F640` anchor both confirm it), so
   `IDA = record.ida_ea + ((cs - 0x1F5) - w0)*16 + ip`. The tempting global
   identity `IDA = (cs<<4)+ip+0xE0B0` holds for only **9 of 68** placements --
   the `s`-suffix records were re-placed by our rebuild at `0x100000+`, so the
   record-relative form is the general one.

**Variant swap:** `R05_1E10`, `R27_1E10s`, `R28_1E10s`, `R29_1E10s` all declare
`w0 = 0x1E10` -- mutually exclusive copies of one module claiming the same link
paragraphs, loaded according to scenario. Candidates are therefore disambiguated
**by content** (does a ret-like instruction END exactly at the target, checking
`ret imm16` too -- finding 59's boundary evidence reused), with loader
read-evidence as tie-break:

| CS | events | chosen | hits | alternatives |
|---|---|---|---|---|
| `0x3BEC` | 26,622 | **R29** `base 0x138230` | **2/2** | R05 0/2 |
| `0x2159` | 1,210 | **R05** `base 0x2F640` | **17/19** | R29 2/19, R28 0/19 |
| `0x2005` | 272 | **R27** (read-evidence) | 1/2 | R05/R28/R29 0/2 |
| `0x6000` | 142 | **R15** | 15/18 | R11/R12 0/18 (R14 out of range) |
| `0x5894` | 18 | **R31** | 3/3 | 28 records share this pool segment |

Re-mining independently shows **both R05 and R29 loaded at base `0x2005` in
different runs** (`record 5 segments=[0x2005, 0x2fed, ...]`, `record 29
segments=[0x2005, 0x2fb9, ...]`) -- the swap is real, not an inference.

`tools/map_runtime_segments.py` -> `analysis/traces/runtime_seg_map.json`:
**overlay events resolved 432 -> 28,264 (65x)**; unmapped **32,392 -> 4,560**,
whose residue is honest: `0188:0000` (4,469 far jumps below the image, in no
record arena) and `0x77A3` (91 calls into a 751-para heap MCB block).
`callgraph_bottomup` now consults that map first (content-proven, range-guarded
-- it refuses rather than guesses past a proved record) with the old segment
join as fallback: **dynamic_unresolved 122,263 -> 64,067**, dynamic edges
**17 -> 36**, union **4,016 -> 4,034**.

### The negative that matters for the plan

With everything mapped, **zero events (src or dst) land in
`0x3ACAC..0x669F0`**: the traced runs never exercised those modules. P1 buys
the machinery (a proven, reusable runtime->IDA map and finding 51's gap closed
for future traces), not upper-half call evidence -- so the upper half remains
a **static** job: P2's chain sweep, then P3 registration under a manifest.

Gates: `naming.py check` OK (267) . `verify_rebuild` faithful . `verify_idb`
**INTACT (0 span / 0 name / 0 data-hole problems)**. Analysis only -- the IDB
was not touched.

---

## 2026-10-18 61 — P2+P3: the upper-half chain sweep and manifest-backed
registration — 116 new functions, `static_unresolved` 957 -> 772

Executes finding 60's plan steps P2 and P3 on the evidence-rich blocks:
`0x3B830..0x43AE0` (163 refs), `0x43AE0..0x48DB0` (93), the `0x4E520..0x4FD20`
cluster (82) and the `0x54AF0..0x669F0` UI block (36). The three zero-evidence
blocks (1,552 / 880 / **18,992 B**) were left documented-unregistered -- no
chain from an adjacent verified entry reached them.

### Step 1 -- the gate first: `REGISTER` (parentless ranges)

`verify_rebuild.py` gained a **REGISTER** class for ranges that never had a
parent function (a plain ADDED wave would otherwise sail through, as finding
54's 45 entries did). A range validates only if
`new_fns | keep_fns | data_holes` tiles `[lo,hi)` **exactly** (no gap, no
overlap) and every hole's sha256 matches the **live** export that
`verify_idb.py` writes to `data_holes.json`; before anything is applied the
range reports `pending`, so the gate stays green pre-mutation. `verify_idb`
now exports three hole kinds: **3 split + 58 register + 10 standalone = 71**,
and enforces register/standalone holes are function-free always, data-flagged
once their range is registered.

### Step 2 -- P2: forward-chain + preceding-terminator sweep (`sweep_upper.py`)

The sweep walks each gap (range minus keep fns minus holes) with these rules,
each added because a run refused to give the coverage it promised:

1. **an existing IDA decode always wins**; fresh decode only fills undefined
   bytes;
2. **`00` does not decode in this IDB**, so zero runs are skipped only when
   what follows is entry-like (`ENTRY_AFTER_PAD`) -- and only 64 bytes of it;
   leading padding becomes uncovered, padding after a terminator is attributed
   to the previous instruction (so the next boundary still counts as
   terminator-preceded);
3. a **mid-item conflict adopts IDA's item and resyncs to its end** (never
   walks backwards, never contradicts) -- this alone took block i from 12.5 KB
   to 24 KB;
4. a **stale `<=15 B` data item** (a 2-byte `dw` was blocking 19 KB of block
   ii) is stepped over; **`>=16 B` stops** the sweep unless mid-body;
5. **mid-body island bridging**: on an undecodable byte or a real data blob,
   the sweep may jump at most 64 bytes to a position where a chain **re-closes
   on a terminator** within 160 instructions (this is what unblocked block ii
   past the `0F 3C` island and took block iii to 6,143/6,144 B);
6. **seeds** (the 197 in-scope unresolved destinations + RTLink `entry_ea`s)
   become boundaries only on a sweep boundary whose previous instruction is a
   terminator -- finding 59's rule, now exact because the stream is known;
7. **emission evidence**: a piece is registered only with an accepted seed
   inside, an existing IDA code item, a chain closed on an authoritative
   keep/hole/range boundary, or *any* referenced destination inside (an
   interior call still proves code);
8. **stage 2**: self-contained chains seeded at leftover destinations
   (terminator behind + chain closes, <=4 KB) -- 2 of 94 qualified (36 had no
   terminator behind, the rest could not close); **9 suspect holes** (a sweep
   overran into them) were dropped from tiling and the plan re-run 2x.

Result: **22,240 instructions walked, 59,641 B covered**, 77 contiguous
ranges, **116 planned functions** (block i 49 / ii 36 / iii 24 / iv 7), 167
spans left uncovered (74,631 B) with stop reasons recorded.

### Step 3 -- P3: manifest, then mutate

`tools/plan_register.py` -> `registry/upper_register_expected.json`
(77 ranges, 116 new + 24 keep fns, **68 pinned holes / 6,278 B** -- all of
them, including the 10 outside any range, so `YOUR PLANE HAS BEEN
DESTROYED!` and friends are protected). The generator refuses to write on any
tiling gap/overlap, duplicate key, drifted keep function or missing hash.
Then `tools/register_upper.py` (backup `FALCONCD.EXE.i64.bak_upper`):
preconditions checked (pre-state == keep for all 77 ranges, all 68 hashes
match) -> 58 holes converted to data (sha re-verified after conversion) ->
**116 functions registered, 19,289 instructions created** (only where no item
existed) -> guards: spans match plan, ranges still tile, holes byte-identical
and function-free, heads/code-refs never decreased -> **guards PASSED, SAVED**.

### Measured effect

| metric | f60 | f61 |
|---|---|---|
| functions | 1,935 | **2,051** (+116) |
| static edges | 4,013 | **4,907 (+894)** |
| `static_unresolved` | 957 | **772 (-185)** |
| union | 4,034 | 4,928 |
| code refs | 9,244 | 10,917 (**+1,673 revealed**) |
| new fns with >=1 incoming edge | - | **107 / 116** |
| overlay zero-indegree orphans | 226 | 234 (+8 uncalled pieces) |

The drop decomposes exactly: **957 - 291 (in-scope destinations now inside a
function: 153 of 197 dsts) + 106 (refs revealed by the new instructions whose
destination is still outside every function) = 772**. Per block: i 49 fns /
24,675 B, ii 36 / 19,028, iii 24 / 5,908, iv 7 / 1,262 plus 5,263 B of pinned
strings; 44 in-scope dsts (83 refs) remain unresolved inside the stops
(data, undecodable, chains that never close), and 318 dsts / 583 refs are
outside the four scope blocks.

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- REGISTER 18
applied / 59 pending (hole-only ranges), ADDED 116 all manifest-planned, LOST
0, CHANGED 0** . `verify_idb` **INTACT (2,051, 0 span / 0 name / 0 data-hole
problems)** . read-back **265/265 + 2/2**. Backup `FALCONCD.EXE.i64.bak_upper`.

Impact: the upper half went from **38 functions / 2.4% coverage to 154
functions / ~35% of its bytes inside registered ranges** (59,641 B covered +
3,505 B keep), the zero-evidence blocks were deliberately left alone, and the
REGISTER gate now makes any future parentless registration exact-match
instead of a free ADDED wave. Remaining: the 44 in-scope stragglers, the
`0x54AF0` UI block's data-dominated gaps, and 74,631 B of documented
uncovered scope.

---

## 2026-10-18 62 — The R05_1E10 sweep is finished: 82 more functions,
`static_unresolved` 772 -> 660, and the block-iv anomaly diagnosed

Finding 61 left the four evidence-rich blocks registered and the rest of
`R05_1E10` (the lower `0x3ACAC..0x3B830` tail, the `0x48DB0..0x4FD20` run,
the `0x4FD20..0x500C0` tail, and the untouched `0x500C0..0x54AF0`) pending a
recount. This session ran that recount, swept every remaining evidence-bearing
block, registered the result, and diagnosed why the `0x54AF0` UI block yielded
only 7 functions.

### Step 1 -- the post-f61 recount

Re-running `dst_list.py` against the finding-61 refs: **415 destinations /
772 refs** (was 515/957). The **13 other anchor blocks** of `0x3ACAC..0x669F0`
carry **26,260 B / 83 dsts / 130 refs** now (the recount moved some evidence:
the previously zero-evidence `0x48DB0..0x493C0` gained **4 dsts / 10 refs**
from a newly revealed reference, so it enters scope per the standing rule;
`0x4DAD0..0x4DE40` and `0x500C0..0x54AF0` remain at 0 and stay out).

### Step 2 -- sweep + register the remaining evidence-bearing blocks

`register_scope.json` now lists **12 blocks / 26,260 B** (unioned with the
finding-61 four = 16 scope blocks total, 0x3ACAC..0x669F0 minus the two
untouched zero-evidence blocks). The same
`sweep_upper.py -> plan_register.py -> register_upper.py` pass ran, with two
findings:

1. **a gap may start on a small data item.** `blk_4FD20` starts on a 2-byte
   `word_4FD48`; the sweep's small-data skip advanced `cur` but not
   `gap_start`, so the planned function `0x4FD48..0x4FD80` began on a data
   byte and `add_func` refused the whole range. Fixed: when a gap *starts* on
   a `<=15 B` data item, move `gap_start` past it and record it as
   lead-padding (the range split cleanly into `0x4FD20..0x4FD38` keep +
   `0x4FD4A..0x4FD80` new).
2. **suspect holes must not be enforced.** The sweep dropped 10 holes it had
   overrun into (`0x4aca1`, `0x5a33b`, ... `0x5c04d`) from tiling, but they
   stayed in `all_holes` and flowed into `standalone_holes`, where the mutator
   required `sha256 + not in function`. A guard-failed attempt then left a
   dirty DB (idat persists on exit) that covered `0x4ACA1`. Fixed in
   `plan_register.py`: suspects are recorded (`suspect_holes_not_enforced`)
   but never enforced, and `register_upper.py` became **idempotent** (pre-state
   accepts `keep` *or* `keep+new`; already-converted holes and already-added
   functions are skipped), so the re-run after the guard was a no-op that
   passed and saved.

Result: **96 ranges, 82 new functions, 58 in-range holes converted, 8,727
instructions created; guards PASSED, SAVED** (backup `FALCONCD.EXE.i64.bak_upper2`).

### Measured effect

| metric | f61 | f62 |
|---|---|---|
| functions | 2,051 | **2,133** (+82) |
| static edges | 4,907 | **5,289 (+382)** |
| `static_unresolved` | 772 | **660 (-112)** |
| union | 4,928 | 5,310 |
| new fns with >=1 incoming edge | - | **76 / 82** |
| overlay zero-indegree orphans | 234 | 238 |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- REGISTER 19
applied / 77 pending, ADDED 82 all manifest-planned, LOST 0, CHANGED 0** .
`verify_idb` **INTACT (2,133, 0 span / 0 name / 0 data-hole problems)** .
read-back **265/265 + 2/2**.

### Step 3 -- diagnose the remaining 660 unresolved

**Block `iv` (`0x54AF0..0x669F0`, 73,472 B, only 7 fns):** 28 dsts / 36 refs
remain. The forward sweep from the anchor dies at `pad-then-nonentry` /
`undecodable` / `zero-run` ~40 times because between the 7 functions sit
**binary UI/struct tables**, not `00` padding. **Stage-2 (cap raised 4 KB ->
16 KB) rejects all 27 attempts: 26 have no terminator behind them**, and the
one that does (`0x5DF97`, `prev=jmp`) sits inside an already-covered range
whose piece was rejected for no other evidence. Finding-58's audit agrees:
**27 of 28 are class-c anomalies with no terminator behind** — so these are
*not* clean functions separated by tables; the destinations themselves are
mid-instruction / data points, and only a handful of genuine functions exist
in the block (which the 7 registered).

**Residency of the remaining 660 (347 dsts):**

| zone | dsts | refs |
|---|---|---|
| **Resident `0x10000..0x2CF60`** | **93** | **236** |
| **other `R*` overlays** | **254** | **424** |
| — `R05_1E10` (in-scope stops + carved region) | 79 | 109 |
| — `R30_569F` | 71 | - |
| — `R06_5CD9` | 25 | - |
| — `R53_569Fs` / `R14_5E0B` / `R17_5E8F` / `R35_569Fs` | 16/14/12/12 | - |
| carved region `0x2E2F0..0x3ACAC` | 4 | 12 |
| untouched zero block `0x500C0..0x54AF0` | **0** | **0** |

The **in-scope residue is 63 dsts / 109 refs** — all in the sweep's documented
stops (the 40 `pad-then-nonentry` / `undecodable` / `zero-run` in block iv,
plus anomalies like `0x43E0C` ×16 which is class-c undecodable in block ii).
The bulk of the remainder (**93 resident + 254 other-overlay**) is outside
`R05_1E10` entirely: resident needs the same treatment as finding 54's
registration pass, and the `R*` overlays (`R30_569F` 71 dsts, `R06_5CD9` 25,
etc.) are the next registration targets (they are separate RTLink records
already mapped by finding 60's runtime map).

---

## 2026-10-18 63 — Registering the Verified Resident Destinations:
`static_unresolved` 660 -> 564, 24 new functions, and the `0x43E0C`
variant-swap answered

Finding 62 left **93 Resident destinations / 236 refs** (`0x10000..0x2CF60`) as
the largest single bucket of `static_unresolved`. Finding 58 had already
classified them (59 `a_frameless_fn`, 15 `b_ptr_or_indirect` jump-table, 6
`c_anomaly`, 6 unknown). This session ran a guarded registerability pass over
all of them, registered the clean ones under the `REGISTER`/`ADDED` manifest
gate, and answered the read-only `0x43E0C` variant question.

### Step 1 -- audit the 93 (`audit_resident.py` + `decode_resident.py`)

`dst_list` post-f62 gives 86 distinct Resident dsts / 229 refs (the zone
filter found 86, not 93 -- a few of the original 93 resolve after f62). For
each, IDA-side: decode forward to a terminator (`retf`/`retn`/`jmp`/`iret`),
check no overlap with an existing function or named data, and classify
jump-table targets as standalone handler (ends `retn`/`retf`) vs tail (ends
`jmp`):

| category | dsts | refs | action |
|---|---|---|---|
| standalone, clean decode, no overlap | 36 | 124 | **register** |
| already inside an existing function | 27 | 45 | no action |
| forward-decode runs into an existing fn (gap-into-existing) | 18 | 48 | not standalone |
| undecodable (class-c anomaly) | 3 | 4 | rejected |
| jump-table target, ends `retn` (standalone handler) | 1 | 2 | **register** |
| jump-table target, ends `jmp` (case tail) | 1 | 6 | not standalone |

### Step 2 -- alignment correction (the `0x28CAB` lesson)

`add_func sub_28CAB 0x28CAB..0x28D06 -> None` on the first guarded run. The
diagnosis: **`0x28CAB` is mid-instruction** -- `get_item_head(0x28CAB) =
0x28CA8`, a 4-byte `mov` (`decode_insn(0x28CAB)` returns a spurious k=1).
The ref target lands 3 bytes into a real instruction. Finding 58's dst was
correct as a *destination*, but it is not a valid *entry*. `add_func` refuses
mid-instruction starts.

**3 of the 37 candidates are mid-instruction** and were re-aligned to their
real item head (then re-decoded to a terminator):

- `0x28CAB` -> `0x28CA8` (the top destination, 36 refs)
- `0x10423` -> `0x10422`
- `0x108E7` -> `0x108E6`

### Step 3 -- guarded registration

A per-candidate `add_func` dry-run (finding-59 clear-blocking-items retry on
failure, then `add_func(entry, end)` with explicit span + name + span check)
sorted the 37 aligned candidates:

- **23 confirmed registerable** (dry-run `add_func` + exact span) -- written to
  `registry/resident_register_expected.json` (24 ranges; `sub_28CA8` added as
  the 24th after a stray dry-run left it in the DB and the manifest was
  patched to match).
- **13 rejected**: 10 whose `add_func` still failed after the retry (mid-function
  case labels / crossing an existing function boundary), 3 whose explicit-end
  dry-run span-mismatched (`0x10897`, `0x108E6`, `0x28CA4`).

`register_upper.py` (now parameterized by `FALCON_MANIFEST`/`FALCON_REG_LOG`)
ran the resident manifest: **24 ranges, 24 new fns, 0 holes, guards PASSED,
SAVED** (backup `FALCONCD.EXE.i64.bak_resident`). `verify_rebuild` was
extended to load **both** register manifests (`upper` + `resident`), so the
24 count as `ADDED planned by the manifests`.

### Measured effect

| metric | f62 | f63 |
|---|---|---|
| functions | 2,133 | **2,157** (+24) |
| static edges | 5,289 | **5,341 (+52)** |
| `static_unresolved` | 660 | **564 (-96)** |
| union | 5,310 | 5,362 |
| Resident unresolved refs | 236 | **140 (-96)** |
| Resident unresolved dsts | 93 | 73 |
| new resident fns with >=1 incoming edge | - | **24 / 24 (0 orphans)** |

Gates: `naming.py check` OK (267) . `verify_rebuild` **faithful -- ADDED 24
all manifest-planned, REGISTER 43 applied / 77 pending, LOST 0, CHANGED 0** .
`verify_idb` **INTACT (2,157, 0 span / 0 name / 0 data-hole problems)** .
read-back **265/265 + 2/2**.

The remaining **73 Resident dsts / 140 refs** are exactly the non-registerable
categories: 27 already-fn, 18 gap-into-existing, 3 undecodable, 13 rejected
standalone (the 10 `add_func` failures + 3 span mismatches), 1 jt-tail. They
are honest residue, not missed functions.

### Step 4 -- the `0x43E0C` variant-swap check (read-only)

`0x43E0C` (16 refs) sits at offset **`+0x15D0C` from `0x2E100`** (R05's upper
base). Since `R05_1E10`, `R27_1E10s`, `R28_1E10s`, `R29_1E10s` all declare
`w0 = 0x1E10` (finding 60's variant swap), the question was whether the *same
relative offset* `+0x15D0C` inside R27/R28/R29 lands on a valid
terminator-preceded entry.

**Answer: no -- and it is not checkable as posed.** Three independent reasons:

1. **The variants are mutually exclusive load scenarios.** Finding 60 proved
   only one of R05/R27/R28/R29 is placed per CS/segment (the swap is real:
   both R05 and R29 loaded at base `0x2005` in *different runs*). There is no
   concurrent R27/R28/R29 module in the IDB at a base where `+0x15D0C` is a
   checkable function entry.
2. **The `s`-suffix variants are re-placed only as sparse entry-record
   snippets**, not contiguous modules: the entire IDB contains exactly **6**
   `r27_*`/`r28_*`/`r29_*` named functions (`r27_e05` @`0x10DAC5`,
   `r27_e62`, `r27_e64`, `r28_e65`, `r29_e06`, `r29_e63`). Treating the
   lowest of each as a "base" and adding `0x15D0C` lands in **empty space**
   (`r27` base `0x10CC60` + `0x15D0C` = `0x12296C`, no function; same for R28
   `0x131F13`, R29 `0x132FAC`).
3. **`0x43E0C` is itself a class-c anomaly in R05** -- first byte does not
   decode (`unk_43E0C`), so even in its own variant it is not a valid
   terminator-preceded entry.

So the offset coincidence does not yield a registerable entry in any sibling
variant; `0x43E0C` stays an honest unresolved dst.

---

## 2026-10-18 64 — Sweep & Register the Top 6 `R*` Overlays:
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

## 2026-10-18 65 — Call-Graph Audit: 4 anomalies in the Level-0 queue,
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

## 2026-10-18 66 — Global Level-0 Naming Pass: Batch 1 (Top 30),
`named` 265 -> 295, Level-0 queue 718 -> 688

Finding 65 handed us a clean Level-0 `naming_queue` of 718 (thunks excluded,
ea-join named detection). This session ran **Batch 1: the Top 30** by
`(dyn_calls DESC, static_in_degree DESC)`, after two hygiene checks.

### Hygiene

1. **`last_insns.json` refreshed.** `export_epilogues.py` re-ran across all
   **2,237/2,237** functions (0 missing), then `classify_routines.py`. The
   DATA count stayed 92 — the epilogue exporter confirms each *current span's*
   last instruction (`sub_22C62` last_mnem=`jo`, `sub_22C91` last_mnem=`mul`),
   corroborating that their spans end mid-code before the real `retf`.
2. **The two DATA targets verified (record-only, spans untouched):**
   * **`sub_22C62`** (rank #6): real body `mov ax,[22C71]; mov bx,[22C73];
     mov cx,[22C75]; retf` @ `0x22C70` — a **3-word state reader**. The bytes
     `0x22C71..0x22C8B` **after** the `retf` are the **data table it reads**
     (`1CE5h, 7307h, ...`), not code; the 41-B span over-extends into that
     table (hence `DATA` class). Confirmed: `0x22C71..0x22C8A` all fall inside
     the `sub_22C62` span and decode as garbage after the terminator.
   * **`sub_22C91`** (rank #4): real chain runs `push ax; push dx; mov ax,
     [22C71]; mul; ...; pop dx; pop ax; retf` @ `0x22CD4` (**~66 B**), a
     **mul/div accumulator over the same `22C71/73/75` triple**. Its 13-B span
     is **truncated by a spurious `nullsub_19`** (2 B, `36 C3`) at `0x22C9E`.
     The 13-byte epilogue window found no `retf` -> `DATA`.

### The 30 names (semantic analysis from full disasm + caller context)

Disassembled all 30 from `callgraph_partial.json`'s Level-0 queue
(`dump_batch0.py` -> `batch0_disasm.txt`/`batch0_context.json`). Key families:

* **`mouse_int33_dispatch`** (`sub_1018F`, 337K dyn, rank #1) — full C
  prologue, compares `[si]` against INT 33h subfn codes {9,0C,10,14,16-19,
  1F-21}, runs `int 33h`, writes the 4-word result to `es:[di]`. Indirect
  far-call target (0 static refs).
* **`timer_tick_isr`** (`sub_22AFF`, 229K dyn, rank #3) — ends `iret`,
  EOI to PIC `out 20h,20h`, tick counters `cs:22220/22222`.
* **`bda_equipment_flag_get`** (`sub_24E5D`, 243K) — `ES=0,BX=417h ->
  AL=ES:[BX]` = BDA `0040:0417` shift-flag byte.
* **fixed-vec3 state family** around `cs:22C71/73/75` (shared with
  `sub_22CD5`'s `22C77/79/7B` twin): `fixed_vec3_write` (`sub_22C53`),
  `fixed_vec3_read` (`sub_22C62`), `fixed_vec3_accumulate_a` (`sub_22C91`),
  `fixed_vec3_accumulate_b` (`sub_22CD5`), `fixed_vec2_half_add`
  (`sub_25CCB`).
* **far-call dispatch trampolines** through runtime-populated `cs:220xx`
  pointers (all `0000:0000` in the static image): `dispatch_220a4_stub`
  (`sub_256B2`), `dispatch_220a8_stub` (`sub_24D46`), `dispatch_220d4_stub`
  (`sub_263F0`), `dispatch_220d8_via_24bba` (`sub_24DDC`),
  `dispatch_220dc_stub` (`sub_24DE6`), `dispatch_220ec_invoke`
  (`sub_25EF4`), `dispatch_220ec_stub` (`sub_25F0D`),
  `dispatch_22100_invoke` (`sub_25DEB`), `dispatch_22120_stub`
  (`sub_25EEE`). (These are API/gateway stubs, conf: med — the slot target is
  loader-filled.)
* **state getters/setters** (high conf, single-word CS access):
  `state_word_2223e_set`, `state_byte_word_set`, `state_word_11cc8_get`,
  `state_byte_25487_get`, `state_word_22d26_get`, `state_word_22e27_set`,
  `state_farptr_dxax_store`, `bda_kb_flag_10000_get`.
* **math/helpers**: `fixed_abs_div4` (`|AX|/4` with sign fix),
  `int32_to_ascii_short` (`sub_22884` — a **sibling** of the existing
  `int32_to_ascii` @ `0x228BF`, adjacent back-to-back, same prologue but
  shorter body), `tick_rate_compute`, `control_axis_scale_store`,
  `fixed_matrix_load_7b0e` (9-word matrix copy from `DS=7B0E:3820`).

All 30 appended to `registry/naming.yaml` (+30 -> **297 entries**) and
`registry/routines.yaml` (+30 -> **296 ea entries**, CRLF preserved via
normalize). `naming.py apply` propagated to `function_bytes.json` (30
fb_fields); `naming.py push-ida` renamed all 30 in the IDB.

### Gates (all green)

`naming.py check` **OK (297)** . `verify_rebuild` **faithful (2,237==2,237,
LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span / 0 name / 0 data-hole
problems)** . `name_readback` **295/295 function + 2/2 global**.

### Effect + next slice

| metric | pre | post |
|---|---|---|
| named (fb join) | 265 | **295 (+30)** |
| naming_queue | 1,676 | **1,646 (−30)** |
| Level-0 queue | 718 | **688 (−30)** |

`callgraph_bottomup` re-run: **all 30 removed from the queue** (0 remain).
**dyn>0 in Level-0 shrinks 160 -> 130** (last dyn>0 now rank 130); **first
dyn==0 at rank 131 = `r30_e66`** (`ea=0x669F0`, `in=39`, overlay) — that is
where the static-fan-in R05/overlay leaves begin (beyond the trace's dynamic
reach). Next slice (ranks 31-50) is the tail of the dyn>0 band: `sub_103C6`
(162), `sub_25247` (136), `sub_27673` (131), ... `sub_254BB` (70).

---

## 2026-10-18 67 — The Level-0 Value Cliff + Global Batch 2 (30 named
across dyn & static fan-in), `named` 295 -> 325, queue 688 -> 658

Finding 66 left a 688-entry Level-0 queue with a sharp inflection: Rank #30
had 15,191 dynamic calls but Rank #31 drops to 162, while `r30_e66` sits at
`dyn==0` with `in_degree=39`. This session first **bucketed the queue to locate
the value cliff**, then ran **Batch 2 across both the dynamic and static
high-value buckets**.

### 1. The Value Cliff (688 Level-0 leaves bucketed)

| bucket | count | metric |
|---|---|---|
| **dyn >= 10** | **99** | 19,944 calls |
| 1 <= dyn < 10 | 31 | 176 calls |
| **dyn==0, in>=5 (high static fan-in)** | **45** | 450 in_edges |
| dyn==0, 2<=in<=4 | 142 | 365 in_edges |
| dyn==0, in==1 (single caller) | 203 | 203 in_edges |
| **dyn==0, in==0 (ORPHANS)** | **168** | 0 (excluded) |

**The cliff:** the top **99** `dyn>=10` functions capture **19,944** of the
~20,120 total dyn calls in Level-0 (top-15 alone = 11,717), whereas the entire
`1<=dyn<10` band (31 fns) yields only **176**. So after the 99 `dyn>=10` leaves,
dynamic value collapses ~100x. Cumulative: top-30 = 16,391; top-50 = 18,474;
top-100 = 19,953 (the last 30 dyn>0 fns add <170).

**168 orphans** (`dyn==0 AND in==0`) are **disconnected** — 0 callers and 0
callees — and must be **excluded from bottom-up naming** (they are not
reachable in the graph; class mix: ASM 106, C 26, LEAF 21, DATA 15). The
**effective nameable Level-0 queue is 688 − 168 = 520**.

**45 high static fan-in leaves** (`in>=5`) split **27 overlay + 18 resident** —
these are the static hubs (R05_1E10 / carved overlay leaves) the trace never
exercised.

### 2. Batch 2 (30 = Slice A 15 dyn>0 + Slice B 15 dyn==0 in>=5)

Rather than grinding through 130 low-dyn leaves first, Batch 2 took the two
highest-value buckets. Disassembled via `dump_batch2.py` ->
`batch2_disasm.txt`/`batch2_context.json`.

**Slice A (top 15 remaining dyn>0)** — mostly the `dispatch_220xx` gateway
family + hot state setters:
`dispatch_22088_invoke_4arg` (1,172), `dispatch_22090_invoke_4arg` (1,157),
`dispatch_22094_stub` (1,144), `dispatch_22144_via_834a` (1,105),
`dispatch_2208c_stub` (1,061), `xlat_mask_or_setbit` (860 — XLAT mask-table
bit-set), `state_byte_25488_get` (777), `dispatch_22134_stub` (688),
`dispatch_220e4_invoke_farptr` (636), `state_byte_1f743_set` (542),
`state_word_25499_set_clamp` (541), `state_byte_2549e_set` (540),
`state_byte_25489_shadow_save` (498), `state_byte_25488_shadow_restore` (498),
`fixed_vec3_transform_7e900` (498 — 3x3 fixed matrix transform with
saturated `0x8001/0x7FFF` clamp).

**Slice B (top 15 dyn==0, in>=5)** — the static hubs the trace missed:
`r30_state_init_all` (**in=39**, R30 overlay global init), `game_state_setup_multi`
(in=33), `farobj_table_snapshot` (in=33, near `retn`, snapshots 4 far-object
table groups), `r12_farptr_load_thunk` (in=19), `sbi_command_wait` (in=15 —
Sound-Blaster port 330h/331h handshake), `r08_farptr_load_thunk` (in=14),
`fixed_scale_clamp_or40` (in=13), `r69_farptr_dispatch_entry` (in=13),
`sbi_data_write` (in=12), `trig_table_lookup` (in=12 — ES=8364h trig table,
quadrant-fold via bits 12/13 -> sin/cos pair; hot caller `sub_23D2B` 108K),
`r39_farptr_call_gate` (in=12), `sprite_clip_bounds_check` (in=10),
`fixed_vec3_transform_es` (in=9, near twin of `..._7e900`),
`sprite_project_screen_y` (in=9), `r05_dgroup_save_reg` (in=9 — saves
DS/SI/BX to DGROUP 632A:0).

Four low-confidence overlay thunks (`r12`/`r08`/`r39`/`r69`) have undecodable
mid-instruction spans (class-c, finding 65) — named provisionally by caller
context, flagged `conf: low`.

### 3. Ledger + gates

`naming.yaml` **297 -> 327** (+30), `routines.yaml` **296 -> 326** ea (+30,
CRLF normalized). `naming.py apply` (30 fb_fields + 1 source text file, 4
hits) + `push-ida` (30 renamed in IDB).

Gates (all green): `naming.py check` **327** . `verify_rebuild` **faithful
(2,237==2,237, LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span/name/
hole problems)** . `name_readback` **325/325 function + 2/2 global**.

### 4. Effect + re-bucketed queue

| metric | f66 | f67 |
|---|---|---|
| named (fb join) | 295 | **325 (+30)** |
| naming_queue | 1,646 | **1,616 (−30)** |
| Level-0 queue | 688 | **658 (−30)** |

`callgraph_bottomup` re-run: **all 30 removed** (0 remain). Re-bucketed Level-0
(658): `dyn>=10` 84 (8,227 calls), `1<=dyn<10` 31 (176), `dyn0,in>=5` 30,
`dyn0,2<=in<=4` 142, `dyn0,in1` 203, **orphans 168 (excluded)**. The
`dyn>=10` band is the remaining high-value dynamic target (84 leaves); after
that the queue is static fan-in + orphans.

---

(append new findings below)
