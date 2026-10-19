import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 83 Level-12 (11, LEVEL COMPLETE)
analysis = {
 "sub_10EC7": ("key_event_gated_process",
   "FAR retf (64B): ax==100h/101h -> require cs:byte_10E22==1 else retf; ax==102h -> require cs:byte_10E23==1 else retf; else fall through: ds=cs:10842, push dx/bx/cx/ax -> key_event_process (4 args), add sp,8; retf; 8 callers (sub_30356, sub_3327A, sub_3421C, sub_345BA, sub_3470D, sub_3480F, sub_41646, sub_46D42)",
   "64B far, in=8, dyn=266 (hottest L12), callee key_event_process (L11). Mode-gated key event processor: keys 100/101 only fire when the 10E22 latch is 1, key 102 when 10E23 is 1 (the latches written by key_action_100/102_apply), then forwards ax..dx to key_event_process via the 10842 context segment. conf: med-high", "med-high"),
 "sub_10F07": ("key_code_resolve_entry",
   "FAR retf (23B): ds=cs:10842; bx=1; push bx; push ax; key_code_resolve; add sp,4; retf; 4 callers (sub_3467D, sub_348AD, sub_46D42, sub_47BDE)",
   "23B far, in=4, dyn=83, callee key_code_resolve (L11). Far wrapper: loads the 10842 context segment and invokes key_code_resolve(ax, flag=1). conf: med-high", "med-high"),
 "sub_1318C": ("farobj_tile_stream_build",
   "NEAR retn (234B): delta64 = (ax-11C2E):(dx-11C2C), OR-ed -> self-mod word cs:131F7; scales 11BC8<<=2, 11BC6<<=2; stream loop cx=lodsb count: if byte_11C8B==0: per entry lodsb posn (>>2 +11BC8 -> 11BCC, &3 +11BC6 -> 11BCA), lodsw -> si, farobj_batch_build_project; loop. Else: pick table 59CBh (16-entry via 11C2A&3 / 11C28&3) or 598Bh (byte_11C7A*8); bp=10h match loop: es:[bx] vs [si] byte match (3-byte stride), matched -> same posn + farobj_batch_build_project; inc bx, dec bp; pop ds, clc, retn; 11 callers (sub_2F6D0, sub_2FD42, sub_305E4, sub_310B7, sub_31138, sub_31319, sub_320D9, sub_321DD, sub_322E5, sub_32C62)",
   "234B, in=11, callee farobj_batch_build_project (L11). Tile stream batch builder: scales the 11BC6/11BC8 base, walks the compressed tile stream (count + packed position bytes + list pointers), or in table mode matches against the 59CB/598B pick tables, setting the shared 11BCC/11BCA view-center vars per tile before each farobj batch build. conf: med-high", "med-high"),
 "sub_399F2": ("fixed_matrix_proj_factor",
   "NEAR retn class-DATA (183B): 47D6/47D8 = [di+0C/0E], di=es:[di+14] -> fixed_matrix_mul; load second vector via cs:2E12B farptr at es:[..+1734] -> fixed_matrix_mul again; four 16.16 accumulations with coefficients [si+8A]/[si+8C] through off_23134 (far fn ptr, imul/shl pairs); sums cx/bp; stub_to_23dcd divides the combined sum, sign-abs -> es:[di+88]; retn; 8 callers (sub_3099C, sub_30AA8, sub_39F1D, sub_3AB59, sub_49428, sub_494B2, sub_49546, sub_495DF)",
   "183B, in=8, callees fixed_matrix_mul x2 + off_23134 x4 + stub_to_23dcd. Fixed-point projection factor: transforms two vectors through their matrices, dot-accumulates against the +8A/+8C coefficients via the far 23134 helper, divides, and stores the absolute scalar at the record's +88 -- the per-record scale/depth factor. conf: med", "med"),
 "sub_2E52E": ("viewobj_5982_scan100",
   "FAR retf (59B): ds=5982h es=54AFh; gate byte_59820 bit0; ax=0, di=1; loop to ax==0x63 (100 x 0Ch-byte entries): [di]==1 -> ax+155h index, bx=20h -> viewobj_project_if_moved; inc ax, di+=0Ch; retf; 3 callers (sub_2E2E0, sub_3E16B, sub_3E552)",
   "59B far, in=3, callee viewobj_project_if_moved (L11). 5982 segment scanner (bit0): walks 100 x 12-byte entries at 5982:1, projecting those with word==1 using ascending object indices 155h..1B7h (bx=20h). conf: med", "med"),
 "sub_2F400": ("terrain_vm_sweep_sample",
   "FAR retf (309B): ds=ax segment; VM ops via op_dispatch (0,6,0x14 / 0,0xA,4,0x54 / 0,6,8): builds a matrix at 54h, [54]/[56]/5B5h -> 1Eh/22h; loc_22EFE; loop (cx passes): op_dispatch(0,6,8) -> 26h, vectors 26h..2Ch stride 6 (66h...), stub_to_24980 tile quad sample, fixed_matrix_mul(7FFFh), store vec at 2Eh, angle_matrix_far_invoke, fixed_matrix_load_7b0e(54), stub_to_248d1 terrain block scan; 90-degree rotation of [si] (swap/neg); loop while 2Ch!=118h (280) && 2Ah!=8Ch (140); op_dispatch(0,8), loc_22F15; zero 2E vec; retf; 3 callers (sub_3001E, sub_3EEDB, sub_4FCBE)",
   "309B far, in=3, callees op_dispatch (L4 VM) + tile_quad_sample + stub_to_248d1/24980 + fixed_matrix_mul + angle_matrix_far_invoke + fixed_matrix_load_7b0e. Terrain VM sweep: runs bytecode ops to build the working matrix, then sweeps the grid with 90-degree rotations of the sample vector (up to 280 x 140 bound), sampling terrain blocks per step -- terrain correlation/matching pass. conf: med", "med"),
 "sub_2E5A4": ("viewobj_5982_scan40",
   "FAR retf (59B): ds=5982h es=54AFh; gate byte_59820 bit4 (test al,4); ax=0, di=4EDh; loop to ax==0x27 (40 x 0Eh-byte entries): [di]!=0 -> ax+1C3h index, bx=20h -> viewobj_project_if_moved; inc ax, di+=0Eh; retf; 2 callers (sub_2E2E0, sub_4E520)",
   "59B far, in=2, callee viewobj_project_if_moved (L11). 5982 segment scanner (bit4): walks 40 x 14-byte entries at 5982:4ED, projecting those with nonzero word using ascending object indices 1C3h..1EAh (bx=20h). conf: med", "med"),
 "sub_132F2": ("tile_base_batch_build",
   "LEAF (15B): push ds; tile_base_set_11bc6; jb fail (plain retn); farobj_batch_build_project; pop ds; clc; retn; 1 caller (sub_1575E)",
   "15B leaf, in=1, callees tile_base_set_11bc6 (L1) + farobj_batch_build_project (L11). One-shot: set the 11BC6 tile base and, on success, run a single farobj batch build. conf: med-high", "med-high"),
 "sub_2E569": ("viewobj_5982_scan10",
   "FAR retf (59B): ds=5982h es=54AFh; gate byte_59820 bit1 (test al,2); ax=0, di=4B1h; loop to ax==9 (10 x 06h-byte entries): [di]==1 -> ax+1B9h index, bx=20h -> viewobj_project_if_moved; inc ax, di+=06h; retf; 1 caller (sub_2E2E0)",
   "59B far, in=1, callee viewobj_project_if_moved (L11). 5982 segment scanner (bit1): walks 10 x 6-byte entries at 5982:4B1, projecting those with word==1 using ascending object indices 1B9h..1C2h (bx=20h). conf: med", "med"),
 "sub_2FEC5": ("viewobj_self_copy_project",
   "NEAR retn (45B): if ds:45E==0 retn; si=cs:2E128+1 record; if !([si+74]&1) retn; if [si+0A]!=0 retn; farobj_copy_invoke(0); bx=20h, ax=0 -> viewobj_project_select; retn; 1 caller (sub_2FD42)",
   "45B, in=1, callees farobj_copy_invoke (L3) + viewobj_project_select (L11). Self-object refresh: when ds:45E and the +74 bit0/+0A gates pass, copies object 0 and projects it through the 11C88 selector. conf: med", "med"),
 "sub_4A47B": ("entity_move_project_step",
   "FAR retf (90B): ds=65E4h es=54AFh; si=68h, cx=ds:65EA4 count; loop: push cx/ds/si; bp=9C40h (40000), ax=[si+4], si=[si+6] farptr, ds=ax, di=20h, ax=1 -> pos_move_angle_step; restore si/ds; ax==0 -> skip; if [si]==2 && ([si+0C]&10h): ax=[si+2], bx=20h -> viewobj_project_select; si+=3Ah; loop; retf; 1 caller (sub_2FD42)",
   "90B far, in=1, callees pos_move_angle_step (L5) + viewobj_project_select (L11). Entity list mover: for each 58-byte 65E4:68 record runs pos_move_angle_step (40000 rate), then projects type-2 records with the +0Ch bit4 flag through the 11C88 selector. conf: med", "med"),
}
names=[v[0] for v in analysis.values()]
assert len(analysis)==11, len(analysis)
assert len(set(names))==11, "dups: %s"%[n for n in names if names.count(n)>1]
bad=[n for n in names if not re.match(r'^[a-z_][a-z0-9_]*$',n)]
assert not bad, bad
nonascii=[(k,f) for k,v in analysis.items() for f in (v[1],v[2]) for ch in f if ord(ch)>127]
assert not nonascii, nonascii
txt=io.open('registry/naming.yaml',encoding='utf-8').read()
existing=set(re.findall(r'name:\s*([a-z_][a-z0-9_]*)',txt))
coll=[n for n in names if n in existing]
print("collisions:", coll)
print("total:", len(names), "OK:", not coll)
json.dump(analysis, open('analysis/ida_falconcd/level12_names.json','w'), indent=1)
print("wrote level12_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))
