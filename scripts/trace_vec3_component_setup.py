import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\vec3_setup_trace.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Tracing vec3 component setup before fixed_vec3_accumulate_a calls...")
idaapi.auto_wait()

print("="*70)
print("UNDERSTANDING THE CALCULATION")
print("="*70 + "\n")

print("fixed_vec3_accumulate_a calculates:")
print("  CX = (X * scale_x / divisor_x)")
print("     + (Y * scale_y / divisor_y)")
print("     + (Z * scale_z / divisor_z)")
print()
print("This is a scaled 3D vector magnitude calculation.")
print("The result becomes object_category after masking to 0x3FF.")
print()

print("Key question: Where are vec3_x/y/z_component set before the call?")
print()

# Global addresses
vec3_x = 0x235B1  # cs:vec3_x_component
vec3_y = 0x235B3  # cs:vec3_y_component
vec3_z = 0x235B5  # cs:vec3_z_component

print("Global vector components:")
print(f"  vec3_x_component @ cs:0x{vec3_x:04X}")
print(f"  vec3_y_component @ cs:0x{vec3_y:04X}")
print(f"  vec3_z_component @ cs:0x{vec3_z:04X}")
print()

print("="*70)
print("ANALYZING ag_weapon_entity_initialize CONTEXT")
print("="*70 + "\n")

# Look at code before first call to fixed_vec3_accumulate_a in ag_weapon_entity_initialize
call_site = 0x4C3E8

print(f"Call site: ag_weapon_entity_initialize @ 0x{call_site:05X}")
print("\n30 instructions before call:\n")

# Go back and show context
ea = call_site - 100
shown = 0

while ea < call_site and shown < 35:
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    marker = ""
    if mnem == "call":
        # Check if it's a call that might set vec3 components
        target = idc.get_operand_value(ea, 0)
        if target != idc.BADADDR:
            target_name = idc.get_func_name(target)
            if target_name:
                marker = f" (calls {target_name})"
    
    if ea == call_site:
        marker = " <-- CALL fixed_vec3_accumulate_a"
    elif "si+" in disasm:
        marker = " <-- Entity field access"
    
    print(f"0x{ea:05X}: {disasm:55s}{marker}")
    
    ea = idc.next_head(ea, call_site + 5)
    shown += 1

print("\n" + "="*70)
print("SEARCHING FOR vec3 COMPONENT WRITES")
print("="*70 + "\n")

# Search for writes to the vec3 globals
print("Searching for writes to vec3_x/y/z_component...\n")

vec3_writes = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    # Only search code segments
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for references to the vec3 globals
        if ("vec3_x_component" in disasm or "vec3_y_component" in disasm or 
            "vec3_z_component" in disasm):
            
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ["mov", "add", "sub"]:
                func_name = idc.get_func_name(ea)
                vec3_writes.append((ea, func_name, disasm))
        
        ea = idc.next_head(ea, seg.end_ea)

print(f"Found {len(vec3_writes)} operations on vec3 components:\n")

# Group by function
by_func = {}
for addr, func, disasm in vec3_writes:
    if func not in by_func:
        by_func[func] = []
    by_func[func].append((addr, disasm))

for func, ops in sorted(by_func.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
    print(f"\n{func} ({len(ops)} operations):")
    for addr, disasm in ops[:8]:
        print(f"  0x{addr:05X}: {disasm}")
    if len(ops) > 8:
        print(f"  ... ({len(ops) - 8} more)")

print("\n" + "="*70)
print("CHECKING BEFORE EACH WEAPON TYPE CALL")
print("="*70 + "\n")

# Each weapon type block in ag_weapon_entity_initialize calls fixed_vec3_accumulate_a
# Let's check what happens before each call

weapon_calls = [
    (0x4C3E8, "BX=5"),
    (0x4C434, "BX=6"),
    (0x4C480, "BX=9"),
    (0x4C4CC, "BX=7"),
    (0x4C51D, "BX=8"),
]

for call_addr, weapon_type in weapon_calls[:3]:
    print(f"\nWeapon type {weapon_type} - Call @ 0x{call_addr:05X}:")
    print("="*60)
    
    # Show 15 instructions before call
    ea = call_addr - 60
    shown = 0
    
    while ea < call_addr and shown < 18:
        disasm = idc.generate_disasm_line(ea, 0)
        
        marker = ""
        if ea == call_addr:
            marker = " <-- CALL HERE"
        elif "vec3" in disasm:
            marker = " <-- VEC3 SETUP"
        elif "[si+" in disasm:
            marker = " <-- Entity field"
        
        print(f"  0x{ea:05X}: {disasm:50s}{marker}")
        
        ea = idc.next_head(ea, call_addr + 5)
        shown += 1

print("\n" + "="*70)
print("HYPOTHESIS")
print("="*70 + "\n")

print("Based on the pattern, fixed_vec3_accumulate_a is calculating:")
print("  CX = weighted_sum(X, Y, Z)")
print()
print("But there's NO setup of vec3 components visible before the calls!")
print()
print("Possibilities:")
print("  1. vec3 components are global state set earlier in initialization")
print("  2. The function reads position from entity directly (via SI)")
print("  3. There's an inline setup we're missing")
print("  4. The components are set by a previous call in the same weapon block")
print()

print("Looking at the caller pattern in ag_weapon_entity_initialize:")
print("  1. Compare BX (weapon type)")
print("  2. Set entity fields +0x00, +0x02, +0x03, +0x04, +0x06, +0x08, +0x0A")
print("  3. Call fixed_vec3_accumulate_a")
print("  4. Mask CX to 0x3FF")
print("  5. Store in [si+0Ch]")
print()
print("The entity fields set before the call likely affect the calculation!")
print("Specifically: +0x06, +0x08, +0x0A might be X, Y, Z components?")

print("\nvec3 component setup trace complete.")
output_file.close()
idc.qexit(0)
