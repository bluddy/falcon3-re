#!/usr/bin/env python3
"""Compute sha256 hashes for new REBASE entries - corrected version."""
import os
os.environ["DBFL_KILL"] = "1"

import hashlib
import idc
import json

# New REBASE entries for finding 205
# Format: (old_start, new_start, end, clear_lo, ds_para)
rebases = [
    (0x407BF, 0x407BE, 0x40843, 0x407BE, None),  # sub_407BF
    (0x40DDB, 0x40DDA, 0x40E35, 0x40DDA, None),  # sub_40DDB
    (0x40C69, 0x40C68, 0x40C73, 0x40C68, None),  # sub_40C69
    (0x40045, 0x40044, 0x4005C, 0x40044, None),  # sub_40045
    (0x3FD66, 0x3FD65, 0x3FD89, 0x3FD65, None),  # sub_3FD66
    (0x404F1, 0x404F0, 0x404F6, 0x404F0, None),  # sub_404F1
]

results = []
for old_start, new_start, end, clear_lo, ds_para in rebases:
    clear_hi = end
    
    # Get function name at old location
    func_name = idc.get_func_name(old_start)
    if not func_name:
        func_name = "sub_%X" % old_start
    
    # REBASE clears [clear_lo, clear_hi) which is [new_start, end)
    # Hash the bytes that will be cleared
    clear_bytes = idc.get_bytes(clear_lo, clear_hi - clear_lo)
    if clear_bytes:
        sha256 = hashlib.sha256(clear_bytes).hexdigest()
    else:
        sha256 = "ERROR_NO_BYTES"
    
    # Check what's at these addresses
    byte_at_new = idc.get_wide_byte(new_start)
    byte_at_old = idc.get_wide_byte(old_start)
    
    entry = {
        "old": f"0x{old_start:X}",
        "new": f"0x{new_start:X}",
        "end": f"0x{end:X}",
        "clear_lo": f"0x{clear_lo:X}",
        "clear_hi": f"0x{clear_hi:X}",
        "name": func_name,
        "sha256": sha256,
        "size": end - new_start,
        "byte_at_new": f"0x{byte_at_new:02X}",
        "byte_at_old": f"0x{byte_at_old:02X}",
    }
    results.append(entry)
    print(f"{entry['old']} -> {entry['new']}: {func_name} ({entry['size']}B)")
    print(f"  byte@new=0x{byte_at_new:02X}, byte@old=0x{byte_at_old:02X}")
    print(f"  sha256={sha256[:16]}...")

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_manifest_v2.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nWrote {len(results)} entries")

idc.qexit(0)
