"""Validate and emit orphan-batch-3 names (66 fns) -> orph3_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "orph3_batch_names.json"

NAMES = {
    "r32_e83": ("r32_track_menu_step_entry", "medium",
        "1572B, ASM, in=0, 10 callees. jpt_156DD4 jump table over 7894h mode words (79B6C==32h/34h/36h, 79F16 index 0..9), 12Ch (300) threshold gates on 79E80, 79E7E scroll counter idiv 10h/8, hud_track_distance_draw + ui_menu_transition_step + bound_check_gated_4a83 + r30_counter_step_tail, 4FC2h:4FD52 counter wraps 0..5 driving unk_43D52/unk_43E0C, closes r32_farptr_gate - r32 overlay track/HUD menu step machine."),
    "r37_e137": ("r37_hud_strip_render_entry", "medium",
        "788B, ASM, in=0, 9 callees. Renders 8x box_edge_strip_draw (ids 0Bh/0Ch/14h/15h/18h/19h/1Dh over 7894h/602Eh/4FC2h rects) plus 5x hud_track_label_strip into a bp-210h buffer, ui_menu_panel_init(1,...), sub_2C513 -> word_79E9E, copies 82h bytes to 7894h:79BEC, sets word_79EEC=1; retf - r37 overlay HUD strip render entry."),
    "r23_e61": ("r23_menu_key_dispatch_loop", "medium",
        "570B, C, in=0, 7 callees. 6E45h DGROUP modal loop: dispatch_22100_invoke(1,0,200,...), 3x unk_6DFF0 rect draws on 6E48x/6E4Bx coords, dispatch_220f4_invoke_2arg(200,0), flag_table_pop_far_thunk -> word_6E8D2 masked FF00h/DFh, r17_menu_event_loop, 10-way key scan at cs:23Ah -> jmp word cs:[bx+14h] table, pane state byte_6E8D6 (FFh/0 -> 2/1), r22_farptr_helper - r23 overlay menu key dispatch loop."),
    "sub_16BACF": ("overlay_undecoded_body_16bacf", "low",
        "552B, C, in=0, no callees. enter 4,0 then undecodable hex dump (push/mov/call 9Ah stream, retf tail) - overlay body not fully decoded by IDA."),
    "sub_1659A2": ("overlay_undecoded_body_1659a2", "low",
        "453B, C, in=0, no callees. enter 20h,0 then undecodable hex dump (imul/idiv and far 9Ah calls, retf tail) - overlay body not fully decoded by IDA."),
    "r39_e139": ("r39_four_slot_render_entry", "medium",
        "406B, C, in=0, 6 callees. Loads far ptr 602Eh:616DC, sub_2C4F5(0); sub_2C58B(byte_63926,79BDA) -> word_6390A, sub_2C4B9/2 -> word_6390E clamped 28h (40); 4x sub_2C4FF far draws (slots 1..3 at 6/28h/1F4h rects plus slot 4 wide 12Ch/15h) each followed by sub_2C59F; closes r39_farptr_call_gate(1,0,0) - r39 overlay four-slot render entry."),
    "sub_166313": ("overlay_undecoded_body_166313", "low",
        "331B, C, in=0, no callees. enter 4,0 then undecodable hex dump (mov byte/push stream, far 9Ah calls, retf tail) - overlay body not fully decoded by IDA."),
    "sub_15FBE4": ("overlay_undecoded_body_15fbe4", "low",
        "310B, C, in=0, no callees. enter 54h,0 then undecodable hex dump (loop/jcc bytes, retf tail) - overlay body not fully decoded by IDA."),
    "r39_e152": ("r39_queue_slot_render_entry", "medium",
        "269B, C, in=0, 6 callees. Takes bp+6 arg as si; far ptr 602Eh:616DC base; farobj_queue_drain_dispatch(byte_63926) -> ax, sub_2C563 fills 4 out-coords; 2x sub_2C4FF draws (78h/1C2h rects, slots 1,2) plus wide 12Ch slot 3 (79BDA), each followed by sub_2C59F; closes r39_farptr_call_gate(1,3,si) - r39 overlay queue-slot render entry."),
    "r34_e126": ("r34_record_field_store_step", "medium",
        "232B, ASM, in=0, 4 callees. std; sets 602Eh:3646h, sub_2C4B9(bp-3,79BDA) > 28h -> word_63955=9; 4Eh-stride record writes at 7894h:dword_79B6E rows [bx+4]=byte 63955; accum_record_append -> byte_63926, r34_farobj_proc probe sets [bx+4]=0Ah on nonzero; byte_63927=FFh; retf - r34 overlay record field store step."),
    "r39_e141": ("r39_angular_slot_render_entry", "medium",
        "207B, C, in=0, 4 callees. di=1C2h (450), [bp-6]=64h (100); far ptr 602Eh:616DC; sub_2C58B(byte_63926,79BDA) -> si; 2x sub_2C4FF (6, h/2 or h, 450, type 7/8, x=(si+0B4h) mod 168h or si, slots 1,2) each followed by sub_2C59F; dump ends mid-tail (triplet bytes) - r39 overlay angular slot render entry."),
    "sub_29917": ("record_span_build_and_dispatch", "medium",
        "190B, ASM, in=0, 9 callees. Copies cx+1 [si+8/+0Ah] word pairs (10h stride) into 6360h and updates cs:word_2796E; flag gates cs:byte_1F72E/1F739/1F741/1F73F/1F72D with a cs:off_1F708 table call (param6_append_cursor_a/avg_b/3w_c/scale_d/joystick_gate_counter) and (1<<cl)*3 calc; then record_span_init_eba + record_op_dispatch_220b0, farobj_batch_dispatch_loop, rect_edge_dispatch_a; retn - record span build and dispatch."),
    "r29_e06": ("r29_yesno_confirm_loop", "medium",
        "166B, ASM, in=0, 14 callees. Interactive confirm: mouse_gate_far_entry, viewport_rect_state_store + hud_track_distance_draw (loc_4276E+1), dispatch_220ec_invoke(69972 rect, di=52h, si=2Ch), hw_cfg_copy_a76f -> v/2 with si=100-v/2, hw_cfg_copy_ac13(si,di); loop flag_table_pop_far_thunk keys 79h/59h (y) -> state_mode_check(0) + jmp_loc_10b1c, 6Eh/4Eh (n) -> exit; bound_check_gated_4a83 - r29 overlay yes/no confirm loop."),
    "sub_102DFA": ("overlay_undecoded_body_102dfa", "low",
        "152B, ASM, in=0, no callees. push ds then undecodable hex dump (far 9Ah calls, loop near calls, retf tail) - overlay body not fully decoded by IDA."),
    "r36_e110": ("r36_slot_char_flag_scan", "medium",
        "135B, ASM, in=0, no callees. Takes bp+6 count; loops si=0..7 over 4Eh-stride rows at 7894h:dword_79B6E: when byte [row+si+28h]==FFh or fetched glyph bit7 set (glyph via dword_79E28 + word[row+30h+si*2]) writes 602Eh:3677h[si]=0, else =1; retf - r36 overlay slot char flag scan."),
    "sub_16CE5": ("ems_sample_stream_tick", "medium",
        "131B, ASM, in=0, 3 callees. EMS sample-stream tick: es=ds:93h page, index ds:81h vs limit ds:83h; refill via ems_paging_nested_save (ds:0ADh=1) + pit_period_set_1000 + call dword ds:14h; ds:77h==2 -> out 40h to AdLib port 388h; ds:77h==1 every-3rd ds:0C1h countdown; sample es:[bx] with optional signed gain shift (ds:0ABh), callback call dword ds:0C6h - EMS-backed sample stream tick."),
    "sub_1553F7": ("overlay_undecoded_body_1553f7", "low",
        "123B, ASM, in=0, no callees. push es then undecodable hex dump (mov es/call 9Ah stream, retf tail) - overlay body not fully decoded by IDA."),
    "r15_e16": ("r15_op_init_sequence", "medium",
        "105B, ASM, in=0, 7 callees. Fixed opcode sequence: op_dispatch(bl=5) -> save ax -> state_word_27476_set_ax -> op_dispatch(0Ah,4Dh,566h), far_cb_8(1), dispatch_22180_then_27474_8(di=0), farptr_table_invoke(0), dispatch_22174_stub, far_cb_8(0), far_cb_4(0,0,200,1,2), op_dispatch(8); pops es/ds; retn - r15 overlay op init sequence."),
    "r32_e120": ("r32_farptr_state_mirror_entry", "medium",
        "98B, ASM, in=0, 3 callees. Stores ax->ds:351Ah; mirrors 691Eh overlay state into 602Eh: word_637F8=[691FE]+1Ah, 63802/63800=word_69204/69202; far_cb_1; sub_2BFC3(49F7h:14B6h, 49F7h:1507h, 7A26E/7A270 args); far_cb_0; retf - r32 overlay farptr state mirror entry."),
    "r54_e119": ("r54_far_table_load_fragment", "low",
        "96B, ASM, in=0, no callees. Partial decode: al = far word table [bp+8 + ax*2] (shl ax,1 / les bx / mov al,es:[bx]) then imul 82h, tail decodes as retf 6894h misdecode - r54 overlay far-table load fragment, body not fully decoded."),
    "r64_e187": ("r64_window_scroll_step_entry", "low",
        "96B, ASM, in=0, 2 callees. Head misdecodes (and ds:6C9Ah,bl / or ax,39F7h), real tail: call slot3_window_scroll_up(6894h:0F32h,0,0,6) -> if != FFFFh entity_step_flags(69E64 far, 2104h, bp+0Eh, 10); then entity_step_flags(&bp-2, 0, ax, 8); retf - r64 overlay window scroll/record step entry, head undecodable."),
    "r35_e156": ("r35_undecoded_fragment", "low",
        "94B, ASM, in=0, no callees. Disassembly undecodable (dec si; add [bx+si-75h],dl; retn 0EBF7h misdecode) - r35 overlay fragment, not decoded as code."),
    "sub_6D838": ("r06_mode_step_tick", "medium",
        "83B, ASM, in=0, 1 callee. Gates on al==1; ds:4AB1h index bx: [bx+4A4Ah]->ds:4A97h, [bx+4A3Ah]+4AA1h->4A9Fh, ([bx+4A42h]*49A0h)>>8->4AB3h; calls loc_6D875 + r06_mode_dispatch_bx8; wraps index at 8 - r06 mode step tick."),
    "r52_e163": ("r52_data_fragment", "low",
        "76B, DATA, in=0, no callees. Garbage decode (push/or/lodsw/sbb stream) - r52 overlay data fragment, not decoded as code."),
    "r08_e29": ("r08_flag80_skip_gate", "medium",
        "70B, ASM, in=0, no callees. ds=es=6BE0h: if byte_6CD79==FFh or [word_6CD66+3] bit7 clear -> loc_1032DD continuation; bit7 set with byte!=FFh -> immediate pop ds; retf (dump covers first 26B, continuation path outside) - r08 overlay flag-80h skip gate entry."),
    "r36_e104": ("r36_farptr_8word_store", "medium",
        "63B, ASM, in=0, no callees. Stores 8 argument words (bp+0Ah..18h) into far struct at es:bx=[bp+6] (16 bytes, +0..+0Eh), retf - r36 overlay far-pointer 8-word store entry."),
    "r12_e41": ("r12_xy_nibble_mask_entry", "medium",
        "60B, ASM, in=0, no callees. Math on [si..+6] as q16.16: +333400h, div 3334h, >>4, -31, negate -> cx (x nibble); y: +333400h div 3334h -> ax; ax=(ax & 0F0h) & (cx & 0Fh); retf - r12 overlay xy nibble-mask entry."),
    "r12_e31": ("r12_fd09_state_record_entry", "medium",
        "58B, ASM, in=0, 2 callees. ds=es=709Fh, di=1D1h: if ax < word_71B8E record starts FD09h else FD0Bh + 05h byte; optional state_farptr_get -> ah=bl word; stores ax/bx/bp fields; r12_farptr_helper; retf - r12 overlay FD09h/FD0Bh state record entry."),
    "sub_1BFBC": ("irq_unmask_count_wait", "medium",
        "54B, ASM, in=0, 1 callee. es=7772h: zeroes word_77806, loops push cs; call irq_unmask_and_query until ax!=0 and word_77806 >= arg_0, final query; returns 1 if final query ax==0 else 0 - IRQ unmask/count wait gate."),
    "sub_161945": ("overlay_undecoded_body_161945", "low",
        "51B, ASM, in=0, no callees. push bp then undecodable hex dump (loop/jcc bytes, retf tail) - overlay body not fully decoded by IDA."),
    "r64_e189": ("r64_undecoded_fragment", "low",
        "50B, ASM, in=0, no callees. Garbage decode (adc ch,bl / push 0C08Eh / jmp far 8E68h:94BAh / retn 0D426h mix) - r64 overlay fragment, not decoded as code."),
    "r27_e62": ("r27_state_buffer_init_entry", "medium",
        "46B, ASM, in=0, 1 callee. es=7A32h: word 0AF68h=0, farptr 0AF40h/0AF3Eh = 7A32h:0AF96h; state_word_26400_get_zero(); dump ends mid-body before terminator - r27 overlay state buffer init entry."),
    "r60_e176": ("r60_data_fragment", "low",
        "43B, DATA, in=0, no callees. Garbage decode (mov di/push/sbb stream, jcxz) - r60 overlay data fragment, not decoded as code."),
    "r12_e28": ("r12_fd05_record_entry", "medium",
        "40B, ASM, in=0, no listed callees (near call unk_106AD0). ds=es=709Fh, di=1D1h: record FD05h + 0Bh byte + ax, then call unk_106AD0; restores; retf - r12 overlay FD05h record entry."),
    "r12_e24": ("r12_fd07_record_entry", "medium",
        "35B, ASM, in=0, no listed callees (near call unk_106AD0). ds=es=709Fh, di=1D1h: record FD07h + 0Ah byte + dx + ax fields, then call unk_106AD0; retf - r12 overlay FD07h record entry."),
    "sub_68291": ("overlay_undecoded_body_68291", "low",
        "31B, DATA, in=0, no callees. Head garbage (adc/add), plausible tail cmp byte es:[bx+1],3 -> loc_682E0 (inside ui_slot_record_init) and 79F34*17h index - overlay fragment not fully decoded by IDA."),
    "r15_e14": ("r15_flag_param_test_entry", "medium",
        "26B, ASM, in=0, 1 callee. Head misdecodes (cwd; adc al,0A3h); then bx=(cs:byte_10776A==0 ? 6 : 1Ah), ax=102h, call r15_flag_10788b_test; retn - r15 overlay flag param test entry."),
    "r33_e195": ("r33_data_fragment", "low",
        "25B, DATA, in=0, no callees. Head fsubr garbage, tail reads 602Eh:byte_61615 -> si and jmps loc_15ACBC (beyond entry) - r33 overlay data fragment."),
    "sub_20BC4": ("farptr_off1f710_scaled_set", "medium",
        "23B, ASM, in=0, no callees. ds=7B0Eh: cs:off_1F710 = (ax<<3) + 347Ah; pops; retn - scaled far-pointer offset table base setter."),
    "sub_27908": ("cs_vector_2218c_invoke", "medium",
        "22B, ASM, in=0, no callees. Far entry: cx=[bp+arg_4], lds si,[bp+arg_0], call cs:dword_2218C vector; restores; retf - cs:2218Ch vector invoke wrapper."),
    "r34_e106": ("r34_state_word5_set", "medium",
        "20B, ASM, in=0, 1 callee. es=602Eh: word_63955=5 then jmp loc_160BF4; linearly falls into call fixed_vec3_read - r34 overlay state word-5 set entry."),
    "sub_2513A": ("mouse_button_gate_far_wrapper", "medium",
        "17B, ASM, in=0, 1 callee. bp frame: forwards arg_0 to near mouse_button_gate_5762 (nop), restores, retf - mouse button gate far wrapper entry."),
    "sub_10A0B4": ("overlay_undecoded_body_10a0b4", "low",
        "16B, LEAF, in=0, no callees. push cx then undecodable hex dump (far 9Ah call, reg pops, retf tail) - overlay stub not fully decoded by IDA."),
    "r59_e179": ("r59_farptr_pair_push_entry", "low",
        "15B, DATA, in=0, no callees. mov es,502Eh; push es:word_537BD; push es:word_537AB - dump ends without terminator, partial entry - r59 overlay farptr pair push fragment."),
    "r32_e157": ("r32_mouse_gate_entry", "medium",
        "13B, ASM, in=0, 1 callee. ax==FFh -> call mouse_gate_far_entry, else jmp loc_156472 (beyond dump) - r32 overlay mouse gate entry stub."),
    "sub_10A00F": ("overlay_undecoded_body_10a00f", "low",
        "13B, ASM, in=0, no callees. push bp then undecodable hex dump (far 9Ah call, retf tail) - overlay stub not fully decoded by IDA."),
    "r02_e03": ("r02_farptr_pair_call_entry", "medium",
        "12B, LEAF, in=0, no callees. Pushes 2CF6h and 0CA8h as far-ptr pair, call near unk_10007F; retf - r02 overlay farptr pair call entry."),
    "sub_260B3": ("table_rec_load_scaled_far_wrapper", "medium",
        "12B, ASM, in=0, 1 callee. bx=[bp+arg_0]; push cs; call table_rec_load_scaled; pop bp; retf - table record load-scaled far wrapper."),
    "sub_2BFEB": ("tail_bridge_to_flag_gate_2e100_skip", "medium",
        "10B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp near flag_gate_2e100_skip (3 pad bytes) - tail-bridge stub into flag_gate_2e100_skip."),
    "r08_e08": ("r08_farptr_load_gate_entry", "medium",
        "8B, LEAF, in=0, 1 callee. call far r08_farptr_load_thunk; jnz unk_1031C8; retf - r08 overlay farptr load gate stub."),
    "sub_2BE97": ("tail_bridge_to_r05_farptr_dispatch_big", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r05_farptr_dispatch_big - tail-bridge stub into r05_farptr_dispatch_big."),
    "sub_2C365": ("tail_bridge_to_r30_config_block_link", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp near r30_config_block_link - tail-bridge stub into r30_config_block_link."),
    "sub_2C455": ("tail_bridge_to_r30_farobj_proc_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_farobj_proc_b (unk_6A2E1) - tail-bridge stub into r30_farobj_proc_b."),
    "sub_2C4C3": ("tail_bridge_to_ui_loadout_menu_enter_a", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_691F2+2) - tail-bridge stub into ui_loadout_menu_enter (variant A)."),
    "sub_2C581": ("tail_bridge_to_ui_loadout_menu_enter_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_6881D) - tail-bridge stub into ui_loadout_menu_enter (variant B)."),
    "sub_2C603": ("tail_bridge_to_r30_state_init_all_e", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_state_init_all - tail-bridge stub into r30_state_init_all (variant E)."),
    "sub_2C63F": ("tail_bridge_to_r30_entry_partial_d", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_entry_partial_d - tail-bridge stub into r30_entry_partial_d."),
    "sub_2C67B": ("tail_bridge_to_menu_event_dispatch", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far menu_event_dispatch (loc_67571) - tail-bridge stub into menu_event_dispatch."),
    "sub_2C6CB": ("tail_bridge_to_ui_loadout_menu_enter_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_loadout_menu_enter (loc_68EC4+4) - tail-bridge stub into ui_loadout_menu_enter (variant C)."),
    "sub_2C707": ("tail_bridge_to_r30_mode_set_637fc_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_mode_set_637fc_c (loc_6A153) - tail-bridge stub into r30_mode_set_637fc_c."),
    "sub_2C7C5": ("tail_bridge_to_r30_state_init_all_f", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_state_init_all (loc_66A32) - tail-bridge stub into r30_state_init_all (variant F)."),
    "sub_2C83D": ("tail_bridge_to_r30_state_init_all_g", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far r30_state_init_all - tail-bridge stub into r30_state_init_all (variant G)."),
    "sub_2C883": ("tail_bridge_to_ui_menu_transition_step_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_menu_transition_step (loc_67C5A+1) - tail-bridge stub into ui_menu_transition_step (variant B)."),
    "sub_2C90F": ("tail_bridge_to_ui_menu_frame_enter", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp far ui_menu_frame_enter (loc_67686+1) - tail-bridge stub into ui_menu_frame_enter."),
    "sub_10A009": ("cs_word_get_25499_far_wrapper", "medium",
        "6B, LEAF, in=0, 2 callees (record_script_exec_quad, cs_word_get_25499). call resolving to cs_word_get_25499/record_script_exec_quad then retf (0CBh shown as triplet) - far wrapper stub into cs_word_get_25499."),
    "sub_6F5DD": ("null_frame_retf_stub", "medium",
        "5B, ASM, in=0, no callees. push bp; mov bp,sp; pop bp; retf - empty frame no-op far stub."),
}

BANNED = ("sub_", "loc_", "off_", "byte_", "word_", "dword_", "unk_", "seg_")
CIDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def main():
    keys = list(NAMES)
    assert len(keys) == 66, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 66, "duplicate names"
    for n in names:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n), n
        assert not n.startswith(BANNED), n
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
