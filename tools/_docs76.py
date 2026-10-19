"""Record finding 76 (Global Level-5 COMPLETE: 2 batches = 60 named,
L5 queue 60 -> 0, named 1163 -> 1223) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 76 — Global Level-5 COMPLETE: 2 batches named all 60
Level-5 functions (`named` 1,163 -> **1,223**), L5 queue 60 -> 0

Finding 75 closed Level-4 and delivered L5 batch 1 (36). This finding
finishes Level 5 with batch 2 (24): 7 truncated bodies full-dumped
(`dump_full.py`).

| batch | named after | L5 queue after | highlights |
|---|---|---|---|
| l5a (f75) | 1,199 | 24 | op_dispatch_far_entry (in=30), tail_bridge_overlay_load (in=302, cd=50,839), group_children_release, slot2/slot3 handle subsystem, record_script_exec trio, terrain_attr_scan_draw_a/b, 4 object_*_draw variants, pos_step_chain_engine + pos_move_angle_step |
| l5b (this) | **1,223** | **0** | **`startup_overlay_init`** (from `start`: DOS>=3 mode, C1F patch scan, block move, preload of every loaded-flag overlay row), **`slot3_tile_record_load`** + **`slot3_record_publish`** / **`op_slot_release`** (the 3052/3054 slot producer-consumer pair), **`farobj_cmd_sweep`** (third member of the sweep family), `handle_release_all` + `handle_query_onetime` + `handle_build_8f/75_block` (handle lifecycle), `r17_menu_event_loop` (5-row menu, 5-module RTLink callers r22-r26) + `r17_router_event_loop` (hands off to r69_ui_event_loop), `hud_value_format_draw` (value/TIME formatter through self-patched draw fn ptrs), `entity_proj_depth_class` (distance bands 0x100/400/800/0), `farobj_height_gate_wrap`, the strip-draw family `rot_segment_strip_draw` / `view_rect_strip_draw` / `sprite_rect_strip_draw` / `cross_strip_draw`, `farobj_flag_record_push`, `op26400_table_scatter`, `classify_fill_patched`, `r06_mode_tick_wrapper`, `scroll_scale_lookup`, `handle_seg_publish` |

### MILESTONE

**Levels 0, 1, 2, 3, 4 AND 5 are all complete.** `named` = **1,223**;
global `naming_queue` = **408** across Levels 6..21 (L6=60 next, then
L19=206 giant SCC); L5 residue = **11 orphans, 0 thunks, 0 other**.

### Gates (all green)

`naming.py check` **1,225** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,223/1,223
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 32) | ~4 h | **Finding 76: Global Level-5 "
       "COMPLETE -- batch 2 (24) named all 60 L5 fns, `named` 1,199 -> "
       "**1,223**, L5 queue 60 -> 0 (11 orphans, 0 thunks, 0 other).** 7 "
       "truncated bodies full-dumped. Highlights: **startup_overlay_init** "
       "(from `start`: DOS>=3 open mode, C1F patch scan, block move, "
       "preloads every loaded-flag overlay row), **slot3_tile_record_load** "
       "(32x32 coord -> page+cell -> EMS/op read -> record at 162+8idx + "
       "handle at idx+150) with its producer/consumer pair "
       "**slot3_record_publish**/**op_slot_release** (3052/3054 slots, same "
       "caller sub_137E0), **farobj_cmd_sweep** (the 4B1/bit1 third sweep "
       "sibling of farobj_slot_sweep and farobj_entity_accum_sweep), "
       "handle lifecycle (handle_release_all, handle_query_onetime, "
       "handle_build_8f/75_block, handle_seg_publish), **r17_menu_event_loop** "
       "(5-row menu with r17_state_zero transitions, callers r22-r26) + "
       "r17_router_event_loop (event 0x4A -> r69_ui_event_loop), "
       "hud_value_format_draw (value/TIME via self-patched draw ptrs), "
       "entity_proj_depth_class (bands 100/400/800/0), farobj_height_gate_"
       "wrap (tail into farobj_pos_wrap_update), strip family (rot/view/"
       "sprite/cross), farobj_flag_record_push, op26400_table_scatter, "
       "classify_fill_patched, r06_mode_tick_wrapper, scroll_scale_lookup. "
       "**MILESTONE: Levels 0-5 all complete**; queue 432 -> 408 (L6=60, "
       "L19=206). **Gates green:** check 1,225, verify_rebuild faithful, "
       "verify_idb INTACT, read-back 1223/1223+2/2. |")

STATUS_PARA = (
    "**Global Level-5 COMPLETE (finding 76):** batch 2 named the final 24 "
    "Level-5 functions (`named` 1,199 → **1,223**), **L5 `naming_queue` 60 → "
    "0** (residue = 11 orphans, 0 thunks, 0 other). Headlines: "
    "**`startup_overlay_init`** (called from `start` beside "
    "`startup_arena_init`: DOS>=3 open mode, C1F patch scan, mem block move, "
    "preloads every loaded-flag overlay row through `overlay_segment_load`), "
    "the slot3 trio **`slot3_tile_record_load`** / **`slot3_record_publish`** "
    "/ **`op_slot_release`** (the 3052/3054 slot pair's producer and "
    "consumer, same caller), **`farobj_cmd_sweep`** (completing the three-"
    "table sweep family), the handle lifecycle set, **`r17_menu_event_loop`** "
    "(five-row menu across five RTLink modules) and `r17_router_event_loop`, "
    "`hud_value_format_draw`, `entity_proj_depth_class` and the four strip-"
    "draw variants. **Levels 0–5 are now all complete**; global "
    "naming_queue = **408** across Levels 6–21 (L6 = 60 next, L19 = 206 "
    "giant SCC). **Gates all green** (check 1,225, verify_rebuild faithful, "
    "verify_idb INTACT, read-back **1,223/1,223 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 5 COMPLETE (finding 76):** 2 batches (36 in f75 + 24",
    "  here) named all 60 L5 fns, `named` **1163 -> 1223**, **L5 queue 60 ->",
    "  0** (11 orphans, 0 thunks, 0 other). Highlights: startup_overlay_init",
    "  (start-callee preload loop), slot3 load/publish/release trio,",
    "  farobj_cmd_sweep, handle lifecycle, r17_menu/router_event_loop,",
    "  hud_value_format_draw, entity_proj_depth_class, 4 strip-draw variants.",
    "  All 4 gates green (check 1225, verify_rebuild faithful, verify_idb",
    "  INTACT, read-back 1223/1223+2/2).",
    "- **Next: Global Level-6** (60 targets, top by dyn/cd/in) -- global",
    "  queue 408 across L6..L21 (L6=60, L7=21, ..., L19=206 giant SCC,",
    "  L20=25, L21=2).",
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
if "## 2026-10-19 76" in raw:
    print("findings_log: 76 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 76 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 32" in raw:
    print("time_log: 32 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 31" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 32 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-5 COMPLETE (finding 76)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f76 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 5 COMPLETE (finding 76)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f76 status (%d bytes)" % len(block))