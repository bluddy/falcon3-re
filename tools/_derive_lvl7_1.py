import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 78 Level-7 (21, LEVEL COMPLETE)
analysis = {
 "sub_12895": ("slot2_map_window_refresh",
   "FAR retf (12B LEAF): cs:byte_11C88=al; if al==0 retn; call slot2_map_window_read; retf; 2 callers (sub_3001E, sub_32C62)",
   "12B leaf, cd=0, in=2, callee slot2_map_window_read. Gated map-window refresh: stores the gate byte cs:11C88 and, when non-zero, re-reads the 5x5 slot2 window (callers sub_3001E / sub_32C62 pass the mode). conf: med-high", "med-high"),
 "sub_10CC3": ("op_cstring_bank_far_entry",
   "FAR retf (21B): save ds/es/si/di; lds dx,[bp+arg_0] (load caller far ptr); push cs, call op_cstring_bank_load; restore; retf; NO static caller (indirect far-call target, dyn=24)",
   "21B far wrapper, cd=0, in=0, callee op_cstring_bank_load. Far entry trampoline for the 13-cstring bank loader: converts the seg:off arg pair into ds:dx and tail-calls op_cstring_bank_load -- the dynamic-call target reached 24x in traces. conf: med-high", "med-high"),
 "sub_184F1": ("kb_record_load_far",
   "FAR retf (18B): push [bp+arg_2], push [bp+arg_0]; call kb_record_load; pop cx, pop cx; retf; 1 caller (sub_10F1E)",
   "18B far wrapper, cd=0, in=1, callee kb_record_load. Far trampoline for kb_record_load (dyn=10), forwarding the two far-ptr args. conf: med-high", "med-high"),
 "sub_1A8BF": ("kb_preset_table_load",
   "FAR retf (62B): op_dispatch_far_entry(6, 9A20:0) open -> di (handle); loop si=0..0x22 (35): kb_preset_record_scatter(di handle, si index); op 8 close; retf; 1 caller (mode_slot_setup)",
   "62B, cd=16, in=1, callees op_dispatch_far_entry (op 6 open / 8 close) + kb_preset_record_scatter x35. Keyboard preset table loader: opens the 9A20:0 resource and scatters all 35 preset records into the 7772:6D6/6F4 0x3C-stride tables via kb_preset_record_scatter. conf: med-high", "med-high"),
 "sub_47A9B": ("r32_hud_phase_dispatch",
   "FAR (299B, 5 attached entries, partial): entry0 (47A9B): es=63FD; gate ds:6847A: <3 tail into sub_37A0A internals (37AAE+2), <=4 tail 37AC1+1, else zero [bx+15h] for 10 records stride 0x1A; retf. Entry1 (47AC2): call hud_timer_countdown_draw(+4, bx=0xA, cx=0xA); loop 63FD records stride 0x1A: gate [bx+14] (test 8, 0x606 mask, [bx+15]!=0) -> rect_clip_then_dispatch_2209c ops 0xE and 4 per record; retf. Helpers: 47B10 (ds=54AF scale table 47AE*di -> ah:dl), 47B2A (same + fixed_matrix_mul + sprite_project_screen_y projection), 47B68 (cbw*4 -> 54AF:1734 farptr table, al&0xF gate, 1980/1940 table writes + fixed_vec3_accumulate_b); 6 callers (r32_e74, sub_2FD42, sub_3CE92, sub_3E552, sub_3F861, sub_3FFEF)",
   "299B far, cd=0, in=6, callees hud_timer_countdown_draw + rect_clip_then_dispatch_2209c + fixed_matrix_mul + sprite_project_screen_y + fixed_vec3_accumulate_b (+ sub_37A0A tails). R32 HUD phase dispatcher: the 6847A phase word routes into the sub_37A0A rowlist internals or clears the 10-record 63FD flag table; the second entry draws the timer countdown then rect-dispatches ops 0xE/4 per gated record, with the 54AF scale/matrix/projection helpers attached. conf: med", "med"),
 "sub_12D2F": ("slot2_map_window_update",
   "NEAR retn (242B, partial): row delta ax=11C26-11C10: |delta|>1 (or <-1) -> full slot2_map_window_read + gate 11CF3/11C88==FF -> far sub_2BEAB; else row AND col deltas in [-1,1] and not both 0: publish 11C0E/11C10/11C12=(cx<<5), clamp 11C0C/11C0D via clamp_al4_ge, slot2_handle_alloc, incremental fill: row read (bh!=0, bp=+/-0x7C/0xFF7C, slot2_window_row_read) + col read (bl!=0, bp=-0x7C/0xFF84, slot2_window_col_read), slot2_handle_release, optional far 2BEAB; 5 callers (entity_update_batch, sub_32453, sub_3252B, sub_327BE, sub_329B1)",
   "242B, cd=11109, in=5, callees slot2_map_window_read + slot2_window_row_read/col_read + slot2_handle_alloc/release + clamp_al4_ge + far sub_2BEAB. Slot2 map-window updater: on a 1-cell move refreshes just the entered row+column through a fresh handle (11C0C/0D clamped to 0..4), on a larger jump re-reads the whole 5x5 window, then optionally hands off to the far 2BEAB (the hot incremental path behind entity_update_batch). conf: med-high", "med-high"),
 "sub_13755": ("slot3_tile3x3_load",
   "NEAR (139B, partial): release 9 handles at ds:150.. (lodsw !=-1 -> op_dispatch bx=2); slot3_handle_alloc_pair; 11BC4=11C26, 11BC2=11C24 (center); load 9 tile records around (center-1,-1) in 3x3 order si=0,2,4 / 6,8,A / C,E,10 via slot3_tile_record_load; slot3_mask_rebuild; gate 11CF3==0 -> far sub_2BEBF(ax=0x7F); tail-jmp slot3_handle_release_pair; 5 callers (entity_seg_reset, entity_setup_step, sub_130D5, sub_13406, sub_355E6)",
   "139B, cd=981, in=5, callees slot3_tile_record_load x9 + slot3_handle_alloc_pair/release_pair + slot3_mask_rebuild + far sub_2BEBF. Slot3 3x3 tile loader: drops the 9 old backing handles, allocates a fresh pair, loads the 3x3 neighbourhood centred on (11C24,11C26), rebuilds the mask table and optionally pings 2BEBF(0x7F) -- the full-reload sibling of the slot3_window_scroll_* incremental paths. conf: med-high", "med-high"),
 "sub_17643": ("adlib_synth_init",
   "FAR retf (123B): hw_reg_write_pair(0, si=1..0xF5) zero-fill; hw_reg_write_pair(6,4); 9x: word [-51B0+si*2]=0x2000, byte [-517A+si]=[-5194+si]=0; 0x0B bytes [-5186+si]=0x7F; channel_widen_forward_apply(1); channel_mode3_store(0,0,0); hw_seq_index_clamp(1); channel_mode20_write_ae76(1); retf; 5 callers (sub_17625, sub_316B6, sub_317AF, sub_318DD, sub_3A32? sub_31A32)",
   "123B far, cd=46, in=5, callees hw_reg_write_pair x2 + channel_widen_forward_apply + channel_mode3_store + hw_seq_index_clamp + channel_mode20_write_ae76. AdLib/OPL synth initializer: zeroes registers 1..0xF5, writes (6,4), inits the 9-channel 0x2000 period tables + zero bytes + 0x7F volume bytes, then applies widen-forward(1), mode3(0,0,0), seq clamp(1) and mode20(1). conf: med-high", "med-high"),
 "sub_2142E": ("farobj_record_step",
   "NEAR retn (393B): record_xform_apply; farobj_flag24_select; 1F742=0; si=[di+22] record: gate [di+24]&0x10 -> resolve 7B0E:3052 slot handle + skip len byte; stride walk (25499>1 && es:[si+2]&0x1000); [di+1A] vs es:[si] threshold (4000h shift via 1F743); flag_byte_get -> 1F742 when [di+24]&4000h; 1F73D=[di+24]&2 ? 0xFF : 0; load ax=[bx+2] flags / si=[bx+4]: 4000h -> active_farptr_match_b2 return; 8000h -> active_farptr_match_b2 + jmp 215C1; else decode 1F741 (20h), 1F731/1F730/1F738/1F739 direction flags from ax bits 0..3, scale [di+20] by 1F75E (80h -> 32-bit shl variant), op-table dispatch cs:off_26426[bx] (bx=[bx+6]&~3 <=0x34), restore 1F731/1F730/1F741, active_farptr_match_b2; 3 callers (view_projection, sub_2131C, sub_213E6)",
   "393B, cd=338048 (hottest caller_dyn in the queue), in=3, callees record_xform_apply + farobj_flag24_select + active_farptr_match_b2 x3 + flag_byte_get + off_26426 op-table dispatch (the whole L6 object family). Farobj record step: the per-record driver behind view_projection -- resolves the record (or the 3052 slot handle), walks the 8-stride threshold tables, decodes the flag word into the 1F73x direction globals, scales [di+20] and dispatches one of the 14 object op handlers. conf: med-high", "med-high"),
 "sub_13640": ("slot3_window_reload_col1",
   "NEAR (237B, partial): release handles ds:150/156/15C (op 2); far sub_2BEBF(ax=1); pair-shift the 150/156/15C triples (movsw with skip-2 gaps); op_slot_mask_release x3 (si=162/192/1C2); roll mask rows 172->162, 182->172, 1A2->192, 1B2->1A2, 1D2->1C2, 1E2->1D2; 154/15A/160=FFFF; slot3_handle_alloc_pair; load 3 tiles at si=4, 4+6, 4+12 with (ax=11BC4-1, bx=11BC2+2) via slot3_tile_record_load; slot3_mask_rebuild; tail-jmp slot3_handle_release_pair; 2 callers (sub_13406, sub_13578)",
   "237B, cd=0, in=2, same callee set as slot3_tile3x3_load. Slot3 middle-column reload: refreshes only the centre column (si=4/0xA/0x10) of the 3x3 window at (11BC2+2, 11BC4-1), rolling the 0xC0 mask row block by one and far-pinging 2BEBF(1) -- the no-scroll incremental sibling of slot3_tile3x3_load / slot3_window_scroll_left/right (all from sub_13406/sub_13578). conf: med", "med"),
 "sub_40F5D": ("hud_data_panel_gate_draw",
   "FAR retf (26B): ds=es=54AF; ax=cs:loc_337DD+2; call flag_quad_state_clear(+2); jb -> tail loc_30F71+2 (hud_data_panel_draw internal); else push cs, call hud_data_panel_draw(+2); retf; 2 callers (sub_3252B, sub_329B1)",
   "26B, cd=0, in=2, callees flag_quad_state_clear + hud_data_panel_draw (both via +2 internal entries). HUD data panel gate: runs the quad-state clear and, depending on carry, either tail-enters an internal hud_data_panel_draw path or calls its +2 entry -- the dispatch shim used by the sub_3252B/329B1 UI steps. conf: med", "med"),
 "sub_1B684": ("kb_stream_open_write_close",
   "FAR retf (106B): accumulate_wait(arg_6:arg_4) -> 0 -> return 0:0; op_dispatch_far_entry(6, arg_2:arg_0) open -> si; FFFF -> state_7894_all_far_thunk + return 0:0; kb_stream_far_write(arg_6:arg_4, si); op 8 close; return 7772:unk_77A62:unk_77A60 (published dgroup ptr); retf; 1 caller (kb_records_rebuild)",
   "106B, cd=12, in=1, callees accumulate_wait + op_dispatch_far_entry (op 6/8) + kb_stream_far_write + state_7894_all_far_thunk. Keyboard stream one-shot writer: waits on the accumulator, opens the stream handle, writes through kb_stream_far_write, closes and returns the published 77A60/62 far ptr (0:0 on wait/open failure) -- called from kb_records_rebuild. conf: med-high", "med-high"),
 "sub_13464": ("slot3_window_scroll_left",
   "NEAR (146B, tail-jumps shared loader at loc_1372D): release handles ds:15C/15E/160 (op 2); far sub_2BEBF(ax=0); shift triples 15C<=156, 156<=150 (3 words each); op_slot_mask_release x3 (si=1C2/1D2/1E2); copy mask rows 192->1C2 (0x18 words) and 162->192 (0x18 words); 150/152/154=FFFF (first slot emptied); ax=11BC4-2, si=0 -> shared tail (slot3_handle_alloc_pair + 3x slot3_tile_record_load at si=0,6,0xC + slot3_mask_rebuild + release); 1 caller (sub_13406)",
   "146B, cd=0, in=1, callees op_slot_mask_release x3 + op_dispatch + far sub_2BEBF + shared slot3 alloc/load/rebuild tail. Slot3 scroll left: shifts the 3-slot queue toward 15C (slot0->slot1->slot2), rolls the mask rows up (162/192 -> 192/1C2), empties slot0 and loads the new left column (si=0/6/0xC at ax=11BC4-2) -- the prepend sibling of slot3_window_scroll_right / slot3_window_reload_col1. conf: med", "med"),
 "sub_134F6": ("slot3_window_scroll_right",
   "NEAR (130B, tail-jumps shared loader at loc_1372D): release handles ds:150/152/154 (op 2); far sub_2BEBF(ax=2); copy triple 156->150 (6 words); op_slot_mask_release x3 (si=162/172/182); copy mask rows 192->162 (0x30 words = 3 rows); 15C/15E/160=FFFF (last slot emptied); ax=11BC4+2, si=0x0C -> shared tail (3x slot3_tile_record_load at si=0x0C,0x12,0x18 + rebuild + release); 1 caller (sub_13406)",
   "130B, cd=0, in=1, same callee set as slot3_window_scroll_left. Slot3 scroll right: shifts the 3-slot queue toward 150 (slot1->slot0, slot2->slot1), rolls the mask rows down (192/1A2/1B2 -> 162/172/182), empties slot2 and loads the new right column (si=0x0C/0x12/0x18 at ax=11BC4+2) -- the append sibling. conf: med", "med"),
 "sub_1CBB3": ("channel_mode_cmd_dispatch",
   "FAR C-frame retf (122B): di=arg_0 switch: ==1 -> expand the es:arg_2 table (count=es:[bx], bytes es:[bx+si+1] -> 0x1C-word ss array) then channel_program_pair_write(array, count); ==2 -> channel_widen_forward_apply(es:[bx]); ==3 -> hw_seq_index_clamp(es:[bx]); else fall through; retf; 1 caller (sub_1CC2D)",
   "122B far, cd=0, in=1, callees channel_program_pair_write + channel_widen_forward_apply + hw_seq_index_clamp. Channel mode command dispatcher: mode 1 byte-expands the caller's program table and writes it through channel_program_pair_write, mode 2 applies widen-forward, mode 3 the seq-index clamp -- the command switch behind sub_1CC2D. conf: med-high", "med-high"),
 "sub_1D7DA": ("channel_list_register_batch",
   "FAR C-frame retf (178B): pushf/cli; loop di over count at es:arg_0: si=es:[(di+1)*2 + arg_0]; list_record_register(arg_6:arg_4, si) -> var_4; if 0: unlink nodes 0..di via list_node_unlink (rollback) and abort; else channel_volume_store(7772:[si*2+61E], [si*2+664]) + scaled_hw_write([si*2+5D8], [si*2+592], si); inc di; popf; retf; 1 caller (sub_1D914)",
   "178B far, cd=0, in=1, callees list_record_register + list_node_unlink + channel_volume_store + scaled_hw_write. Channel list register batch: under cli registers each node of the caller's list (with full unlink rollback on the first failure), then publishes its volume pair (7772:61E/664) and scaled HW write (5D8/592) per voice. conf: med", "med"),
 "sub_2EA78": ("entity_slot_pair_create",
   "NEAR retf (47B): lodsw -> cs:2E108, lodsw -> cs:2E10A (two stream words); for each !=-1: entity_slot_create(ax=callback, bx=0 then bx=1); retf; 1 caller (sub_30AA8)",
   "47B leaf, cd=0, in=1, callee entity_slot_create x2. Entity slot pair creator: reads two callback ids from the record stream and creates slot 0 / slot 1 through entity_slot_create (skipping FFFF entries). conf: med-high", "med-high"),
 "sub_36347": ("terrain_point_label_draw",
   "NEAR (112B): terrain_point_project_store; jb retn; point_in_rect_6e8: in -> view_rect_strip_draw (restores di/bx) then marker loop: es=ds:796, si=0F8E, bp=2, cx=9, bounds-check di vs 702/6FE and bx vs 6FC/700, (bx-8, di-4) draw via dword ptr cs:loc_343E0; out -> alt label: si=0FA0 or 0FB6 (ds:4A82 gate), (bx-8, di-5) 0xB-char draw; retn; 1 caller (sub_3606C)",
   "112B, cd=0, in=1, callees terrain_point_project_store + point_in_rect_6e8 + view_rect_strip_draw + dword draw at cs:343E0. Terrain point label: projects the point, and when it lands in the 6E8 rect strip-draws the view rect then stamps a bounds-checked 9-char marker from the 0F8E table (or the 0FA0/0FB6 alt label) at the projected (bx,di) -- the label companion of view_rect_strip_draw. conf: med-high", "med-high"),
 "sub_384D0": ("record_script_field14_setup",
   "NEAR retn (54B): si=ds:48BA; push [si+0x14]; farwrap_25a1c (terrain_pos_delta_11cfc xref; si=0x11, di=0x75, cx=0xB8, dx=0xB8, bx=0x18, bp=0x20, ax=1); pop ax; ax=[si+0x14]*0xA+0x800; record_script_coord_dispatch(si=0xC6, di=0x7F, cl=0x63); retn; 1 caller (sub_382AB)",
   "54B, cd=0, in=1, callees farwrap_25a1c (terrain_pos_delta xref) + record_script_coord_dispatch. Record-script field+0x14 setup: runs the (0x11,0x75,0xB8x0x20) terrain-delta reveal for the 48BA entity's field+0x14, scales it x10+0x800 and dispatches the (0xC6,0x7F) coord block with opcode 0x63 -- the +0x14 sibling of record_script_field0c_setup. conf: med-high", "med-high"),
 "sub_38506": ("record_script_field0c_setup",
   "NEAR retn (49B): si=ds:48BA; push [si+0x0C]; farwrap_25a1c (si=0x2C, di=0x90, cx=0xD8, dx=0xD8, bx=0x18, bp=0x16, ax=1); pop ax; ax+0x800; record_script_coord_dispatch(si=0xE2, di=0x9C, cl=0x63); retn; 1 caller (sub_382AB)",
   "49B, cd=0, in=1, same callee set as record_script_field14_setup. Record-script field+0x0C setup: the (0x2C,0x90,0xD8x0x16) terrain-delta reveal for field+0x0C (no x10 scale), then the (0xE2,0x9C) coord dispatch with opcode 0x63. conf: med-high", "med-high"),
 "sub_4F168": ("entity_record_build_gate",
   "FAR retf (25B): ds=es=709F; call loc_2EED3 (entity_record_table_build internal); or ax,ax; jle -> tail loc_2F17A+4 (skip); call far sub_2C1CB; retf; 1 caller (sub_2F6D0)",
   "25B far, cd=0, in=1, callees entity_record_table_build (internal entry 2EED3) + far sub_2C1CB. Entity record build gate: runs the 709F-group table build and, only when it returns >0, hands off to the far 2C1CB continuation (used by the sub_2F6D0 UI step). conf: med", "med"),
}
# validate
names=[v[0] for v in analysis.values()]
assert len(analysis)==21, len(analysis)
assert len(set(names))==21, "dups: %s"%[n for n in names if names.count(n)>1]
bad=[n for n in names if not re.match(r'^[a-z_][a-z0-9_]*$',n)]
assert not bad, bad
nonascii=[(k,f) for k,v in analysis.items() for f in (v[1],v[2]) for ch in f if ord(ch)>127]
assert not nonascii, nonascii
txt=io.open('registry/naming.yaml',encoding='utf-8').read()
existing=set(re.findall(r'name:\s*([a-z_][a-z0-9_]*)',txt))
coll=[n for n in names if n in existing]
print("collisions:", coll)
print("total:", len(names), "OK:", not coll)
json.dump(analysis, open('analysis/ida_falconcd/level7_names.json','w'), indent=1)
print("wrote level7_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))
