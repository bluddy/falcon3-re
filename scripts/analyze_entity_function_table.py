import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_function_table.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing entity function dispatch table...")
idaapi.auto_wait()

print("=== CRITICAL DISCOVERY ===")
print("entity_slot_update_loop @ 0x3C254:")
print("  mov di, [si+0Ch]      ; Load object_category")
print("  shl di, 1             ; Multiply by 2 (word table)")
print("  mov bx, funcs_3C261[di]  ; Load function pointer")
print("  call bx               ; Call entity-specific function")
print()
print("This means: object_category is used as INDEX into function table!")
print("Each category has its own update function!")
print()

# Read the function table at 0x3C261
table_addr = 0x3C261
print(f"=== Function Dispatch Table @ 0x{table_addr:X} ===\n")
print("Reading function pointers (word size, 2 bytes each):\n")

# Read up to 20 entries
functions = []
for i in range(20):
    ptr_addr = table_addr + (i * 2)
    func_ptr = idc.get_wide_word(ptr_addr)
    
    if func_ptr == 0 or func_ptr == 0xFFFF:
        # End of table or invalid
        if i < 5:
            functions.append((i, func_ptr, "NULL or invalid"))
            continue
        else:
            break
    
    # Try to get function name
    func_name = idc.get_func_name(func_ptr)
    if not func_name:
        func_name = idc.get_name(func_ptr)
    
    if not func_name:
        func_name = f"sub_{func_ptr:X}"
    
    functions.append((i, func_ptr, func_name))

print("Category | Function Pointer | Function Name")
print("---------|------------------|------------------------------------------")

for idx, ptr, name in functions:
    print(f"   {idx:2d}    |      0x{ptr:04X}      | {name}")

print("\n\nThis table maps object_category values to their update functions!")
print()

# Analyze each function
print("=== ANALYZING CATEGORY FUNCTIONS ===\n")

for idx, ptr, name in functions[:10]:
    if ptr == 0 or ptr == 0xFFFF:
        print(f"\nCategory {idx}: NULL/Invalid - no special processing")
        continue
    
    print(f"\nCategory {idx}: {name} @ 0x{ptr:X}")
    print("-" * 60)
    
    # Check if it's a valid function
    func_start = ptr
    func_end = idc.find_func_end(func_start)
    
    if func_end == idc.BADADDR:
        print("  Not a valid function")
        continue
    
    size = func_end - func_start
    print(f"  Size: {size} bytes")
    
    # Show first 20 instructions
    print("  First 20 instructions:")
    ea = func_start
    count = 0
    while ea < func_end and count < 20:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"    {disasm}")
        ea = idc.next_head(ea, func_end)
        count += 1
    
    if count >= 20:
        print("    ... (truncated)")

# Try to correlate with known object categories
print("\n\n=== CORRELATING WITH ObjectCategory ENUM ===\n")

category_names = {
    0: "UNKNOWN_0",
    1: "AIRCRAFT",
    2: "GROUND_VEHICLE", 
    3: "SHIP",
    4: "BUILDING",
    5: "RADAR_SITE",
    6: "SAM_SITE",
    7: "AAA_SITE",
}

print("Category | ObjectCategory Name | Function")
print("---------|---------------------|------------------------------------------")

for idx, ptr, fname in functions[:10]:
    cat_name = category_names.get(idx, f"Unknown_{idx}")
    status = "✓ CONFIRMED" if idx == 4 else "hypothesis"
    print(f"   {idx:2d}    | {cat_name:19s} | {fname:30s} [{status}]")

# Check if any category points to same function (category aliasing)
print("\n\n=== CHECKING FOR CATEGORY ALIASING ===\n")
print("Multiple categories pointing to same function:\n")

func_groups = {}
for idx, ptr, fname in functions:
    if ptr not in func_groups:
        func_groups[ptr] = []
    func_groups[ptr].append(idx)

for ptr, categories in func_groups.items():
    if len(categories) > 1 and ptr != 0 and ptr != 0xFFFF:
        fname = idc.get_func_name(ptr) or f"sub_{ptr:X}"
        print(f"Function {fname} @ 0x{ptr:X}:")
        print(f"  Used by categories: {categories}")
        cat_names = [category_names.get(c, f"unknown_{c}") for c in categories]
        print(f"  Category names: {', '.join(cat_names)}")

print("\n\nEntity function table analysis complete.")
output_file.close()
idc.qexit(0)
