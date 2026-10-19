import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 84 Level-13 (15, LEVEL COMPLETE)
analysis = {
 "sub_10E24": ("irq_state_init_entry",
   "FAR retf (21B): push ds/es; ds=cs:10842; ah=0; push ax; irq_state_init; add sp,2; pop es/ds; retf; 3 callers (state_swap_far_call, sub_33443, sub_3460E)",
   "21B far, in=3, dyn=37, callee irq_state_init (L12). Far wrapper: loads the 10842 context segment and invokes irq_state_init(flag=0). conf: med-high", "med-high"),
 "sub_1575E": ("tile_base_opcode_interpreter",
   "NEAR retn (421B): gate cs:byte_11C69 bit0; loop cx=31h entries from cs:11C8C: lodsb idx; 5ACBh=idx*2; table 32C0h+idx*5 opcode byte 11C7C; bit7 -> tile_base_batch_build (pair farptr from 54AF:1734+idx*4 via 5869/586B); else bits 4/2/1 select farobj_flag_record_push pair checks (entries at si+0Ah) then conditional tile_base_batch_build; dec cx, loop; retn; 3 callers (sub_153A5, sub_359B2, sub_3A5D2)",
   "421B, in=3, dyn=11155 (hottest overall), callees tile_base_batch_build (L12) + farobj_flag_record_push (L5). Tile-base opcode interpreter: walks the 0x31-entry command stream at cs:11C8C, decoding per-entry opcode bits to either direct tile_base_batch_build or flag-record pair tests gating the batch build -- the core per-frame terrain base emit loop. conf: med-high", "med-high"),
 "sub_18074": ("mode_slot_masks_entry",
   "NEAR retn (20B): push cx/dx/bx/ax; cs_word_get_10842 -> ds; mode_slot_masks; add sp,8; retn; 2 callers (sub_18062, sub_1806A)",
   "20B, in=2, cd=20, callees cs_word_get_10842 (L0) + mode_slot_masks (L12). Far-context shim: loads the 10842 segment then runs mode_slot_masks on the saved args. conf: med-high", "med-high"),
 "sub_2E2E0": ("viewobj_5982_scan_all",
   "FAR retf (16B): push cs; call viewobj_5982_scan100; nop; push cs; call viewobj_5982_scan10; nop; push cs; call viewobj_5982_scan40; nop; retf; 1 caller (sub_2FD42)",
   "16B far leaf, in=1, callees viewobj_5982_scan100/scan10/scan40 (L12). Fan-out: runs all three 5982-segment scanners in sequence. conf: high", "high"),
 "sub_310B7": ("terrain_stream_pos_update",
   "NEAR retn (66B): al=0; if ds:530==0 and (ds:82C&1 or ds:41B!=0): bx=(82C>>1)+((82C>>1)>>2)+41B*15 -> ds:674=bx, state_byte_word_set(1); else ds:674=0, state_byte_word_set(0); retn; 3 callers (sub_3001E, sub_310F9, sub_40F77)",
   "66B, in=3, callees farobj_tile_stream_build dup (L12) + state_byte_word_set (L0). Terrain stream cursor: derives a packed row/column index from the 82Ch scroll byte and 41Bh counter, publishes it to ds:674 and raises the 22D28 state-set flag (or zeroes both when disabled). conf: med-high", "med-high"),
 "sub_320D9": ("hud_metric_rows_draw",
   "NEAR retn (232B): cb_args_save; cb_args_table_set(2); cs_word_store(45h); four rows: stub_to_205c3 rect (cl=6, x ranges 39h-47h / 83h-97h / 0F5h-10Eh / 2Fh-39h, y 0B2h/0B7h or 0BAh/0BFh), int32_to_ascii(_short) of ds:40E*5A0>>16 / ds:40C / ds:410:412 (clamped >=0) / state_word_22d26_get, far_cb_gated string at 41Fh; cb_args_restore; retn; 2 callers (sub_322E5, sub_42025)",
   "232B, in=2, many L0/L1 text+state callees + stub_to_205c3 rect placer + far_cb_gated painter. HUD metric rows: formats four numeric fields (scaled 40E, 40C, 32-bit 410:412, 22D26) as strings and paints them into fixed panel rects -- the multi-metric status strip. conf: med", "med"),
 "sub_3421C": ("viewobj_batch_project_test",
   "NEAR retn (423B): if ds:45E!=0 retn; viewer pos via fixed_matrix_mul -> ds:4C9-4D3; loop cx=0Fh entries at 54AF:1734+bx: if [es:di+74]&1 and [es:di+86]<12h: stub_to_24980/24988 angle tests (<=1000h both axes), entity pos via fixed_matrix_mul -> ds:4D5-4DF, angle_xy_near between viewer and entity, +2000h stub_to_24980 vs [es:di+0C] <=1000h -> ax=4Dh bx=4 cx=1 dx=0, key_event_gated_process, stc, retn; else next entry; clc, retn; 2 callers (sub_2F6D0, sub_44352)",
   "423B, in=2, callees key_event_gated_process (L12) + coord_point_group_project dup + farobj_batch_build_project dup + tile_quad_sample + angle_xy_near + fixed_matrix_mul + stub_to_24980/24988. Candidate selector: projects the viewer, sweeps 15 farptr-table objects doing double angle+range gates, and on the first match fires key 4Dh (selection confirm) returning CF set. conf: med", "med"),
 "sub_345BA": ("object_farptr_dispatch",
   "FAR retf (84B, dual entry): entry1: ds=500C, bx=[400C0], ds=709F; if [609F0]!=0: [60A28]=bx, cx=byte_60A2A, farptr=[54AF:1734+cx*4] -> 2F64:unk_1F669/1F667, call far sub_2C08B; retf. entry2 (345FD): if cs:2E176==1: bx=0Ch -> key_event_gated_process; retf; 8 callers (sub_32AF6, sub_3C1BD, sub_3DC55, sub_41C5A, sub_41CD8, sub_41D21, sub_4289E, sub_44352)",
   "84B far, in=8, callees key_event_gated_process (L12) + sbi_int8_close (L3) + sub_2C08B. Object farptr dispatcher: when the 609F0 latch is set, installs the 54AF-table farptr selected by byte 60A2A into the 2F64:1F669 callback slot and far-calls 2C08B; second entry forwards key 0Ch when 2E176==1. conf: med", "med"),
 "sub_3470D": ("range_key_event_dispatch",
   "FAR retf (258B, five entries): entry2 (3470E): farptr_table_get(dx)->es:di; ds=54AF; si=20h cx=3: per pair abs-diff of [si] vs es:[di] (4-byte stride), keep max if <=2940h else bail; bl=bh, dx=bx>>3 -> key_event_gated_process; jmp entry3. entry3 (34771): gate es:[45E]; per 3 pairs abs-diff [si] vs es:[di], <=64h -> bx=5 else half-step approach [si]+=(diff/2) -> bx=4; push cs:51B9; jmp entry2. entry4: stack-restore retf; entry5: ax=cs:2E171; retf; 6 callers (sub_2FC79, sub_33443, sub_396D7, sub_44352, sub_446CB, sub_4D544)",
   "258B far, in=6, callees key_event_gated_process (L12) + farptr_table_get (L0). Range-gated key event: compares the 54AF working triple against a farptr-table triple with a 2940h ceiling (or a 64h tight gate with half-step attract), then fires a key event whose code/scale derives from the worst-case delta >>3. conf: med", "med"),
 "sub_3480F": ("key_event_gate_check",
   "FAR retf (35B): si=54AF, ds=si, si=ax, ax=0; if ds:44FEE!=0 and ds:44F4E==0: ax=si -> key_event_gated_process; pop ds/si; retf; 6 callers (sub_2F6D0, sub_303C4, sub_3327A, sub_33443, sub_34832, sub_47BDE)",
   "35B far, in=6, callee key_event_gated_process (L12). Conditional forwarder: passes the incoming key code ax through to key_event_gated_process only while 54AF:44FEE is set and 54AF:44F4E is clear (input-enable latch pair). conf: med-high", "med-high"),
 "sub_348AD": ("key_code_pending_drain",
   "NEAR retn (90B, dual entry): entry1: key_code_resolve_entry(); if ds:4893: clear it, key_code_resolve_entry(4); if ds:4894: clear it, key_code_resolve_entry(3); retn. entry2 (348ED): 4x movsw 667h, farobj_tile_copy_resolve(667h), stosw 0,0; retn; 8 callers (sub_2F6D0, sub_30356, sub_303C4, sub_33443, sub_3460E, sub_34644, sub_3467D, sub_34832)",
   "90B, in=8, callees key_code_resolve_entry (L12) + farobj_tile_copy_resolve (L2). Pending drain: resolves the incoming key then services the 4893/4894 deferred-request latches with codes 4 and 3; second entry resolves a 4-word tile copy request. conf: med", "med"),
 "sub_34B01": ("view_extent_default_reset",
   "NEAR retn (145B): clear ds:45E,5A1,546,548,664,665,5CA,5A0,666,662; ds:23B=1Ah -> state_word_22d28_set_ax; rect at 24Fh = 0,24h,13Fh,C7h,A0h,96h -> view_extent_init_0c; view_extent_compute_1f6da(555h); view_extent_get_quad -> ds:78E-794; lodsw_quad_to_state_25450(24Fh); retn; 2 callers (sub_32C62, sub_446CB)",
   "145B, in=2, callees view_extent_init_0c (L2) + view_extent_compute_1f6da (L0) + view_extent_get_quad (L0) + state_word_22d28_set_ax (L0) + lodsw_quad_to_state_25450 (L0). Viewport reset: zeroes the view-state cluster, programs the default 320x199-ish extent rect (0,24h..13Fh,C7h), recomputes the projection quad and publishes it. conf: med-high", "med-high"),
 "sub_49428": ("obj_range_slot_init",
   "FAR retf (138B): ds=65A7; farobj_height_gate_wrap -> ax; if ax==0FFFFh bail (pop x3, retf); ds:3CC|=1; [si]=1|10h (|8 if ch!=0); [si+1]=ax+12Dh; [si+3]=0FFFFh; [si+0D]=20h; [si+0F]=0; [si+10]=ax,[si+12]=bx,[si+5]=dx; 3x far fixed_vec3_accumulate_a with cx&7FFh-3FFh -> [si+7]/[si+9]/[si+0B]; fixed_matrix_proj_factor(bx=29h); farobj_copy_cond([si+1]); retf; 1 caller (sub_41646)",
   "138B far, in=1, callees fixed_vec3_accumulate_a (L0) + farobj_copy_cond (L1) + farobj_height_gate_wrap (L5) + fixed_matrix_proj_factor (L12). Range-slot initializer: allocates a 65A7:0C+(range-301h)*18h record for store index ax+12Dh, seeds it with clamped angles and the wrapped height, runs the projection factor (bx=29h) and copies the result out. Pairs with obj_range_slot_activate. conf: med", "med"),
 "sub_494B2": ("obj_range_slot_activate",
   "FAR retf (96B): if ax<12Dh or >=155h bail; if bh*bl<64h bail; si=65A7:0C+(ax-12Dh)*18h; if [si]==0 bail; if [si]&2: [si+0E]=6Eh, bx=0Ch (or 16h if [si]&8), fixed_matrix_proj_factor([si+1]), retf; else [si]=0, farptr_table_get([si+1]), es:[di+26h]|=40h, retf; 2 callers (sub_46D42, sub_4A4F6)",
   "96B far, in=2, callees farptr_table_get (L0) + fixed_matrix_proj_factor (L12). Range-slot activator: for store index 301h-354h with a live 65A7 record and bh*bl>=100, either fires the projection (record bit1 set) or clears the slot and ORs the 40h release flag on the far object. Pairs with obj_range_slot_init. conf: med", "med"),
 "sub_3AB59": ("terrain_grid_cb_dispatch",
   "NEAR retn (55B): stub_to_205c3 rect (cl=3Dh, x 98h-A7h, y 97h-9Ch); di=8Ch bx=8Fh si=4B5Dh al=ds:4A7Eh -> far_cb_6; retn. tail entry (3AB7E): fixed_matrix_proj_factor; retf; 1 caller (sub_31CA1)",
   "55B, in=1, callees stub_to_205c3 (L1) + far_cb_6 (L0) + fixed_matrix_proj_factor (L12). Terrain grid painter: sets the rect then invokes far_cb_6 with the 4A7Eh mode and 4B5Dh string; tail entry is a one-shot projection factor forwarder. conf: med", "med"),
}
names=[v[0] for v in analysis.values()]
assert len(analysis)==15, len(analysis)
assert len(set(names))==15, "dups: %s"%[n for n in names if names.count(n)>1]
bad=[n for n in names if not re.match(r'^[a-z_][a-z0-9_]*$',n)]
assert not bad, bad
nonascii=[(k,f) for k,v in analysis.items() for f in (v[1],v[2]) for ch in f if ord(ch)>127]
assert not nonascii, nonascii
txt=io.open('registry/naming.yaml',encoding='utf-8').read()
existing=set(re.findall(r'name:\s*([a-z_][a-z0-9_]*)',txt))
coll=[n for n in names if n in existing]
print("collisions:", coll)
print("total:", len(names), "OK:", not coll)
json.dump(analysis, open('analysis/ida_falconcd/level13_names.json','w'), indent=1)
print("wrote level13_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))
