# Next Analysis Options

Written 2026-11-12, updated 2026-11-12 after S4 Level-0 batch 1 (findings 180-182).
Current state: 4,127 functions, 2,049 named (49.6%), 289 Level-0 in naming queue.

---

## S1 Deferred (IDB boundaries, highest priority)

### P5 — R30 menu handler cluster ← **NEXT**
**Range:** `0x6E696..0x6E8B7` (R14_5E0B overlay)  
**Problem:** One large `[bp+6]` / `[bp-0Eh]` dispatch switch was split into ~25
named pieces by P1. The pieces cannot be read in call-graph order independently —
they are really case arms of one function.  
**Fix:** *Function-merge* mode (inverse of P1): delete the split pieces, redecode
the range as one body, move ledger names to inline comments or a case-label list.
Decision needed on which of the ~25 names becomes the owning function name.  
**Also in range:** orphan runs `0x6E7C7` (66 B), `0x6E8BC` (3 B), `0x67BA3` (3 B)
(were P6 targets; still unregistered).  
**Gate:** `survey_mid.py` merged targets; `naming.py check`; `verify_rebuild` faithful.  
**Reference:** idb_stabilisation_plan.md P5; status.md "Left open" section.

### 0x4E520 chain
**Problem:** 12 auto-queue sub-functions inside function `0x4E520..0x4E803`.
PLAN mode crashes (IDA native crash) when adding split `(0x4E520, 0x4E5B4)` —
likely because adding a 591-byte function triggers native analysis that segfaults.  
**Fix options:** (a) write a standalone split script bypassing PLAN/MANIFEST for
this entry; (b) run auto_wait on a probe limited to that one segment; (c) investigate
the crash with a debug build.  
**Impact:** 12 more function registrations; minor.

### P2 deferred misdecodes
- 10 type-1 not_head targets: external callers to null-byte heads; need sub-block
  fixup or individual REBASE/GLUE per target.
- 5 off>1 R14 misdecodes: R14 overlay has multi-byte instruction misalignments.
- 1 66-prefix misdecode (0x356A7): interacts with plan-mode state; deferred.

---

## S2 Remaining (new segments)

### VGRAPHH / VGRAPHM
**Decision (2026-11-12):** SKIP for Falcon 3 analysis.  
VGRAPHM = Mig-29 expansion graphics driver (97.8% identical to VGRAPH, same entry
IPs, Mig-29 needed a few extra graphics ops).  
VGRAPHH = Harrier expansion graphics driver (47.7% identical, shifted entry IPs,
Harrier needed significantly more rendering capability).  
Both companion games need completely separate analysis in their own IDB instances.
Not relevant to the Falcon 3 deep dive.

### VGRAPH slot naming
Currently `vgraph_slot_0..39` are placeholder names. Reading the top-called slots
(slot_1 = 127K calls, slot_39 = second most) would reveal the graphics primitive
names (tile-blit, pixel-write, clear-screen, line-draw, etc.). Low effort,
high value for the deep dive since ~10% of all runtime calls go here.

### Other MCB-allocated runtime segment (cs=0x7A93 / seg 31379)
Allocated at `paras=4064` (64 KB) right after VGRAPH from site `1161:2F53`.
Has a few call targets in boundary_report. Might be menu graphics buffer,
font data, or another small driver. Worth checking what `falcon3.def` loads into it.

---

## S3 Remaining (trace edges)

### Full callgraph rebuild
Parse `trace_20261015_211031_fileio.jsonl` (the comprehensive 1.2 MB session trace
with 379,498 events). Current 159 xrefs came only from harvctl3 + debug_test.
A full parse would cover more overlay scenarios and produce better callgraph levels.
Rebuild with `tools/export_callrefs.py` + `tools/callgraph_bottomup.py`.

### memderef xrefs (data segment xrefs)
`memdump/debug_test_memderef.jsonl` has 8,352 unique CS:IP segment-override sites.
These are data xrefs (DS:/ES: overrides) that IDA currently shows as BADSEL
implicit operands. Adding them as XREF_USER data refs would halve the 11,195
remaining unknown-DS operands identified in finding 122.

---

## S4 Deep dive

### Bottom-up function reading — BATCH 1 COMPLETE (2026-11-12)
The callgraph has **289 Level-0 in naming queue, 30 levels** (callgraph rebuilt with findings 180-182).

**S4 Level-0 Batch 1 (10 functions, 91K total dyn calls):**
- Finding 180: CS-segment state block accessors (0x2B76-0x2B84+)
  - 7 tiny functions (2-5B): `cs_word_2b76_get`, `cs_word_2b78_get`, `cs_word_2b80_set`, 
    `cs_word_2b82_set`, `cs_word_2b84_set`, `cs_byte_00e8_get`, `zero_ax`
  - Overlay-persistent CODE-segment storage, likely flight physics state
- Finding 181: `farobj_dispatch_table` (sub_263F6, 122B, 18K calls)
  - Polymorphic dispatch table/vtable for FarObj entity types
  - Called by 8 high-level object managers
- Finding 182: Trig lookup pair (`trig_lookup_sin`, `trig_lookup_cos`)
  - Fixed-point sin/cos tables, 14-bit angle + quadrant flags
  - 88-92B functions, 8K-9K calls each

**Previous names (findings 145-177):**
- `bda_kb_flag_get`, `map_tile_pos_get`, `clip_or_draw_dispatch`, `farobj_vec3_accum_b_ret`
- `farptr_table_get`, `active_farptr_set/restore`, `timer_tick_isr`, `farobj_render_vtable`

**Next options:**
1. **Function boundary fixes** ← HIGH PRIORITY: 25% of call sites land mid-body, blocking probes
2. Continue Level-0 naming (279 remaining, next batch: sub_100B5, sub_22DE6, sub_22F2C...)
3. Level-1 naming (398 functions after Level-0 complete)

---

## Notes
- VGRAPHH/VGRAPHM and EGRAPH0/EGRAPH1: separate game executables, out of scope here.
- P5 is the highest-value S1 remaining item (gate: `survey_mid` merged targets ~20→~0).
- After P5, the IDB is clean enough to begin S4 without further S1 work.
