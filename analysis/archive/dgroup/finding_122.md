
## 2026-11-10 122 - Per-function DS/SS applied to the IDB from runtime evidence and caller propagation
Status: APPLIED (canonical IDB; backup `FALCONCD.EXE.i64.bak_defds`)

**Problem.** After finding 121, 15,130 of the 18,471 implicit-DS memory operands in functions had DS =
BADSEL, so they had no data xrefs. A global "DS = DGROUP" default would be wrong, because 205 functions are
entered at runtime with the sim far-data segment (runtime 0x46A4 = IDA 0x54AF), and another 193 see mixed
DS. Several kinds of existing values were also artifacts:
- **303 seg021 functions** inherit 0x2AA3 linearly from `mov ds,dx` at 0x2B482. Runtime confirms 2AA3 for
  only 3 of them; 144 disagree.
- **20 R29 functions** inherit DS 0, the default left on the segments created in finding 120.
- **9 R05_33AE functions** have 63FD, which conflicts with runtime 54AF.

**Pipeline (manifest-first).**
1. `tools/export_ds_facts.py` is a read-only IDA export, written to `analysis/dgroup/ds_facts.json`. Per
   function it records:
   - entry DS, and the range that DS comes from;
   - every in-function DS change point with its opener, classified as matched/unmatched `pop ds` (from a
     flow-sensitive stack emulation), `mov ds,cs:[slot]`, `mov r,ss|es|ds|cs; mov ds,r`, `xor r,r; mov ds,r`,
     `lds`, or `mov ds,mem`;
   - callers, including fall-throughs, with their DS state;
   - tail-chunk entries, chunk ends, and the prologue;
   - for each segment, its default DS/SS, plus all SS ranges.
2. `tools/plan_default_ds.py` is the host planner. It reads the facts and `memdump/*fartrans.jsonl`, and
   writes `registry/ds_expected.json`. The entry DS rules, in order:
   - **runtime.** If every observed far entry has the same DS (at least 99%) and that DS lies inside an IDA
     segment, use it (711 changed). If the evidence is mixed, or the value is a heap/PSP paragraph, use
     BADSEL.
   - **callers.** If every call, jump, and fall-through into the function arrives with the same known DS,
     use it. This is iterated to a fixpoint (5 rounds, 1,011 changed). **Cross-check:** with half of the
     runtime-known functions hidden, caller propagation re-derived **108/108 correctly, 0 disagreements**.
   - **artifact.** A value inherited from a range opened inside a *different* function, or the R29 zero,
     becomes BADSEL (83).

   Inner ranges are re-derived from the entry DS:
   - `pop ds` matched to a `push ds` takes the DS at the push (562 matched; 248 changed from BAD).
   - An unmatched epilogue `pop ds; ...; ret` in a function whose prologue pushes ds takes the entry DS (246).
   - `mov r,ss; mov ds,r` gives DGROUP (6).
   - `mov ds,cs:[0x10842]` and `cs:[0x27470]` give DGROUP: those slots hold runtime 0x6C27 in 12/12 memdumps.
     Every other slot varies between dumps and stays BADSEL.
   - Slots, `lds`, `mov ds,mem`, and non-zeroing `mov ds,r` that IDA had read as 0 become BADSEL.
   - Genuine `xor ax,ax; mov ds,ax` (BIOS data area) keeps 0.

   A restore point follows each changed chunk, so code after the chunk keeps its value.

   **SS.** Runtime SS is DGROUP for every target outside startup. The only exceptions are seg021/seg022/R01
   on the initial EXE stack 852C, and BIOS F000. So 133 CODE segments get default SS 7A32, and 12 inner SS
   ranges are set to 7A32: 10 `pop ss` inside misdecoded data, plus the R02 stack-restore. The R29 split
   segments get default DS BADSEL instead of 0.
3. `tools/apply_default_ds.py` is the IDA apply step. It refuses to run unless every planned point holds its
   recorded "before" value, and it is a no-op if every point already holds "after". It uses only
   `split_sreg_range(SR_user)` and `set_default_sreg_value`, then re-creates the 1,472 code heads whose DS
   changed and that carry an implicit-DS direct memory operand, so their drefs follow the new DS.
   **It never calls auto_wait or plan_range.** The canonical IDB's auto queue is not empty, and draining it
   creates 94 unrelated functions (3,354 -> 3,448; `analysis/dgroup/exp_q.py`).

**Result.**
- Plan size: 3,155 DS points (1,813 entry, 457 inner, 16 tail, 869 restore), 12 SS points, and 141 segment
  defaults.
- **Implicit-DS operands with unknown DS: 15,130 -> 11,195.**
- New data xrefs from re-based heads, by target segment: R69_606E (DGROUP and its sibling data segments)
  10,803; R05_44AF (sim far data) 5,356; R05_3FD2 938; R14 923; seg020 427.
- SR_user ranges survive later reanalysis (`exp_user.py`). Inner auto ranges are not re-propagated from a new
  entry value, which is why the planner emits them explicitly (`exp_prop.py`).

**What remains BADSEL (11,195 operands), and why.**
- 5,481: entry DS undecidable, because callers arrive with unknown or conflicting DS.
- 2,618: unmatched `pop ds` that is not a plain epilogue.
- 511: `mov ds,ax` loaded from a call result or a variable.
- 350: functions with no callers and no runtime hit.
- 294: runtime-mixed entries, which really are called with several DS values.
- 242: dynamic cs-slots.

The rest are `lds` and copies from an unknown ES. These are left unknown on purpose, rather than guessed.

**Gates.**
- Function table unchanged (3,354).
- Implicit-DS operand count unchanged.
- `verify_idb_local` log identical to the pre-change baseline. That baseline is itself DAMAGED versus the
  committed ground truth; its 3/91/49/5 problems are pre-existing.
- `extract_ida_bytes` output identical.
- A rerun on the canonical IDB reports "already applied: nothing to do".

**Not done.** R69_606E (0x706E0..0x85067) still holds DGROUP plus five sibling data segments as one IDA
segment, and DGROUP BSS/stack 0x85067..0x85AC0 is unmapped. Splitting a DGROUP segment at 0x7A320 would
re-base data names and drefs, so it is deferred.
