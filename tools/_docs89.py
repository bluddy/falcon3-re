"""Record finding 89 (L19 Batch 3 of 6: 34 named, L19 queue 136 -> 102,
named 1468 -> 1502) -- docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 89 — L19 Batch 3 of 6: 34 named, L19 queue 136 -> 102
(`named` 1,468 -> **1,502**)

Third slice of the giant Level-19 SCC. 34 of 136 named from
`level19_batch3.txt` (6,436 ln). Highlights:

**`farobj_behavior_dispatch_step`** (sub_3CE92, 2580B, **in=19 — the
batch-3 hub**): master farobj entity behavior/AI step. Many entry points;
3334h tile-wrap on the si+31/32/33/35 grid fields; far_obj_field_call +
farobj_field_set type-3 distance thresholds selecting the 3013h/304Ch/
3065h/307Fh/3259h behavior tables; [si+0Bh] multi-bit mode gates (bits
1/2/3/4/8/10h/40h) routing speed/altitude clamp branches via funcs_4E5C0.

**`ui_menu_page_setup`** (sub_6A5BD, 2204B, in=5) +
**`ui_menu_panel_init`** (sub_66E62, 1365B, in=17): the two menu
foundations. Page setup pushes a farobj_arg_thunk arg block (9,35h,0Bh,
4,19h), clears the 7894h:79B66/79B68 selection fields, and runs
current_item_check. Panel init writes the 4FC2h:4FD5E/4FD72/4FD46/4FD48
slot fields and farptr_lds_invoke — ui_loadout_menu_enter (F87) tail-
jumps into it. Siblings: **`ui_slot_record_fill`** (sub_6798C, 327B —
fills 7894h:79E60 fields 2BD6h..2BDBh with the E0h/2Eh/1Eh type pattern),
**`menu_pending_task_step`** (sub_67AE1, 197B — pending_task_run +
vga_dac_palette_upload), **`ui_slot_scan_step`** (r30_e77, R30 overlay —
steerpoint_scan_update + ui_slot_record_init).

**View / farobj stack:** **`farobj_view_project_step`** (sub_3EEDB,
1485B, in=11 — viewvec_loop_project + viewvec3_project_track_max +
palette_delta_blend; callers include the main loop and
far_mode_event_dispatch); **`farobj_slot_update_driver`** (sub_3C1BD,
821B — loads funcs_4E5C0 from 2F64h:37h/39h then walks 16 slots at 386Fh
stride 5Ch); **`farobj_pos_move_angle_step`** (sub_4AEC4, 1146B);
**`farobj_range_slot_init`** (sub_41646 — calls hud_track_strip_pipeline
+ obj_range_slot_init); **`record_bitpack_pack`** (sub_48292, 284B — the
pack half of entity_bitpack_unpack, F87); **`farobj_attr_apply_step`**
(sub_3FD89 — farobj_attr_table_lookup + fuel/range dec [di+0B0h]/sub
[di+26h]); **`hud_track_gate_draw`** (sub_42640, 70B — parallel to
hud_project_gate_draw from F88).

**HUD / terrain:** **`hud_rowlist_timer_step`** (sub_47BDE, 960B — 16
4-byte timer rows over 63FD:1940h → hud_rowlist_panel_draw);
**`terrain_angle_time_step`** (sub_37818, 498B — int 21h/2Ch time-of-day
→ 5A0h wrap angle); **`tile_sprite_strip_project`** (sub_39748, 179B);
**`terrain_vm_flag_gate`** / **`terrain_vm_blend_apply`** (sub_4F8BC /
sub_4F7B8 — the 7A32:8505x terrain-VM pair beside F88's
terrain_vm_sweep_kick); **`angle_fixed_rotate_apply`** (sub_4FEB5 —
fixed-point sin/cos rotate via ds:0EF5h/0EF7h).

### Gates (all green)

`naming.py check` **1,504** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,502/1,502
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 44) | ~2 h | **Finding 89: L19 Batch 3 of 6 "
       "-- 34 named, `named` 1,468 -> **1,502**, L19 queue 136 -> 102**. "
       "Headlines: **farobj_behavior_dispatch_step** (sub_3CE92, in=19 "
       "master farobj behavior/AI hub), the menu pair "
       "**ui_menu_page_setup** + **ui_menu_panel_init** (in=17; "
       "ui_loadout_menu_enter tail-jumps here) + 3 menu siblings, "
       "**farobj_view_project_step** (in=11), **farobj_slot_update_"
       "driver** (16-slot walk), **record_bitpack_pack** (pack half of "
       "entity_bitpack_unpack), **hud_rowlist_timer_step**, terrain-VM "
       "pair. Queue 163 -> 129. **Gates green:** check 1,504, "
       "verify_rebuild faithful, verify_idb INTACT, read-back "
       "1502/1502+2/2. |")

STATUS_PARA = (
    "**L19 Batch 3/6 (finding 89):** 34 functions named (`named` 1,468 → "
    "**1,502**), **L19 `naming_queue` 136 → 102**. Headlines: "
    "**farobj_behavior_dispatch_step** (sub_3CE92, in=19 — the master "
    "farobj entity behavior/AI step routing distance-tier and [si+0Bh] "
    "mode-gate branches); the menu foundations **ui_menu_page_setup** "
    "(2204B) + **ui_menu_panel_init** (in=17; ui_loadout_menu_enter "
    "tail-jumps here) plus 3 siblings (ui_slot_record_fill, "
    "menu_pending_task_step, ui_slot_scan_step); **farobj_view_project_"
    "step** (in=11) + **farobj_slot_update_driver** (16-slot walk); "
    "**record_bitpack_pack** (the pack half of F87's "
    "entity_bitpack_unpack); **hud_rowlist_timer_step**; and the "
    "terrain-VM pair (terrain_vm_flag_gate + terrain_vm_blend_apply) "
    "beside F88's terrain_vm_sweep_kick. **Gates green:** check "
    "**1,504**, verify_rebuild **faithful**, verify_idb **INTACT**, "
    "read-back **1,502/1,502 + 2/2**. Remaining: L19 batches 4–6 (102), "
    "then L20 (25), L21 (2).\n\n"
)

OPEN_NEW = ("- L19 batches 4–6 (102 fns remaining of the giant SCC; "
            "`level19_batch4.txt`..`batch6.txt` ready) — continue one "
            "finding per batch; then L20 (25) + L21 (2) to hit queue 0.\n")


def main():
    fl = io.open("docs/findings_log.md", encoding="utf-8", newline="")
    raw = fl.read(); fl.close()
    if "## 2026-10-19 89" not in raw:
        i = raw.rindex(FOOT)
        io.open("docs/findings_log.md", "w", encoding="utf-8",
                newline="").write(raw[:i] + ENTRY + raw[i:])
        print("findings_log.md: appended F89 entry")
    else:
        print("findings_log.md: F89 already present")

    tl = io.open("docs/time_log.yaml", encoding="utf-8", newline="")
    raw = tl.read(); tl.close()
    if "Finding 89" not in raw:
        lines = raw.split("\r\n")
        for j, ln in enumerate(lines):
            if "Finding 88" in ln:
                lines.insert(j + 1, ROW)
                break
        io.open("docs/time_log.yaml", "w", encoding="utf-8",
                newline="").write("\r\n".join(lines))
        print("time_log.yaml: inserted Finding 89 row after 88")
    else:
        print("time_log.yaml: Finding 89 already present")

    st = io.open("status.md", encoding="utf-8", newline="")
    raw = st.read(); st.close()
    if "L19 Batch 3/6" not in raw:
        i = raw.rindex("**Still outstanding:**")
        io.open("status.md", "w", encoding="utf-8", newline="").write(
            raw[:i] + STATUS_PARA + raw[i:])
        print("status.md: inserted F89 STATUS_PARA")
    else:
        print("status.md: F89 already present")

    oi = io.open("docs/open_items.md", encoding="utf-8", newline="")
    raw = oi.read(); oi.close()
    if "L19 batches 4" not in raw:
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
