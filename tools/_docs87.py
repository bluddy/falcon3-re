"""Record finding 87 (L19 Batch 1 of 6: 35 named, L19 queue 206 -> 171,
named 1398 -> 1433) -- docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 87 — L19 Batch 1 of 6: 35 named, L19 queue 206 -> 171
(`named` 1,398 -> **1,433**)

First slice of the giant Level-19 SCC (254 nodes). 35 of 206 named from
`level19_batch1.txt` (7,176 ln; 25 truncated → full dump). Highlights:

**THE MAIN GAME LOOP — `main_frame_update_loop`** (sub_31319, 257B, **45
callees — most of any L19 fn**). Mode-gated entry (ds:23Bh),
flag_bits_dispatch, then a full frame: farobj_sweep_all +
farobj_slot_step_spawn + hud_data_panel_draw + vga_dac_palette_upload +
tick_rate_compute + dgroup_cycle_step_438 + dgroup_cycle_435_436; si=32h
→ state_table_apply_71c1; then the indirect tail `mov bx,4A7h; call
dword ptr [bx]`. Callers: sub_33443, sub_4111F.

**`ui_loadout_menu_enter`** (sub_683C5, 4169B, in=55 — biggest by size
and fan-in): the modal menu state machine; builds 7894h slot records,
pushes choice callbacks, tail-jumps into sub_66E62 and friends.
Siblings: **`ui_slot_list_mode_enter`** (1393B), **`ui_slot_record_init`**
(232B, in=6 — writes type bytes 1Eh/1Eh/1 into up-to-6 7894h records at
17h stride, then unpacks via **`entity_bitpack_unpack`** (275B, five
bit-plane passes), **`menu_page_draw_step`** (122B — sets 7A313 flag,
paints a label via sub_3A29C, falls into the menu body),
**`menu_event_dispatch`** (360B), **`menu_choice_tail_dispatch`** (9B —
zero arg falls to sub_67BAF else tail-jumps into the menu choice
handler), **`ui_slot_count_tally`** (744B — counts 602Eh slot records by
type and raises the 7A312/7A319/7A30E presence flags).

**EMS bootstrap path:** **`ems_slot_bootstrap_step`** (sub_30EBE, 83B,
**15 callees — EMS install in one function**: slot2/3 alloc+copy,
ems_alloc_execute_43h, data blob invoke, mem_unmap_all,
ems_state_bootstrap_2e100). Its data payload: **`data_farcall_script_blob`**
(sub_16BE48, 321B — **NOT real code**, an embedded far-call init script
of `call far sub_2C58B` + constant args). Helpers:
**`ems_farptr_table_init`** (104B — fills the 4E5C0 dispatch words),
**`ems_terrain_pos_gate`** (135B).

**View / farobj stack:** **`map_view_entity_project`** (198B — 9-word
transform copy → angle_xy_far + angle_aux_far → map_view_project_pipeline),
**`view_terrain_frame_step`** (460B — wraps map_view_entity_project +
farobj_snapshot_scan), **`farobj_snapshot_scan`** (186B — picks the first
active far_obj from a table snapshot, self-modifies cs:loc_346EA),
**`far_obj_visibility_gate`** (291B — mode/state gates +
far_obj_field_call type check + fixed-point distance; shares code with
sub_386F2 via tail-jumps), **`tile_object_interpreter`** (1855B — tile
opcodes → 29h-byte entity records, per-type fixed-point shifts),
**`tile_object_init_opstream`** (394B), **`entity_spawn_from_tile`**
(508B), **`entity_build_dispatch`** (213B),
**`farobj_record_clear_fields`** (333B — clears 7894h fields at 82h
stride).

**Simulation:** **`aircraft_slot_cycle_step`** (153B — 40 slots × 18h,
aircraft_motion_step + fixed_matrix_proj_factor per slot),
**`store_fall_sim_step`** (1165B — 40-slot fall: velocity decay + ground
impact), **`store_impact_step`** (169B — velocity clamp [28h,FFh] +
sprite_clip + altitude scale), **`store_cmd_interpreter`** (987B —
dispatches via the 4E5C0 far-function table), **`steerpoint_scan_update`**
(895B — 16-object scan advancing the 4A83/4AC2/4AC3/4AC4 steerpoint
state machine), **`steerpoint_state_gate`** (20B),
**`target_cycle_scan`** (620B), **`hud_track_strip_pipeline`** (2772B —
10-slot 1Ah-byte track records → terrain/sprite strips),
**`hud_data_panel_slot_mgr`** (424B), **`view_mode_bits_step`** (70B),
**`mode_state_dispatch`** (28B — jump table at ds:392h),
**`farobj_selection_gate`** (49B), **`farobj_flag_gate_check`** (42B).

### Gates (all green)

`naming.py check` **1,435** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,433/1,433
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 43) | ~2 h | **Finding 87: L19 Batch 1 of 6 "
       "-- 35 named, `named` 1,398 -> **1,433**, L19 queue 206 -> 171** "
       "(of the 254-node giant SCC; 25 truncated -> full dump). "
       "Headlines: **main_frame_update_loop** (sub_31319, 45 callees -- "
       "THE main game loop), **ui_loadout_menu_enter** (4169B, in=55 "
       "modal menu state machine) + 6 menu siblings, "
       "**ems_slot_bootstrap_step** (15-callee EMS install) + "
       "data_farcall_script_blob + ems_farptr_table_init + "
       "ems_terrain_pos_gate, **tile_object_interpreter** (1855B), "
       "**entity_bitpack_unpack**, **map_view_entity_project**, "
       "**farobj_snapshot_scan**, **aircraft_slot_cycle_step**, "
       "**steerpoint_scan_update**, **hud_track_strip_pipeline**, "
       "**store_fall_sim_step**, **store_impact_step**, "
       "**store_cmd_interpreter**. Queue 233 -> 198. **Gates green:** "
       "check 1,435, verify_rebuild faithful, verify_idb INTACT, "
       "read-back 1433/1433+2/2. |")

STATUS_PARA = (
    "**L19 Batch 1/6 (finding 87):** 35 functions named (`named` 1,398 → "
    "**1,433**), **L19 `naming_queue` 206 → 171**. Headlines: "
    "**main_frame_update_loop** (sub_31319, 45 callees — THE main game "
    "loop: full sweep/spawn/HUD/palette/tick-rate pass then the "
    "ds:4A7h indirect tail); the **ui_loadout_menu_enter** modal menu "
    "state machine (4169B, in=55) plus 6 menu siblings "
    "(ui_slot_list_mode_enter, ui_slot_record_init, entity_bitpack_unpack, "
    "menu_page_draw_step, menu_event_dispatch, menu_choice_tail_dispatch, "
    "ui_slot_count_tally); the EMS bootstrap path "
    "(**ems_slot_bootstrap_step** 15 callees + data_farcall_script_blob + "
    "ems_farptr_table_init + ems_terrain_pos_gate); the view/farobj stack "
    "(map_view_entity_project, view_terrain_frame_step, "
    "farobj_snapshot_scan, far_obj_visibility_gate, "
    "tile_object_interpreter 1855B, entity_bitpack_unpack); and the "
    "simulation core (aircraft_slot_cycle_step, store_fall_sim_step, "
    "store_impact_step, store_cmd_interpreter, steerpoint_scan_update, "
    "hud_track_strip_pipeline). **Gates green:** check **1,435**, "
    "verify_rebuild **faithful**, verify_idb **INTACT**, read-back "
    "**1,433/1,433 + 2/2**. Remaining: L19 batches 2–6 (171), then "
    "L20 (25), L21 (2).\n\n"
)

OPEN_NEW = ("- [ ] L19 batches 2–6 (171 fns remaining of the 254-node "
            "giant SCC; `level19_batch2.txt`..`batch6.txt` ready) — "
            "continue one finding per batch; then L20 (25) + L21 (2) "
            "to hit queue 0.\n")


def main():
    fl = io.open("docs/findings_log.md", encoding="utf-8", newline="")
    raw = fl.read(); fl.close()
    if "## 2026-10-19 87" not in raw:
        i = raw.rindex(FOOT)
        io.open("docs/findings_log.md", "w", encoding="utf-8",
                newline="").write(raw[:i] + ENTRY + raw[i:])
        print("findings_log.md: appended F87 entry")
    else:
        print("findings_log.md: F87 already present")

    tl = io.open("docs/time_log.yaml", encoding="utf-8", newline="")
    raw = tl.read(); tl.close()
    if "session 43" not in raw:
        lines = raw.split("\r\n")
        for j, ln in enumerate(lines):
            if "session 42" in ln:
                lines.insert(j + 1, ROW)
                break
        io.open("docs/time_log.yaml", "w", encoding="utf-8",
                newline="").write("\r\n".join(lines))
        print("time_log.yaml: inserted session 43 row after 42")
    else:
        print("time_log.yaml: session 43 already present")

    st = io.open("status.md", encoding="utf-8", newline="")
    raw = st.read(); st.close()
    if "L19 Batch 1/6" not in raw:
        i = raw.rindex("**Still outstanding:**")
        io.open("status.md", "w", encoding="utf-8", newline="").write(
            raw[:i] + STATUS_PARA + raw[i:])
        print("status.md: inserted F87 STATUS_PARA")
    else:
        print("status.md: F87 already present")

    oi = io.open("docs/open_items.md", encoding="utf-8", newline="")
    raw = oi.read(); oi.close()
    if "L19 batches 2" not in raw:
        lines = raw.split("\r\n")
        # insert after the last existing "- [ ]" line
        last = max(j for j, ln in enumerate(lines) if ln.startswith("- [ ]"))
        lines.insert(last + 1, OPEN_NEW.rstrip("\r\n"))
        io.open("docs/open_items.md", "w", encoding="utf-8",
                newline="").write("\r\n".join(lines))
        print("docs/open_items.md: appended OPEN_NEW")
    else:
        print("docs/open_items.md: OPEN_NEW already present")


if __name__ == "__main__":
    main()
