import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_structure_exploration.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Exploring EntitySlotRecord structure (92 bytes at 0x54AF:0x386F)...")
idaapi.auto_wait()

print("=== STRATEGY ===")
print("EntitySlotRecord is 92 bytes (0x5C stride)")
print("We've documented ~50 fields, but many gaps remain")
print("Search for all offset patterns [si+XX], [di+XX], [bx+XX] in 0x00-0x5C range")
print("Group by offset to find commonly accessed fields")
print()

# Track all entity field accesses
field_accesses = {}  # offset -> [(ea, func_name, mnem, disasm)]

print("=== Scanning All Code for Entity Field Accesses ===\n")
print("This will take a moment...\n")

# Common registers used for entity pointers: si, di, bx
registers = ['si', 'di', 'bx']

for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            mnem = idc.print_insn_mnem(ea)
            
            # Look for [reg+offset] patterns
            for reg in registers:
                if f"{reg}+" in disasm and "[" in disasm:
                    # Try to extract offset
                    # Patterns: [si+2Eh], [di+0Ch], [bx+74h], etc.
                    for offset in range(0, 0x5C):  # 0-91 bytes
                        hex_patterns = [
                            f"{reg}+{offset:X}h",
                            f"{reg}+0x{offset:X}",
                            f"{reg}+{offset}]",
                        ]
                        
                        if any(pattern in disasm for pattern in hex_patterns):
                            func_name = idc.get_func_name(ea)
                            if func_name:
                                if offset not in field_accesses:
                                    field_accesses[offset] = []
                                field_accesses[offset].append((ea, func_name, mnem, disasm))
                            break
            
            ea = idc.next_head(ea, seg_end)

print(f"Scanned all code segments.")
print(f"Found accesses to {len(field_accesses)} different offsets\n")

# Sort by number of accesses (most used fields first)
sorted_offsets = sorted(field_accesses.items(), key=lambda x: len(x[1]), reverse=True)

print("=== Entity Field Usage Statistics ===\n")
print("Offset | Accesses | Known Field")
print("-------|----------|------------------------------------------")

# Known fields for reference
known_fields = {
    0x00: "header",
    0x06: "farobj_slot",
    0x08: "distance_lo",
    0x0A: "distance_hi",
    0x0C: "object_category",
    0x10: "impact_state",
    0x2E: "velocity_component",
    0x74: "status_flags",
    0x75: "weapon_type",
    0x76: "unknown_flags_76",
    0x79: "tracking_flags",
    0x7A: "target_slot_index",
    0x8E: "angle_azimuth",
    0x92: "range",
    0x96: "position_x",
    0x98: "position_y",
    0x9A: "position_z",
    0xAE: "heat_signature",
    0xB3: "target_field_1",
    0xCA: "damage_status_flags",
}

for offset, accesses in sorted_offsets[:40]:  # Top 40 most accessed fields
    known = known_fields.get(offset, "UNKNOWN - NEW FIELD!")
    print(f"  +0x{offset:02X} | {len(accesses):6d}  | {known}")

# Now analyze the most accessed UNKNOWN fields in detail
print("\n\n=== DETAILED ANALYSIS OF TOP UNKNOWN FIELDS ===\n")

for offset, accesses in sorted_offsets[:50]:
    if offset not in known_fields:
        print(f"\n+0x{offset:02X} ({len(accesses)} accesses) - UNKNOWN FIELD")
        print("=" * 60)
        
        # Analyze access patterns
        read_count = 0
        write_count = 0
        test_count = 0
        cmp_count = 0
        
        func_usage = {}
        
        for ea, func_name, mnem, disasm in accesses:
            if mnem in ["mov", "movb", "movw"]:
                # Check if read or write
                op0 = idc.print_operand(ea, 0)
                if "[" in op0:
                    write_count += 1
                else:
                    read_count += 1
            elif mnem in ["test", "and", "or", "xor"]:
                test_count += 1
            elif mnem == "cmp":
                cmp_count += 1
            
            if func_name not in func_usage:
                func_usage[func_name] = 0
            func_usage[func_name] += 1
        
        print(f"  Access patterns:")
        print(f"    Reads: {read_count}, Writes: {write_count}")
        print(f"    Tests/logic: {test_count}, Comparisons: {cmp_count}")
        
        # Show top functions using this field
        top_funcs = sorted(func_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top functions:")
        for fname, count in top_funcs:
            print(f"    {fname}: {count} accesses")
        
        # Show sample instructions
        print(f"  Sample instructions:")
        for ea, func_name, mnem, disasm in accesses[:5]:
            print(f"    0x{ea:X}: {disasm}")

# Look for clusters of adjacent fields (likely struct members)
print("\n\n=== FIELD CLUSTERS (Adjacent Accesses) ===\n")
print("Fields accessed within 4 bytes of each other may be related\n")

for offset in range(0, 0x5C - 4):
    cluster = []
    for i in range(5):
        if (offset + i) in field_accesses:
            cluster.append(offset + i)
    
    if len(cluster) >= 3:  # 3 or more adjacent fields
        print(f"Cluster at +0x{offset:02X}:")
        for off in cluster:
            known = known_fields.get(off, "unknown")
            count = len(field_accesses[off])
            print(f"  +0x{off:02X}: {known} ({count} accesses)")

# Look for multi-byte fields (word/dword patterns)
print("\n\n=== POTENTIAL MULTI-BYTE FIELDS ===\n")
print("Adjacent offsets accessed in pairs may be 16-bit or 32-bit fields\n")

for offset in range(0, 0x5C - 2, 2):  # Check even offsets
    if offset in field_accesses and (offset + 2) in field_accesses:
        count1 = len(field_accesses[offset])
        count2 = len(field_accesses[offset + 2])
        
        # If both accessed frequently, might be a dword
        if count1 > 10 and count2 > 10:
            known1 = known_fields.get(offset, "unknown")
            known2 = known_fields.get(offset + 2, "unknown")
            print(f"+0x{offset:02X} + +0x{offset+2:02X}: {known1}, {known2} ({count1}, {count2} accesses)")

print("\n\nEntity structure exploration complete.")
output_file.close()
idc.qexit(0)
