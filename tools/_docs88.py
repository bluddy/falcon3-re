"""Record finding 88 (L19 Batch 2 of 6: 35 named, L19 queue 171 -> 136,
named 1433 -> 1468) -- docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 88 — L19 Batch 2 of 6: 35 named, L19 queue 171 -> 136
(`named` 1,433 -> **1,468**)

Second slice of the giant Level-19 SCC. 35 of 171 named from
`level19_batch2.txt` (6,794 ln). Highlights:

**`far_mode_event_dispatch`** (sub_33443, 2688B, **137 callees — most of
any L19 fn**): the master FAR mode/key/event switchboard. Multi-entry,
dispatching on xlat_mask_setbit_47e codes to dozens of retf handler stubs;
fans out to mouse_buttons_test, hud/map/store/view stacks, module/EMS.
Its callers include main_frame_update_loop.

**`viewobj_screen_project_step`** (sub_38CF3, 2284B, in=15): the big
object screen-projection pass — fixed-point imul against ds:1350/1352/
1354/1356 scale factors, self-modifying cs:locret_377E1/loc_377DC, with
farobj_rect_ratio_build + obj_fuel_exhaust_step + tile_quad_sample.

**`game_frame_pipeline_step`** (sub_2FD42, 387B, in=7): the core per-frame
pipeline under main_frame_update_loop — joystick_poll +
terrain_frame_update_driver + entity_update_batch + farobj_sort_and_step
+ viewobj scans + hud_readout_render + aircraft_motion_step.

**`farobj_rect_state_setup`** (sub_327BE, 499B, **in=24 — most callers in
the batch**): farobj rect compute/state setup hub (farobj_rect_compute_
store, state_farptr_dxax_store, angle_adjusted_copy); called by most L19
step fns.

**Other named:** farobj_move_accumulate_step (1706B), farobj_record_ops_
exec (1365B, in=10), tile_grid_scan_step (1161B), ems_entity_slot_script
(987B), farobj_cmd_accum_sweep (865B), hud_map_overlay_step (718B),
record_script_coord_entry (604B), key_event_mode_gate (452B),
view_pos_matrix_step (418B), viewport_bounds_setup (356B),
tile_strip_project_draw (331B), farobj_record_flag_ops (319B),
ems_opstream_buffer_append (286B), nav_table_entry_resolve (270B),
hud_object_text_format (256B), entity_slot_cycle_select (227B),
key_mode_switch_step (206B), hud_track_project_draw (197B), farobj_slot_
scan_cycle (181B), palette_delta_blend (169B), menu_list_script_step
(152B), entity_mask_bitstep (130B), mode_audio_state_step (121B),
viewvec_loop_project (99B), terrain_menu_triple_step (82B), hud_project_
gate_draw (70B), farobj_range_bounds_test (49B), terrain_vm_sweep_kick
(38B), mode_byte_dispatch (27B), menu_page_jump_stub (14B),
key_mode_switch_tramp (5B).

### Gates (all green)

`naming.py check` **1,470** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,468/1,468
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 44) | ~2 h | **Finding 88: L19 Batch 2 of 6 "
       "-- 35 named, `named` 1,433 -> **1,468**, L19 queue 171 -> 136**. "
       "Headlines: **far_mode_event_dispatch** (sub_33443, 137 callees -- "
       "master FAR mode/key/event switchboard), "
       "**viewobj_screen_project_step** (2284B, fixed-point screen "
       "projection), **game_frame_pipeline_step** (core per-frame "
       "pipeline under main_frame_update_loop), **farobj_rect_state_"
       "setup** (in=24, most callers). Queue 198 -> 163. **Gates green:** "
       "check 1,470, verify_rebuild faithful, verify_idb INTACT, "
       "read-back 1468/1468+2/2. |")

STATUS_PARA = (
    "**L19 Batch 2/6 (finding 88):** 35 functions named (`named` 1,433 → "
    "**1,468**), **L19 `naming_queue` 171 → 136**. Headlines: "
    "**far_mode_event_dispatch** (sub_33443, 137 callees — the master FAR "
    "mode/key/event switchboard dispatching to dozens of retf handler "
    "stubs); **viewobj_screen_project_step** (2284B fixed-point "
    "screen-projection pass); **game_frame_pipeline_step** (core per-frame "
    "pipeline: joystick_poll + terrain_frame_update_driver + "
    "entity_update_batch + farobj_sort_and_step); **farobj_rect_state_"
    "setup** (in=24, the most-called helper in the batch). "
    "**Gates green:** check **1,470**, verify_rebuild **faithful**, "
    "verify_idb **INTACT**, read-back **1,468/1,468 + 2/2**. Remaining: "
    "L19 batches 3–6 (136), then L20 (25), L21 (2).\n\n"
)

OPEN_NEW = ("- L19 batches 3–6 (136 fns remaining of the giant SCC; "
            "`level19_batch3.txt`..`batch6.txt` ready) — continue one "
            "finding per batch; then L20 (25) + L21 (2) to hit queue 0.\n")


def main():
    fl = io.open("docs/findings_log.md", encoding="utf-8", newline="")
    raw = fl.read(); fl.close()
    if "## 2026-10-19 88" not in raw:
        i = raw.rindex(FOOT)
        io.open("docs/findings_log.md", "w", encoding="utf-8",
                newline="").write(raw[:i] + ENTRY + raw[i:])
        print("findings_log.md: appended F88 entry")
    else:
        print("findings_log.md: F88 already present")

    tl = io.open("docs/time_log.yaml", encoding="utf-8", newline="")
    raw = tl.read(); tl.close()
    if "session 44" not in raw:
        lines = raw.split("\r\n")
        for j, ln in enumerate(lines):
            if "session 43" in ln:
                lines.insert(j + 1, ROW)
                break
        io.open("docs/time_log.yaml", "w", encoding="utf-8",
                newline="").write("\r\n".join(lines))
        print("time_log.yaml: inserted session 44 row after 43")
    else:
        print("time_log.yaml: session 44 already present")

    st = io.open("status.md", encoding="utf-8", newline="")
    raw = st.read(); st.close()
    if "L19 Batch 2/6" not in raw:
        i = raw.rindex("**Still outstanding:**")
        io.open("status.md", "w", encoding="utf-8", newline="").write(
            raw[:i] + STATUS_PARA + raw[i:])
        print("status.md: inserted F88 STATUS_PARA")
    else:
        print("status.md: F88 already present")

    oi = io.open("docs/open_items.md", encoding="utf-8", newline="")
    raw = oi.read(); oi.close()
    if "L19 batches 3" not in raw:
        if not raw.endswith("\r\n"):
            raw += "\r\n"
        raw += OPEN_NEW.rstrip("\r\n") + "\r\n"
        io.open("docs/open_items.md", "w", encoding="utf-8",
                newline="").write(raw)
        print("docs/open_items.md: appended OPEN_NEW")
    else:
        print("docs/open_items.md: OPEN_NEW already present")


if __name__ == "__main__":
    main()
