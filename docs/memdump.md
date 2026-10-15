- [x] Carve heap blocks (MCB-owned, owner=0x1E5) -> scan DGROUP for far
      pointers into them (advice.md §4) -> **find decompressed asset buffers**
      (compression format UNKNOWN, finding 31 -- do this instead of guessing
      the algorithm)
- [x] Emit segment classification JSON (SEG_DGROUP / SEG_STATIC /
      SEG_OVERLAY_ID(n) / SEG_HEAP_ALLOC(callsite)) from the trace build's
      `*_fartrans.jsonl` + these dumps -- **DONE 2026-10-14**:
      `tools/classify_segments.py` -> `analysis/traces/segment_classification.json`.
      **Multi-kind segments** (per user choice): each segment carries a
      `kinds[]` list plus a highest-rank `kind` for single-label consumers.
      Per run: 116-119 segments, 47-48 `SEG_DATA`, 18 `SEG_STATIC`,
      1 `SEG_DGROUP` (27687, stable across both runs), 3 `SEG_VGA_VRAM`,
      15 overlay pool ids + 80-90 `SEG_OVERLAY_DATA(n)` carved from them.
      DGROUP certainty = HYPOTHESIS (ranked by distinct entry-IP coverage,
      not raw observation count); resident base = PROVEN (finding 32/33).
      Heap call-site (`SEG_HEAP_ALLOC`) needs the new INT 21h AH=48h hook --
      the two committed traces predate it, so 0 heap blocks so far; a fresh
      traced run will populate it.
- [x] Cross-check carved overlay bytes against `function_bytes.json` ground
      truth (validates fixup application, finding 21)