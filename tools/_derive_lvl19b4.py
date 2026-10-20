"""Validate and emit L19 Batch 4 names (34 fns) -> level19_batch4_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "level19_batch4_names.json"

NAMES = {
    "sub_4C19E": ("farobj_queue_drain_dispatch", "high",
        "2500B, in=9. FAR farobj queue drain: class-range dispatch on bx (12h/13h, 33h-37h), pops cs:word_2E10A records at 1Bh stride, inc 2E10E / dec 2E10C, tail-jumps into farobj_slot_update_driver bodies."),
    "sub_45057": ("hud_state_rowtable_step", "high",
        "2142B, in=4 (main loop). Walks 72 (48h) 63FD:0A5h+ table entries calling farobj_tile_copy_resolve bodies; per-entry entity_step_flags + hw_flag_bit2/3_22e ops, cs:word_2E143/2E145 row state."),
    "sub_45976": ("game_setup_staged_init", "high",
        "1462B, in=1 (sub_3001E). Staged game setup: r08_farptr_load_thunk gate, 6x game_setup_staged_step loop with ds:44AAh stage counter, zeros ds:4892h/4893h/4894h/499Eh/499Fh + sprite_pos_bounce, farobj_field2e_test."),
    "sub_4A7E5": ("mode_record_field_lookup", "medium",
        "1271B, in=9. Retf mode-record field lookup: indexes 65E4h:68h table at 3Ah stride ((ax-65EA2)*3Ah), returns [di+11h]; box_edge_strip_draw/angle bodies; callers incl. ui_loadout_menu_enter + ui_menu_page_setup."),
    "sub_4111F": ("farobj_class_table_entry", "high",
        "1140B, in=12. FAR class table entry: [si+75h] class selects 263Bh or 2A01h table at 2Ah stride, returns [di+2]; farobj_table_snapshot position read (si+50h/52h/54h); sprite_clip + cfg bodies."),
    "sub_3E552": ("farobj_cfg_scan_step", "medium",
        "955B, in=1 (sub_2F6D0). Farobj config scan: farobj_cfg_delta_apply, farobj_rect_state_setup gates cl=6, viewobj_5982_scan100, farobj_cmd_interp tail; [si+0Bh] bit40h gate."),
    "sub_3646B": ("mode_draw_dispatch", "medium",
        "794B, in=2. Mode draw dispatch: ds:704h=0Eh, jump table [bx+70Ch] keyed by ds:44AAh-4, draw_from_struct via dword cs:loc_343E0, int32_to_ascii_short + segment_clip_test bodies."),
    "sub_356A7": ("viewvec_half_add_step", "medium",
        "653B, in=9. Vector half-add step: 4x fixed_vec2_half_add over 44h/83h/B9h record offsets from cs:word_333A2 base; game_setup_variant_5169; callers incl. far_mode_event_dispatch + main loop."),
    "sub_31EBF": ("coord_window_bounds_test", "high",
        "538B, in=5. Coordinate window bounds test: idiv [si]/[si+4] by 4E06h/3031h with sar/rcr halving, then CF set/clear against bx in 60h..E4h and di in 70h..C1h; terrain_menu_field_setup follow-on."),
    "sub_4E90E": ("ems_opstream_table_flush", "high",
        "490B, in=2 (sbi_int8_shutdown_hook, ems_opstream_buffer_append). EMS op-stream flush: inc 709F:70A35, entity_record_table_build + farptr_table_field22_store loop, sub_4DE76 append, ems_opstream_buffer_append; long stream-copy tail."),
    "sub_305E4": ("dgroup_state_cycle_step", "medium",
        "433B, in=2 (far_mode_event_dispatch, sub_3FFEF). DGROUP state cycle: [bx+0CAh] flag test under 54AFh, writes 44F29h/44F2Ah then dgroup_cycle_435_436, returns 44F21h/44F22h; farobj tile stream build + ems_init bodies."),
    "sub_3606C": ("terrain_attr_scan_clamp", "high",
        "400B, in=2. Terrain attr scan+clamp: ds:105Bh gate, table_rec_load_scaled + terrain_attr_scan_draw_a into bbox_clamp (bx=0A0h+6F8h, di=32h+6FAh); sprite_pos_gate_499e/bounce bodies."),
    "sub_359B2": ("view_window_state_clamp", "medium",
        "381B, in=2 (sub_354B1, game_setup_staged_init). View window state clamp: cs_state_copy_es, clamps ax/bx vs 6FCh/700h window, writes 6F8h/6FAh/706h/6F0h; tile_base_opcode_interpreter body."),
    "sub_6760A": ("ui_menu_frame_enter", "medium",
        "346B, in=6 (menu_event_dispatch + 5 far stubs). UI menu frame enter: sets 7894h:78940, copies 602Eh:615B0/615AE->615C0/615BE, vga_dac_palette_upload + pending_task_run + ui_loadout_menu_enter + store_cmd_interpreter."),
    "sub_2F043": ("farobj_config_state_entry", "high",
        "325B, in=7 (incl. game_frame_pipeline_step, farobj_view_project_step). Multi-entry FAR config/state: entry0 returns cs:funcs_4E5C0 low byte; also state_word_2e176_apply + viewvec3_project_track_max + farobj_cfg_delta_apply + farobj_index_resolve_step + hw_flag8505_set + palette_delta_blend."),
    "sub_3A29C": ("hud_track_label_strip", "high",
        "314B, in=8 (steerpoint_scan_update, menus, ui_slot fns). HUD track label strip: es:4AC2h==4 gate, copies [si+8Ch..8Ah]->[si+90h/92h/94h] with 0AABh threshold on [si+79h] bit0, tile_strip_sample_draw at 47D6h."),
    "sub_30882": ("ems_window_load_snapshot", "high",
        "282B, in=6 (ems_slot_bootstrap_step, farobj_record_ops_exec, farobj_slot_update_driver, farobj_behavior_dispatch). EMS window load: ems_map_seg_10233, movsw 1770h words from 5DC0h to 2EE0h + stub_bundle_10d8c + slot2_map_window_load; callers incl. F87/F88/F89 hubs."),
    "sub_41B4E": ("farobj_index_state_swap", "high",
        "268B, in=4 (entity_record_table_ops, ems_entity_slot_script). FAR set/get/swap cs:word_2E104 with 2E102, farobj_table_snapshot on result, 3334h grid idiv with param454_apply_triple tail."),
    "sub_4245B": ("farobj_fuel_apply_step", "medium",
        "248B, in=1 (far_mode_event_dispatch). Farobj fuel apply: farobj_project_transform_write + farobj_attr_table_lookup scaled by [di+0B0h]-2, subs from [di+26h]/[di+5Eh], clamps count to 2."),
    "sub_32453": ("farobj_project_transform_write", "high",
        "216B, in=7 (farobj_rect_state_setup, far_mode_event_dispatch, farobj_behavior_dispatch). Writes pos dx/cx/ax to es:[di+0Ch/0Eh/10h], fixed_matrix_mul + add [si], angle_adjusted_copy; the shared project-transform primitive."),
    "sub_48916": ("entity_timer_row_scan", "medium",
        "204B, in=2 (main-frame pipeline, ui_loadout_menu_enter). Entity timer row scan: dec ds:44CEh by word_2E112, 5-byte stride loop counting ds:44D0h, [si+2] bit tests 44h/28h + xor 4; vec_transform_scale_far body."),
    "sub_32393": ("ui_gauge_panel_draw", "high",
        "192B, in=5 (mode_state_dispatch, farobj_behavior_dispatch). UI gauge panel draw: draw_from_struct x2 on struct slots 2A0h/2ABh + far_cb_gated x5 (2B6h/2C5h/2D8h/2EEh/2F5h) with bx/di params; farobj_single_build_project body."),
    "sub_4E320": ("farobj_cfg_step_control", "medium",
        "177B, in=1 (control_axes_record_write, mutual). Farobj config step control: es=cs:funcs_4E5C0, bx=word_2E10E; toggles cs:word_2E124/2E126/2E128 step flags and off_2E11E/2E120, wraps word_2E10A at word_2E102 bound."),
    "sub_41F7F": ("farobj_window_select_scan", "medium",
        "166B, in=1 (far_mode_event_dispatch). Farobj window select scan: self-modifying cs:loc_346EA picks first active record in word_2E104+55E50 +/-10h window ([si+0Ah] bit0 + [si+30h]!=3 gates)."),
    "sub_3FCF1": ("range_scale_accum_clamp", "high",
        "141B, in=6 (farobj behavior, terrain draw fns). Range scale accumulate: [si+1Dh]-[di+0Ch] distance scaled via 1392h/1394h table into [si+23h], clamped to [di+0DBh]; control_axis_store_step join."),
    "sub_41C5A": ("farobj_index_cycle_advance", "medium",
        "126B, in=1 (far_mode_event_dispatch). Farobj index cycle advance: compares [si+37h]/[si+39h] index tables (self-mod cs:loc_34529), farobj_index_range_check, object_farptr_dispatch al=10h."),
    "sub_307A5": ("control_axes_record_write", "high",
        "118B, in=8 (farobj hubs + farobj_index_resolve_step). Control axes record write: flag_2e125_gate, writes 47Bh x7 words + cs:word_2E137/139 + control_axes_read x2 + control_axis_value + 2E145/147/149 into the record."),
    "sub_30587": ("mode_change_apply_step", "medium",
        "93B, in=1 (main-frame pipeline). Mode change apply: ds:44F39==FFh gate, farobj_state_flag_set (sub_415CE) + cs:byte_343E9 compare, updates ds:48F9A + ds:45B65, far Mode-event dispatch via unk_43BCA."),
    "sub_41CD8": ("farobj_index_decrement_step", "medium",
        "73B, in=1 (far_mode_event_dispatch). Farobj index decrement: [si+39h]-=2 with farobj_index_range_check >=1 guard, object_farptr_dispatch al=16h fallback."),
    "sub_42686": ("hud_track_marker_draw", "medium",
        "70B, in=1 (far_mode_event_dispatch). Gated HUD track marker draw: parallel to hud_track_gate_draw (al=7) but al=8 mode, bx=2E39h/bp=3Bh label; farobj_rect_state_setup + viewvec3_project_track_max."),
    "sub_4BF8B": ("farobj_type_gate_test", "high",
        "45B, in=3 (terrain dispatch, farobj_class_table_entry, sub_4D544). FAR type gate test: farobj_record_ops_exec check then farptr_table_get, CF set/clear on [es:di+14h] in {12h,14h,33h,38h}."),
    "sub_4CCFB": ("farobj_field1a_read", "medium",
        "34B, in=1 (hud_rowlist_timer_step). FAR field1a read: runs farobj_behavior_dispatch body, returns [di+1Ah] (or 0 on 0FFFFh), +4 record skip on al!=0."),
    "sub_38C91": ("terrain_vm_blend_gate", "high",
        "26B, in=1 (game_frame_pipeline_step). Terrain VM blend gate: ds:45Eh/ds:449h both 0 -> ax=cs:loc_37461+3 else 0, tail-calls terrain_vm_blend_apply (sub_4F7B8)."),
    "sub_42206": ("mode_phase_apply_alt", "medium",
        "13B, in=1 (far_mode_event_dispatch). Mode-phase apply alt: cx=0F8E4h, dx=2E77h, bp=17h then tail-calls sub_321DD (variant of mode_phase_apply_stub)."),
}

def main():
    keys = list(NAMES)
    assert len(keys) == 34, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 34, "duplicate names"
    for n in names:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n), n
        assert not n.startswith(("sub_", "loc_", "off_", "byte_", "word_", "dword_", "unk_", "seg_")), n
        assert n.isascii(), n
    existing = set(re.findall(r"^\s+name: (\S+)", NAMING.read_text(encoding="utf-8"), re.M))
    coll = [n for n in names if n in existing]
    if coll:
        print("COLLISION:", coll)
        sys.exit(1)
    out = {}
    for k in keys:
        name, conf, notes = NAMES[k]
        out[k] = [name, notes, notes + " conf: " + conf, conf]
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    from collections import Counter
    print("wrote", OUT, len(out))
    print("confidence:", dict(Counter(v[3] for v in out.values())))
    for k in keys:
        print(f"  {k:12s} -> {out[k][0]}")

if __name__ == "__main__":
    main()
