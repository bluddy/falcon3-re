"""Validate and emit orphan-batch-2 names (66 fns) -> orph2_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "orph2_batch_names.json"

NAMES = {
    "r53_e88": ("r53_opcode_decode_apply", "medium",
        "2736B, ASM, in=0, 10 callees. Byte-stream opcode decode (es:[bp-4Ch] cursor; si=(b>>3)&7, flags=b>>6) feeding jump table cs:jpt_187575 over r53_script_opcode_interpreter/r53_record_walk_dispatch; 42h-stride record field increments at 7894h/6894h, floor_store_4abb + farobj_index_resolve_step scaling, sbi_channel_event_dispatch - r53 overlay script-opcode decode/apply body."),
    "r25_e59": ("r25_four_slot_menu_step", "medium",
        "879B, C, in=0, 7 callees. Lays out 4 menu rows via 4x unk_6DFF0 on 6E45h rects (6E48E..6E4C8 vs 6E6FE..6E710), then r17_menu_event_loop -> 12-way cs:36Fh jump table on word 6E8D2; each case re-invokes 0x6e1ea + r22_farptr_helper and commits slot index into 6E8C3 - r25 overlay four-slot menu step."),
    "r26_e58": ("r26_two_view_menu_step", "medium",
        "577B, C, in=0, 7 callees. Same shape as r25 but 2 view rects (6E4B2/6E4B6 vs 6E714..6E71C) and a 9-way cs:241h table on word 6E8D2; cases call 0x6e1ea + r14_farptr_call_gate and commit state word 6E8E2 = 0/1 - r26 overlay two-view menu step."),
    "sub_16D071": ("overlay_undecoded_body_16d0", "low",
        "554B, C, in=0, no callees. enter 0Eh,0 then undecodable hex dump (es segment loads, far 9Ah calls) - overlay body not fully decoded by IDA."),
    "sub_4B36A": ("sprite_step_clip_project_body", "medium",
        "459B, ASM, in=0, 8 callees. Saves [di+0Dh]/bp into cs:loc_2F9B6 params; tests [si+0Ah]&200h -> pos_step_chain_engine; fixed_vec3_accumulate_a + sprite_clip_bounds_check + farobj_project_request_clear + mode_frame_step_core loop over 3-byte entries at 36h; toggles [si+0Ch]^8 then bound_range_check_4aad pair - sprite step with clip/project body."),
    "r39_e154": ("r39_farobj_batch_entry", "medium",
        "422B, C, in=0, 5 callees. Loads far ptr 602Eh:616DC into [bp-4]/[bp-2], sub_2C4F5(0), then 5x sub_2C4FF far-call batches (opcodes 1,2,3,4,5 with 1C2h/46h/7 args) each followed by sub_2C59F; closes r39_farptr_call_gate(1,1,0) - r39 overlay farobj batch entry."),
    "r27_e05": ("r27_coord_pair_select_entry", "medium",
        "351B, ASM, in=0, 3 callees. Indexes 31F0h tables (far ptr at +0AB0h[si*4], 0Ch-stride word at +0B38h[si*2]) into 7A32h:0AF52/0AF50, pushes unk_10C9E0/unk_10CA28 callbacks into sub_2BFC3 then dispatch_220f4_invoke_2arg; gated on 7A32h:0AF42==1 and si==14h/16h field pair select + clip_pending_atomic_apply - r27 overlay coord-pair select entry."),
    "sub_5FC50": ("overlay_undecoded_body_5fc5", "low",
        "315B, C, in=0, no callees. enter 0,0 then undecodable hex dump (hlt and data bytes) - overlay body not fully decoded by IDA."),
    "r59_e177": ("r59_slope_slot_update_entry", "medium",
        "281B, ASM, in=0, 3 callees (slope_far_call_driver, fixed_vec3_dot_es, farobj_slot_update_driver). Entry bytes decode as retn 0C426h (misdecode tail) so the body is only partly readable - r59 overlay slope/slot update entry."),
    "sub_2385D": ("fixed_vec3_magnitude_gate", "medium",
        "237B, ASM, in=0, no callees. Reads 3 longs at [si..+0Ah], abs each (neg dx/neg ax/sbb 0), keeps componentwise max hi-word in cx (or of lo-words in bp); if all small (cx==0 and bp&0C000h==0) copies 12 bytes si->di, else jumps to neighbouring tail loc_238B9 - fixed vec3 magnitude gate/clip entry."),
    "sub_5E074": ("overlay_undecoded_body_5e07", "low",
        "211B, C, in=0. enter 0,10h then undecodable hex dump (one call to farobj_altitude_scale_step visible) - overlay body not fully decoded by IDA."),
    "sub_681CC": ("ui_slot_record_field_init", "medium",
        "193B, DATA, in=0, 1 callee. 17h-stride record at 7894h:79E6C[79F34]: sets [bx+2/3/4]=2 and word [bx]=203h; gated by byte_7A302 plus 602Eh:[si*4+1]==2 -> word [bx]=96h; calls ui_slot_record_init (dump capped at 150 insns) - ui slot record field init."),
    "sub_172880": ("overlay_undecoded_body_1728", "low",
        "172B, C, in=0, no callees. enter 2,0 then undecodable hex dump (far 9Ah calls) - overlay body not fully decoded by IDA."),
    "sub_1647B2": ("overlay_undecoded_body_1647", "low",
        "160B, C, in=0, no callees. enter 4,0 then undecodable hex dump (es segment loads, far 9Ah call) - overlay body not fully decoded by IDA."),
    "sub_5C8DB": ("overlay_undecoded_body_5c8d", "low",
        "136B, ASM, in=0, no callees. Undecodable hex dump from the first byte (adc/and/fidiv garbage, <undecodable 0x00> tail) - overlay body not fully decoded by IDA."),
    "sub_166746": ("overlay_undecoded_body_1667", "low",
        "132B, ASM, in=0, no callees. push bp then undecodable hex dump (es segment loads, far 9Ah calls) - overlay body not fully decoded by IDA."),
    "sub_13276": ("cell_delta_key_search", "medium",
        "124B, ASM, in=0, 1 callee. Stores ax/bx to cs:11BC8/11BC6, shifts both >>4, deltas vs cs:11C26/11C24 with abs<=1 tests; index (cx*3+bx+4)*2 -> word table [bx+150h] loaded into ds; two sorted_key_search_bl probes with ax&0Fh and bx&0Fh, clc;retn - cell-delta key search entry."),
    "r12_e17": ("r12_index_state_swap_entry", "medium",
        "108B, ASM, in=0, 2 callees. ds=709Fh; if ds:70A8C bit 2 set: r12_farptr_load_thunk(1+70A28) then OR es:[di+0Ah]|1, follow [di+6] and OR [di+1]|1, refresh 70A21/70A20 from byte_70A2A; push cs; call unk_106EE2; farobj_index_state_swap(al=byte_70A2A); retf - r12 overlay index/state swap entry."),
    "sub_102298": ("overlay_undecoded_body_1022", "low",
        "101B, ASM, in=0, no callees. push ds then undecodable hex dump (far 9Ah calls) - overlay body not fully decoded by IDA."),
    "r54_e118": ("r54_far_tail_jump", "medium",
        "96B, ASM, in=0. Entry decodes as misdecode tail (dec si; add bh,dh) then a real far tail jmp to 8E68h:94BAh; remainder is a retn 0C426h misdecode - r54 overlay far tail-jump stub."),
    "r64_e185": ("r64_far_tail_jump", "medium",
        "96B, ASM, in=0, 1 callee (farobj_altitude_scale_step). Entry bytes misdecode then a real far tail jmp to 8E68h:94BAh; remainder retn 0C426h misdecode - r64 overlay far tail-jump stub."),
    "sub_190FA2": ("overlay_undecoded_body_190f", "low",
        "96B, ASM, in=0, no callees. mov bx,6894h then undecodable hex dump (far 9Ah calls) - overlay body not fully decoded by IDA."),
    "sub_1B631": ("kb_record_field22_clear_all", "medium",
        "83B, C, in=0, 6 callees. kb_index_get count; loop si: kb_record_name_get -> kb_field_get_22(name) -> kb_clear_24 -> kb_field_set_25_0; then state_7894_all_zero - clears field 22/25 across all keyboard records."),
    "sub_1BD64": ("stream_playback_resume_gate", "medium",
        "78B, ASM, in=0, 1 callee. If7772h:unk_77B46 is 2/3/4: stream_playback_start(ptr7772h:77B42:77B40, ds:9A32h) and store 7772h:77B36=0; else skip; returns ax=status - stream playback resume gate."),
    "sub_5EC94": ("overlay_undecoded_body_5ec9", "low",
        "71B, C, in=0. enter 0,0 then mostly undecodable hex dump (one call to entity_slot_create visible) - overlay body not fully decoded by IDA."),
    "sub_106CD1": ("overlay_undecoded_body_106cd1", "low",
        "65B, ASM, in=0, no callees. push ds then undecodable hex dump (far 9Ah calls) - overlay body not fully decoded by IDA."),
    "sub_11660": ("buffer_append_709f_record", "medium",
        "61B, ASM, in=0, no callees. Appends the [si] record (len = byte[si+5]+5) at ring pointer 709Fh:70A70 (initializing 70A6E from it when 0), advances ptr +FFh, wraps to 3C5h when it exceeds 7C1h - 709Fh ring-buffer record append."),
    "r07_e45": ("r07_point_range_gate", "medium",
        "58B, ASM, in=0, 1 callee. ds=6BE0h: if word_6CCF9 != 0FFFFh run r07_farptr_helper(byte_6CD01) with clc (jb -> fail tail), then accept only 7Bh<bx<0BAh and 74h<ax<0D3h; success returns clc;retf, otherwise fail tail loc_102DD3/102DD4 outside the function - r07 point-in-range gate."),
    "sub_1026DF": ("overlay_undecoded_body_1026df", "low",
        "55B, ASM, in=0, no callees. push ds then undecodable hex dump (loop near calls) - overlay body not fully decoded by IDA."),
    "sub_103170": ("overlay_undecoded_body_103170", "low",
        "51B, ASM, in=0, no callees. push ds then undecodable hex dump - overlay body not fully decoded by IDA."),
    "r64_e186": ("r64_record_field_read", "medium",
        "50B, ASM, in=0. Two jump-table case tails: (a) read es:[bx+12h] then jmp unk_1A42AD; (b) 7894h:79F34/17h index -> far ptr 6894h:6AE6C record field [bx+13h] then jmp unk_1A42AD; trailing bytes decode as pop bp;retf misdecode - r64 overlay record-field read case."),
    "sub_10175D": ("joystick_detect_state_store", "medium",
        "48B, ASM, in=0, 1 callee. call int15_joystick_detect then a partly undecodable tail that stores the result into a byte state, far-calls a helper and gates on cmp ax, with al reloaded from a data byte - joystick detect result store."),
    "r12_e22": ("r12_record_build_farptr", "medium",
        "44B, ASM, in=0, 1 callee. ds=es=709Fh; di=01D1h; builds a record with stosw 0FD08h, stosb 7, stosw (bl:cl), stosb [ax], stosw si; call r12_farptr_helper; restores regs; retf - r12 overlay record-build farptr stub."),
    "sub_6E558": ("pending_session_step_chain", "medium",
        "41B, ASM, in=0, 4 callees. pending_task_run -> far_cb_1 -> near call loc_6F08A -> far_cb_0 -> clip_pending_atomic_apply; cs:word_6E147=1; jmp near loc_6E9A6; guard then cmp cs:word_6E145,1 -> r69_pending_session_step else retf - pending session step chain."),
    "sub_1FAB6": ("long_div_bp0_by_cx", "medium",
        "36B, ASM, in=0, no callees. Unsigned 32-bit divide of bp:0000h by cx via two 16-bit div steps (bx carry), then sign-corrects dx:ax from the original sign of bp - long value divide-by-cx helper."),
    "sub_67480": ("menu_index_step_dispatch", "medium",
        "32B, ASM, in=0, 2 callees. If ax < 7894h:79E3E: inc [bp-2] and loop back to loc_673C0 while [bp-2] < 0Fh, else fall out to menu_event_dispatch; otherwise copy [bp-2] -> [bp-0Eh] and jmp menu_event_dispatch - menu index step/loop-exit dispatch."),
    "sub_17263": ("device_port_cmd_poll", "medium",
        "27B, ASM, in=0, no callees, 1 caller (sub_16CE5). ds=7772h; dx=[777F0] port; out 10h (command), poll in al,dx until al>=0, then out al (saved in ah); pop ds; retf - device port command/poll write stub."),
    "sub_67F96": ("ui_record_field_clear_frag", "medium",
        "26B, DATA, in=0, no callees. es:[bx+0Ch]=0 then index 7894h:79F34*17h into the 79E6C record (dump capped at 150 insns) - ui record field clear fragment."),
    "sub_10A0C4": ("overlay_undecoded_body_10a0c4", "low",
        "23B, ASM, in=0, no callees. push bp then undecodable hex dump (far 9Ah call, full reg pop) - overlay body not fully decoded by IDA."),
    "sub_256E7": ("farptr_slot_store_wrapper", "medium",
        "22B, ASM, in=0, 1 callee. lds si,[bp+arg_0]; ax=[bp+arg_4]; call farptr_slot_store_7f24a_al; restores ds/si/bp; retf - far-ptr slot store wrapper entry."),
    "sub_106C3D": ("overlay_undecoded_body_106c3d", "low",
        "21B, ASM, in=0, no callees. push ds then undecodable hex dump (near call) - overlay body not fully decoded by IDA."),
    "r12_e23": ("r12_mode0a_call", "medium",
        "17B, ASM, in=0, no callees. ds=es=709Fh; al=0Ah; call unk_1065D1; pop es/ds; retf - r12 overlay mode-0Ah call stub."),
    "sub_10A0A4": ("overlay_undecoded_body_10a0a4", "low",
        "16B, LEAF, in=0, no callees. push ds then undecodable hex dump - overlay stub not fully decoded by IDA."),
    "r32_e173": ("r32_far_tail_call", "medium",
        "15B, LEAF, in=0, no callees. push es:word_4FD52; call far unk_43E0C; pop cx/di/si; leave; retf - r32 overlay far-tail call stub."),
    "sub_25765": ("mouse_coord_clamp_wrapper", "medium",
        "14B, ASM, in=0, 1 callee. ax=[bp+arg_0]; bx=[bp+arg_2]; call mouse_coord_clamp_25474; pop bp; retf - mouse coordinate clamp wrapper entry."),
    "sub_109FE3": ("overlay_undecoded_body_109fe3", "low",
        "13B, ASM, in=0, no callees. push bp then undecodable hex dump (far 9Ah call) - overlay stub not fully decoded by IDA."),
    "sub_24EA8": ("bda_417_store_al_wrapper", "medium",
        "13B, ASM, in=0, 1 callee. ax=[bp+arg_0]; push cs; call bda_417_store_al; nop; pop bp; retf - BDA 417h store-AL far wrapper entry."),
    "sub_25E92": ("state_byte_25486_set", "medium",
        "12B, ASM, in=0, no callees. ax=[bp+arg_0]; cs:byte_25486=al; pop bp; retf - sets state byte 25486h from arg."),
    "sub_2BFE1": ("tail_bridge_to_state_byte_2e100_zero", "medium",
        "10B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp near state_byte_2e100_zero (5 pad bytes follow) - tail-bridge stub into state_byte_2e100_zero."),
    "r38_e131": ("r38_data_fragment", "low",
        "9B, DATA, in=0, no callees. js to unk_1673D0 then undecodable shl/sbb bytes - r38 overlay data fragment, not decoded as code."),
    "sub_2BE29": ("tail_bridge_to_2e048", "medium",
        "8B, ASM, in=0, 1 callee. call tail_bridge_overlay_load; jmp far 2CF6h:10E8h (0x2E048, still unnamed target) - 8-byte tail-bridge stub."),
    "sub_2C35B": ("tail_bridge_to_r30_config_block_create", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_config_block_create - 8-byte tail-bridge stub into r30_config_block_create."),
    "sub_2C441": ("tail_bridge_to_r06_vec3_main_proc", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r06_vec3_main_proc (loc_6BD24) - 8-byte tail-bridge stub into r06_vec3_main_proc."),
    "sub_2C4AF": ("tail_bridge_to_r30_state_init_all_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_state_init_all - 8-byte tail-bridge stub into r30_state_init_all (variant C)."),
    "sub_2C577": ("tail_bridge_to_loadout_menu_e", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_68715) - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant E)."),
    "sub_2C5F9": ("tail_bridge_to_ui_slot_record_fill", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_slot_record_fill (loc_67A85) - 8-byte tail-bridge stub into ui_slot_record_fill."),
    "sub_2C635": ("tail_bridge_to_ui_menu_panel_init_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_menu_panel_init (loc_66EB0) - 8-byte tail-bridge stub into ui_menu_panel_init (variant B)."),
    "sub_2C671": ("tail_bridge_to_mode_session_state_mirror_init", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far mode_session_state_mirror_init (loc_66CEE) - 8-byte tail-bridge stub into mode_session_state_mirror_init."),
    "sub_2C6C1": ("tail_bridge_to_loadout_menu_f", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_68ACF) - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant F)."),
    "sub_2C6FD": ("tail_bridge_to_ui_menu_transition_step", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_menu_transition_step (loc_67D51) - 8-byte tail-bridge stub into ui_menu_transition_step."),
    "sub_2C775": ("tail_bridge_to_r30_entry_retn_1564", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_entry_retn_1564 - 8-byte tail-bridge stub into r30_entry_retn_1564."),
    "sub_2C833": ("tail_bridge_to_loadout_menu_g", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_6885F) - 8-byte tail-bridge stub into ui_loadout_menu_enter (variant G)."),
    "sub_2C879": ("tail_bridge_to_r30_state_init_all_d", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_state_init_all - 8-byte tail-bridge stub into r30_state_init_all (variant D)."),
    "sub_2C8DD": ("tail_bridge_to_slot_record_init_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_slot_record_init (loc_6833C) - 8-byte tail-bridge stub into ui_slot_record_init (variant B)."),
    "sub_109FF0": ("state_byte_254a0_far_ret", "medium",
        "6B, LEAF, in=0, 2 callees. call state_byte_254a0_get; retf - state-byte 254A0h far-return stub."),
    "sub_6E0FE": ("overlay_undecoded_body_6e0f", "low",
        "5B, DATA, in=0, no callees. sub ch,ds:4356h; push dx - undecodable overlay data fragment, not decoded as code."),
}

def main():
    keys = list(NAMES)
    assert len(keys) == 66, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 66, "duplicate names"
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
