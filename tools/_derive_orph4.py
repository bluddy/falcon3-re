"""Validate and emit orphan-batch-4 names (66 fns) -> orph4_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "orph4_batch_names.json"

NAMES = {
    "r48_e191": ("r48_op_dispatch_batch_entry", "medium",
        "1470B, ASM, in=0, 4 callees. ~30x op_dispatch_far_entry(dst seg:off, val, [bp-2], 0Ah) state-init emissions over 7894h/602Eh/7A32h/639Eh fields (opcode-2/6/1 variants); zeroes 79B62/79D6A/79BD6; clamps 79F14 from dword_79E50[30h] when word_78940==0; opcode-8 out-ptr queries, flag2224a_set, farobj_field_scale_check(7894h:0F32,...); dump truncated at 300-insn cap mid-body - r48 overlay op dispatch batch entry."),
    "r39_e145": ("r39_ring_slot_render_entry", "medium",
        "686B, C, in=0, 5 callees. Height by 602Eh:63955 (6->64h, 7->96h, else 32h), [bp-6]=1C2h (450); far ptr 602Eh:616DC; sub_2C4F5(si); sub_2C58B(byte_63926,79BDA)->di; 8x sub_2C4FF draws with x=(di+{180,0,90,180,270,240,120,240}) mod 360 (slots 1-7 typed 7/8 + slot 8 wide 12Ch/15h) each + sub_2C59F; closes r39_farptr_call_gate(1, 5/6 by 63955, si) - r39 overlay ring slot render entry."),
    "r24_e60": ("r24_pane_toggle_menu_loop", "medium",
        "569B, C, in=0, 6 callees. 6E45h DGROUP modal loop: mouse_gate_far_entry, dispatch_22100, 3x unk_6DFF0 rect draws toggled by word_6E8CC (200h/0 -> 2 or 1), dispatch_220f4, bda_kb_flag_10000_get, word_6E8B7=4; key loop flag_table_pop_far_thunk -> 6E8D2 masked FF00h/DFh, r17_menu_event_loop, 10-way scan cs:239h -> jmp word cs:[bx+14h], 6E8CC pane flips via call 6E1EA; exit 6E8B7=0 - r24 overlay pane toggle menu loop."),
    "sub_4DC16": ("view_wrap_projection_entry", "medium",
        "551B, ASM, in=0, 6 callees. Head: two-component wrap probe [si+1]-=cs:word_2E108 and [si+3]-=cs:word_2E10A with 8000h carry test setting cx=1, early retn at +78B (traversal stops; 474B tail undumped; callee set view_projection/fixed_vec3_accumulate_b/vec_transform_scale_far/fixed_matrix_mul/farobj_altitude_scale_step/active_farptr_set) - camera view wrap/projection step entry."),
    "sub_299D5": ("record_span_mask_rebuild", "medium",
        "429B, ASM, in=0, 1 callee. cs:27968=FFFFh, 2796A=0, es:43BEh=cs:2796E; if !(cs:27966 & 1): loop cx iters copying 8 words from 441Eh table into es:43BEh and AND/OR-accumulating [si+6] masks into 27968/2796A; early retn before undumped loc_29A2D tail - record span mask rebuild sibling of record_span_build_and_dispatch."),
    "sub_69ACB": ("op_emit_far_state_step", "medium",
        "402B, ASM, in=0, 1 callee. Stores ax:dx -> 6DE8h:6E007/6E005; op_dispatch_far_entry opcode-6 allocs -> si, opcode-0Ah sets (64h/63AFh values), opcode-8 queries ([bp-4/-6]); far-ptr +43ADh / +0A0h end calc stored at 6DF27+18h/1Ah/1Ch/1Eh; mid-body triplet-undecodable region + near call unk_72A4C; leave/retf - far state op emit step."),
    "sub_17785B": ("overlay_undecoded_body_17785b", "low",
        "331B, C, in=0, no callees. enter 8,0 then all triplet-undecodable hex (far 9Ah stream, leave/retf tail) - overlay body not fully decoded by IDA."),
    "r39_e129": ("r39_column_bar_render_entry", "medium",
        "306B, C, in=0, 5 callees. sub_2C58B(1Ch,79BDA)->word_6390A=[bp-6]; far ptr 602Eh:616DC; 4x sub_2C4FF draws (slots 1,3 type7 19h-high, slot2 96h-high with 6390E, slot4 wide row 0Ah/32h) each + sub_2C59F; closes r39_farptr_call_gate(1,0,si) - r39 overlay column bar render entry."),
    "r36_e116": ("r36_slot_type_priority_scan", "medium",
        "262B, ASM, in=0, 1 callee. 7894h:byte_7A311=FFh; loops si over count=rec[1] (27h-stride records at [bp+6]); priority test byte [rec+0Ah] in order 0,2,1,3,4: when r36_farptr_helper(si)==0 store that code to byte_7A311 and exit - r36 overlay slot type priority scan."),
    "r36_e72": ("r36_record_copy_fragment", "low",
        "224B, DATA, in=0, 1 callee. Garbage head (add ax,14h decode) with plausible core: 4Eh-stride 79B6E record [bx+40h/42h] words -> 7894h:79D6C struct +0Ah/+0Ch/+0Eh, bytes [0..2]=1, jmp loc_16586F (r36_loadout_record_copy) - r36 overlay record copy fragment, not decoded as code."),
    "sub_12BD16": ("overlay_undecoded_body_12bd16", "low",
        "204B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (9Ah far calls, retf tail) - overlay body not fully decoded by IDA."),
    "sub_1BA1C": ("sbi_channel_flags_init", "medium",
        "186B, ASM, in=0, 4 callees. Head: 16x 7772h:0516h[si]=FFh channel flags, early retf at +31B (traversal stops; 155B tail undumped, callee set sbi_data_write/sbi_command_wait/channel_volume_store/channel_program_fetch_write) - SBI channel flags init entry."),
    "r36_e109": ("r36_mod_slot_index_entry", "medium",
        "164B, ASM, in=0, 1 callee. If 602Eh:byte_63954==0 set to 1; fixed_vec3_read() result & 0Fh mod byte_63954, returns remainder+2 - r36 overlay modulo slot index entry."),
    "sub_5711D": ("overlay_undecoded_body_5711d", "low",
        "149B, ASM, in=0, no callees. Fully garbage decode (and/loop junk referencing hud_heading_tape_draw locs, retn 0CE01h) - overlay body not decoded as code."),
    "sub_16472B": ("overlay_undecoded_body_16472b", "low",
        "135B, C, in=0, no callees. enter 2,0 then all triplet-undecodable hex (mov es/call 9Ah stream, leave/retf tail) - overlay body not fully decoded by IDA."),
    "sub_5E210": ("overlay_undecoded_body_5e210", "low",
        "131B, C, in=0, no callees. enter 0,10h; setalc then garbage (add stream, <undecodable 0x00>) - overlay body not decoded as code."),
    "r31_e151": ("r31_score_max_update", "medium",
        "122B, ASM, in=0, no callees. Gate bl>=ds:20h else skip; score=(cs:byte[bx+89Dh]/53h+1)*([bp+9]+1)/([bp+4]+1)*(1+([bp+7]<3?[bp+7]:0)); index bl=[bp+6]*2; keep max into cs:word[bx+11D5h] - r31 overlay score max update."),
    "sub_6E4EF": ("menu_mod_patch_row_set", "medium",
        "105B, ASM, in=0, no callees. Self-modifying: byte cs:6E148=0, cs:6E146=1 operand patches; index=(dx-33h)/7; if index < cs:6E106 store cs:6E104=index; retf - menu DGROUP row index set with operand patch."),
    "r54_e169": ("r54_farwrap_norm_fragment", "low",
        "97B, DATA, in=0, 1 callee. Partial: 64-bit neg of [bp-6:ax] -> [bp+0Ch], farwrap_24aef normalization -> si, +2000h/+4000h sign corrections, si idiv 2Eh; mid/tail undecodable (fcmovne) - r54 overlay farwrap normalization fragment."),
    "r54_e158": ("r54_index_resolve_step_entry", "low",
        "96B, ASM, in=0, 1 callee. Head misdecodes (fsub/add junk); scans si over 4Eh-stride records until 6894h:69B72, then 2x farobj_index_resolve_step (74h,[bp-2] -> dx:ax out; di,[bp+0Ch],[bp-6]) -> si; leave/retf - r54 overlay index resolve step entry, head undecodable."),
    "r67_e194": ("r67_entity_step_pair_entry", "low",
        "96B, ASM, in=0, 1 callee. Two entity_step_flags invocations (arg 1Eh=30; second out-ptr &bp-2), mid-body undecodable (insb/jnb garbage), stores 30h to ss:1524h words and 6894h:69E64 struct; retf - r67 overlay entity step pair entry, garbage region."),
    "sub_1020C9": ("overlay_undecoded_body_1020c9", "low",
        "91B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (9Ah far calls, retf tail) - overlay body not fully decoded by IDA."),
    "r32_e146": ("r32_scale_op_dispatch_step", "medium",
        "81B, ASM, in=0, 2 callees. Head misdecodes (6B); then les bx,es:50524 far ptr, ax=[bx]*[bx+2] product, op_dispatch_far_entry(prod, si, 0Ah), op_dispatch_far_entry(ds:0A3A4h, 0, si, 8), dispatch_220ec_invoke(7894h:79E64, 5, 10h); retf - r32 overlay scale op dispatch step."),
    "r32_e74": ("r32_hud_phase_reset_entry", "medium",
        "75B, ASM, in=0, 3 callees. flag_block_zero_5762_5c63 + r32_farptr_gate + unk_4335A + r32_hud_phase_dispatch sequence; if 4FC2h:4FD52 != FFFFh call unk_43D52(word); zero 7894h:79B60 and 79E86; retf - r32 overlay HUD phase reset entry."),
    "r27_e64": ("r27_table_copy_far_entry", "medium",
        "70B, ASM, in=0, no callees. Head misdecodes (1 insn); si=ds:0CA2h; loop until 31F0h:32BA4 <= si: ax=7A32h:[si*2-5108h] -> [7A32h:0AE96h far ptr + si*2], then ax=7A32h:0AF5Ah; retf - r27 overlay table copy to far pointer entry."),
    "sub_107231": ("overlay_undecoded_body_107231", "low",
        "62B, ASM, in=0, no callees. push bp then all triplet-undecodable hex (9Ah far calls, retf tail) - overlay body not fully decoded by IDA."),
    "sub_183BC": ("key_action_101_range_gate", "medium",
        "60B, ASM, in=0, 2 callees. Validates arg_2 in 0..5 and arg_0==101h else return 0; key_action_execute(101h) + key_action_execute_sbi(101h, si, 0, 0); return 1 - key action 101h range gate wrapper."),
    "r12_e32": ("r12_fd08_state_record_entry", "medium",
        "58B, ASM, in=0, 2 callees. ds=es=709Fh, di=1D1h: record FD08h (or FD0Ah when ax>=word_71B8E) + 08h byte; high branch adds state_farptr_get word; stores cl, bx, ax fields; r12_farptr_helper; retf - r12 overlay FD08h/FD0Ah state record entry."),
    "r08_e50": ("r08_flag80_xy_return", "medium",
        "51B, ASM, in=0, no callees. ds=6BE0h: byte_6CD79==FFh -> loc_1032B9 continuation (undumped); si=word_6CD66, test [si+3],80h set -> ax=[si+0Ah], bx=[si+0Ch], clc, retf (both fallbacks land in undumped +12B tail) - r08 overlay flag-80h xy return entry."),
    "sub_1BD31": ("sbi_channel_release_gate", "medium",
        "51B, ASM, in=0, 1 callee. If 7772h:unk_77B46 in {2,3,4} set word_77B36=1 and call sbi_channel_release_close; returns 1 - SBI channel release gate."),
    "r64_e192": ("r64_counter_decrement_entry", "low",
        "50B, ASM, in=0, no callees. Head misdecodes (3 insns); 6894h:69E50 far struct [bx+26h]+=1Eh (30); index=ss:15F4h*17h stride into ss:152Ch far ptr, dec byte es:[bx+13h]; retf - r64 overlay counter decrement entry, head undecodable."),
    "r12_e26": ("r12_ah0c_far_call_entry", "medium",
        "45B, ASM, in=0, no callees. push ax; ah=0Ch; call loc_10701D (in-function tail undumped, +30B beyond early retf); pop ax; retf - r12 overlay ah=0Ch sub-call entry."),
    "sub_1065A6": ("overlay_undecoded_body_1065a6", "low",
        "43B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (mov es/call 9Ah, retf tail) - overlay body not fully decoded by IDA."),
    "r12_e40": ("r12_farptr_helper_c_record_wrap", "medium",
        "40B, ASM, in=0, 1 callee. ds=es=709Fh, di=11CDh, al=byte_71BB9, jmp r12_farptr_helper_c (unk_106E32); second block copies 7 words 11CAh->1D1h then near call unk_106AD0; retn - r12 overlay farptr helper-c record wrap entry."),
    "r12_e39": ("r12_fd05d_record_entry", "medium",
        "34B, ASM, in=0, no listed callees (near call unk_106AD0). ds=es=709Fh, di=1D1h: record FD05h + 0Dh byte + byte_71BB8 word + byte_70A2A, then call unk_106AD0; retf - r12 overlay FD05h/0Dh record entry."),
    "sub_27415": ("fixed_dot3_product", "medium",
        "30B, ASM, in=0, no callees. 3-term fixed dot product: lodsw [si..+4] * [di],[di+2],[di+4] accumulating bx:bp, result ax:dx; js loc_2742F (beyond dump) else retn - 3-component fixed dot product."),
    "sub_101743": ("overlay_undecoded_body_101743", "low",
        "26B, ASM, in=0, no callees. push es then all triplet-undecodable hex (push 9Ah call stream, retf tail) - overlay stub not fully decoded by IDA."),
    "sub_278C6": ("cs_vector_22184_invoke_c", "medium",
        "25B, ASM, in=0, no callees. di=[bp+arg_0], ax=[bp+arg_2], call cs:dword_22184 vector; cs:27474=0Ch; retf - cs:22184h vector invoke with mode-0Ch set."),
    "sub_254FF": ("dispatch_22158_far_wrapper", "medium",
        "23B, ASM, in=0, 1 callee. les di=[bp+arg_0], cx=arg_4, bx=arg_6, push cs, call dispatch_22158_stub; retf - dispatch_22158 far wrapper entry."),
    "sub_27924": ("cs_vector_22190_invoke", "medium",
        "22B, ASM, in=0, no callees. cx=arg_4, lds si,[bp+arg_0], call cs:dword_22190 vector; retf - cs:22190h vector invoke wrapper."),
    "sub_103040": ("overlay_undecoded_body_103040", "low",
        "20B, ASM, in=0, no callees. push ds then all triplet-undecodable hex (mov es/mov byte stream, retf tail) - overlay stub not fully decoded by IDA."),
    "r15_e11": ("r15_state_107650_far_wrapper", "medium",
        "16B, LEAF, in=0, 1 callee. ds=es=cs, push cs, call r15_state_107650_set, retf - r15 state 107650h far wrapper entry."),
    "sub_10A0DB": ("overlay_undecoded_body_10a0db", "low",
        "16B, LEAF, in=0, no callees. push cx then all triplet-undecodable hex (9Ah far call, retf tail) - overlay stub not fully decoded by IDA."),
    "sub_1018A0": ("overlay_undecoded_body_1018a0", "low",
        "15B, LEAF, in=0, no callees. push ds then all triplet-undecodable hex (mov es/mov byte, retf tail) - overlay stub not fully decoded by IDA."),
    "r33_e121": ("r33_args3_far_tail", "medium",
        "13B, ASM, in=0, no callees. Head misdecodes (2 insns); push 1, 0, 0Fh; jmp loc_15AAFA (far tail beyond entry) - r33 overlay 3-arg far tail jump entry."),
    "sub_10A052": ("overlay_undecoded_body_10a052", "low",
        "13B, ASM, in=0, no callees. push bp then all triplet-undecodable hex (mov/call 9Ah, retf tail) - overlay stub not fully decoded by IDA."),
    "r15_e34": ("r15_state_byte_set", "medium",
        "12B, ASM, in=0, no callees. cs:byte_107A90=al; retf - r15 overlay state byte set stub."),
    "sub_6D7F3": ("r06_mode_state_seed_set", "medium",
        "12B, LEAF, in=0, no callees. ds:4AC0h=1, ds:4A99h=082Eh; retf - r06 mode state seed setter stub."),
    "sub_2BFF5": ("tail_bridge_to_viewvec_loop_project", "medium",
        "10B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp viewvec_loop_project (3 pad bytes) - tail-bridge stub into viewvec_loop_project."),
    "r38_e138": ("r38_popf_fragment", "low",
        "8B, LEAF, in=0, no callees. push es; popf; mid misdecode (add ss:[bx+5Eh],bl); leave; retf - r38 overlay popf fragment stub, partial decode."),
    "sub_2C0A9": ("tail_bridge_to_r05_flag_xor_45e4e", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r05_flag_xor_45e4e (3 pad bytes) - tail-bridge stub into r05_flag_xor_45e4e."),
    "sub_2C3DD": ("tail_bridge_to_ui_menu_panel_init_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_menu_panel_init (loc_66E65+1) - tail-bridge stub into ui_menu_panel_init (variant C)."),
    "sub_2C45F": ("tail_bridge_to_ui_slot_count_tally", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_slot_count_tally (loc_6B6F6+2) - tail-bridge stub into ui_slot_count_tally."),
    "sub_2C4CD": ("tail_bridge_to_r30_state_init_all_h", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r30_state_init_all (variant H) - tail-bridge stub into r30_state_init_all."),
    "sub_2C5A9": ("tail_bridge_to_ui_loadout_menu_enter_d", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_68792+1) - tail-bridge stub into ui_loadout_menu_enter (variant D)."),
    "sub_2C60D": ("tail_bridge_to_menu_choice_tail_dispatch", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp menu_choice_tail_dispatch (loc_67BAA) - tail-bridge stub into menu_choice_tail_dispatch."),
    "sub_2C649": ("tail_bridge_to_r30_farobj_proc_c", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r30_farobj_proc (unk_6A260) - tail-bridge stub into r30_farobj_proc (variant C)."),
    "sub_2C685": ("tail_bridge_to_ui_loadout_menu_enter_e", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_684BA) - tail-bridge stub into ui_loadout_menu_enter (variant E)."),
    "sub_2C6D5": ("tail_bridge_to_ui_menu_page_args_setup", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_menu_page_args_setup (loc_69CA4+2) - tail-bridge stub into ui_menu_page_args_setup."),
    "sub_2C71B": ("tail_bridge_to_ui_loadout_menu_enter_f", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp ui_loadout_menu_enter (loc_68926+3) - tail-bridge stub into ui_loadout_menu_enter (variant F)."),
    "sub_2C7ED": ("tail_bridge_to_menu_pending_task_step", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp menu_pending_task_step (loc_67B40+1) - tail-bridge stub into menu_pending_task_step."),
    "sub_2C847": ("tail_bridge_to_r30_state_init_all_i", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp r30_state_init_all (variant I) - tail-bridge stub into r30_state_init_all."),
    "sub_2C88D": ("tail_bridge_to_display_palette_hud_refresh_step", "medium",
        "8B, ASM, in=0, 2 callees. call tail_bridge_overlay_load; jmp display_palette_hud_refresh_step (loc_67877+1) - tail-bridge stub into display_palette_hud_refresh_step."),
    "r35_e172": ("r35_loop_fragment", "low",
        "6B, LEAF, in=0, no callees. loop unk_1637A4; les cx,[bx+si] misdecode; leave; retf - r35 overlay loop fragment stub."),
    "sub_10A05F": ("flag_byte_get_far_wrapper", "medium",
        "6B, LEAF, in=0, 2 callees (hw_port_bit_test_retn, flag_byte_get). call resolving to flag_byte_get; retf (0CBh triplet) - flag byte get far wrapper stub."),
    "r33_e114": ("r33_tail_epilogue_stub", "medium",
        "4B, LEAF, in=0, no callees. pop di; pop si; leave; retf - r33 overlay tail epilogue stub."),
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

