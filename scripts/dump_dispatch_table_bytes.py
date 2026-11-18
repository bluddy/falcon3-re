import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\dispatch_table_bytes.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Dumping dispatch table bytes...")
idaapi.auto_wait()

# The MOV instruction at 0x3C25D references funcs_3C261[di]
# Let's find where the table actually starts

print("="*70)
print("INSTRUCTION ANALYSIS:")
print("="*70 + "\n")

mov_addr = 0x3C25D
call_addr = 0x3C261

print(f"MOV instruction @ 0x{mov_addr:05X}:")
print(f"  {idc.generate_disasm_line(mov_addr, 0)}")

# Get the bytes
mov_size = idc.get_item_size(mov_addr)
mov_bytes = [idc.get_wide_byte(mov_addr + i) for i in range(mov_size)]
print(f"  Bytes: {' '.join(f'{b:02X}' for b in mov_bytes)}")
print(f"  Size: {mov_size} bytes")

# Decode the MOV instruction
# 8B 9D 44 25 = MOV BX, [DI + 0x2544]
if mov_size == 4 and mov_bytes[0] == 0x8B and mov_bytes[1] == 0x9D:
    # This is MOV BX, [DI + disp16]
    disp_low = mov_bytes[2]
    disp_high = mov_bytes[3]
    displacement = disp_low | (disp_high << 8)
    print(f"  Decoded: MOV BX, [DI + 0x{displacement:04X}]")
    print(f"  This means table is at DS:0x{displacement:04X}")
    
    # Get current DS value
    # In 16-bit segmented mode, we need to calculate linear address
    # Typically DS = 0x54AF for entity data
    ds_segment = 0x54AF
    table_offset = displacement
    # Linear address = segment * 16 + offset
    # But in IDA, segment might be shown differently
    
    print(f"\n  If DS = 0x{ds_segment:04X}:")
    print(f"    Table offset: 0x{table_offset:04X}")
    # IDA flat address might be: segment_base + offset
    # where segment_base is how IDA represents it
    
    # The reference showed 0x3C261, so let's see if that's the table address
    table_flat_addr = 0x3C261 + 4  # After the MOV instruction

print(f"\nCALL instruction @ 0x{call_addr:05X}:")
print(f"  {idc.generate_disasm_line(call_addr, 0)}")

call_size = idc.get_item_size(call_addr)
call_bytes = [idc.get_wide_byte(call_addr + i) for i in range(call_size)]
print(f"  Bytes: {' '.join(f'{b:02X}' for b in call_bytes)}")
print(f"  Size: {call_size} bytes")

# The table should be somewhere nearby
# Let's dump from several possible locations

print("\n" + "="*70)
print("SEARCHING FOR TABLE DATA:")
print("="*70 + "\n")

# Try several locations
possible_locations = [
    ("After CALL (0x3C263)", 0x3C263),
    ("IDA ref address (0x3C261)", 0x3C261),
    ("After MOV (0x3C261)", mov_addr + mov_size),
    ("DS:0x2544 as flat", 0x54AF0 + 0x2544),  # segment to linear
    ("Code segment offset", 0x3B830 + 0x2544),  # code segment base
]

for desc, addr in possible_locations:
    print(f"\n{desc}:")
    print(f"Address: 0x{addr:05X}")
    
    # Check if this looks like a function pointer table
    # Read 10 words (20 bytes)
    words = []
    for i in range(10):
        word_addr = addr + (i * 2)
        word = idc.get_wide_word(word_addr)
        words.append(word)
    
    print("First 10 words:")
    for i, w in enumerate(words):
        # Check if this could be a valid function offset
        # Code segment is around 0x3B830-0x43AEE
        # So offsets might be in range 0x0000-0x8000 (relative to code segment)
        
        # Try as absolute address
        is_func_abs = (idc.get_func_attr(w, idc.FUNCATTR_START) != idc.BADADDR)
        
        # Try as offset from code segment base 0x3B830
        code_base = 0x3B830
        addr_from_code = code_base + w
        is_func_code = (idc.get_func_attr(addr_from_code, idc.FUNCATTR_START) != idc.BADADDR)
        
        # Try as offset from this location
        addr_relative = addr + w
        is_func_rel = (idc.get_func_attr(addr_relative, idc.FUNCATTR_START) != idc.BADADDR)
        
        marks = []
        if is_func_abs:
            marks.append(f"ABS:{idc.get_func_name(w)}")
        if is_func_code:
            marks.append(f"CODE+:{idc.get_func_name(addr_from_code)}")
        if is_func_rel:
            marks.append(f"REL:{idc.get_func_name(addr_relative)}")
        
        mark_str = " [" + ", ".join(marks) + "]" if marks else ""
        
        print(f"  [{i:2d}] 0x{w:04X}{mark_str}")

print("\n" + "="*70)
print("FINDING TABLE BY SEARCHING FOR DATA:")
print("="*70 + "\n")

# Try to find table by looking at what IDA named
table_name_ea = idc.get_name_ea_simple("funcs_3C261")
print(f"IDA name 'funcs_3C261' resolves to: 0x{table_name_ea:X}")

if table_name_ea != idc.BADADDR:
    print(f"\nData at funcs_3C261 (0x{table_name_ea:X}):")
    
    # Get segment info
    seg = idaapi.getseg(table_name_ea)
    if seg:
        print(f"  Segment: {idaapi.get_segm_name(seg)}")
        print(f"  Segment base: 0x{seg.start_ea:05X}")
    
    # Dump the table
    print("\n  Table entries (first 20):")
    for i in range(20):
        word_addr = table_name_ea + (i * 2)
        word = idc.get_wide_word(word_addr)
        
        # Try different interpretations
        interpretations = []
        
        # 1. Absolute address
        if idc.get_func_attr(word, idc.FUNCATTR_START) != idc.BADADDR:
            interpretations.append(("ABS", word, idc.get_func_name(word)))
        
        # 2. Offset from current segment base
        if seg:
            addr = seg.start_ea + word
            if idc.get_func_attr(addr, idc.FUNCATTR_START) != idc.BADADDR:
                interpretations.append(("SEG+", addr, idc.get_func_name(addr)))
        
        # 3. Offset from code segment 0x3B830
        code_base = 0x3B830
        addr = code_base + word
        if idc.get_func_attr(addr, idc.FUNCATTR_START) != idc.BADADDR:
            interpretations.append(("CODE+", addr, idc.get_func_name(addr)))
        
        # Show best interpretation
        if interpretations:
            interp_type, addr, fname = interpretations[0]
            print(f"    [{i:2d}] 0x{word:04X} -> 0x{addr:05X} ({interp_type}) {fname}")
        else:
            print(f"    [{i:2d}] 0x{word:04X} (no valid function found)")

print("\nDispatch table byte dump complete.")
output_file.close()
idc.qexit(0)
