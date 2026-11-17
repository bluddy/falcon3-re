"""
Find CCIP (Continuously Computed Impact Point) calculation code for bombs.

CCIP shows a pipper on HUD indicating where bombs will impact.
Calculation involves:
- Current aircraft position, velocity, altitude
- Bomb ballistics (gravity, drag, initial velocity)
- Impact point prediction

Looking for:
- Gravity constant
- Trajectory calculation
- HUD pipper display
- Functions processing bomb weapon types (0x28, etc.)
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("CCIP BOMB BALLISTICS SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'gravity_constants': [],
    'trajectory_functions': [],
    'hud_pipper_refs': []
}

# Search for gravity-like constants
# Gravity is ~9.8 m/s^2 or ~32 ft/s^2
# In game units, might be scaled differently
# Look for constants around 10, 32, 98, 320, etc.

print("Searching for potential gravity constants...")
print("(Looking for constants ~9.8, 32, 98, 320 that could be gravity)")

# Get .data segment
data_seg = idaapi.get_segm_by_name(".data")
if data_seg:
    print(f"\nScanning .data segment: {data_seg.start_ea:#x} - {data_seg.end_ea:#x}")
    
    # Look for word/dword values that could be gravity
    ea = data_seg.start_ea
    gravity_candidates = []
    
    while ea < data_seg.end_ea:
        # Check word value
        word_val = idc.get_wide_word(ea)
        if word_val in [10, 32, 98, 320, 980, 3200, 9800]:
            # Check for xrefs
            xref_count = 0
            xref_funcs = []
            for xref in idautils.XrefsTo(ea):
                xref_count += 1
                func_name = idc.get_func_name(xref.frm)
                if func_name and func_name not in xref_funcs:
                    xref_funcs.append(func_name)
            
            if xref_count > 0:
                gravity_candidates.append({
                    'address': hex(ea),
                    'value': word_val,
                    'xref_count': xref_count,
                    'functions': xref_funcs[:5]  # First 5 functions
                })
                print(f"  Candidate @ {ea:#x}: value={word_val}, xrefs={xref_count}")
                for func in xref_funcs[:3]:
                    print(f"    -> {func}")
        
        ea += 2  # Move by word

    results['gravity_constants'] = gravity_candidates
    print(f"\nFound {len(gravity_candidates)} gravity constant candidates")

# Search for "CCIP", "PIPPER", "IMPACT" strings
print(f"\n{'=' * 80}")
print("Searching for CCIP/pipper/impact strings...")

for s in idautils.Strings():
    str_val = str(s).upper()
    
    if any(keyword in str_val for keyword in ['CCIP', 'PIPPER', 'IMPACT', 'DROP', 'RELEASE']):
        xrefs = []
        for xref in idautils.XrefsTo(s.ea):
            func_name = idc.get_func_name(xref.frm)
            xrefs.append({
                'address': hex(xref.frm),
                'function': func_name if func_name else 'unknown'
            })
        
        if xrefs or 'CCIP' in str_val:  # Always include CCIP even without xrefs
            results['hud_pipper_refs'].append({
                'string': str(s),
                'address': hex(s.ea),
                'xrefs': xrefs
            })
            print(f"  '{str(s)}' @ {s.ea:#x}")
            if xrefs:
                print(f"    {len(xrefs)} xrefs")

# Search for functions that handle bomb weapon types
print(f"\n{'=' * 80}")
print("Searching for bomb weapon type handlers...")
print("(Functions checking weapon type 0x28 = MK82_BOMB)")

text_seg = idaapi.get_segm_by_name(".text")
if text_seg:
    ea = text_seg.start_ea
    bomb_handlers = []
    
    while ea < text_seg.end_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0:
            # Look for cmp with 0x28 (MK82_BOMB)
            if insn.itype == idaapi.NN_cmp:
                for op in insn.ops:
                    if op.type == idaapi.o_imm and op.value == 0x28:
                        func = idaapi.get_func(ea)
                        if func:
                            func_name = idc.get_func_name(ea)
                            func_start = func.start_ea
                            
                            # Avoid duplicates
                            if not any(h['address'] == hex(func_start) for h in bomb_handlers):
                                bomb_handlers.append({
                                    'address': hex(func_start),
                                    'function': func_name,
                                    'check_at': hex(ea)
                                })
                                print(f"  {func_name} @ {func_start:#x}")
                                print(f"    Checks type 0x28 at {ea:#x}")
                        break
        
        ea = idc.next_head(ea, text_seg.end_ea)
    
    results['trajectory_functions'] = bomb_handlers
    print(f"\nFound {len(bomb_handlers)} functions checking bomb type 0x28")

# Save results
output_file = Path(__file__).parent / "ccip_search.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print(f"Summary:")
print(f"  Gravity candidates: {len(results['gravity_constants'])}")
print(f"  HUD string refs: {len(results['hud_pipper_refs'])}")
print(f"  Bomb handlers: {len(results['trajectory_functions'])}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
