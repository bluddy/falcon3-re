# Next Analysis Options

Written 2026-11-12 after finding 177 (S2 VGRAPH + S3 trace edges partial).
Current state: 4,127 functions, findings 145–177 applied, IDB clean.

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

### Bottom-up function reading — IN PROGRESS (2026-11-12)
The callgraph has **327 endpoints, 2364/4127 Level-0 leaves, 30 levels** (callgraph rebuilt).
Initial Level-0 analysis complete for 28 high-traffic leaves (see `registry/functions.yaml`).

**Confirmed renames:**
- `bda_equipment_flag_get` → `bda_kb_flag_get` (PROVEN: 0x417 is keyboard flags, not equipment)
- `state_farptr_get` → `map_tile_pos_get` (STRONG: clearly returns map X/Y tile coords)
- `fixed_abs_div4` → documented as abs_i16 net effect (HYPOTHESIS: naming.yaml not yet changed)

**New names assigned:**
- `clip_or_draw_dispatch` (sub_26099): sign-of-AX selects draw vs. clip callback
- `farobj_vec3_accum_b_ret`: far wrapper returning fixed_vec3_accumulate_b result

**Key architecture understood:**
- `farptr_table_get` = farobj instance slot lookup (table in R05_400C:0x34, 4B/entry)
- `active_farptr_set/restore` = current 3D batch context pointer (CS globals 0x22210-0x22216)
- `cs:dword_220D0/220D4/220A0/220C8/220E0/220EC` = opcode handler pointers (render pipeline)
- `timer_tick_isr` = IRQ0 at ~18.2Hz, every 4th tick chains to BIOS / joystick poll
- `farobj_render_vtable` at 0x26400 (14 entries: object_quad_proj_draw through flag_1f733_gate)

**Next: continue Level-0 analysis, then Level-1 (398 functions).**

---

## Notes
- VGRAPHH/VGRAPHM and EGRAPH0/EGRAPH1: separate game executables, out of scope here.
- P5 is the highest-value S1 remaining item (gate: `survey_mid` merged targets ~20→~0).
- After P5, the IDB is clean enough to begin S4 without further S1 work.
