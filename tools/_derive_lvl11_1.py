import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 82 Level-11 (15, LEVEL COMPLETE)
analysis = {
 "sub_12B62": ("viewobj_project_select",
   "FAR retf (20B): if cs:byte_11C88 != 0 -> viewobj_project_advance_mark, else -> viewobj_project_advance; retf; 4 callers (sub_2FEC5, sub_3C4F2, sub_495DF, sub_4A47B)",
   "20B far, in=4, dyn=59038 (hottest L11), callees = the L10 pair. State selector: routes the viewobj projection through viewobj_project_advance_mark (11C88 set) or plain viewobj_project_advance (11C88==0) -- the mode gate byte shared with farobj_tile_copy_align paths. conf: med-high", "med-high"),
 "sub_4F271": ("vga_dac_palette_upload",
   "FAR retf entry bundle (306B): main @0x4F271: ds=7A32h, one-shot latch al=byte_8505B (cleared on read), ret if 0; ah=al, dx=3C8h (VGA DAC write addr); flag-select palette tables by bit 20h/80h/4/8/10h/3/ah-40h from 7A32:A856 (240 entries), A970, AA54, AB26 (19-70), AB41 (61) with out dx,al + outsb x3 RGB loops (DAC index 10h/6Eh/BAh/C3h); shadow-copy 7A32:A556->A856 (720B) with ds:AD3C adjustments, clears AD3C bit4; probes @0x4F385/4F394 (byte_85055/85056 tests, preserve ax/ds); 11 callers (sub_2F6D0, sub_31138, sub_31319, sub_322E5, sub_66ABD, sub_66E62, sub_6760A, sub_67781, sub_6798C, sub_67AE1, sub_683C5)",
   "306B far, in=11, callees viewvec3_project_track_max (L10 dup-cref quirk) + farobj_cfg_delta_apply (L1 dup-cref). VGA DAC palette upload: consumes the one-shot 7A32:8505B dirty latch, dispatches on the flag byte to stream one of five 7A32 palette tables to DAC ports 3C8/3C9 via outsb RGB triples, maintains the A556->A856 shadow copy gated by AD3C bits, plus two flag probes (85055/85056). conf: med-high", "med-high"),
 "sub_13CB0": ("farobj_batch_build_project",
   "NEAR retn (346B): scale bp=0CCDh cx=400h; position deltas 11BD6:BD8 = (0x7FF-11BCC-cx)*bp, 11BD2:BD4 = (11BCA-cx)*bp (64-bit); stream loop per record (cx count): lodsb flags; if !(flags&80h) and word &3FFFh!=3FFFh: coord_point_group_project + active_farptr_restore; flags&=7Fh==0 -> done; per-entry: hw_flag_bit1_22e_extract state select, slot di=([bx+9]&7)*2Ah via es_ptr_slots_init, index adjust from ah flags, al==FFh -> skip; es:[di+22]=al+80h, es:[di..+6] += position deltas, farobj_tile_copy_align gated by 11C88==FFh && 11C0B==0, es:[di+8/0A]=ax:dx, ds=es bx=0C57h -> view_projection; si+=0x0Ah; after loop: farobj_sort_and_step + flag_clear; retn; 10 callers (sub_1318C, sub_132F2, sub_2F400, sub_3141A, sub_32453, sub_33443, sub_3421C, sub_386F2, sub_38CF3, sub_399F2)",
   "346B, in=10, callees coord_point_group_project (L10) + farobj_tile_copy_align (L3) + view_projection (L9) + farobj_sort_and_step (L9) + es_ptr_slots_init/hw_flag_bit1_22e_extract/flag_set_lowbit/flag_clear/active_farptr_restore (L0). Batch farobj builder: derives the view-centered position deltas, walks the 10-byte record stream (each optionally group-projected first), fills its 2Ah slot in the es table with position + aligned tile copy + projection, then farobj_sort_and_step -- the bulk sibling of farobj_single_build_project. conf: med-high", "med-high"),
 "sub_1243B": ("farobj_single_build_project",
   "FAR retf (121B): position deltas 11BD2:BD4 = (ax-cx)*bp stored (11BD8=dx entry); bx=cs:11BBA single record; slot di=([bx+9]&7)*2Ah; hw_flag_bit1_22e_extract state select + same index-adjust logic as sub_13CB0; al==FFh -> pop es/ds retf (skip); else tail-jump farobj_tile_align_project (build+align+project); 9 callers (r29_e63, sub_2FC79, sub_307A5, sub_3099C, sub_30AA8, sub_30CB8, sub_32393, sub_33443, sub_34C31)",
   "121B far, in=9, callees farobj_tile_align_project (L10) + hw_flag_bit1_22e_extract (L0). Single-record farobj builder: computes the deltas, resolves the 2Ah slot + state-dependent index from the 11BBA record (same flag logic as the batch loop), then tail-calls farobj_tile_align_project or bails on the FF sentinel. conf: med-high", "med-high"),
 "sub_36785": ("hud_readout_render",
   "NEAR retn (908B): formats signed value [706+24] into 103A-103D (sign 20/2D, digit, '.', digit) -> far text draw via dword cs:loc_343E2+2 at (6F8+bx, 6FA+di) panel coords; repeats for [706+12], [706+0CE] (if ds:4A84); sprite/char draws via dword cs:loc_343E0 (F4C/F4E strings, bp/cx params) and sprite_offset_dispatch_343e (mode 3 sprite si=1Ah, else si=12h; 44AA mode select via 487E xlat / [48BA]+AE table); heading: if 69A!=-1 && !([48BA]+CA &1000h): angle_quad_norm_far(di=692) -> /14A0h -> 3-digit string 1024-1028 else 'XXX'; altitude via int32_to_ascii([2E128+1]+40 <<2, cl=0FBh) at 1038 'A '; view rotation: [706+3A/3C] -> 4816 -> view_rotation_far_thunk -> stub_to_248d1 x4 matrix rows 430C/47D6/47E8 (44D3D mode flag); angle_xy_near/angle_aux_near -> screen pos 798-79C (scale 1C2h + 6C4/6C6), sprite_in_view_test -> sprite 0E84 cursor at (798-4,79A-4) or 105C=0; retn; 6 callers (sub_2FD42, sub_2FEF2, sub_31319, sub_35BCE, sub_45F2C, sub_46999)",
   "908B, in=6, callees 17 (int32_to_ascii, angle_quad_norm_far, angle_xy_near, angle_aux_near, view_rotation_far_thunk, sprite_offset_dispatch_343e, sprite_in_view_test, stub_to_248d1, ...). Cockpit HUD readout renderer: formats and draws the signed numeric fields, heading XXX/degrees, 'A ' altitude, rotation matrix rows, and the view-direction cursor sprite at panel coordinates relative to 6F8:6FA -- the main instrument-text pass. conf: med", "med"),
 "sub_2E82D": ("viewobj_project_if_moved",
   "NEAR retn (42B): farptr_table_get(ax,bx) -> record es:di, si=di; bp=7BC0h; vec3_bound_maxdiff -> ax; ax!=0 -> restore ax/bx, viewobj_project_advance, retn; else skip projection, retn; 4 callers (sub_2E52E, sub_2E569, sub_2E5A4, sub_3E552)",
   "42B, in=4, callees farptr_table_get + vec3_bound_maxdiff (L0) + viewobj_project_advance (L10). Movement gate: bound-checks the record against the 7BC0 reference vector and only runs the projection/advance when the max component difference is nonzero. conf: med-high", "med-high"),
 "sub_3454C": ("view_block4287_angles",
   "FAR retf (84B): ds=es=54AFh; zero 4816h (6 words); si=500h + (ds:44D3D * 0Ch) mode table; ax=(44D3D==3); call off_25693 (far call through block 7B0E:4287 slot) then loc_2568C (returns farptr 7B0E:4287 -> dx:ax); es:di = that farptr; si=4816 -> angle_xy_far -> ds:44AF6, angle_aux_far -> ds:44AF8; retf; 4 callers (sub_2F6D0, sub_3001E, sub_30307, sub_33443)",
   "84B far, in=4, callees view_block4287_entry (L10 stubs) + angle_xy_far + angle_aux_far (L3/L4) + coord_delta_11c56 (L0 dup-cref). Mode-selected view angle computation: picks the 500h+44D3D*12 config row, runs the 7B0E:4287 block entry points, then stores the xy/aux angles at 54AF:44AF6/44AF8. conf: med", "med"),
 "sub_3718D": ("hud_terrain_strip_render",
   "NEAR retn entry family (988B, 3 entries): @0x3718D gate 82C!=1: copy [48BA]+0C 6 words -> 4816, farobj_step_terrain_clamp(bp=dx=100, bx=0), carry -> stc retn; else (100-ax)/[si+4C] < 0x10 -> ds:105D=al, clc retn (terrain level sample). @0x371E3 angle_xy_near/angle_quad_norm_far over [48BA] pos -> 816/818, extents 7FC/7FE via stub_to_249d8 *2D0, quad corners from 80E/812 sign flags, segment_clip_test + byte_26096+3 tile-strip draws (5 per side x2), formats 848/1C7h number at 101D-101F, sprite_offset_dispatch_343e (si=22h). @0x37542 al=105A -> loc_263F6, dispatch_220d4_stub(855, 11 entries) + dispatch_220dc_stub; retn; 3 callers (sub_2F6D0, sub_46D42, sub_47BDE)",
   "988B, in=3, callees 16 (farobj_step_terrain_clamp, tile_strip_sample_draw, segment_clip_test, angle_xy_near, angle_quad_norm_far, sprite_offset_dispatch_343e, terrain_pos_grid_build, ...). Terrain strip renderer: terrain-clamps the [48BA] record into a level index (105D), draws the clipped quad strip pair with edge tiles + a numeric readout (101D-101F), and a small grid dispatch tail -- called alongside hud_readout_render from the 2F6D0 render cluster. conf: med", "med"),
 "sub_34907": ("vec_transform_scale_norm",
   "NEAR retn (28B): es:di = cs:333A8:333AA dest farptr, si = cs:2E128+1 source vector; vec_transform_scale_far; bx=0A5h (165); div bx; retn; 2 callers (sub_34954, sub_34C31)",
   "28B, in=2, callees vec_transform_scale_far (L5) + coord_point_group_project (L10 dup-cref). One-shot scaled transform: runs vec_transform_scale_far from the 2E129 vector into the 333A8:333AA farptr and divides by the 165 normalizer. conf: med", "med"),
 "sub_3708F": ("hud_heading_tape_draw",
   "NEAR retn (254B): if ds:477==2 retn; if [48BA]+0CAh & 1000h retn (hidden); ax=angle_xy_near(di=692), rel = (ax-[48BA]+0C) &3FFFh, wrap >2000h -=4000h, |.|; if !ds:4A84: |rel| < E4h -> two 5-char strings 0FD1/0FCC at (94,106) panel draws via dword cs:loc_343E0, else one string at (A0+dx) choosing 0FCC/0FD1 by sign; if 4A84: |rel| <= 2AFh -> bx=rel*12/0E4h else bx=24h; string 0FD6 at (A0+bx) bp=1 cx=3; retn; 2 callers (sub_35BCE, sub_46D42)",
   "254B, in=2, callees angle_xy_near (L3) + dispatch_220d4_stub (L0 dup-cref). Heading tape: computes the signed wrapped heading delta of the 692 record vs [48BA]+0C, then draws the appropriate 5-char ribbon string (FD1/FCC/FD6) at one of two panel layouts (4A84 mode flag scales 12/224) via the loc_343E0 far draw -- the numeric heading ribbon beside hud_readout_render. conf: med", "med"),
 "sub_10EA5": ("key_action_100_apply",
   "NEAR retn (17B): cs:byte_10E22 = al; ax=100h; push ax; key_action_execute; add sp,2; retn; 1 caller (mode_flags_apply)",
   "17B, in=1, cd=34 (hottest caller_dyn L11 alongside _102), callee key_action_execute (L10). Key-100h wrapper: latches al into cs:10E22 then invokes key_action_execute(0x100) -- the action that sets 7772:77A82 bit1 in the key core. conf: med-high", "med-high"),
 "sub_10EB6": ("key_action_102_apply",
   "NEAR retn (17B): cs:byte_10E23 = al; ax=102h; push ax; key_action_execute; add sp,2; retn; 1 caller (mode_flags_apply)",
   "17B, in=1, cd=34, callee key_action_execute (L10). Key-102h wrapper: latches al into cs:10E23 then invokes key_action_execute(0x102) -- sets 7772:77A82 bit2 in the key core. conf: med-high", "med-high"),
 "sub_468EF": ("viewobj_table64_project",
   "FAR retf (47B): ds=63FDh; si=10Eh, cx=40h (64 x 10h-byte records); loop: [si]==0 -> skip; ax = 0EDh - (cx-40h) (ascending index 0EDh..12Ch), bx=20h -> viewobj_project_advance; si+=10h; loop; retf; 1 caller (sub_2FD42)",
   "47B far, in=1, callee viewobj_project_advance (L10). Table scanner: walks 64 x 16-byte records at 63FD:10E, skipping empty slots, and projects each with its ascending base index 0EDh..12Ch (fixed bx=20h arg). conf: med", "med"),
 "sub_4691E": ("viewobj_table72_flag_project",
   "FAR retf (48B): ds=63FDh; si=50Eh, cx=48h (72 x 1Ah-byte records); loop: if !(byte [si+17h] & 1) -> skip; ax = 0A5h - (cx-48h) (ascending index), bx=20h -> viewobj_project_advance; si+=1Ah; loop; retf; 1 caller (sub_2FD42)",
   "48B far, in=1, callee viewobj_project_advance (L10). Flagged table scanner: walks 72 x 26-byte records at 63FD:50E, projecting only those with +17h bit0 set, ascending indices from 0A5h (bx=20h). conf: med", "med"),
 "sub_4694E": ("viewobj_table32_flag_project",
   "FAR retf (48B): ds=63FDh; si=113Eh, cx=20h (32 x 28h-byte records); loop: if !(byte [si+13h] & 4) -> skip; ax = 85h - (cx-20h) (ascending index), bx=20h -> viewobj_project_advance; si+=28h; loop; retf; 1 caller (sub_2FD42)",
   "48B far, in=1, callee viewobj_project_advance (L10). Flagged table scanner: walks 32 x 40-byte records at 63FD:113E, projecting only those with +13h bit2 set, ascending indices from 85h (bx=20h). conf: med", "med"),
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
json.dump(analysis, open('analysis/ida_falconcd/level11_names.json','w'), indent=1)
print("wrote level11_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))
