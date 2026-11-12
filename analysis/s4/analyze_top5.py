#!/usr/bin/env python3
"""Analyze top 5 overlay functions using IDA."""
import idc
import idaapi
import idautils

def analyze_function(ea, name, description):
    print(f"\n{'='*80}")
    print(f"{name} at 0x{ea:05X} - {description}")
    print(f"{'='*80}")
    
    func = idaapi.get_func(ea)
    if not func:
        print(f"ERROR: No function at 0x{ea:05X}")
        return
    
    print(f"Function bounds: 0x{func.start_ea:05X} - 0x{func.end_ea:05X} ({func.end_ea - func.start_ea}B)")
    print(f"\nDisassembly:")
    print(f"{'Address':<12} {'Bytes':<20} {'Instruction'}")
    print(f"{'-'*80}")
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            bytes_str = " ".join([f"{idc.get_wide_byte(head+i):02X}" for i in range(min(8, func.end_ea - head))])
            disasm = idc.generate_disasm_line(head, 0)
            print(f"0x{head:05X}      {bytes_str:<20} {disasm}")
    
    # Check for xrefs
    xrefs_to = list(idautils.XrefsTo(ea))
    print(f"\nXrefs to this function: {len(xrefs_to)}")
    if len(xrefs_to) <= 10:
        for xref in xrefs_to[:10]:
            caller_name = idc.get_func_name(xref.frm)
            print(f"  0x{xref.frm:05X} from {caller_name}")
    
    xrefs_from = list(idautils.XrefsFrom(ea))
    print(f"\nXrefs from this function: {len(xrefs_from)}")
    for xref in xrefs_from[:10]:
        target_name = idc.get_name(xref.to, idc.GN_VISIBLE) or f"0x{xref.to:X}"
        print(f"  -> {target_name} (type: {xref.type})")

# Analyze top 5
targets = [
    (0x2BFC3, "sub_2BFC3", "Rank 1: 30,515 calls, 8B - Near call + far jump"),
    (0x263F6, "sub_263F6", "Rank 2: 18,079 calls, 122B - Dispatcher + data table"),
    (0x2BEA1, "sub_2BEA1", "Rank 3: 11,155 calls, 8B - Near call + far jump"),
    (0x2295C, "sub_2295C", "Rank 4: 11,154 calls, 2B - sub ax,ax"),
    (0x256A3, "sub_256A3", "Rank 5: 10,222 calls, 15B - DGROUP accessor"),
]

for ea, name, desc in targets:
    analyze_function(ea, name, desc)

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print(f"{'='*80}")

# Special analysis for sub_263F6 embedded data
print(f"\n\nsub_263F6 Embedded Data Analysis:")
print(f"{'='*80}")
ea = 0x263FC  # Start of data after 'retf'
end = 0x2BFC3 + 122  # End of function

print(f"Data region: 0x{ea:05X} - 0x{ea+116:05X} (116 bytes)")
print(f"\nHex dump (first 64 bytes):")
for i in range(0, min(64, 116), 16):
    hex_str = " ".join([f"{idc.get_wide_byte(ea+i+j):02X}" for j in range(16)])
    ascii_str = "".join([chr(idc.get_wide_byte(ea+i+j)) if 32 <= idc.get_wide_byte(ea+i+j) < 127 else '.' for j in range(16)])
    print(f"{ea+i:05X}: {hex_str}  {ascii_str}")

# Try to interpret as word array
print(f"\nAs word array (first 32 words):")
for i in range(0, min(64, 116), 2):
    word = idc.get_wide_word(ea + i)
    print(f"  [{i//2:2d}] 0x{ea+i:05X}: 0x{word:04X} ({word:5d})")
