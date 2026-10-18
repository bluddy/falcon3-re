import sys, json, re, io
sys.stdout.reconfigure(encoding='utf-8')
# Finding 72 Level-1 Batch 5 (FINALE, 5)
analysis = {
 "sub_37FDD": ("entity_event_0e_dispatch",
   "NEAR retn fn; SI=ds:48BA->[SI+0CA]; if == ds:0E: ds:1077=0, retn; else body (110B) with game_state_setup_multi + state_byte_25488_get; 1 caller (sub_37A0A)",
   "110B retn, callees game_state_setup_multi + state_byte_25488_get. Entity event gate: equal-path clears ds:1077, else dispatches the entity state path. conf: med", "med"),
 "sub_6D13D": ("r06_gate_4ac9",
   "void far; gate ds:4AC9!=0 else retf; body (98B) into mode_gate_4a83_4ac2_r; 1 caller (sub_66E62)",
   "98B, callee mode_gate_4a83_4ac2_r. R06 outer gate on ds:4AC9 before the dual mode gate. conf: med", "med"),
 "sub_6F3E9": ("r17_dispatch_seq_2211c",
   "void far; near-call dispatch_2211c_invoke_2arg, then push args (0xC8, 0, ...) + far-call sequence (47B, pad-heavy); 1 caller (sub_2C149)",
   "47B span, callee dispatch_2211c_invoke_2arg. R17 dispatch sequence: 2-arg dispatch then argument-pushed far-call chain. conf: low", "low"),
 "sub_1896D2": ("r53_record_walk_entry",
   "void far; SI=0; tail-jmp r53_record_walk_main (loop-entry alias -- the SCC partner; mutual recursion with r53_record_walk_main); 1 caller",
   "5B, callee r53_record_walk_main (L1 SCC peer). Loop-entry trampoline: clears SI then joins the record walk (condenses with its caller into one SCC). conf: high", "high"),
 "sub_196E63": ("slope_far_call_driver",
   "void far; far-call slope_flag_test_bx, then (304B pad-heavy) far-call dispatch sequence; 1 caller (r59_e177)",
   "304B span, callee slope_flag_test_bx. Far-call driver around the slope test with a long callback sequence. conf: low", "low"),
}
# validate
names=[v[0] for v in analysis.values()]
assert len(analysis)==5, len(analysis)
assert len(set(names))==5, "dups"
bad=[n for n in names if not re.match(r'^[a-z_][a-z0-9_]*$',n)]
assert not bad, bad
nonascii=[(k,f) for k,v in analysis.items() for f in (v[1],v[2]) for ch in f if ord(ch)>127]
assert not nonascii, nonascii
txt=io.open('registry/naming.yaml',encoding='utf-8').read()
existing=set(re.findall(r'name:\s*([a-z_][a-z0-9_]*)',txt))
coll=[n for n in names if n in existing]
print("collisions:", coll)
print("total:", len(names), "OK:", not coll)
json.dump(analysis, open('analysis/ida_falconcd/level1_batch5_names.json','w'), indent=1)
print("wrote level1_batch5_names.json")
for k,(n,s,note,c) in sorted(analysis.items(), key=lambda x:x[1][0]):
    print("  %-34s conf=%s" % (n,c))