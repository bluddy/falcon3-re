"""Record finding 73 (Global Level-2 COMPLETE: 3 batches = 93 named,
L2 queue 93 -> 0, named 964 -> 1057) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 73 — Global Level-2 COMPLETE: 3 batches named all 93
Level-2 functions (`named` 964 -> 1057, **4 digits**), L2 queue 93 -> 0

Finding 72 finished Level 1; **92/93** L2 queue entries started with 100%
named callees (the one exception calls an L2 SCC peer, resolved within the
batch). Same cadence as Level 1 (`dump_level1.py` with
`FALCON_L1_TARGETS`/`TAG`), 3 batches: **36 + 36 + 21 = 93**.

### Cadence

| batch | named after | L2 queue after | highlights |
|---|---|---|---|
| l2a | 1,000 🎉 | 57 | **`channel_reg_dispatch`** (the 0x12-case parent jump-table of the whole channel_reg_write family), `flag_table_pop_far_thunk` (**dyn=542,872 -- hottest callee in the graph**), `farobj_tile_copy_resolve` (in=35 widest, dyn=396,820), `flag_block_build_far_thunk` (160,669), `line_table_build_dispatch`, `angle_delta_quadrant` (cd=116,805) |
| l2b | 1,036 | 21 | `avg_pair_dispatch_149d2` (parent jump-table of the 4 avg variants), `terrain_pos_delta_11cfc` (in=26 widest L2), `view_basis_build_3850` (called by `view_matrix_build`), `sbi_config_081b_opl`, `farptr_table_field22_store`, 4 terrain-attr store twins |
| l2c | **1,057** | **0** | finale: **`overlay_loader_main`** (the RTLink overlay file loader: verify + path + DOS>=3 + open + handle-dup), **`startup_arena_init`** (CRT startup -- called FROM `start`: MCB save + far_entry_register 0x9F4 + arena offsets), `channel_reg_program` (the full ordered 8-callee register program, caller `dgroup_record_writer`), `line_flag_dispatch_28ed8` (dispatcher of the 3 line_flag_patchers), `event_tone_dispatch_1d418` |

### MILESTONE: Level-2 naming_queue = 0 · `named` in four digits

| metric | f72 | f73 |
|---|---|---|
| named (fb join) | 964 | **1,057 (+93)** |
| naming_queue (global) | 667 | **574** |
| **Level-2 queue** | **93** | **0** |

L2 residue = **9 orphans + 3 thunk slots, 0 other**. Global queue 574
remains (Levels 3..22). **`named` crossed 1,000 during batch l2a.**

### Structural parents now named (children all named earlier)

The bottom-up completion surfaced three dispatcher parents whose children
were named in previous levels:
* **`channel_reg_dispatch`** -> 8 `channel_reg_write_*` + `adlib_operator_write`
  + `channel_mode_reg_write` (f71/f72) -- and its composition
  **`channel_reg_program`** (caller: `dgroup_record_writer`).
* **`avg_pair_dispatch_149d2`** -> the 3 `avg_pair_*` + `state_byte_11c61_get_ah`
  (f71).
* **`line_flag_dispatch_28ed8`** -> `line_flag_patch_28f37/29075/291b1` +
  `line_table_scan_slope` (f71/f72).

### Gates (all green)

`naming.py check` **1,059** . `verify_rebuild` **faithful (2,237 == 2,237,
LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span / 0 name / 0 data-hole
problems)** . `name_readback` **1,057/1057 function + 2/2 global**.

---

"""

ROW = ("| 2026-10-18 (session 29) | ~4 h | **Finding 73: Global Level-2 "
       "COMPLETE -- 3 batches named 93 fns, `named` 964 -> **1,057** (4 "
       "digits!), L2 queue 93 -> 0.** 92/93 started with 100% named callees. "
       "l2a (1,000): **channel_reg_dispatch** (0x12-case parent of the whole "
       "channel_reg_write family), flag_table_pop_far_thunk (**dyn=542,872 "
       "hottest callee**), farobj_tile_copy_resolve (in=35/dyn=396,820), "
       "flag_block_build_far_thunk (160,669), line_table_build_dispatch, "
       "angle_delta_quadrant (cd=116,805). l2b (1,036): "
       "avg_pair_dispatch_149d2 (parent of 4 avg variants), "
       "terrain_pos_delta_11cfc (in=26 widest), view_basis_build_3850 (called "
       "by view_matrix_build), sbi_config_081b_opl. l2c (1,057): finale -- "
       "**overlay_loader_main** (the RTLink file loader), **startup_arena_init** "
       "(CRT startup FROM `start`: MCB + far_entry_register 0x9F4 + arena), "
       "**channel_reg_program** (full 8-callee register program, caller "
       "dgroup_record_writer), line_flag_dispatch_28ed8. L2 residue = 9 "
       "orphans + 3 thunks, 0 other. Global queue 574 (L3..22). **Gates "
       "green:** check 1059, verify_rebuild faithful, verify_idb INTACT, "
       "read-back **1057/1057+2/2**. |")

STATUS_PARA = (
    "**Global Level-2 COMPLETE (finding 73):** 3 batches named **all 93 L2 "
    "functions** (`named` 964 → **1,057** — four digits, crossed during batch "
    "l2a), **L2 `naming_queue` 93 → 0** (residue = 9 orphans + 3 thunks, 0 "
    "other). Structural wins: **`channel_reg_dispatch`** (the 0x12-case parent "
    "of the entire `channel_reg_write_*` family) + its composition "
    "**`channel_reg_program`**, **`avg_pair_dispatch_149d2`**, "
    "**`line_flag_dispatch_28ed8`** — all three dispatcher parents now named "
    "with every child named earlier; plus the two system-critical routines "
    "**`overlay_loader_main`** (the RTLink overlay file loader) and "
    "**`startup_arena_init`** (CRT startup called from `start`: MCB save + "
    "`far_entry_register` 0x9F4 + arena offsets). Graph's hottest callees also "
    "named: `flag_table_pop_far_thunk` (dyn=542,872), "
    "`farobj_tile_copy_resolve` (in=35, dyn=396,820). **Gates all green** "
    "(check 1,059, verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,057/1,057+2/2**). Global naming_queue = 574 (Levels 3–22)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 2 COMPLETE (finding 73):** 3 batches named all 93 L2",
    "  fns, `named` **964 -> 1,057 (4 digits)**, **L2 queue 93 -> 0** (9",
    "  orphans + 3 thunks, 0 other). Structural parents resolved:",
    "  channel_reg_dispatch / avg_pair_dispatch_149d2 / line_flag_dispatch_28ed8",
    "  + channel_reg_program; system routines overlay_loader_main +",
    "  startup_arena_init. All 4 gates green (check 1059, verify_rebuild",
    "  faithful, verify_idb INTACT, read-back 1057/1057+2/2).",
    "- **Next: Global Level-3 naming** (queue 574 across Levels 3..22). Same",
    "  cadence; callees now 100% named 3 levels deep. Long tail ahead: most",
    "  remaining nodes are dyn0/in=1 static-only leaves + in=2-4 bands.",
    "- **Follow-ups carried:** class-c undecodable overlay spans (conf:low),",
    "  92 low-conf DATA fns, 24 trap-only thunks, 397 global orphans",
    "  excluded from bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 73" in raw:
    print("findings_log: 73 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 73 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 29" in raw:
    print("time_log: 29 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 28" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 29 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-2 COMPLETE (finding 73)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f73 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 2 COMPLETE (finding 73)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f73 status (%d bytes)" % len(block))