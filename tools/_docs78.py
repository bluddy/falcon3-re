"""Record finding 78 (Global Level-7 COMPLETE: 21 named,
L7 queue 21 -> 0, named 1283 -> 1304) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 78 — Global Level-7 COMPLETE: 21 named, L7 queue 21 -> 0
(`named` 1,283 -> **1,304**)

Finding 77 closed Level 6. This finding delivers all of Level 7 in a
single batch (21 fns; 4 truncated bodies -- sub_47A9B, sub_12D2F,
sub_2142E, sub_36347 -- were full-dumped via `dump_full.py`). The new
generic `tools/_extract_level.py` + `tools/_trunc_check.py` (from f77)
sped up the queue/dump/verify loop.

### Highlights

| function | what it is |
|---|---|
| `farobj_record_step` | **hottest fn in the queue** (caller_dyn = 338,048) -- the per-record farobj driver behind `view_projection`: resolves the record (or the 7B0E:3052 slot handle), walks the 8-stride threshold tables, decodes the flag word into the 1F73x direction globals, scales [di+20] and dispatches one of the 14 object op handlers via off_26426 |
| `slot2_map_window_update` | incremental slot2 5x5 window updater (1-cell move = one-row/one-column refresh through a fresh handle, bigger jump = full `slot2_map_window_read`); hot behind `entity_update_batch` (cd = 11,109) |
| slot3 windowing | `slot3_tile3x3_load` (full 3x3 neighbourhood reload + mask rebuild) with the three incremental siblings `slot3_window_scroll_left` / `slot3_window_scroll_right` (3-slot queue shift + new column load via the shared loc_1372D loader) and `slot3_window_reload_col1` (centre-column refresh, no scroll) |
| `r32_hud_phase_dispatch` | 5-entry R32 HUD cluster: 6847A phase routing into `hud_rowlist_panel_draw` internals, timer countdown + per-record `rect_clip_then_dispatch_2209c` ops 0xE/4, plus the 54AF scale/matrix/projection helpers |
| keyboard | `kb_preset_table_load` (op6 open, scatter all 35 presets via `kb_preset_record_scatter`), `kb_stream_open_write_close` (wait, op6/open, `kb_stream_far_write`, op8 close), `kb_record_load_far` + `op_cstring_bank_far_entry` (far trampolines) |
| audio | `adlib_synth_init` (OPL init: zero regs 1..0xF5, 0x2000 period tables, widen/mode3/seq-clamp/mode20), `channel_mode_cmd_dispatch` (mode 1 program write / 2 widen / 3 clamp), `channel_list_register_batch` (cli list-register with unlink rollback + volume/HW publish) |
| entity/UI | `entity_slot_pair_create` (2 stream words -> 2 `entity_slot_create`), `entity_record_build_gate` (709F table build -> far 2C1CB), `terrain_point_label_draw` (projected point -> view-rect strip draw + 9-char marker), `record_script_field14_setup` / `record_script_field0c_setup` (terrain-delta reveal + coord dispatch for the 48BA entity fields), `hud_data_panel_gate_draw` (quad-clear + `hud_data_panel_draw` dispatch shim), `slot2_map_window_refresh` (gate byte + optional re-read) |

### MILESTONE

**Levels 0, 1, 2, 3, 4, 5, 6 AND 7 are all complete.** `named` =
**1,304**; global `naming_queue` = **327** across Levels 8..22 (L8=13
next, then L19=206 giant SCC); L7 residue = 3 unnamed (0 queue:
thunks/orphans), **0 to_name**.

### Gates (all green)

`naming.py check` **1,306** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,304/1,304
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 34) | ~2 h | **Finding 78: Global Level-7 "
       "COMPLETE -- 21 named, `named` 1,283 -> **1,304**, L7 queue 21 -> "
       "0.** 4 truncated bodies full-dumped. Highlights: farobj_record_step "
       "(hottest queue fn, cd=338048, object op dispatch), slot2_map_window_update "
       "(incremental row/col refresh), slot3 windowing triad (tile3x3_load + "
       "scroll_left/right + reload_col1), r32_hud_phase_dispatch, keyboard "
       "(kb_preset_table_load, kb_stream_open_write_close, kb_record_load_far, "
       "op_cstring_bank_far_entry), audio (adlib_synth_init, "
       "channel_mode_cmd_dispatch, channel_list_register_batch), entity "
       "(slot_pair_create, record_build_gate), terrain_point_label_draw, "
       "record_script field0c/14_setup, hud_data_panel_gate_draw, "
       "slot2_map_window_refresh. **MILESTONE: Levels 0-7 all complete**; "
       "queue 348 -> 327 (L8=13, L19=206). **Gates green:** check 1,306, "
       "verify_rebuild faithful, verify_idb INTACT, read-back "
       "1304/1304+2/2. |")

STATUS_PARA = (
    "**Global Level-7 COMPLETE (finding 78):** 21 Level-7 functions named "
    "(`named` 1,283 → **1,304**), **L7 `naming_queue` 21 → 0**. Headlines: "
    "**`farobj_record_step`** (the hottest fn in the whole queue at "
    "caller_dyn 338,048 -- the per-record farobj driver behind "
    "`view_projection`, decoding flags into the 1F73x globals and "
    "dispatching the 14 object op handlers), **`slot2_map_window_update`** "
    "(the incremental 1-cell row/column refresh behind "
    "`entity_update_batch`), the slot3 windowing quartet "
    "(`slot3_tile3x3_load` + `slot3_window_scroll_left`/`_right` + "
    "`slot3_window_reload_col1`), `r32_hud_phase_dispatch`, the keyboard "
    "trio (`kb_preset_table_load`, `kb_stream_open_write_close`, far "
    "trampolines), audio (`adlib_synth_init`, `channel_mode_cmd_dispatch`, "
    "`channel_list_register_batch`), and `terrain_point_label_draw`. "
    "**Levels 0–7 are now all complete**; global naming_queue = **327** "
    "across Levels 8–22 (L8 = 13 next, L19 = 206 giant SCC). **Gates all "
    "green** (check 1,306, verify_rebuild faithful, verify_idb INTACT, "
    "read-back **1,304/1,304 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 7 COMPLETE (finding 78):** 21 named, `named`",
    "  **1283 -> 1304**, **L7 queue 21 -> 0**. Highlights: farobj_record_step",
    "  (hottest queue fn, cd=338048), slot2_map_window_update, slot3",
    "  windowing triad (tile3x3_load + scroll_left/right + reload_col1),",
    "  r32_hud_phase_dispatch, kb_preset_table_load,",
    "  kb_stream_open_write_close, op_cstring_bank_far_entry,",
    "  kb_record_load_far, adlib_synth_init, channel_mode_cmd_dispatch,",
    "  channel_list_register_batch, entity_slot_pair_create,",
    "  entity_record_build_gate, terrain_point_label_draw, record_script",
    "  field0c/14_setup, hud_data_panel_gate_draw, slot2_map_window_refresh.",
    "  All 4 gates green (check 1306, verify_rebuild faithful, verify_idb",
    "  INTACT, read-back 1304/1304+2/2).",
    "- **Next: Global Level-8** (13 targets) -- global queue 327 across",
    "  L8..L22 (L8=13, L9=7, L10=11, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 78" in raw:
    print("findings_log: 78 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 78 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 34" in raw:
    print("time_log: 34 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 33" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 34 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-7 COMPLETE (finding 78)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f78 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 7 COMPLETE (finding 78)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f78 status (%d bytes)" % len(block))
