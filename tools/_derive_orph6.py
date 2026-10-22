"""Validate and emit orphan-batch-6 names (66 fns) -> orph6_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "orph6_batch_names.json"

NAMES = {
    "r22_e57": ("r22_slot_select_modal_loop", "medium",
        "936B, C, in=0, 9 callees. 6E45h DGROUP modal loop: 4x slot setup calls to unk_6DFF0 (word pairs 6E4A6..6E4B0 / 6E6D2..6E6E4 gated by 6E8C5 slot index 0-3 vs 6E8C5 parity 1/2), 11-word event compare loop at cs:3A8h with jmp cs:[bx+16h] dispatch (each arm re-runs slot setup via 0x6E1EA check, sets 6E8C5, r14_farptr_call_gate + r22_farptr_helper + overlay_ems_farptr_setup(2/0)), r17_menu_event_loop per iteration, flag_table_pop_far_thunk + dispatch_22100_invoke + dispatch_220f4_invoke_2arg + mouse_gate_far_entry + bda_kb_flag_10000_get bookkeeping, exits when 6E8B7==0 - r22 slot select modal loop."),
    "r39_e136": ("r39_rotational_render_entry", "medium",
        "595B, C, in=0, 6 callees. Sets 602Eh:63910=400, 6390C=450, si=byte_63926; 4x sub_2C4FF op-mode 1..4 draws at rotation (6390A, +5Ah, +0B4h, +10Eh) mod 360 (idiv 168h) each + sub_2C59F, op 5 (12Ch wide) + op 6 (79BDA slot), closes r39_farptr_call_gate(1, 6, di=0) - r39 overlay rotational render entry."),
    "r39_e135": ("r39_rotational_render_entry_b", "medium",
        "566B, C, in=0, 5 callees. si = sub_2C58B(byte_63926, 79BDA); 6x unrolled sub_2C4FF op draws at rotation si+{0B4h,5Ah,10Eh,10Eh,0B4h+78h} mod 360 (div 168h, width 1C2h/400h, di=64h steps) each + sub_2C59F, tail ops 7 and 5, closes r39_farptr_call_gate(1, 2, 0) - r39 overlay rotational render entry B."),
    "sub_162882": ("overlay_undecoded_body_162882", "low",
        "530B, C, in=0, no callees. enter 6,0 then all triplet-undecodable hex (9Ah far-call stream, leave/retf tail bytes) - overlay body not fully decoded by IDA."),
    "r39_e153": ("r39_dual_index_render_entry", "medium",
        "423B, C, in=0, 5 callees. si=3; sub_2C58B(byte_63926/63927, 79BDA) -> 6390A; 4x sub_2C4FF draws (ops 1/2/3/4 at y=46h w=1C2h, ops 2/3 keyed on byte_63926 vs byte_63927) + op 5 (12Ch/0Fh), each + sub_2C59F, closes r39_farptr_call_gate(1, 7, 0) - r39 overlay dual-index render entry."),
    "sub_16B4DC": ("overlay_undecoded_body_16b4dc", "low",
        "372B, C, in=0, no callees. enter 0Ah,0 then all triplet-undecodable hex (9Ah far-call stream, leave/retf tail bytes) - overlay body not fully decoded by IDA."),
    "r39_e143": ("r39_variant_switch_render_entry", "medium",
        "321B, C, in=0, 5 callees. si = 2 or 3 by [bp+6]; sub_2C4FF ops 1/2/3 (y=46h w=1C2h + 12Ch/0Fh op 3) + sub_2C59F each; then 602Eh:word_6397A 5-way jmp cs:jpt_16A492 switch (values 0-4 pick gate op 9/8/10/7, 2 arms jmp $+2) closing r39_farptr_call_gate(1, op, 0) - r39 overlay variant switch render entry."),
    "sub_106721": ("overlay_undecoded_body_106721", "low",
        "286B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (9Ah far calls, retf tail) - overlay body not fully decoded by IDA."),
    "sub_5E97E": ("farobj_ems_behavior_init", "low",
        "249B, C, in=0, 4 callees (op_accumulate_dispatch, ems_farptr_table_init, farobj_behavior_dispatch_step, farobj_altitude_scale_step). Body dump dies after enter 0,0 + xor cl,[bp+di] + <undecodable 0x00> so only the callee set is readable - farobj EMS behavior init/step cluster, named from callees."),
    "sub_189819": ("record_pool_admit_demote", "medium",
        "218B, C, in=0, no callees. Walks 66B records at 6894h:69E3A (stride 42h, count at 6AE3A far ptr +0A8Dh): counts +63h==0 (di) and ==1 (cx); returns 1 when di >= [bp+6], 0 when arg <= cx, else demotes: prio=[bp-2] from 64h down to 1Dh, records with +62h==prio get +63h=0 (di++) until quota met - record pool admit-by-demote."),
    "sub_10A5A0": ("overlay_undecoded_body_10a5a0", "low",
        "201B, C, in=0, no callees. enter 2,0 then all triplet-undecodable hex (9Ah far-call stream, leave/retf tail bytes) - overlay body not fully decoded by IDA."),
    "r35_e100": ("r35_field_scale_op_step", "medium",
        "181B, C, in=0, 3 callees. Guard 602Eh:byte_63989==8 else retn; mode_record_field_lookup(7894h:0F5A, 4FC2h:4FD52); farobj_field_scale_check twice (7894h:0F32 vs 602Eh:63031/6302F and 6310C/6310A); op_dispatch_far_entry ops 4 -> 0Ch (602Eh:68F, 76E) -> 8 (ss:&[bp-2]) - r35 field scale op step."),
    "r36_e112": ("r36_record_grids_clear", "medium",
        "160B, C, in=0, no callees. Zeros 8x130B records at 7894h:79BEC (stride 82h), 16x23B records at 79E6C (stride 17h), word_79B62, word_79EEC, and 602Eh:byte_63952 - r36 overlay record grids clear."),
    "sub_15CC1A": ("overlay_undecoded_body_15cc1a", "low",
        "142B, ASM, in=0, no callees. push bp then all triplet-undecodable hex (mul/imul-style stream, retf tail) - overlay body not fully decoded by IDA."),
    "r35_e107": ("r35_mode8_state_init", "medium",
        "132B, ASM, in=0, no callees. Sets 602Eh:byte_63989=8 (the r35_e100 guard), 63955=14h(20), 7894h:79B6E record [+88Ch]=20 and stride-4Eh record [+4]=20 (index word_79BDA=0 -> 63925), ors 60964|=40h and 7A32h:85067|=1 (palette dirty); es:67Ah=4Fh; head misdecodes (pusha vs tail pop bp) - r35 mode-8 state init."),
    "sub_103087": ("overlay_undecoded_body_103087", "low",
        "127B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (9Ah far-call stream, retf tail) - overlay body not fully decoded by IDA."),
    "r36_e101": ("r36_slot_max_flag_pick", "medium",
        "112B, C, in=0, no callees. Scans 8 slot flags at 602Eh:[si+3677h]; for active slots reads arg record (stride 4Eh @ 7894h:79B6E) byte +28h+si as index into 602Eh:3689h table, keeps max value (cx) and slot (di), clears winning slot flag 3677h+di, returns slot index or 0FFFFh - r36 slot max flag pick."),
    "r33_e128": ("r33_garbage_fragment", "low",
        "103B, ASM, in=0, no callees. Fully garbage decode from entry (sar [bp+si+4Eh],0F7h / jmp far 8E78h:94BAh / retn 0C426h) - r33 overlay fragment with no coherent core."),
    "r53_e166": ("r53_map_window_quota_step", "medium",
        "96B, ASM, in=0, 1 callee. Incs es:[517DA]+1Fh; loop resets 6894h:69E3A+1Dh counter to 0, and when 6AE3A+1Dh > 200 uses slot2_map_window_load()&7FFF%200+200 as new quota di for 69E3A+1Dh, incrementing 69E3A+21h when its old count > di - r53 map window quota step."),
    "r55_e78": ("r55_entity_flags_op_step", "medium",
        "96B, ASM, in=0, 1 callee. Head misdecodes (or cl,[bx+di-2FBAh] / mov ss,ax junk); 3x entity_step_flags calls: (far ptr es:14FAh/14FCh +7F9h, op 294h, [bp-30h]), (6894h:69E3A far ptr +565h, op 294h, [bp-30h], 0Ah), (ss:&[bp-30h], [bp-30h], op 8) - r55 entity flags op step."),
    "r67_e197": ("r67_flags_op_garbage_fragment", "low",
        "96B, ASM, in=0, 2 callees (entity_step_flags, game_state_setup_multi). Starts mid-tail (add sp,0Ah; 1x entity_step_flags ss:&[bp-2] op 8) then decodes to garbage (aam 1Eh / adc al,26h / <undecodable 0xC7>), remainder undumped - r67 fragment."),
    "sub_2408F": ("fixed_vec3_cross", "medium",
        "86B, ASM, in=0, no callees. 3x 32-bit imul/sub producing di[0..2] as 16:16 pairs: dx:ax = bx[2]*si[4]-bx[4]*si[2], bx[0]*si[4]-bx[4]*si[0], bx[2]*si[0]-bx[0]*si[2] - fixed-point vec3 cross product (bx x si -> di)."),
    "r48_e91": ("r48_field_slot_scan_store", "medium",
        "80B, ASM, in=0, 1 callee. Head misdecodes (mov bh,0F0h / out dx,al junk); mode_record_field_lookup(far ptr es:14FAh:14FCh +3); on hit stores [bp-1] to 7A32h:byte_8506C and returns, else increments [bp-1] looping (jl unk_1791A8) while < 6, exhaust -> 8506C=0FFh - r48 field slot scan store."),
    "start": ("startup_entry_stack_swap", "medium",
        "73B, ASM, in=0, 3 callees (startup_arena_init, startup_overlay_init, sub_2BFAF). Program startup stub: saves es/ds to cs:2B4B6/2B4B8, ds=seg021, startup_arena_init, optional stack swap (cli; ss=ds:0C0Fh, sp=200h) around startup_overlay_init, restores ss/sp, loads es:ds from ds:0A86/0A88, far-jumps sub_2BFAF - startup entry with stack swap."),
    "r33_e90": ("r33_record_field_range_check", "medium",
        "68B, ASM, in=0, no callees. Returns 1 iff 0 < record byte +3 (stride 4Eh at 7894h:79B6E, arg index) < 4, else 0 - r33 record field range check."),
    "r52_e167": ("r52_indexed_pair_step", "low",
        "61B, DATA, in=0, 1 callee. Head undecodable (cli / adc al,3 / fsub dword ds:578Ah junk) then index=al<<2 pushes 602Eh:[bx+1AE8h] and [bx+2AD6h] pair into dgroup_save_reg_dxbp, then push 6894h:1F32h + 14h-stride 69D3E index - dump ends mid-les - r52 indexed pair step fragment."),
    "sub_10656B": ("overlay_undecoded_body_10656b", "low",
        "59B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (retf tail) - overlay body not fully decoded by IDA."),
    "r07_e48": ("r07_angle_xy_norm_pair", "medium",
        "57B, ASM, in=0, 2 callees. Guard 6BE0h:word_6CCF9!=0FFFFh else early exit; ds=54AFh, si=593AA, di=0F03: angle_xy_far then push ax, angle_quad_norm_far, div 2940h -> bx, pop ax, clc, retf - r07 angle xy/quad norm pair."),
    "r34_e96": ("r34_flag_slot_pick", "medium",
        "51B, ASM, in=0, no callees. Scans 6 stride-4 entries at 602Eh:[bx+1] (bx=cx*4) for value 1; on hit stores index cl to 7894h:byte_7A30A and returns 1, else 0 - r34 flag slot pick."),
    "r48_e165": ("r48_op_wide_entry_step", "medium",
        "50B, ASM, in=0, 2 callees. Head misdecodes (or al,9Ah / fsubr dword ds:1F6Ch) then add sp,0Ah, op_dispatch_far_wide(2, 0, 0, si, 0Eh), op_dispatch_far_entry(ss:&[bp-28h], 0, [bp-28h], 8), epilogue - r48 op wide/entry step."),
    "sub_279E5": ("cs_bitfield_byte_extract", "medium",
        "50B, ASM, in=0, no callees. ds=cs:1F712; si=cs:word_27984 + byte_2798A*byte_27982 + (byte_27989>>3), cx=byte_27989&7; lodsb, shl cl, shl 1, return byte - cs packed bitfield byte extract."),
    "r33_e92": ("r33_vec3_lowbyte_avg", "medium",
        "45B, ASM, in=0, 1 callee. 6x fixed_vec3_read(); sum += (ax&0FFh) % 64h(100); returns sum/6 (quotient in ax) - r33 vec3 low-byte average."),
    "r07_e54": ("r07_list_heads_init", "medium",
        "42B, ASM, in=0, no callees. Head misdecodes (add [bx+0Ch],bh); movsw pairs, si=10h/di=12h movsw x2, then stores ax->ds:2, bx->ds:8, dx->ds:0Eh with each target's first byte zeroed, pop ds/es, retn - r07 three list-head init."),
    "r61_e164": ("r61_garbage_fragment", "low",
        "37B, ASM, in=0, no callees. Fully garbage decode from entry (stosw / adc / lahf / xlat junk, retn tail) - r61 overlay fragment with no coherent core."),
    "sub_10C26": ("overlay_seg_word_set2_if3", "medium",
        "33B, ASM, in=0, 2 callees. overlay_seg_word_read(cs, 6) -> ax; if ax==3 and cs:byte_1084B==0 then overlay_seg_word_write(2, cs, 6) - sets overlay seg word 6 to 2 when currently 3 and gate clear."),
    "r12_e10": ("r12_flag_offset_init", "medium",
        "28B, ASM, in=0, 1 callee. ds=709Fh; flag_gate_2e100_get_ax()+11h -> ds:71B8E; ds:70A3D=ds:70A3F=11h - r12 flag offset init."),
    "sub_10A08A": ("overlay_undecoded_body_10a08a", "low",
        "26B, ASM, in=0, no callees. push cx then all triplet-undecodable hex (3x 9Ah far calls, retf tail) - overlay body not fully decoded by IDA."),
    "sub_24DA0": ("far_cb_with_args_far_wrapper", "medium",
        "24B, ASM, in=0, 1 callee. bx=[bp+arg_0], di=[bp+arg_2], lds si=[bp+arg_4], push cs, far_cb_with_args, restore, retf - far wrapper marshalling three far-pointer args into far_cb_with_args."),
    "sub_10188A": ("overlay_undecoded_body_10188a", "low",
        "22B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (retf tail) - overlay body not fully decoded by IDA."),
    "r07_e49": ("r07_state_byte_skip_gate", "medium",
        "21B, ASM, in=0, no callees. ds=es=6BE0h; if byte_6CD0E==0FFh restore and retf, else jmp unk_102796 continuation - r07 state byte skip gate."),
    "r12_e43": ("r12_render_cb_setup", "medium",
        "19B, ASM, in=0, 2 callees. cs:byte_10614A=cl; bx=3Eh r12_cb_args_render(cs), cx=48h r12_farptr_helper_b, retf - r12 render callback setup stub."),
    "r58_e68": ("r58_garbage_fragment", "low",
        "16B, DATA, in=0, no callees. Fully garbage decode from entry (lodsw / pop es / rcr junk) - r58 overlay fragment with no coherent core."),
    "r07_e15": ("r07_state_byte_toggle", "medium",
        "15B, LEAF, in=0, no callees. ds=6BE0h; xor ds:byte_6CD53, 1; retf - r07 state byte bit toggle."),
    "r36_e102": ("r36_entity_f38_1a_step", "medium",
        "14B, ASM, in=0, 1 callee. entity_f38_set_8fc(1Ah), inc ax, retf - returns callee result + 1."),
    "sub_109FBD": ("overlay_undecoded_body_109fbd", "low",
        "13B, ASM, in=0, no callees. push bp then all triplet-undecodable hex (9Ah far call, pop bp/retf tail) - overlay body not fully decoded by IDA."),
    "sub_24E6E": ("bda_417_mask_clear_far_wrapper", "medium",
        "13B, ASM, in=0, 1 callee. ax=[bp+arg_0], push cs, bda_417_mask_clear, retf - far wrapper for the BDA 417h mask clear."),
    "sub_1004BF": ("overlay_undecoded_body_1004bf", "low",
        "12B, LEAF, in=0, no callees. mov ax,2CF6h then all triplet-undecodable hex (retf tail) - overlay body not fully decoded by IDA."),
    "sub_24A85": ("trig_table_lookup_83a5_far_wrapper", "medium",
        "11B, ASM, in=0, 1 callee. ax=[bp+arg_0], call trig_table_lookup_83a5, retf - far wrapper for the 83Ah trig table lookup."),
    "sub_4DE6C": ("cs_byte_2e12b_store", "medium",
        "10B, ASM, in=0, no callees. mov byte ptr cs:2E12B (word_2E12A+1), al; retf - one-byte cs store paired with word_2E12A."),
    "sub_2BE15": ("tail_bridge_2d63a", "medium",
        "8B, ASM, in=0, 1 callee. call tail_bridge_overlay_load; jmp far 2CF6h:6DAh (linear 0x2D63A, raw unnamed target) - tail-bridge stub."),
    "sub_2C2F7": ("tail_bridge_to_sprite_blend_0ad2d", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp sprite_blend_0ad2d - tail-bridge stub into sprite_blend_0ad2d."),
    "sub_2C423": ("tail_bridge_to_r33_farptr_gate_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r33_farptr_gate_c - tail-bridge stub into r33_farptr_gate_c."),
    "sub_2C473": ("tail_bridge_to_r06_table_zero_30b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r06_table_zero_30b - tail-bridge stub into r06_table_zero_30b."),
    "sub_2C51D": ("tail_bridge_to_ui_loadout_menu_enter_h", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_68921+2) - tail-bridge stub into ui_loadout_menu_enter (variant H)."),
    "sub_2C5C7": ("tail_bridge_to_mode_session_state_mirror_init_b", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp mode_session_state_mirror_init (loc_66C68+1) - tail-bridge stub (variant B)."),
    "sub_2C621": ("tail_bridge_to_ui_loadout_menu_enter_i", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_6864F+1) - tail-bridge stub into ui_loadout_menu_enter (variant I)."),
    "sub_2C65D": ("tail_bridge_to_ui_menu_transition_step_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_menu_transition_step (loc_67E1A+2) - tail-bridge stub (variant C)."),
    "sub_2C699": ("tail_bridge_to_farobj_record_clear_fields", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp farobj_record_clear_fields (loc_68052) - tail-bridge stub into farobj_record_clear_fields."),
    "sub_2C6E9": ("tail_bridge_to_ui_menu_panel_init_d", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_menu_panel_init (loc_6728C) - tail-bridge stub into ui_menu_panel_init (variant D)."),
    "sub_2C757": ("tail_bridge_to_r30_state_init_all_m", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r30_state_init_all (variant M) - tail-bridge stub into r30_state_init_all."),
    "sub_2C801": ("tail_bridge_to_ui_menu_frame_enter_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_menu_frame_enter (loc_6772D) - tail-bridge stub into ui_menu_frame_enter (variant C)."),
    "sub_2C865": ("tail_bridge_to_r30_state_init_all_n", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r30_state_init_all (variant N) - tail-bridge stub into r30_state_init_all."),
    "sub_2C8A1": ("tail_bridge_to_ui_loadout_menu_enter_j", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_68809+2) - tail-bridge stub into ui_loadout_menu_enter (variant J)."),
    "sub_109FCA": ("state_byte_2549e_far_wrapper", "medium",
        "6B, LEAF, in=0, 2 callees (record_script_exec_quad, state_byte_2549e_get - dup-cref at the call target). call state_byte_2549e_get (no args pushed) then retf - 6B far wrapper around the state byte getter."),
    "r35_e182": ("r35_frame_epilogue_stub", "medium",
        "5B, LEAF, in=0, no callees. add sp,8; pop bp; retf - r35 overlay frame epilogue tail stub."),
    "sub_6EC14": ("data_fragment_6ec14", "low",
        "3B, DATA, in=0, no callees. sbb ax,[bx+si]; inc cx - 3-byte data fragment, not a function."),
}

BANNED = ("sub_", "loc_", "off_", "byte_", "word_", "dword_", "unk_", "seg_")

def main():
    raw = NAMING.read_text(encoding="utf-8")
    existing = set(re.findall(r"^\s+name: (\S+)", raw, re.M))
    keys = list(NAMES)
    if len(keys) != 66:
        print("COUNT: %d != 66" % len(keys)); sys.exit(1)
    names = [v[0] for v in NAMES.values()]
    if len(set(names)) != len(names):
        dups = sorted({n for n in names if names.count(n) > 1})
        print("DUPES:", dups); sys.exit(1)
    for k, (n, conf, notes) in NAMES.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) or not n.isascii():
            print("BAD NAME:", k, n); sys.exit(1)
        if n.startswith(BANNED):
            print("BANNED PREFIX:", k, n); sys.exit(1)
        if n in existing:
            print("COLLISION:", n); sys.exit(1)
        if conf not in ("medium", "low"):
            print("BAD CONF:", k, conf); sys.exit(1)
    out = {k: [v[0], v[2], v[2] + " conf: " + v[1], v[1]] for k, v in NAMES.items()}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n",
                   encoding="utf-8", newline="\n")
    print("OK 66 ->", OUT)

if __name__ == "__main__":
    main()
