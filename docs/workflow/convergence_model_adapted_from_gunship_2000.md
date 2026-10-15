# Convergence Model (adapted from gunship_2000)
## Convergence Model (adapted from gunship_2000)

The GS2000 workflow converges on ground truth via two mutually-checking tracks:

- **Track 1** = end-to-end byte-identical rebuild → *prevents veering from ground truth*.
- **Track 2** = incremental C ports → each verified port + registry rename records a
  learning/hypothesis; over time the C files and registry become the knowledge store,
  and Track 1 keeps re-proving nothing drifted.

### Falcon3 gap analysis vs this model

| GS2000 element | Falcon3 status | Action |
|---|---|---|
| Track 1: relink original binary | ❌ **No relink — original linker is RTLink/Plus, no binary available** | Use **splice-in-place** Track 1 (below) |
| Full asm skeleton (IDA .lst → UASM) | ❌ We have `function_bytes.json`/TSV, no instruction listing, no data/code boundary map | IDA listing export + `lst2asm`-style generator (adapt gunship scripts) |
| Track 2 batch driver | ⚠️ `portcheck_falcon.py` verifies one routine at a time | Add batch driver + pass/fail convergence metric |
| Registry with per-routine hypotheses | ⚠️ Schema + first entries exist (`registry/routines.yaml`); 3/839 tracked | Keep filling on classify/verify; renames land there + in C files |
| `mzdiff` verification | ✅ **Reusable, not game-specific** — WSL binary exists (see below) | Only `.map` files are per-EXE (`mzmap` makes them, can ingest IDA `.lst`) |
| Ghidra decompile → draft C | ❌ Not wired in (Ghidra installed; gunship has `ghidra_dump_to_lst_final.py`) | Add dump script, human-verify via portcheck |
| Coverage ground truth | ⚠️ Resident **proven** (815/815 = raw+relocs, finding 15); **overlay IDB layout wrong** (finding 16) | Rebuild overlay placement from primary anchors (plan 1.2b) |

### Track 1 without RTLink: splice-in-place

We cannot relink with RTLink/Plus, but Track 1's purpose — *prove we haven't veered* —
is achievable without it:

1. Original FALCONCD.EXE is an **immutable scaffold** (MZ header, 2717 relocations,
   RTLink directory, 1.2 MB overlay tail all verbatim).
2. Overwrite a routine's file-offset range (`hdr + (ea - 0x10000)`, length = IDA size)
   with our reassembled/recompiled bytes.
3. Require **byte-identity at every patched site** (portcheck already enforces this).
4. Verify the whole image with `mzdiff` (instruction-stream diff + `mzmap` maps).
5. Functional smoke test in DOSBox-X.

Because portcheck guarantees identical bytes, all MZ relocations and the RTLink tail
remain valid for free — no RTLink needed. As verified routines accumulate, the
"regenerated" fraction of the resident image grows toward 100% while the container
stays ground truth. This is GS2000's assurance inverted: *original-around-us* instead
of *rebuild-matching-it*.

---