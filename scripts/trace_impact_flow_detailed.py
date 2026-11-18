import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\impact_flow_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting detailed impact flow analysis...")
idaapi.auto_wait()

print("=== STRATEGY ===")
print("Trace the complete flow from weapon impact to damage application")
print("by analyzing all function calls and data accesses in the chain:")
print()
print("entity_ground_collision_check @ 0x47787")
print("  → store_impact_step @ 0x397FB")
print("    → damage_event_dispatch_handler @ 0x2EAA7")
print("      → [mystery: find what determines hit object type]")
print()

# Analyze entity_ground_collision_check in detail
print("=== Deep Analysis: entity_ground_collision_check @ 0x47787 ===\n")

func_start = 0x47787
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")

# Find what it calls
print("Function calls:\n")
ea = func_start
call_count = 0
calls = []

while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem in ["call", "lcall"]:
        target = idc.get_operand_value(ea, 0)
        target_name = idc.get_name(target) if target != idc.BADADDR else None
        if target_name:
            calls.append((ea, target, target_name))
            print(f"  0x{ea:X}: call {target_name} @ 0x{target:X}")
            call_count += 1
    ea = idc.next_head(ea, func_end)

print(f"\nTotal: {call_count} calls")

# Find callers of entity_ground_collision_check
print("\n\nCalled by:\n")
callers = list(idautils.CodeRefsTo(func_start, True))
for caller in callers:
    caller_func = idc.get_func_name(caller)
    print(f"  0x{caller:X} in {caller_func if caller_func else 'unknown'}")

# Now analyze store_impact_step in extreme detail
print("\n\n=== EXTREME DETAIL: store_impact_step @ 0x397FB ===\n")

func_start = 0x397FB
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")

# Disassemble every instruction with analysis
print("Complete disassembly with annotations:\n")

ea = func_start
count = 0
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    # Add annotations for interesting instructions
    annotation = ""
    
    # Mark function calls
    if mnem in ["call", "lcall"]:
        target = idc.get_operand_value(ea, 0)
        target_name = idc.get_name(target)
        if target_name:
            annotation = f" ; → {target_name}"
    
    # Mark comparisons
    elif mnem == "cmp":
        op0 = idc.print_operand(ea, 0)
        op1 = idc.print_operand(ea, 1)
        if "[" in op0:
            try:
                val = idc.get_operand_value(ea, 1)
                if val == 4:
                    annotation = " ; *** CRITICAL: checking == 4 (building event?)"
                elif val == 0xFF:
                    annotation = " ; checking == 0xFF (pristine state?)"
            except:
                pass
    
    # Mark memory writes
    elif mnem in ["mov", "movb"] and "[" in idc.print_operand(ea, 0):
        op0 = idc.print_operand(ea, 0)
        try:
            # Look for status_flags writes
            if "+74h" in op0:
                annotation = " ; writing to status_flags"
            elif "+10h" in op0 and "di" in op0:
                val = idc.get_operand_value(ea, 1)
                if val == 0xA0:
                    annotation = " ; *** CRITICAL: set impact state = 0xA0"
        except:
            pass
    
    # Mark OR operations (setting bits)
    elif mnem == "or" and "[" in idc.print_operand(ea, 0):
        op0 = idc.print_operand(ea, 0)
        if "+74h" in op0:
            try:
                val = idc.get_operand_value(ea, 1)
                if val == 4:
                    annotation = " ; *** CRITICAL: set DESTROYED bit (bit 2)"
            except:
                pass
    
    print(f"  {disasm}{annotation}")
    ea = idc.next_head(ea, func_end)

# Find what calls store_impact_step
print("\n\nstore_impact_step called by:\n")
callers = list(idautils.CodeRefsTo(0x397FB, True))
for caller in callers:
    caller_func = idc.get_func_name(caller)
    print(f"  0x{caller:X} in {caller_func if caller_func else 'unknown'}")

# Now trace damage_event_dispatch_handler
print("\n\n=== Analyzing damage_event_dispatch_handler @ 0x2EAA7 ===\n")

func_start = 0x2EAA7
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)")
print("\nThis function is very abstract - uses op_dispatch pattern")
print("Let's find what it calls and what calls it:\n")

# Find calls
print("Calls:\n")
ea = func_start
calls = []
while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem in ["call", "lcall"]:
        target = idc.get_operand_value(ea, 0)
        target_name = idc.get_name(target) if target != idc.BADADDR else None
        if target_name:
            if target_name not in [name for _, _, name in calls]:
                calls.append((ea, target, target_name))
    ea = idc.next_head(ea, func_end)

for ea, target, name in calls:
    print(f"  {name}")

print("\n\nCalled by:\n")
callers = list(idautils.CodeRefsTo(0x2EAA7, True))
for caller in callers:
    caller_func = idc.get_func_name(caller)
    print(f"  0x{caller:X} in {caller_func if caller_func else 'unknown'}")
    
    # Show a few instructions before the call for context
    print(f"    Context:")
    context_ea = caller - 20
    for i in range(5):
        if context_ea < caller:
            disasm = idc.generate_disasm_line(context_ea, 0)
            print(f"      {disasm}")
            context_ea = idc.next_head(context_ea, caller + 1)

# Search for functions that check building/object types near coordinates
print("\n\n=== Searching for Coordinate-Based Object Lookup Functions ===\n")
print("Looking for functions that might check object type at (X,Y) position...\n")

# Pattern: functions that take coordinates and return type/object info
# Look for functions with multiple coordinate parameters

# Search for tile coordinate functions
tile_functions = []
for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if func_name and ("tile" in func_name.lower() or 
                      "coord" in func_name.lower() or
                      "position" in func_name.lower() or
                      "lookup" in func_name.lower()):
        func_end = idc.find_func_end(func_ea)
        tile_functions.append((func_ea, func_name, func_end - func_ea))

print(f"Found {len(tile_functions)} coordinate-related functions:\n")
for addr, name, size in sorted(tile_functions, key=lambda x: x[2], reverse=True)[:20]:
    print(f"  0x{addr:X}: {name} ({size}B)")

# Look for array access patterns with 2D indexing
print("\n\n=== Searching for 2D Array Access Patterns ===\n")
print("Pattern: [base + X*stride + Y] or similar\n")

# This is hard to detect statically, but we can look for:
# - LEA instructions computing addresses
# - IMUL/SHL followed by ADD (X*stride + Y pattern)

array_access_patterns = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for LEA with complex addressing
            if mnem == "lea":
                disasm = idc.generate_disasm_line(ea, 0)
                # Look for [base+reg*scale+reg] patterns
                if "*" in disasm or "+" in disasm:
                    func_name = idc.get_func_name(ea)
                    if func_name:
                        array_access_patterns.append((ea, func_name, disasm))
            
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(array_access_patterns)} potential 2D array access patterns:\n")

# Group by function
func_patterns = {}
for ea, func_name, disasm in array_access_patterns:
    if func_name not in func_patterns:
        func_patterns[func_name] = []
    func_patterns[func_name].append((ea, disasm))

for func_name in sorted(func_patterns.keys())[:15]:
    patterns = func_patterns[func_name]
    print(f"\n{func_name}: {len(patterns)} patterns")
    for ea, disasm in patterns[:3]:
        print(f"  0x{ea:X}: {disasm}")

print("\n\nDetailed impact flow analysis complete.")
output_file.close()
idc.qexit(0)
