"""Record finding 66 (Global Level-0 Batch 1: 30 named) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 66 — Global Level-0 Naming Pass: Batch 1 (Top 30),
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

"""

ROW = ("| 2026-10-18 (session 22) | ~3 h | **Finding 66: Global Level-0 "
       "Batch 1 -- 30 named, `named` 265 -> 295, Level-0 queue 718 -> 688.** "
       "Hygiene: `export_epilogues` re-ran **2,237/2,237** (0 missing); "
       "verified the 2 DATA targets record-only -- `sub_22C62` is a 3-word "
       "state reader whose 41B span over-extends into the `22C71/73/75` data "
       "table it reads (retf@0x22C70), `sub_22C91` runs to retf@0x22CD4 "
       "(~66B) but is **truncated by a spurious nullsub_19@0x22C9E**. "
       "Disassembled all 30 from the Level-0 queue (dump_batch0.py). Names: "
       "`mouse_int33_dispatch` (337K, INT 33h subfn dispatch), "
       "`timer_tick_isr` (iret+EOI), `bda_equipment_flag_get` (BDA 0040:0417), "
       "the **fixed-vec3 state family** (write/read/accumulate_a/accumulate_b "
       "over cs:22C71/73/75 + twin 22C77/79/7B), **9 far-call dispatch "
       "trampolines** through runtime cs:220xx slots (0000:0000 in image), "
       "8 state get/setters, `fixed_abs_div4`, `int32_to_ascii_short` "
       "(sibling of int32_to_ascii@0x228BF, adjacent), `tick_rate_compute`, "
       "`control_axis_scale_store`, `fixed_matrix_load_7b0e`. Appended +30 to "
       "naming.yaml (297) + routines.yaml (296, CRLF-normalized), apply + "
       "push-ida. **Gates all green:** check 297, verify_rebuild faithful "
       "(2237), verify_idb INTACT, read-back **295/295+2/2**. Re-run "
       "callgraph: 30 removed from queue, **dyn>0 160 -> 130**, first dyn==0 "
       "at rank **131 = r30_e66 (overlay, in=39)** -- where static-fan-in "
       "R05/overlay leaves begin. |")

STATUS_PARA = (
    "**Global Level-0 Batch 1 (finding 66):** named the Top 30 Level-0 leaves "
    "by `(dyn, in_degree)` after hygiene (epilogues re-exported 2,237/2,237; "
    "the two DATA targets verified record-only — `sub_22C62` over-extends into "
    "its own `22C71/73/75` data table after `retf@0x22C70`, `sub_22C91` is "
    "**truncated by a spurious `nullsub_19`** with the real chain to "
    "`retf@0x22CD4`). Names span the `mouse_int33_dispatch` / `timer_tick_isr` "
    "hottest leaves, the **fixed-vec3 state family**, **9 far-call dispatch "
    "trampolines** through runtime `cs:220xx` slots, 8 state getters/setters, "
    "and math helpers (`fixed_abs_div4`, `int32_to_ascii_short` — a sibling of "
    "the existing `int32_to_ascii`). Appended to both ledgers (+30), applied, "
    "pushed to IDA. **Gates all green** (check 297, verify_rebuild faithful, "
    "verify_idb INTACT, read-back **295/295+2/2**). Re-ran the call graph: "
    "**named 265→295, Level-0 queue 718→688**, all 30 removed; **dyn>0 band "
    "160→130**, first `dyn==0` at **rank 131 = `r30_e66`** (overlay, in=39) — "
    "where the static-fan-in R05/overlay leaves begin."
)

OPEN_NEW = [
    "- **Global Level-0 Batch 1 done (finding 66):** 30 named, `named`",
    "  **265 -> 295**, Level-0 queue **718 -> 688**. All 4 gates green",
    "  (check 297, verify_rebuild faithful, verify_idb INTACT, read-back",
    "  295/295+2/2). Hygiene: epilogues 2,237/2,237; `sub_22C91` confirmed",
    "  truncated by spurious `nullsub_19@0x22C9E` (real retf@0x22CD4),",
    "  `sub_22C62` span over-extends into its own data table.",
    "- **Next (Batch 2):** Level-0 ranks 31-60 (tail of the dyn>0 band: last",
    "  dyn>0 at rank **130**, first dyn==0 at rank **131 = r30_e66** overlay",
    "  in=39). Ranks 31-50: sub_103C6(162), sub_25247(136), sub_27673(131),",
    "  ... sub_254BB(70). After rank 130 the queue becomes static-fan-in",
    "  R05/overlay leaves (no trace coverage).",
    "- **Follow-ups:** reclassify the 92 low-confidence DATA fns (epilogue",
    "  window + `nullsub_19` truncation of `sub_22C91`); resolve the 24",
    "  trap-only thunk far-targets (point at `word_*`/`unk_*` data).",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 66" in raw:
    print("findings_log: 66 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 66 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 22" in raw:
    print("time_log: 22 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 21" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 22 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-0 Batch 1 (finding 66)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f66 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Global Level-0 Batch 1 done (finding 66)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f66 status (%d bytes)" % len(block))