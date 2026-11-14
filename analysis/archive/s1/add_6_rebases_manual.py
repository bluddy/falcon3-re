#!/usr/bin/env python3
"""Manually add 6 REBASE entries to manifest with correct sha256 computation."""
import json
import hashlib

# First, restore the manifest to before my changes
import shutil
shutil.copy('ofe_before_205.json', '../../registry/orphan_funcs_expected.json')

# Load live IDB to compute hashes
# Unfortunately we can't easily read IDA bytes from Python without IDA API
# So I'll use the hashes I computed earlier (which should be correct for [new, end))
# and manually add the old_sha256 and prefix_sha256

# These are the entries with computed sha256 for [new_start, end):
entries_with_sha = [
    {"ea": 0x407BE, "old_ea": 0x407BF, "end": 0x40843, "clear_lo": 0x407BE, "name": "sub_407BF",
     "sha256": "865ac6577852a45d062b651d2f4aae81d3716e1a9e8f629d964c7b1eb8234313"},
    {"ea": 0x40DDA, "old_ea": 0x40DDB, "end": 0x40E35, "clear_lo": 0x40DDA, "name": "sub_40DDB",
     "sha256": "57b9523599976e2abc67aa63f452f34c1684f8a76d369a283d732cdb93f1db51"},
    {"ea": 0x40C68, "old_ea": 0x40C69, "end": 0x40C73, "clear_lo": 0x40C68, "name": "sub_40C69",
     "sha256": "8a43726e6d7f82004b1d76f393f0b7264f7acac8d81eca3df91d3c895e8f3d55"},
    {"ea": 0x40044, "old_ea": 0x40045, "end": 0x4005C, "clear_lo": 0x40044, "name": "sub_40045",
     "sha256": "1c267adc4163599912121fa65737774fdaca4660ff618e14b80ce6544c9472ef"},
    {"ea": 0x3FD65, "old_ea": 0x3FD66, "end": 0x3FD89, "clear_lo": 0x3FD65, "name": "sub_3FD66",
     "sha256": "97714aac5da9ff39e6d426db24b7a1d61dcd2145a289a15ade9d608ea4143124"},
    {"ea": 0x404F0, "old_ea": 0x404F1, "end": 0x404F6, "clear_lo": 0x404F0, "name": "sub_404F1",
     "sha256": "85ce4c0822a742c39ae30ef63a94f1c3ce0f758cee20abc3067ff8808408cf94"},
]

# For old_sha256 and prefix_sha256, I need to compute from IDB
# But since I can't easily do that, I'll mark them as needing computation
# Actually, let me check if plan mode would work now that I understand the format

print("Need to compute old_sha256 and prefix_sha256 values in IDA")
print("These require:")
print("  old_sha256 = sha256 of bytes [old_ea, end)")
print("  prefix_sha256 = sha256 of bytes [ea, old_ea)  (just 1 byte)")
print("\nCan't proceed without IDA API access to get_bytes()")
