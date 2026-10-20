"""Validate and emit L19 Batch 3 names (34 fns) -> level19_batch3_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "level19_batch3_names.json"

NAMES = {
    "sub_3CE92": ("farobj_behavior_dispatch_step", "high",
        "2580B, in=19. Master farobj entity behavior/AI step: many entry points; 3334h tile-wrap on si+31/32/33/35, far_obj_field_call + farobj_field_set type-3 thresholds (3013h/304Ch/3065h/307Fh/3259h), [si+0Bh] mode gates, speed/alt clamps via funcs_4E5C0."),
    "sub_6A5BD": ("ui_menu_page_setup", "high",
        "2204B, in=5. Menu page/panel setup: farobj_arg_thunk with (9,35h,0Bh,4,19h), clears 7894h:79B66/79B68, current_item_check, flag_block_zero; called by ui_loadout_menu_enter siblings and menu_page_jump_stub."),
    "sub_3EEDB": ("farobj_view_project_step", "high",
        "1485B, in=11. Farobj view/project pipeline step: flag1084c_get, farptr_state_set, far_obj_field_call, viewvec_loop_project + viewvec3_project_track_max + palette_delta_blend (sub_2F043); callers incl. main loop + far_mode_event_dispatch."),
    "sub_66E62": ("ui_menu_panel_init", "high",
        "1365B, in=17. Shared menu/UI panel init: writes 4FC2h:4FD5E/4FD72/4FD46/4FD48, pushes 0B3h/0C7h to sub_39BD3, state_byte_25488_set_arg, farptr_lds_invoke; ui_loadout_menu_enter tail-jumps here."),
    "sub_4AEC4": ("farobj_pos_move_angle_step", "high",
        "1146B, in=2 (ui_loadout_menu_enter, sub_69C5D). Farobj position-move/angle step: pos_move_angle_step fallbacks, bound_range_check_4aad x2, farobj_tile_copy_resolve, angle_aux_far + angle_xy_far, farobj_copy_cond."),
    "sub_47BDE": ("hud_rowlist_timer_step", "high",
        "960B, in=2. HUD row-list timer step: loops 16 rows over 63FD:1940h (4-byte records), decrements timers, hud_rowlist_panel_draw; key_code_resolve_entry + hud_field14_value_draw + hud_terrain_strip_render."),
    "sub_3C1BD": ("farobj_slot_update_driver", "high",
        "821B, in=4 (main loop). Loads funcs_4E5C0+word_2E102 from 2F64h:37h/39h, viewmode3_vector_project + farobj_rect_compute_store, then 16 slots at 386Fh stride 5Ch calling sub_30AA8/farobj_record_ops_exec/far_mode_event_dispatch."),
    "sub_3F861": ("farobj_index_resolve_step", "medium",
        "705B, in=9. Farobj index resolve: stores [si+18h] into cs:loc_32071, sub_48E25 lookup, scans 1396h 16-entry table, farobj_table_snapshot + farptr_table_offset_apply."),
    "sub_4EF1C": ("entity_record_table_ops", "high",
        "588B, in=9. FAR entity-record table ops (retf entries): entity_record_table_build under 709Fh, flag1084c_get gate, handle_release_all, 70A2A/70A2D slot compare."),
    "sub_37818": ("terrain_angle_time_step", "medium",
        "498B, in=8. Terrain time-of-day angle: int 21h/2Ch get-time, 5A0h (90 deg) wrap + 3Ch scale, farwrap_25a1c grid init, tile_strip_sample_draw + record_script_coord_dispatch."),
    "sub_4FEB5": ("angle_fixed_rotate_apply", "medium",
        "437B, in=1. Fixed-point 2D rotation: imul against ds:0EF5h/0EF7h (sin/cos) with shl/rcl doubling; retf entries for rotate mode set (6BE0h:6CD78 clamp 0..1)."),
    "sub_4F4FE": ("view_pos_cache_update", "medium",
        "407B, in=3 (game_frame_pipeline_step, main loop). View pos cache: tests 7A32:8505C/85052, compares ax/dx vs 85048/8504A, xchg into 0AD28h/0AD2Ah, viewmode3_vector_project."),
    "sub_4F8BC": ("terrain_vm_flag_gate", "medium",
        "383B, in=1 (game_frame_pipeline_step). Terrain VM flag gate: flag_gate_zero_abc bits 2/1/4 + 7A32:8505C bit10h, 8505F toggle, dispatch_2216c_stub."),
    "sub_382AB": ("terrain_menu_field_setup", "medium",
        "346B, in=5. Terrain/menu field setup: farwrap_25a1c 124h/2Fh/20h grid, game_state_setup_multi + dispatch_220ec_stub, record_script_field14_setup + record_script_field0c_setup."),
    "sub_6798C": ("ui_slot_record_fill", "high",
        "327B, in=2 (ui_loadout_menu_enter). Fills 7894h:79E60 record fields 2BD6h-2BDBh (E0h/2Eh/1Eh type pattern like ui_slot_record_init); store_cmd_interpreter + vga_dac_palette_upload + sub_4F3EC."),
    "sub_41646": ("farobj_range_slot_init", "high",
        "318B, in=5. Farobj range-slot init: key_event_gated_process, state_farptr_dxax_store, sets [si+74h]|=4, calls hud_track_strip_pipeline (sub_46D42) + obj_range_slot_init; param454_apply_thresholds/tableinit."),
    "sub_48292": ("record_bitpack_pack", "high",
        "284B, in=2. Record bit-pack (counterpart to entity_bitpack_unpack): 10 slots of 1Ah stride then 8 slots of 8 words, 807Fh mask + movsw, calls terrain_menu_field_setup (sub_382AB)."),
    "sub_4BFB8": ("farobj_tile_key_cache", "medium",
        "269B, in=2. Farobj tile-key cache: packs (al-8)<<4|(bl-8) nibble key, caches in 69FFh:69FE5, invalidates via farobj_record_ops_exec + farobj_table_init_69ff."),
    "sub_398A4": ("view_scale_compute_step", "medium",
        "254B, in=3. View scale compute: divides [si+26h/28h] packed pos by farptr_entry_store_41b result under ds:135Ch mode, writes cs:word_377E9; 0B6h (182) secondary scale."),
    "sub_4F7B8": ("terrain_vm_blend_apply", "medium",
        "219B, in=1 (sub_38C91). Terrain VM blend: sets 7A32:85058/85056/8505B bit20h, copies 0F0h words of 0A856h with 3Fh clamp; farptr swap on 0AD38h/0AD36h."),
    "sub_3FD89": ("farobj_attr_apply_step", "high",
        "206B, in=2. Farobj attr apply: flag gates via cs:loc_33495 bits 10h/1/4, sub_2C0B3, farobj_attr_table_lookup, dec [di+0B0h] + sub [di+26h] (fuel/range), far_mode_event_dispatch + hud_track_strip_pipeline."),
    "sub_67AE1": ("menu_pending_task_step", "high",
        "197B, in=4. Menu pending-task step: pending_task_run, farobj_range_slot_init (sub_41646), store_cmd_interpreter, vga_dac_palette_upload; writes 602Eh:63980=1 + copies 615B0/615AE->615C0/615BE."),
    "sub_39748": ("tile_sprite_strip_project", "high",
        "179B, in=3. Tile sprite-strip project: tile_quad_sample + tile_strip_sample_draw against cs:word_377E5/377E7, -32h (0FFCEh) clamp, 0FAh/0EEh near-field thresholds."),
    "sub_42553": ("farobj_matrix_project_copy", "medium",
        "167B, in=1 (far_mode_event_dispatch). Farobj matrix project+copy: viewmode3_vector_project on 7 words [si+3Ah..44h], copies result to 54AFh:83C; fixed_vec3_accumulate_a tail."),
    "sub_331E4": ("key_mode_state_setup", "high",
        "150B, in=2. Key/mode state setup: matrix_constants_copy_es3852, xlat_mask_setbit_47e, key_state_machine_tick; sets ds:40Ah/352h/354h + farptr ds:4ABh -> view_terrain_frame_step."),
    "sub_35934": ("mode_ratio_dispatch", "medium",
        "126B, in=4. Mode ratio dispatch on cs:byte_343E9 (0/1/2/3+): farobj_rect_ratio_build + far_cb_with_args + state_word_704_set_5a; sets cs:off_343EA to 7BA3h/631Ah/6618h/6E32h."),
    "sub_415CE": ("farobj_state_flag_set", "medium",
        "120B, in=1 (sub_30587). Farobj state-flag set: farobj_table_snapshot, checks [di+0Ch]==2 -> returns 1/8 else clears [di+0Ch]=4 + [di+8]|=100h."),
    "r30_e77": ("ui_slot_scan_step", "medium",
        "97B, in=4 (R30 overlay). UI slot scan: sets 709F:70A2D, steerpoint_scan_update (sub_39F1D), r30_shared_tail_es, ui_slot_record_init; 7894h:78940==1 gate."),
    "sub_4E0B9": ("terrain_ratio_select", "medium",
        "80B, in=1 (sub_38405). Terrain ratio select: computes from word_2E102/2E10A/2E124/2E126, 9x mul/div scale, returns 1 or 2."),
    "sub_42640": ("hud_track_gate_draw", "high",
        "70B, in=1 (far_mode_event_dispatch). Gated HUD track draw: viewvec3_project_track_max + farobj_table_snapshot + farobj_rect_state_setup (sub_327BE), al=7 track mode; parallel to hud_project_gate_draw."),
    "sub_24EC4": ("key_event_table_dispatch", "high",
        "47B, in=1 (flag_bits_dispatch). Key-event table dispatch: scans [di] for matching al, indirect call via cs:byte_24E42 farptr; flag_bits_clear + key_event_mode_gate + far_mode_event_dispatch."),
    "sub_4CCAE": ("farobj_field2e_test", "medium",
        "35B, in=1 (sub_45976). Farobj field2e test: calls farobj_behavior_dispatch (sub_3CE92) body, checks 0FFFFh/al=0 + [di+2] bit1, returns 0FFFFh on fail."),
    "sub_345A0": ("sbi_int8_shutdown_hook", "medium",
        "26B, in=4. SBI int8 shutdown hook: checks 709F:609F0, calls sbi_int8_close + farobj_bl_15_init (sub_4E90E); callers incl. record_script_coord_entry."),
    "sub_421F9": ("mode_phase_apply_stub", "medium",
        "13B, in=1 (far_mode_event_dispatch). Mode-phase apply stub: sets cx=71Ch, dx=2E63h, bp=21h then tail-calls sub_321DD."),
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
