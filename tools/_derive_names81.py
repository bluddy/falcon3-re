import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 71 Batch 16 (L0 FINALE, last 22)
analysis = {
 "r06_e52": ("r06_scale_clamp_c3",
   "void far (partial entry): scale AX around base 0xC3 by CL (shl/sar by sign), clamp result to [0x72..0xBE], then continues; 1 caller (sub_2C257)",
   "58B span, 0 dyn, cd=0, 1 caller. R06 entry: signed scale about 0xC3 with CL shift + clamp 0x72..0xBE (head `in ax,dx` is a mid-instruction artifact). conf: low", "low"),
 "r06_e53": ("state_word_4ab1_zero",
   "void far; ds:4AB1 = 0; retn (clears a DGROUP word)",
   "8B LEAF, 0 dyn, cd=0, 1 caller (sub_2C261). Clears DGROUP word 0x4AB1. conf: high", "high"),
 "sub_6DC09": ("mode_gate_4ac2_4ac4",
   "void far; early-ret if ds:4AC2==4 or ds:4AC4==0 (else falls into body); retf at 0x6DC17",
   "108B span (body to retf@0x6DC17), 0 dyn, cd=0, 1 caller (sub_3A3D6). Dual mode gate: requires ds:4AC2!=4 AND ds:4AC4!=0 before the R06 body. conf: med", "med"),
 "sub_6DC75": ("entity_table_walk_49a3",
   "void far; if ds:49A3!=0: jmp 6DCD8; CX=ds:48B8<<2 -> self-mod word cs:6DC93 (immediate patch); SI=0, CX=0x10 walk loop over entity records; 1 caller (sub_3A3D6)",
   "38B span, 0 dyn, cd=0, 1 caller, DATA-class head. Entity-table walk with a self-modifying immediate at cs:6DC93 (patched from ds:48B8). conf: med", "med"),
 "sub_6DC9C": ("r06_proc_ah34",
   "void far; mov AH,0x34 then (span largely undecodable, far calls); 1 caller (sub_66E62)",
   "118B span, 0 dyn, cd=0, 1 caller, undecodable body. R06 procedure entered with AH=0x34 selector. conf: low", "low"),
 "sub_6E02A": ("farptr_proc_6e02a",
   "void far; push ds ... (span undecodable to 0x6E074 byte 0x00, far calls 9A); 1 caller (sub_2C045)",
   "92B span, 0 dyn, cd=0, 1 caller, undecodable. Far-ptr procedure in the 0x6E02A region (R06 tail / pre-R14 gap). conf: low", "low"),
 "sub_6E4CE": ("r14_entry_partial",
   "void far (partial entry, mid-instruction head): decodes through a far call to retf; 1 caller (sub_2BE51)",
   "33B span, 0 dyn, cd=0, 1 caller, partial (head `add [bp+di]` artifact). R14-region entry glue. conf: low", "low"),
 "sub_6EF1C": ("r17_entry_partial",
   "void far (DATA-class partial 3B span, mid-instruction head); 1 caller (sub_2C0EF)",
   "3B span, 0 dyn, cd=0, 1 caller, DATA/partial. R17-region entry stub (mid-instruction start, class-c signature). conf: low", "low"),
 "sub_6F3E1": ("r17_push_args_c8",
   "void far; push bp, mov bp,sp; push 0x0C8, push 0 (call-frame setup with args 200/0, span 8B); 1 caller (sub_6E8F0 C)",
   "8B span, 0 dyn, cd=0, 1 caller. R17-region call-frame setup pushing arguments 0xC8 and 0. conf: med", "med"),
 "sub_6F54A": ("r17_farobj_proc_g",
   "void far; push bp ... (147B, undecodable head); 1 caller (sub_6E8F0 C)",
   "147B span, 0 dyn, cd=0, 1 caller, undecodable head. R17 far-object processor. conf: low", "low"),
 "sub_102DD6": ("r07_farptr_helper",
   "void far; push ds ... (34B partial); 1 caller (r07_e45)",
   "34B span, 0 dyn, cd=0, 1 caller, partial, called by r07_e45. R07 overlay far-ptr helper. conf: low", "low"),
 "sub_106E10": ("r12_farptr_helper_c",
   "void far; push ds ... (86B partial); 1 caller (r12_e40)",
   "86B span, 0 dyn, cd=0, 1 caller, partial, called by r12_e40. R12 overlay far-ptr helper C. conf: low", "low"),
 "sub_107316": ("r12_farptr_helper_d",
   "void far; push ds ... (59B partial); 1 caller (r12_e42)",
   "59B span, 0 dyn, cd=0, 1 caller, partial, called by r12_e42. R12 overlay far-ptr helper D. conf: low", "low"),
 "sub_107F2E": ("r15_state_107650_set",
   "void far; cs:107650 = 0x8DE (state word store, body continues with far calls); 1 caller (r15_e11)",
   "42B span, 0 dyn, cd=0, 1 caller, called by r15_e11. Stores 0x8DE into R15 overlay state word cs:107650. conf: med", "med"),
 "sub_108570": ("r15_flag_10788b_test",
   "void far; cmp cs:10788B, 0; jz ... retf (flag-byte test, partial span); 1 caller (r15_e14)",
   "9B LEAF span, 0 dyn, cd=0, 1 caller, partial, called by r15_e14. Tests R15 flag byte cs:10788B != 0. conf: med", "med"),
 "sub_108BAC": ("r15_flag_107762_body",
   "void far; cmp cs:107762, 0; jz/jmp into a large far-call body (288B, pad-heavy); 1 caller (r15_e38)",
   "288B span, 0 dyn, cd=0, 1 caller, pad-heavy. R15 dispatch gated on flag byte cs:107762. conf: low", "low"),
 "sub_11C1D2": ("r28_farptr_helper",
   "void far; push ax ... (53B partial, far calls); 1 caller (r28_e65)",
   "53B span, 0 dyn, cd=0, 1 caller, partial, called by r28_e65. R28 overlay far-ptr helper. conf: low", "low"),
 "r33_e87": ("r33_record_scan_4e",
   "void far; DI=[bp+6]; SI=0; loop: record = es:7894 dword_79B6E + DI*0x4E; skip if es:[bx+si+44]==0xFF (record scan, 0x4E stride); 1 caller (r33_e86)",
   "98B, 0 dyn, cd=0, 1 caller. R33 record scan over the 0x4E-stride table at 7894:79B6E keyed by DI, skipping 0xFF-empty slots. conf: med", "med"),
 "r33_e89": ("r33_record_walk_4e",
   "void far; CL=[bp+6]; loop: index = es:7894:79BDA * 0x4E into dword_79B6E far-ptr table (record walk, 258B); 1 caller (r33_e85)",
   "258B, 0 dyn, cd=0, 1 caller. R33 record walk: 79BDA*0x4E index through the 79B6E far-ptr table. conf: med", "med"),
 "sub_1661DA": ("r36_farptr_helper",
   "void far; push bp ... (51B partial); 1 caller (r36_e116)",
   "51B span, 0 dyn, cd=0, 1 caller, partial, called by r36_e116. R36 overlay far-ptr helper. conf: low", "low"),
 "sub_18537E": ("r53_farptr_proc",
   "void far; push ds ... (96B partial, far calls); 1 caller (r53_e88)",
   "96B span, 0 dyn, cd=0, 1 caller, partial, called by r53_e88. R53 overlay far-ptr procedure. conf: low", "low"),
 "sub_1896D7": ("r53_record_walk_82",
   "void far (DATA-class partial): AX=SI*0x82 index into es:6894 dword_69BEC far-ptr table (record walk, 0x82 stride); 1 caller (r53_e12)",
   "19B span, 0 dyn, cd=0, 1 caller, DATA/partial head. R53 record walk: SI*0x82 index through the 6894:69BEC far-ptr table. conf: low", "low"),
}
# validate
names=[v[0] for v in analysis.values()]
assert len(analysis)==22, len(analysis)
assert len(set(names))==22, "dups: %s"%[n for n in names if names.count(n)>1]
bad=[n for n in names if not re.match(r'^[a-z_][a-z0-9_]*$',n)]
assert not bad, bad
nonascii=[(k,f) for k,v in analysis.items() for f in (v[1],v[2]) for ch in f if ord(ch)>127]
assert not nonascii, nonascii
txt=io.open('registry/naming.yaml',encoding='utf-8').read()
existing=set(re.findall(r'name:\s*([a-z_][a-z0-9_]*)',txt))
coll=[n for n in names if n in existing]
print("collisions:", coll)
print("total:", len(names), "OK:", len(set(names))==22 and not bad and not coll)
json.dump(analysis, open('analysis/ida_falconcd/batch16_names.json','w'), indent=1)
print("wrote batch16_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))