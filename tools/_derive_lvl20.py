"""Validate and emit L20 names (25 fns) -> level20_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "level20_batch_names.json"

NAMES = {
    "sub_188DF2": ("r53_record_walk_dispatch", "medium",
        "2272B, in=1 (r53_e88). r53 overlay record-walk driver: walks a byte stream counting entries with code>=20h and high-bits in 1..2, jpt on code 27h..2Bh to 0x184F68/0x186739; callees r53_record_walk_main + slot2_map_window_load + terrain_angle_time_step + dgroup_save_reg_dxbp + farobj_store_32075 + farobj_index_resolve_step + farobj_field_scale_check."),
    "r36_e75": ("r36_loadout_record_copy", "medium",
        "1839B, in=1 (r36_e72). r36 overlay: stride-4Eh loop over 7894h:dword_79B6E table (count word_79B72), copies fields +40h/+42h to dword_79D6C +1C/+1E/+20 (+14h add); callees fixed_vec3_read + ui_loadout_menu_enter."),
    "sub_187E94": ("r53_farobj_pipeline_body", "low",
        "1483B, in=2 (r53_e51, sub_186ADC). r53 overlay mixed data/code body, mutual SCC with r53_e51; real callees farobj_record_ops_exec + farobj_index_resolve_step + mode_record_field_lookup + viewvec_half_add_step + terrain_angle_time_step + matrix_constants_setup + dgroup_save_reg_dxbp + stream_reset_gate_4a83."),
    "sub_66ABD": ("mode_session_state_mirror_init", "medium",
        "768B, in=9 (sub_2C531/2C559/2C5C7/2C671/2C743/2C74D/2C815/2C937/2C941). Copies 6DE8h state-word chain 6E14D/6E14B -> 6E119/6E117 -> 6E10D/6E10A+1 -> 6E129/6E127; clears 7894h flag bytes 7A312/7A319/7A30E/7A318; [bp+6]==5 gate else sub_2BED3; farptr_7b0e_43ba_const + 7A270 store; callees r30_config_block_create + bda_kb_flag + state_mode_check + irq_unmask_and_query + event_mode_set_77c98."),
    "sub_1820C0": ("r53_sbi_stream_dispatch", "low",
        "616B, in=1 (r53_e88). r53 overlay: mostly an embedded data table (cmp/pop/xor decode pattern) with real code sections; callees stream_state_init + sbi_command_flush_clear + sbi_channel_event_dispatch + line_table_scan_slope + mode_axis_state_select."),
    "r53_e51": ("r53_far_call_case_block", "low",
        "451B, in=1 (sub_187E94). r53 overlay far-call case block: pushes args then far-calls unk_5CFEF/5D144/5D4B4/5D5AB/5D680/5D620/5DF97, neg/sbb flag returns; jmp def_1882E6 into sub_187E94 - mutual SCC."),
    "sub_67781": ("display_palette_hud_refresh_step", "medium",
        "376B, in=1 (sub_2C88D). r05_farptr_dispatch_big + store_cmd_interpreter; dword_79E60 -> 79E3A copy; unk_43D52/unk_43E0C with 4FC2h:4FD52h state; word_78940 gate -> jmp ui_menu_panel_init; clears 7A30D/7A31A; flag_block_zero_5762_5c63 + r32_farptr_gate + terrain_vm_buffer_decay(3) + vga_dac_palette_upload + hud_track_label_strip + box_edge_strip_draw."),
    "sub_162A94": ("ui_loadout_menu_frame_scan", "medium",
        "364B, in=1 (sub_162C31). Loadout-menu outer frame: loop si<79B72 clearing record [bx+4]; reads 7894h:79B52 control byte (shr 2 -> [bp-1], and 3 -> [bp-2]); clears 602Eh:60954; 60964 bit40h -> 79BDA=0/1; dispatches via r35_e127; callees ui_menu_transition_step + ui_loadout_menu_enter."),
    "r35_e127": ("ui_loadout_menu_cmd_dispatch", "high",
        "213B, in=12 - hub of the 162C family (sub_162A94 + all cmd cases). Two-level jump-table dispatcher: cs:off_162DAF[bx] 12-entry table (cmd0..cmd10 + self slots) with nested jpt_162D0F/jpt_162D49; cases set 602Eh:60956=0 or 63989=8 then call ui_loadout_menu_enter."),
    "sub_4DF9D": ("overlay_teardown_restore_state", "medium",
        "182B, in=1 (sub_6E29E). Teardown/state-restore block: sub_2C153/2C15D/2C167 probes; unk_102B0 + handle_release_all(1) + op_bitmap_sweep_clear + ems_seg_free_21_49 + clc/retf exit path; restores cs:2E118->2E104, 2E116->2E10E, 2E112->2E106, 2E114->2E10A, 2E11A->off_2E11E, 2E11C->off_2E120 and zeros 2E128/2E126/2E10C/2E108."),
    "sub_30307": ("hw_config_apply_chain", "high",
        "79B, in=1 (sub_2BDD9). Stores bx->word_2E135, ax:dx->dword_2E13F; ds=es=54AFh; view_block4287_angles + hw_cfg_scan_22158 + terrain_vm_buffer_decay + hw_config_copy_85061; r37_farptr_store_gate with ds:44D3D; bda_417_mask_clear; mode_session_state_reset; state_byte_22246_set_ff; jmp game_config_apply_init - the hw-config apply chain."),
    "r34_e94": ("menu_cmd_store_and_record_scan", "medium",
        "73B, in=1 (r34_e126). Reads 7894h:79B52 byte and 3 (==3 -> [bp-9]=1 mode flag); store_cmd_interpreter; 602Eh:63989=0FFh; loop [bp-2] stride 27Ah over seg 602Eh records."),
    "sub_39CAA": ("mode_frame_gate_floor_clamp", "high",
        "41B, in=1 (r56_e174). ds:4AC2h mode gate: ==4 -> jmp mode_frame_step_core; ==3 or ==2 -> retn; else ax += ds:4AA1h clamped to ds:4AB9h via floor_store_4abb."),
    "sub_162C31": ("ui_loadout_cmd2_slot_scan", "high",
        "36B, in=2 (r35_e127, sub_162A94). Loadout cmd table case 2: ui_slot_scan_step + ui_slot_record_init then jmp loc_162BC7 frame tail; nested [bp-2] jpt_162C50 -> cmd3..cmd6."),
    "sub_162C00": ("ui_loadout_cmd0_transition", "high",
        "30B, in=2 (r35_e127, sub_162A94). Loadout cmd table case 0: 602Eh:60956=0, 63989=8, ui_menu_transition_step, jmp def_162D0F."),
    "sub_162C78": ("ui_loadout_cmd6_enter", "high",
        "30B, in=3 (r35_e127, sub_162A94, sub_162C31). Loadout cmd table case 6: ui_loadout_menu_enter (loc_685E3+1); nested [bp-2] jpt_162C91 -> cmd7..cmd10."),
    "r30_e98": ("cmd_terrain_decay_step", "medium",
        "24B, in=1 (sub_2C4A5). r30 overlay: store_cmd_interpreter then terrain_vm_buffer_decay(3); cmp 7894h:7A30B,7 gate."),
    "sub_162C1E": ("ui_loadout_cmd1_record_clear", "high",
        "19B, in=2 (r35_e127, sub_162A94). Loadout cmd table case 1: 602Eh:63989=8, farobj_record_clear_fields, jmp def_162D0F."),
    "sub_162C55": ("ui_loadout_cmd3_enter", "high",
        "19B, in=2 (r35_e127, sub_162C31). Loadout cmd table case 3: 602Eh:60956=0, ui_loadout_menu_enter (loc_6845B), jmp def_162D0F."),
    "sub_162C96": ("ui_loadout_cmd7_enter", "high",
        "19B, in=2 (r35_e127, sub_162C78). Loadout cmd table case 7: 602Eh:60956=0, ui_loadout_menu_enter (loc_68608), jmp def_162D0F."),
    "sub_162CB9": ("ui_loadout_cmd10_enter", "high",
        "15B, in=3 (r35_e127, sub_162A94, sub_162C78). Loadout cmd table case 10: ui_loadout_menu_enter (loc_686CE), jmp def_162D0F."),
    "sub_162C68": ("ui_loadout_cmd4_enter", "high",
        "8B, in=2 (r35_e127, sub_162C31). Loadout cmd table case 4: ui_loadout_menu_enter (loc_684C9+3), jmp def_162D0F."),
    "sub_162C70": ("ui_loadout_cmd5_enter", "high",
        "8B, in=2 (r35_e127, sub_162C31). Loadout cmd table case 5: ui_loadout_menu_enter (loc_68554), jmp def_162D0F."),
    "sub_162CA9": ("ui_loadout_cmd8_enter", "high",
        "8B, in=2 (r35_e127, sub_162C78). Loadout cmd table case 8: ui_loadout_menu_enter (loc_68645+1), jmp def_162D0F."),
    "sub_162CB1": ("ui_loadout_cmd9_enter", "high",
        "8B, in=2 (r35_e127, sub_162C78). Loadout cmd table case 9: ui_loadout_menu_enter (loc_6867A), jmp def_162D0F."),
}

def main():
    keys = list(NAMES)
    assert len(keys) == 25, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 25, "duplicate names"
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
