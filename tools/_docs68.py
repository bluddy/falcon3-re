"""Record finding 68 (orphan exclusion + caller_dyn_sum + Batch 3: 36 named)
in docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 68 — Orphan Exclusion + `caller_dyn_sum` (the fartrans
blind spot) + Global Batch 3 (36 named), `named` 325 -> 361, Level-0 queue
490 -> 454

Finding 67 surfaced why `trig_table_lookup` (caller 108K) and
`farobj_table_snapshot` (in=33) had `dyn==0`: **`fartrans.jsonl` only hooks
FAR calls, so every NEAR (`retn`) leaf has `dyn==0` regardless of how hot its
FAR caller is.** This session (1) excluded the disconnected orphans from the
queue, (2) computed `caller_dyn_sum` to surface those hidden hot NEAR leaves,
and (3) ran **Batch 3 (36)** across both the `dyn>=10` band and the
`caller_dyn_sum`-ranked static band.

### 1. Orphan exclusion + `caller_dyn_sum` in `callgraph_bottomup.py`

* **Orphans** = `dyn==0 AND static_in_degree==0` (0 callers, 0 callees — not
  reachable bottom-up). Excluded from `naming_queue`, tracked separately in
  `orphans`. **Level-0 queue 658 -> 490 (−168)**; global orphan count 397
  (all levels), **204 at Level 0** (the other 36 were already out for thunks /
  other reasons). Effective nameable Level-0 = 490.
* **`caller_dyn_sum(u) = sum(dyn_calls(c) for c in static_callers(u))`** —
  surfaces hot NEAR leaves indirectly via their FAR callers' call counts.
  Confirmed the insight: `dyn>0` Level-0 = 114 far / **1 near** (outlier),
  while `dyn==0` = **361 near** / 182 far — fartrans is FAR-only.
* **caller_dyn_sum analysis (dyn==0 Level-0, connected):**
  - `in>=5` bucket (**30 fns**): **6 with caller_dyn >= 10,000** —
    `sub_24988` (323,575), `sub_24980` (226,642), `sub_22FD7` (222,221),
    `sub_23DCD` (95,867), `sub_2647E` (86,416), `sub_25268` (22,483).
  - `1<=in<=4` bucket (**345 fns**): **16 with caller_dyn >= 10,000** —
    `sub_2128E` (282,832, in=1!), `sub_212D6` (282,832, in=1),
    `sub_256CD` (228,087, in=1), `sub_23A1B` (113,485), etc.

These are the hot NEAR leaves the fartrans blind spot was hiding.

### 2. Batch 3 (36 = Slice A 18 dyn>=10 + Slice B 18 dyn==0 flag-ranked)

Targets from `batch3_targets.json`; disassembled via `dump_batch3.py` ->
`batch3_disasm.txt`/`batch3_context.json`.

**Slice A (top 18 `dyn>=10`)** — gateways + timers + state:
`state_word_7e54d_get` (498), `dispatch_22130_stub` (498),
`vec_delta_scaled_stosw` (480 — 3-axis fixed delta >> CX),
`state_word_26400_get_zero` (415, 23 callers),
`rect_clip_then_dispatch_2209c` (370 — rect bounds then far-dispatch),
`tick_wait_until_22220` (351 — spin on tick counter), `dispatch_220f4_invoke_2arg`
(334), `lodsw_quad_to_state_25450` (286), `tick_add_wait_22220` (284),
`state_word_77b34_get` (229), `state_word_27470_set_ds` (199),
`flag_bits_clear_mask_5750` (194), `dispatch_22108_invoke_7arg` (190),
`pit_channel0_latch_read` (175 — **PIT port 40h 3-latch into cs:22C71/73/75**,
the seed for `fixed_vec3_read`), `dispatch_22174_stub` (171),
`ems_page_move_67` (162 — INT 67h AH=44h EMS move), `flag_block_zero_5762_5c63`
(136), `state_word_27476_set_ax` (131).

**Slice B (top 18 `dyn==0`, ranked `(in>=5 OR caller_dyn>=10000, in DESC,
caller_dyn DESC)`)** — the fartrans-blind-spot hotspots + high-fan-in hubs:
`r14_farptr_call_gate` (in=9), `r05_farptr_dispatch_big` (in=9),
`fixed_angle_mask_3fff` (in=8, **cd=226,642**), `r14_farptr_call_gate2` (in=8),
`hw_port_bit_test_retn` (in=8), `state_block_77720_store8` (in=8),
`dgroup_save_reg_dxbp` (in=8), `farobj_field_scale_check` (in=8),
`fixed_angle_fold_e000` (in=7, **cd=323,575** — caller `sub_24984` NEARTHUNK
303K!), `fixed_ratio_blend` (in=7, cd=222,221 — hot callers sub_23C9B 87K),
`fixed_vec_normalize_7b0e` (in=7, cd=95,867), `farobj_field4_get_stc` (in=7),
`flag_gate_zero_abc` (in=7), `farobj_field2e_zero_dispatch` (in=7),
`farobj_field_scale_check2` (in=7), `farobj_type_field_get` (in=6, cd=86,416),
`hw_flag_bit1_22e_extract` (in=6), `r37_farptr_store_gate` (in=6).
Seven low-confidence overlay/farobj routines with undecodable mid-instruction
spans (class-c, finding 65) flagged `conf: low`.

Note the Slice-B rank fix: the first selection pass sorted the whole `dyn==0`
list but the `flag=1` (in>=5 OR cd>=10000) nodes must come first — corrected
to `(-flag, -in, -cd, ea)` so all 46 flag=1 nodes rank above the flag=0 ties.

### 3. Ledger + gates

`naming.yaml` **327 -> 363** (+36), `routines.yaml` **326 -> 362** ea (+36,
CRLF normalized). `naming.py apply` (36 fb_fields + 1 source text, 2 hits) +
`push-ida` (36 renamed in IDB).

Gates (all green): `naming.py check` **363** . `verify_rebuild` **faithful
(2,237==2,237, LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span/name/
hole problems)** . `name_readback` **361/361 function + 2/2 global**.

### 4. Effect + re-bucketed queue

| metric | f67 | f68 |
|---|---|---|
| named (fb join) | 325 | **361 (+36)** |
| naming_queue | 1,306 | **1,270 (−36)** |
| Level-0 queue | 490 | **454 (−36)** |

`callgraph_bottomup` re-run: **all 36 removed** (0 remain). Re-bucketed
Level-0 (454): `dyn>=10` **66**, `1<=dyn<10` 31, `dyn0,in>=5` **12** (was
30), `dyn0,2-4` 142, `dyn0,in1` 203 (orphans excluded). Remaining
`caller_dyn_sum>=1000` hotspots: **24** (17 >=10000) — the `1<=in<=4` band
still holds **16 with cd>=10000** (the fartrans-blind NEAR leaves).

---

"""

ROW = ("| 2026-10-18 (session 24) | ~3 h | **Finding 68: orphan exclusion + "
       "caller_dyn_sum + Batch 3 -- 36 named, `named` 325 -> 361, L0 queue "
       "490 -> 454.** Confirmed **fartrans is FAR-only** (dyn>0 L0 = 114 far/"
       "1 near; dyn0 = 361 near/182 far) -> every retn leaf has dyn==0. "
       "callgraph now excludes **orphans (dyn0 AND in0)** from naming_queue "
       "(L0 658->**490**, −168; 204 orphans at L0, 397 global) and computes "
       "**caller_dyn_sum(u)=sum(dyn of static callers)**. Analysis: in>=5 "
       "bucket (30) has **6 with cd>=10k** (sub_24988=323K, sub_24980=226K, "
       "sub_22FD7=222K, sub_23DCD=95K, sub_2647E=86K); 1<=in<=4 bucket (345) "
       "has **16 with cd>=10k** (sub_2128E=282K in=1, sub_212D6=282K, "
       "sub_256CD=228K) -- the hidden hot NEAR leaves. **Batch 3 (36):** "
       "Slice A (18 dyn>=10): pit_channel0_latch_read (PIT 40h -> 22C71/73/75 "
       "seed), rect_clip_then_dispatch_2209c, tick_wait/add_22220, "
       "ems_page_move_67 (INT 67h), dispatch_220f4/22108/22130/22174, "
       "vec_delta_scaled_stosw, flag_block_zero_5762_5c63, state setters; "
       "Slice B (18 flag-ranked): fixed_angle_fold_e000 (cd=323K, caller "
       "NEARTHUNK 303K), fixed_angle_mask_3fff (cd=226K), fixed_ratio_blend "
       "(cd=222K), fixed_vec_normalize_7b0e (cd=95K), farobj_type_field_get "
       "(cd=86K), + r14/r05/r37 farptr gates, 7 low-conf undecodable "
       "farobj/overlay. Ledgers 327->**363** / 326->**362**, apply+push-ida. "
       "**Gates green:** check 363, verify_rebuild faithful, verify_idb "
       "INTACT, read-back **361/361+2/2**. Re-bucketed L0 (454): dyn>=10=66, "
       "in>=5=12, cd>=1000 hotspots=24. |")

STATUS_PARA = (
    "**Orphan exclusion + caller_dyn_sum + Batch 3 (finding 68):** confirmed "
    "**`fartrans.jsonl` is FAR-only** (dyn>0 Level-0 = 114 far / 1 near; "
    "dyn==0 = 361 near) — every `retn` leaf has `dyn==0` regardless of caller "
    "heat. `callgraph_bottomup` now (1) **excludes disconnected orphans** "
    "(`dyn==0 AND in==0`) from `naming_queue` — **Level-0 658→490 (−168)**, "
    "tracked in `orphans`; and (2) computes **`caller_dyn_sum(u)` = sum of "
    "static callers' dyn_calls**, surfacing hidden hot NEAR leaves: the `in≥5` "
    "bucket (30) has **6 with caller_dyn≥10k** (`sub_24988` 323K, "
    "`sub_24980` 226K, `sub_22FD7` 222K …) and the `1≤in≤4` bucket (345) has "
    "**16 with ≥10k** (`sub_2128E` 282K at in=1 …). Ran **Batch 3 (36)**: "
    "Slice A (18 dyn≥10) = `pit_channel0_latch_read` (PIT 40h → the "
    "`22C71/73/75` seed), `rect_clip_then_dispatch_2209c`, tick waits, EMS "
    "page-move, dispatch gateways, flag-block reset; Slice B (18 flag-ranked) "
    "= `fixed_angle_fold_e000` (cd 323K), `fixed_angle_mask_3fff` (226K), "
    "`fixed_ratio_blend` (222K), `fixed_vec_normalize_7b0e` (95K), "
    "`farobj_type_field_get` (86K) + R-overlay farptr gates (7 low-conf "
    "undecodable). Ledgers 327→**363** / 326→**362**, applied + pushed. "
    "**Gates all green** (check 363, verify_rebuild faithful, verify_idb "
    "INTACT, read-back **361/361+2/2**). Re-ran the call graph: **named "
    "325→361, Level-0 queue 490→454**; re-bucketed, `dyn≥10` down to 66, "
    "`in≥5` down to 12, **24 caller_dyn≥1000 hotspots remain** (17 ≥10000)."
)

OPEN_NEW = [
    "- **Orphans excluded + caller_dyn_sum added + Batch 3 done (finding 68):**",
    "  36 named, `named` **325 -> 361**, Level-0 queue **490 -> 454**. fartrans",
    "  confirmed FAR-only; orphans (dyn0 AND in0) excluded from naming_queue;",
    "  caller_dyn_sum surfaces hidden hot NEAR leaves (6 in in>=5 bucket, 16 in",
    "  1<=in<=4 with cd>=10k). All 4 gates green (check 363, verify_rebuild",
    "  faithful, verify_idb INTACT, read-back 361/361+2/2).",
    "- **Next (Batch 4):** remaining **66 `dyn>=10` Level-0 leaves** + the",
    "  **24 caller_dyn>=1000 hotspots** (17 >=10000, mostly in the 1<=in<=4",
    "  band) -- use caller_dyn_sum as the secondary rank so hot NEAR leaves are",
    "  not starved by the fartrans blind spot. `in>=5` bucket down to 12.",
    "- **Follow-ups:** 7 low-conf farobj/overlay routines (r14/r05/r37",
    "  farptr gates + farobj_field_*) have undecodable mid-instruction spans",
    "  (class-c) -- reclassify when span repair lands; 92 low-conf DATA fns;",
    "  24 trap-only thunk far-targets at word_*/unk_* data.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 68" in raw:
    print("findings_log: 68 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 68 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 24" in raw:
    print("time_log: 24 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 23" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 24 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Orphan exclusion + caller_dyn_sum + Batch 3 (finding 68)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f68 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Orphans excluded + caller_dyn_sum added + Batch 3 done (finding 68)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f68 status (%d bytes)" % len(block))