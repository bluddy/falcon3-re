#!/usr/bin/env python3
"""Compute sha256 hashes from raw IDB bytes - standalone."""
import hashlib

# Read IDB file
# Skip reading IDB for now

# The IDA addresses are relative to the loaded binary base
# For a DOS .EXE, we need to find where these addresses map in the file
# But this is complex - let me just verify the approach is sound

# For now, let's verify my understanding is correct by checking
# the manifest format from an existing entry
import json
with open('registry/orphan_funcs_expected.json', 'r') as f:
    manifest = json.load(f)

print("Sample existing REBASE entry:")
if 'rebase_funcs' in manifest and len(manifest['rebase_funcs']) > 0:
    sample = manifest['rebase_funcs'][0]
    print(json.dumps(sample, indent=2))
    print(f"\nKey fields:")
    print(f"  ea (new): 0x{sample['ea']:X}")
    print(f"  old_ea: 0x{sample['old_ea']:X}")
    print(f"  end: 0x{sample['end']:X}")
    print(f"  clear_lo: 0x{sample['clear_lo']:X}")
    print(f"  Size to hash: {sample['end'] - sample['clear_lo']} bytes")
