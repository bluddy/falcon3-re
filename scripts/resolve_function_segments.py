import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\function_segments.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Resolving function pointer segment base...")
idaapi.auto_wait()

# The dispatch table is at 0x3C261
# The call site is at 0x3C259 (entity_slot_update_loop)
call_site = 0x3C259
table_addr = 0x3C261

print(f"Call site: 0x{call_site:X}")
print(f"Table address: 0x{table_addr:X}\n")

# Get segment information for call site
seg = idaapi.getseg(call_site)
if seg:
    print(f"Call site segment:")
    print(f"  Start: 0x{seg.start_ea:X}")
    print(f"  End: 0x{seg.end_ea:X}")
    print(f"  Name: {idaapi.get_segm_name(seg)}")
    seg_base = seg.start_ea
    print(f"  Base: 0x{seg_base:X}")
else:
    print("Could not find segment for call site")
    seg_base = 0x30000  # Guess based on typical code segment

print("\n" + "="*60)

# Try to determine segment by looking at the instruction
print("\nAnalyzing call instruction at 0x{:X}:".format(call_site))
disasm = idc.generate_disasm_line(call_site, 0)
print(f"  {disasm}")

# Read a few instructions around the call
print("\nContext (5 instructions before call):")
ea = call_site - 20  # Go back a bit
for i in range(8):
    disasm = idc.generate_disasm_line(ea, 0)
    marker = " <-- CALL HERE" if ea == call_site else ""
    print(f"  0x{ea:05X}: {disasm}{marker}")
    ea = idc.next_head(ea, call_site + 10)

print("\n" + "="*60)

# Now try different segment bases
print("\nTrying different segment bases for function pointers:\n")

# Read first few function pointers
func_ptrs = []
for i in range(5):
    ptr_addr = table_addr + (i * 2)
    func_offset = idc.get_wide_word(ptr_addr)
    func_ptrs.append((i, func_offset))

segment_bases_to_try = [
    ("Code segment (0x30000)", 0x30000),
    ("Absolute (no base)", 0x00000),
    ("Data segment (0x54AF0)", 0x54AF0),
    ("Seg from call site", seg_base if seg else 0x30000),
]

print("Cat | Offset | Segment Base | Absolute Addr | Valid? | Function Name")
print("----|--------|--------------|---------------|--------|---------------------------")

for seg_name, seg_base in segment_bases_to_try:
    print(f"\n{seg_name} (0x{seg_base:X}):")
    for cat, offset in func_ptrs[:3]:
        abs_addr = seg_base + offset
        
        # Check if this is a valid function
        func_start = idc.get_func_attr(abs_addr, idc.FUNCATTR_START)
        is_valid = (func_start != idc.BADADDR)
        
        func_name = idc.get_func_name(abs_addr) if is_valid else "---"
        
        valid_str = "✓ YES" if is_valid else "✗ NO"
        
        print(f" {cat:2d} | 0x{offset:04X} | 0x{seg_base:05X}    | 0x{abs_addr:05X}      | {valid_str:6s} | {func_name}")

print("\n" + "="*60)

# Check the actual bytes at table address
print(f"\nRaw bytes at table 0x{table_addr:X} (first 20 bytes):")
bytes_data = []
for i in range(20):
    b = idc.get_wide_byte(table_addr + i)
    bytes_data.append(b)

# Show as hex
hex_str = " ".join(f"{b:02X}" for b in bytes_data)
print(f"  {hex_str}")

# Show as words (little-endian)
print("\nAs words (little-endian):")
for i in range(10):
    word_offset = i * 2
    word = bytes_data[word_offset] | (bytes_data[word_offset + 1] << 8)
    print(f"  Category {i}: 0x{word:04X}")

print("\n" + "="*60)

# Look at entity_slot_update_loop more carefully
print("\nDetailed analysis of entity_slot_update_loop:")
loop_start = 0x3C1BD
print(f"\nFunction: entity_slot_update_loop @ 0x{loop_start:X}")

# Find the exact instruction sequence around the dispatch
search_start = 0x3C250
search_end = 0x3C270

print(f"\nInstructions from 0x{search_start:X} to 0x{search_end:X}:")
ea = search_start
while ea < search_end:
    disasm = idc.generate_disasm_line(ea, 0)
    # Get bytes
    size = idc.get_item_size(ea)
    byte_str = " ".join(f"{idc.get_wide_byte(ea+i):02X}" for i in range(min(size, 6)))
    
    marker = ""
    if ea == 0x3C254:
        marker = " <-- Load object_category"
    elif ea == 0x3C256:
        marker = " <-- Shift left (x2)"
    elif ea == 0x3C259:
        marker = " <-- Call function"
    
    print(f"  0x{ea:05X}: {byte_str:18s} {disasm}{marker}")
    ea = idc.next_head(ea, search_end)

print("\nSegment resolution complete.")
output_file.close()
idc.qexit(0)
