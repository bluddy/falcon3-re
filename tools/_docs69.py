"""Record finding 69 (Batch 4: 36 named across dyn>=10 + caller_dyn hotspots)
in docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 69 — Global Batch 4 (36 named across `dyn>=10` + the
`caller_dyn_sum` hotspots), `named` 361 -> 397, Level-0 queue 454 -> 418

Finding 68 left a 490-entry Level-0 queue with **66 `dyn>=10`** leaves and
**24 `caller_dyn>=1000`** hotspots (17 of them `>=10000`) — the fartrans-blind
NEAR leaves. This session ran **Batch 4 (36)**: Slice A took the top 18
`dyn>=10` (rank `dyn DESC, caller_dyn DESC, in DESC`) and Slice B the top 18
`caller_dyn>=1000` hotspots (rank `cd DESC, in DESC`).

### Batch 4 (36)

Disassembled via `dump_batch4.py` -> `batch4_disasm.txt`/`batch4_context.json`.

**Slice A (top 18 `dyn>=10`)** — state getters/setters, EMS, view math:
`state_word_2222a_get` (129), `state_byte_af90_get` (128),
`state_word_2747a_set_ax` (126), `state_word_22d28_set_ax` (126 — the
`fn_table_dispatch` index), `view_extent_compute_1f6da` (122 — width =
`1F6D0-1F6CC+1`, scale `0x972/width`), `ems_save_restore_set` (114 — INT 67h
AH=44h), `volume_exponential_adjust` (112 — 2^si scaling of `es:77DEC` with
clamp), `view_extent_get_quad` (105), `dispatch_220f0_stub` (91),
`state_word_10219_get` (91), `state_pair_7981a_clear_if_set` (77),
`dispatch_220f0_invoke_1arg` (75), `dispatch_22180_then_27474_8` (74),
`dispatch_220f4_stub` (73), `state_byte_2549e_get` (71),
`state_byte_254a0_get` (70), `ems_page_move_alt` (70 — INT 67h AH=44h),
`event_time_compare_77dea` (68, **caller_dyn=42,958** — hot caller
`sub_1AB34` 42K, compares event time window -> AX 0/1).

**Slice B (top 18 `caller_dyn>=1000` hotspots)** — the fartrans-blind NEAR
leaves + high-fan-in hubs:
`farobj_record_push_7c054` (**cd=282,832**, caller `sub_20BDB` 282K — pushes a
6B record into the 300-cap `7C054` queue), `farobj_record_push_7d0c6`
(282,832 — near-twin queue at `7D0C6`), `farptr_slot_store_7f24a` (228,087 —
caller `sub_256BE` 228K), `fixed_quadrant_classify` (113,485 — hot callers
`sub_23C18` 67K, `sub_23B03` 38K, classifies DI sign bits -> 1/2/4/8),
`fixed_abs_neg64` (105,416 — 64-bit negate), `state_byte_11171_get` (48,004 —
caller `sub_2234B` 38K), `dispatch_22084_near` (40,844 — NEAR trampoline,
callers `sub_205BF` NEARTHUNK 18K + `int32_to_ascii` 22K),
`flag_bits_test_5740` (31,219), `fixed_neg_clamp_f000` (26,999),
`flag_block_merge_zero_5c63` (22,483), `mouse_coord_clamp_25474` (21,521),
`matrix_constants_copy_3820` (13,393), `fixed_matrix_scale_shift_7e900`
(11,155), `r39_farptr_gate_big` (11,155, low-conf undecodable),
`fixed_arith_shift_loop` (11,155, low-conf truncated DATA),
`state_cursor_advance_11c94` (11,155, low-conf no-terminator),
`terrain_height_lookup_11cc8` (11,118 — world XY -> grid -> table at
`es:3840` -> `cs:11CC8`), `fixed_long_div_64` (9,818 — 64-bit divide
`DX:AX/BP:SI`).

Three low-confidence routines (undecodable/truncated spans, class-c finding
65) flagged `conf: low`.

### Ledger + gates

`naming.yaml` **363 -> 399** (+36), `routines.yaml` **362 -> 398** ea (+36,
CRLF normalized). `naming.py apply` (36 fb_fields + 1 source text, 9 hits) +
`push-ida` (36 renamed in IDB).

Gates (all green): `naming.py check` **399** . `verify_rebuild` **faithful
(2,237==2,237, LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span/name/
hole problems)** . `name_readback` **397/397 function + 2/2 global**.

### Effect + re-bucketed queue

| metric | f68 | f69 |
|---|---|---|
| named (fb join) | 361 | **397 (+36)** |
| naming_queue | 1,270 | **1,234 (−36)** |
| Level-0 queue | 454 | **418 (−36)** |

`callgraph_bottomup` re-run: **all 36 removed** (0 remain). Re-bucketed
Level-0 (418): `dyn>=10` **48** (was 66), `1<=dyn<10` 31, `dyn0,in>=5` 11,
`dyn0,2-4` 131, `dyn0,in1` 197. **`caller_dyn>=1000` hotspots now 6 (0
>=10000)** — Batch 4 consumed all 17 of the `>=10000` hotspots, the fartrans
blind spot is largely closed at Level 0.

---

"""

ROW = ("| 2026-10-18 (session 25) | ~3 h | **Finding 69: Batch 4 -- 36 named "
       "across dyn>=10 + caller_dyn hotspots; `named` 361 -> 397, L0 queue "
       "454 -> 418.** Slice A (18 dyn>=10): state_word_2222a/10219/2747a/"
       "22d28_get/set, state_byte_af90/2549e/254a0_get, "
       "view_extent_compute_1f6da + view_extent_get_quad, ems_save_restore_set "
       "+ ems_page_move_alt (INT 67h AH=44h), volume_exponential_adjust "
       "(2^si on es:77DEC), event_time_compare_77dea (cd=42,958, caller "
       "sub_1AB34 42K), dispatch_220f0/220f4/22180, "
       "state_pair_7981a_clear_if_set. Slice B (18 caller_dyn>=1000 "
       "hotspots, the fartrans-blind NEAR leaves): farobj_record_push_7c054 "
       "(**cd=282,832**, caller sub_20BDB 282K) + _7d0c6 twin, "
       "farptr_slot_store_7f24a (228K), fixed_quadrant_classify (113K, hot "
       "callers sub_23C18 67K), fixed_abs_neg64 (105K), "
       "state_byte_11171_get (48K), dispatch_22084_near (40K, NEARTHUNK+"
       "int32_to_ascii callers), flag_bits_test_5740, fixed_neg_clamp_f000, "
       "flag_block_merge_zero_5c63, mouse_coord_clamp_25474, "
       "matrix_constants_copy_3820, fixed_matrix_scale_shift_7e900, "
       "terrain_height_lookup_11cc8 (world->grid->table), fixed_long_div_64, "
       "+ 3 low-conf undecodable (r39_farptr_gate_big, fixed_arith_shift_loop, "
       "state_cursor_advance_11c94). Ledgers 363->**399** / 362->**398**, "
       "apply+push-ida. **Gates green:** check 399, verify_rebuild faithful, "
       "verify_idb INTACT, read-back **397/397+2/2**. Re-bucketed L0 (418): "
       "dyn>=10=48, **caller_dyn>=1000 hotspots 6 (0 >=10000)** -- blind spot "
       "largely closed. |")

STATUS_PARA = (
    "**Batch 4 (finding 69):** named 36 across the two remaining Level-0 "
    "high-value buckets — Slice A (18 `dyn≥10`: state getters/setters, EMS "
    "INT 67h save/move, `view_extent_*`, `volume_exponential_adjust`, "
    "`event_time_compare_77dea`) and Slice B (18 `caller_dyn≥1000` hotspots, "
    "the fartrans-blind NEAR leaves: `farobj_record_push_7c054` cd=282K, "
    "`farptr_slot_store_7f24a` 228K, `fixed_quadrant_classify` 113K, "
    "`fixed_abs_neg64` 105K, `terrain_height_lookup_11cc8`, "
    "`fixed_long_div_64`, + dispatch gateways). Ledgers 363→**399** / "
    "362→**398**, applied + pushed. **Gates all green** (check 399, "
    "verify_rebuild faithful, verify_idb INTACT, read-back **397/397+2/2**). "
    "Re-ran the call graph: **named 361→397, Level-0 queue 454→418**; "
    "re-bucketed, `dyn≥10` down to 48 and **`caller_dyn≥1000` hotspots down "
    "to 6 (0 ≥10000)** — the fartrans blind spot is largely closed at Level 0."
)

OPEN_NEW = [
    "- **Batch 4 done (finding 69):** 36 named, `named` **361 -> 397**,",
    "  Level-0 queue **454 -> 418**. Slice A = dyn>=10 state/EMS/view math;",
    "  Slice B = caller_dyn>=1000 fartrans-blind NEAR hotspots (all 17 >=10000",
    "  consumed; only 6 cd>=1000 remain, 0 >=10000). All 4 gates green (check",
    "  399, verify_rebuild faithful, verify_idb INTACT, read-back 397/397+2/2).",
    "- **Next (Batch 5):** remaining **48 `dyn>=10` Level-0 leaves** + 6",
    "  caller_dyn hotspots; then the long tail (31 dyn 1-9, 11 in>=5, 131",
    "  in 2-4, 197 in=1). Orphans (397) stay excluded.",
    "- **Follow-ups:** 3 low-conf undecodable/truncated spans this batch",
    "  (r39_farptr_gate_big, fixed_arith_shift_loop, state_cursor_advance_11c94)",
    "  join the class-c repair list; 92 low-conf DATA fns; 24 trap-only thunks.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 69" in raw:
    print("findings_log: 69 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 69 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 25" in raw:
    print("time_log: 25 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 24" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 25 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Batch 4 (finding 69)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f69 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Batch 4 done (finding 69)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f69 status (%d bytes)" % len(block))