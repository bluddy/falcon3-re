# Track C: Splice Rebuild + mzdiff (PLANNED — adapted from gunship_2000)
## Track C: Splice Rebuild + mzdiff (PLANNED — adapted from gunship_2000)

Goal: replace verified C routines **inside** the original MZ image (splice-in-place,
see "Convergence Model" above) and prove no drift with `mzdiff`, which compares
instruction streams via segment maps rather than raw bytes — relocation-tolerant.

### mzdiff availability (verified 2026-10-11) — NOT game-specific

`mzdiff`/`mzmap` are **generic MZ tools** from `f19re/mzretools`; only the `.map`
files are per-EXECUTABLE (`mzmap` generates them and can ingest an IDA `.lst` directly).
No build needed — reuse the existing WSL binary (GS2000's doc says `build/mzdiff`;
actual location is **`debug/`**):

```
/mnt/c/Users/yotam/projects/gunship_2000/tools/f19re/mzretools/debug/mzdiff   # v1.0.20 ✅ runs
/mnt/c/Users/yotam/projects/gunship_2000/tools/f19re/mzretools/debug/mzmap    # v1.0.20 ✅ runs
```

Usage:
```
mzmap FALCONCD.EXE falconcd.map            # once per EXE (or feed IDA .lst)
mzdiff [--map ref.map] [--tmap tgt.map] [--loose] [--verbose] ref.exe[:entry] tgt.exe[:entry]
```

### Components to build

1. **IDA listing export** → `.lst` (mzmap can use it directly as a map; also feeds
   the asm-skeleton generator below)
2. **`extract_routines.py`** (borrow gunship): parse MSC `.cod` → per-routine `.asm` + auto-`EXTRN` for far calls
3. **`replace_routines.py`** (borrow gunship): take IDA-generated asm skeleton, swap target routines with C-generated asm
4. **Splice driver** (`tools/splice.py`, new): write verified routine bytes into a
   copy of FALCONCD.EXE at `hdr + (ea - 0x10000)`; refuse if bytes differ
5. **Assemble**: UASM (`uasm -0 -q`) for transcribed hand-ASM routines → extract bytes → splice
   - Note: no RTLink binary ⇒ a faithful final *link* is impossible; splice sidesteps it
     (header/relocs/tail verbatim, code byte-identical ⇒ structurally valid by construction)
6. **`mzdiff` whole-image check**: `mzdiff falconcd.map original.exe splice.exe` —
   instruction-stream equality across the resident image

### Why not just byte-compare the whole EXE?
- RTLink overlay records + fixups live in a 1.2 MB tail whose full structure is not yet
  decoded (68 KB of records known, rest undecoded; compression format UNKNOWN, finding 31)
- Relocations (2717 MZ + 1569 RTLink) make naive whole-file diffs useless
- `mzdiff` normalizes via segment maps → compares the *code stream*
- Splice guard: byte-identity at each patch site ⇒ relocs/tail stay valid automatically

### Verification levels

| Level | Tool | What it proves |
|-------|------|----------------|
| 1. Routine bytes | `portcheck_falcon.py` | C compiles to identical instruction bytes |
| 2. Routine asm roundtrip | `extract_routines.py` + UASM + byte diff | `.cod` → `.asm` → `.obj` lossless |
| 3. Resident image | `mzdiff ref.exe target.exe --loose` | Replacements don't disturb neighbors |
| 4. Full functional | Run in DOSBox-X | Game plays |

---