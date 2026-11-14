#!/usr/bin/env python3
"""Add 6 new REBASE entries to manifest."""
import json

# Load manifest
with open('../../registry/orphan_funcs_expected.json', 'r') as f:
    manifest = json.load(f)

# New entries from rebase_manifest.json
new_entries = [
    {"ea": 0x407BE, "old_ea": 0x407BF, "end": 0x40843, "clear_lo": 0x407BE, "ds": None, "name": "sub_407BF", "far": True,
     "sha256": "865ac6577852a45d062b651d2f4aae81d3716e1a9e8f629d964c7b1eb8234313"},
    {"ea": 0x40DDA, "old_ea": 0x40DDB, "end": 0x40E35, "clear_lo": 0x40DDA, "ds": None, "name": "sub_40DDB", "far": True,
     "sha256": "57b9523599976e2abc67aa63f452f34c1684f8a76d369a283d732cdb93f1db51"},
    {"ea": 0x40C68, "old_ea": 0x40C69, "end": 0x40C73, "clear_lo": 0x40C68, "ds": None, "name": "sub_40C69", "far": True,
     "sha256": "8a43726e6d7f82004b1d76f393f0b7264f7acac8d81eca3df91d3c895e8f3d55"},
    {"ea": 0x40044, "old_ea": 0x40045, "end": 0x4005C, "clear_lo": 0x40044, "ds": None, "name": "sub_40045", "far": True,
     "sha256": "1c267adc4163599912121fa65737774fdaca4660ff618e14b80ce6544c9472ef"},
    {"ea": 0x3FD65, "old_ea": 0x3FD66, "end": 0x3FD89, "clear_lo": 0x3FD65, "ds": None, "name": "sub_3FD66", "far": True,
     "sha256": "97714aac5da9ff39e6d426db24b7a1d61dcd2145a289a15ade9d608ea4143124"},
    {"ea": 0x404F0, "old_ea": 0x404F1, "end": 0x404F6, "clear_lo": 0x404F0, "ds": None, "name": "sub_404F1", "far": True,
     "sha256": "85ce4c0822a742c39ae30ef63a94f1c3ce0f758cee20abc3067ff8808408cf94"},
]

# Add to rebase_funcs
if 'rebase_funcs' not in manifest:
    manifest['rebase_funcs'] = []

manifest['rebase_funcs'].extend(new_entries)

# Save manifest
with open('../../registry/orphan_funcs_expected.json', 'w', newline='\r\n') as f:
    json.dump(manifest, f, indent=2)

print(f"Added {len(new_entries)} entries. Total rebase_funcs: {len(manifest['rebase_funcs'])}")
