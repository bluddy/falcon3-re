"""Validate and emit orphan-batch-1 names (67 fns) -> orph1_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "orph1_batch_names.json"

NAMES = {
    "sub_3FFEF": ("game_frame_far_entry", "medium",
        "3685B, in=0, 42 callees. Far-entry thunk (pop ax; cmp ax,0FFFFh). Multi-purpose game frame entry: farobj_table_snapshot + farobj_rect_state_setup + bulk 200h-copy + game_config_apply_init + game_state_load_apply + key_range_wheel_handler + dgroup_state_cycle_step + control_axes_record_write/store + state_bits_pack/unpack + ems_window_load_snapshot + event_table_name_fill + farobj_record_bulk_copy + terrain_state_reinit + view_terrain_frame_step + far_mode_event_dispatch + hud_track_strip_pipeline + r32_hud_phase_dispatch + farobj_project_request_setup + stream_record_point_find + entity_record_table_ops - the main game far-entry dispatcher."),
    "r48_e97": ("r48_mouse_event_entry", "medium",
        "931B, C, in=0. mode_record_field_lookup + two farobj_field_scale_check on 602Eh fields + mouse_gate_far_entry + op_dispatch_far_entry (opcodes 4/0Ch/2/8/1/0Ah etc across 602Eh/7894h record slots) - r48 overlay mouse/event dispatcher entry."),
    "sub_165E18": ("overlay_undecoded_body_165e", "low",
        "585B, C, in=0, no callees. enter 8,0 then undecodable hex dump (6894h/7894h record ops) - overlay body not fully decoded by IDA."),
    "r39_e147": ("r39_queue_drain_entry", "medium",
        "566B, C, in=0. farobj_queue_drain_dispatch + far ptr 602Eh:616DC + 8x r39_farptr_call_gate via sub_2C4FF with opcodes 1-8/28h - r39 overlay farobj queue drain + far-call batch entry."),
    "sub_10CA51": ("overlay_undecoded_body_10ca", "low",
        "527B, C, in=0, no callees. enter 4,0 then undecodable hex dump (6894h record ops) - overlay body not fully decoded by IDA."),
    "sub_16CECA": ("overlay_undecoded_body_16ce", "low",
        "423B, C, in=0, no callees. enter 10h,0 then undecodable hex dump (7894h record ops) - overlay body not fully decoded by IDA."),
    "sub_6DD12": ("distance_tier_classify_entry", "medium",
        "369B, in=0. abs dx/dy diff vs 0BB8h (3000) selects bp tier 45h/54h/4Eh; far_cb_2(bp) + dispatch_220d4_stub(bp) - distance-tier classifier entry."),
    "sub_26281": ("trig_clip_project_entry", "medium",
        "316B, in=0. Far wrapper: push cs; call loc_2629A (inner body after retf at 0x26299); trig_table_lookup + segment_clip_test + far_cb_2 - trig/clip far projection entry."),
    "r36_e99": ("r36_record_compare_entry", "medium",
        "281B, C, in=0. Compares two 4Eh-stride records (+40h/+42h fields) via farobj_queue_drain_dispatch + hw_flag8505_set fixed-mul; result idiv 35h - r36 overlay record compare entry."),
    "r10_e67": ("r10_flag_bits_entry", "medium",
        "242B, in=0. flag_bits_dispatch(0,1Ch,cs) + lodsw 5-word copy from 0C2h->5Ch + cb_args_invoke(al=0Eh) + ds:35h gate + far_cb_0 - r10 overlay flag-bits dispatcher entry."),
    "r36_e115": ("r36_record_type_scatter", "medium",
        "213B, C, in=0. 27h-stride records at [bp+6]; type byte [bx+0Ah] * 39h indexes 602Eh:106Dh table; 21h-word far-ptr scatter via 79E28 - r36 overlay record-type scatter entry."),
    "sub_2A248": ("ui_bounds_clip_entry", "medium",
        "198B, in=0. Copies 10h-stride [si] rects to 7B0Eh:6360h, bounds-checks vs cs:1F6CC/1F6D0/1F6CE/1F6D2, ORs flags into 27968h/2796Ah, calls uibounds_top_bottom_dispatch - UI bounds clip entry."),
    "sub_16F6D5": ("overlay_undecoded_body_16f6", "low",
        "173B, in=0, no callees. push bp then undecodable hex dump - overlay body not fully decoded by IDA."),
    "r39_e81": ("r39_vec3_frame_entry", "medium",
        "160B, in=0. r06_vec3_main_proc -> es:3646h mode select; sub_2C58B + sub_2C4FF far-call with opcodes 3/5 + sub_2C59F - r39 overlay vec3 frame entry."),
    "sub_21ABE": ("state_nibble_gate_entry", "medium",
        "142B, in=0. test byte ds:0F73h,0Fh; jnz; retn - gates on low nibble of ds:0F73h state word, early-return path; body continues after retn - state-nibble gate entry."),
    "r54_e162": ("r54_record_loop_step", "medium",
        "132B, DATA, in=0. es:1534h=11h; 4Eh-stride records at 6894h:69B6E, loop si < 69B72h, [bx+2] check + xlat - r54 overlay record loop step (partially undecodable)."),
    "r33_e86": ("r33_record_scan_gate", "medium",
        "124B, in=0. 11h-stride record at 639Eh:di, [bx+1A0h] flag gate + r33_record_scan_4e(di) - r33 overlay record scan entry with active-flag gate."),
    "r33_e148": ("r33_menu_args_farobj_entry", "medium",
        "109B, in=0. di/2 index + ui_menu_page_args_setup + fixed_vec3_read + and ax,0Fh / idiv 7 - r33 overlay menu-args + farobj field entry."),
    "sub_2B135": ("overlay_ems_stack_segment_load", "medium",
        "103B, in=0. pushf/sub sp,4; pops args into [bp+2]/[bp+4]; ds=seg021; word_2B4A0 stack si-=6, ds=seg_2B4A4, ax=[si+2] - overlay EMS/segment stack push entry."),
    "r54_e117": ("r54_far_vector_stub", "medium",
        "96B, in=0. push 0C28Eh; les bx,es:12ACh; es:[bx]=ax; mov ax,si; retf 82h - r54 overlay far-vector stub (retf 82h pops 82h bytes of stack args on return)."),
    "r58_e180": ("r58_line_table_entry", "medium",
        "96B, in=0. overlay_segment_load + line_table_build_dispatch (partially undecodable start) - r58 overlay line-table build entry."),
    "sub_18B689": ("overlay_undecoded_body_18b6", "low",
        "96B, in=0, no callees. pushf then undecodable hex dump - overlay body not fully decoded by IDA."),
    "sub_4FDAD": ("state_word_0f0e_set", "medium",
        "85B, in=0. mov ds:0F0Eh,ah; pop ds; retf - stores ah into state word ds:0F0Eh then far-returns (body continues after retf)."),
    "r12_e35": ("r12_state_word36_reset", "medium",
        "78B, in=0. partially undecodable start; mov word ptr ds:36h,0FFFFh; retf - r12 overlay state-word36 reset stub."),
    "r33_e79": ("r33_farcb_seq_entry", "medium",
        "72B, in=0. r30_farcb_seq + r33_farptr_gate_c - r33 overlay far-callback sequence entry (retn 8A26h at start is misdecode tail of prior function)."),
    "sub_27877": ("callback_far_invoke", "medium",
        "66B, in=0. Loads 4 args into bx/di/ax/bp; call cs:dword_2217C (far callback); cs:word_27474=4 - generic far-callback invoke entry."),
    "r64_e190": ("r64_table_entry_reset", "medium",
        "61B, in=0. 17h-stride record at 6894h:6AE6C from 69F34h; [bx+15h]=0; 9x loop es:[bx+15E0h]=1000h - r64 overlay table-entry reset entry."),
    "sub_216B8": ("fixed_long_div_normalize", "medium",
        "59B, in=0. or dx,dx; jns; mov ax,1000h; retn - sign-clamp then falls through; callees: fixed_long_div_64, vec2_normalize_seq, trig_value_bsearch_8364 - fixed-long divide + normalize entry."),
    "r64_e184": ("r64_vector_select", "medium",
        "56B, in=0. 3-way vector select: es:1510h/[bx+1Ah] or 69E50h/[bx+0Eh] or 79E50h/[bx+22h] - r64 overlay vector-field select entry (partially undecodable)."),
    "r35_e103": ("r35_loadout_enter_bridge", "medium",
        "51B, in=0. or es:676h,20h; ui_loadout_menu_enter(0,3,0,79BDAh byte); or es:60956h,40h - r35 overlay loadout-enter bridge entry."),
    "r53_e47": ("r53_opcode_flag_combine", "medium",
        "50B, in=0. byte&7 opcode test: 4->si=1, 7->di=1; OR di; returns (si!=0)-1 - r53 overlay opcode-flag combine entry (reads via [bp-4] far ptr)."),
    "sub_101677": ("overlay_undecoded_body_1016", "low",
        "49B, in=0, no callees. push ds then undecodable hex dump - overlay body not fully decoded by IDA."),
    "sub_6CF63": ("counter_incr_gate", "medium",
        "45B, in=0. cmp di,1; jnz r06_farptr_dispatch; cmp ds:4A87h,cl; jnz; inc ds:4A87h; ds:4A89h=200h; clc; retn - counter increment gate entry."),
    "sub_26667": ("triangle_winding_sign", "medium",
        "41B, in=0. 2D cross-product sign test: (ax-bx)*(dx-cx) - (cx-bx)*(ax-si) via imul; js/stc; retn - triangle winding/orientation sign test entry."),
    "r12_e27": ("r12_record_store_stub", "medium",
        "36B, in=0. ds=es=709Fh; di=1D1h; stosw 0FD08h + stosb 3 + stosw cx + stosb bx + stosw si; call unk_106AD0 - r12 overlay record store stub (builds 0FD08h-typed record then calls near helper)."),
    "sub_2CB4D": ("callback_table_iterate", "medium",
        "33B, in=0. Iterates 6-byte entries at cs:14Ch: far-ptr [bx]/[bx+2], mask [bx+4] & al -> pushf/call dword [bx]/popf, bx+=6 until null - callback table iterate entry."),
    "r58_e178": ("r58_record_index_step", "medium",
        "27B, DATA, in=0. 82h-stride record index: ds:1222h * 82h -> 6894h:dword_69BEC (partially undecodable) - r58 overlay record index step."),
    "sub_10F46": ("mode_slot_enter_far_wrapper", "medium",
        "26B, in=0. overlay_seg_word_read(24h) -> ds=cs:byte_10842; mode_slot_enter(ax); add sp,2; retf - mode-slot-enter far wrapper entry."),
    "sub_4FD20": ("string_table_copy", "medium",
        "24B, in=0. di=0A754h; cx=1Bh; movsb; pop es/ds; retf - copies 27 bytes from ds:si to es:0A754h then far-returns (string table copy)."),
    "sub_23AA1": ("angle_quad_norm_far_wrapper", "medium",
        "22B, in=0. lds si,[bp+arg_0]; les di,[bp+arg_4]; call angle_quad_norm_scale; pop; retf - angle-quad normalize-scale far wrapper entry."),
    "r12_e25": ("r12_bank_switch_call", "medium",
        "21B, in=0. push ds/es/pusha; ds=es=709Fh; al=7; call unk_1065D1; popa; retf - r12 overlay bank-switch call stub (mode 7 via near helper in 709Fh)."),
    "r59_e160": ("r59_record_index_step", "medium",
        "18B, DATA, in=0. ds:1222h * 82h -> 7894h:dword_79BEC - r59 overlay record index step (mirrors r58_e178)."),
    "sub_1033F8": ("overlay_undecoded_body_1033", "low",
        "16B, LEAF, in=0, no callees. push es then undecodable hex dump - overlay stub not fully decoded by IDA."),
    "r07_e44": ("r07_state_flag_set", "medium",
        "15B, LEAF, in=0. ds=6BE0h; ds:byte_6CD53=1; retf - r07 overlay state-flag set stub."),
    "r48_e159": ("r48_arg_forward_stub", "medium",
        "14B, C, in=0. enter 2,0; push si; push 7894h; push 0F5Ah; push [bp+6] - r48 overlay arg-forward stub (forwards 7894h:0F5Ah + arg to callee)."),
    "sub_109FD0": ("overlay_undecoded_body_109fd0", "low",
        "13B, in=0, no callees. push bp then undecodable hex dump; pop bp; retf - overlay stub not fully decoded by IDA."),
    "sub_24E8C": ("bda_417_far_wrapper", "medium",
        "13B, in=0. push bp; mov bp,sp; mov ax,[bp+arg_0]; push cs; call bda_417_or_al; pop bp; retf - BDA 417h OR-AL far wrapper entry."),
    "sub_11842": ("int7a_bx3_invoke", "medium",
        "12B, LEAF, in=0. push ds/es/pusha; bx=3; int 7Ah; popa; retf - int 7Ah invoke with bx=3 (save/restore-all wrapper)."),
    "r55_e175": ("r55_vector_stub_pad", "low",
        "10B, DATA, in=0. or ds:569Fh,si; jmp unk_19580C (then pad data) - r55 overlay vector stub (partially undecodable)."),
    "r08_e30": ("r08_farptr_load_entry", "medium",
        "9B, LEAF, in=0. call r08_farptr_load_thunk; jnz; stc; retf - r08 overlay farptr-load entry stub."),
    "sub_2BE1F": ("tail_bridge_to_6fd06", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far 6E8Fh:1416h (0x6fd06) - 8-byte tail-bridge stub into overlay target."),
    "sub_2C31F": ("tail_bridge_to_r30_state_init_all", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far r30_state_init_all - 8-byte tail-bridge stub into r30_state_init_all."),
    "sub_2C437": ("tail_bridge_to_r30_farobj_proc_c", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far r30_farobj_proc_c - 8-byte tail-bridge stub into r30_farobj_proc_c."),
    "sub_2C4A5": ("tail_bridge_to_terrain_decay", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far cmd_terrain_decay_step - 8-byte tail-bridge stub into cmd_terrain_decay_step."),
    "sub_2C56D": ("tail_bridge_to_loadout_menu_a", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant A)."),
    "sub_2C5DB": ("tail_bridge_to_r30_entry_partial_a", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far r30_entry_partial_a - 8-byte tail-bridge stub into r30_entry_partial_a."),
    "sub_2C62B": ("tail_bridge_to_loadout_menu_b", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant B)."),
    "sub_2C667": ("tail_bridge_to_ui_menu_panel_init", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_menu_panel_init - 8-byte tail-bridge stub into ui_menu_panel_init."),
    "sub_2C6B7": ("tail_bridge_to_loadout_menu_c", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant C)."),
    "sub_2C6F3": ("tail_bridge_to_r30_mode_set", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far r30_mode_set_637fc_c - 8-byte tail-bridge stub into r30_mode_set_637fc_c."),
    "sub_2C76B": ("tail_bridge_to_slot_list_mode", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_slot_list_mode_enter - 8-byte tail-bridge stub into ui_slot_list_mode_enter."),
    "sub_2C829": ("tail_bridge_to_slot_record_init", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_slot_record_init - 8-byte tail-bridge stub into ui_slot_record_init."),
    "sub_2C86F": ("tail_bridge_to_r30_state_init_all_b", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far r30_state_init_all - 8-byte tail-bridge stub into r30_state_init_all (variant B)."),
    "sub_2C8B5": ("tail_bridge_to_loadout_menu_d", "medium",
        "8B, in=0. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant D)."),
    "sub_109FDD": ("state_byte_2549f_far_ret", "medium",
        "6B, LEAF, in=0. call state_byte_2549f_get; retf - state-byte 2549Fh far-return stub."),
    "r53_e133": ("overlay_undecoded_body_r53e133", "low",
        "5B, LEAF, in=0, no callees. adc al,83h; retn 893Dh - undecodable overlay stub (likely misdecode tail of prior function)."),
    "nullsub_19": ("nullsub_19", "medium",
        "2B, LEAF, in=0. retn - nullsub (no-op far/near return, already auto-named nullsub_19 by IDA)."),
}

def main():
    keys = list(NAMES)
    assert len(keys) == 67, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 67, "duplicate names"
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
        print("  %s -> %s" % (k, out[k][0]))

if __name__ == "__main__":
    main()
