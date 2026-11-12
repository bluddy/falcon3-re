#!/usr/bin/env python3
"""Plan SPLIT manifest for Level-0 batch 1 collision fixes (Phase 1).

Creates split_funcs entries for the 6 functions that were named in Level-0
batch 1 but are actually merged with parent functions:

1. cs_word_2b80_set (0x22846) - inside state_word_2223e_set (0x22841)
2. cs_word_2b82_set (0x2284B) - inside state_word_2223e_set (0x22841)
3. cs_word_2b84_set (0x22850) - inside state_word_2223e_set (0x22841)
4. farobj_dispatch_table (0x263F6) - inside dispatch_220d4_stub (0x263F0)
5. cs_word_2b76_get (0x22436) - inside control_axes_read (0x2234B)
6. cs_word_2b78_get (0x2243B) - inside control_axes_read (0x2234B)

These splits must happen in dependency order (parent first, then children if
parent has multiple splits).
"""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "s4" / "split_batch1_collisions.json"

# Phase 1 splits (owner ea, split point, tail name)
# Order matters: do state_word_2223e_set first (3 splits), then others
SPLITS = [
    # state_word_2223e_set (0x22841, 5B total) splits into 3 pieces:
    # - Head 0x22841..0x22846 (5B, keeps name)
    # - Tail 1: 0x22846..0x2284B (5B, cs_word_2b80_set)
    # - Tail 2: 0x2284B..0x22850 (5B, cs_word_2b82_set)
    # - Tail 3: 0x22850..0x22855 (5B, cs_word_2b84_set) [end guessed, will verify]
    (0x22841, 0x22846, "cs_word_2b80_set"),    # split 1
    (0x22846, 0x2284B, "cs_word_2b82_set"),    # split 2 (from tail 1)
    (0x2284B, 0x22850, "cs_word_2b84_set"),    # split 3 (from tail 2)
    
    # dispatch_220d4_stub (0x263F0, 6B) → farobj_dispatch_table at +0x006
    (0x263F0, 0x263F6, "farobj_dispatch_table"),
    
    # control_axes_read (0x2234B, 211B) has 2 tiny accessors merged:
    # - cs_word_2b76_get at +0xEB = 0x22436
    # - cs_word_2b78_get at +0xF0 = 0x2243B
    (0x2234B, 0x22436, "cs_word_2b76_get"),    # split at +0xEB
    (0x22436, 0x2243B, "cs_word_2b78_get"),    # split tail at +0x0F0
]

def compute_sha256(bytecode_hex):
    """Compute SHA256 of hex bytecode string."""
    return hashlib.sha256(bytes.fromhex(bytecode_hex)).hexdigest()

def main():
    fb = json.loads(FB.read_text())
    
    # Load naming.yaml to get names
    naming_map = {}
    import re
    for m in re.finditer(r'- ida: (sub_[0-9A-F]+)\s+name: (\S+)', NAMING.read_text()):
        naming_map[m.group(1)] = m.group(2)
    
    split_funcs = []
    
    for owner_ea, split_at, tail_name in SPLITS:
        owner_key = f"sub_{owner_ea:X}"
        split_key = f"sub_{split_at:X}"
        
        # Get owner info from function_bytes
        owner = fb.get(owner_key)
        if not owner:
            print(f"ERROR: {owner_key} not found in function_bytes.json")
            continue
        
        owner_end = owner["ea"] + owner["size"]
        owner_name = naming_map.get(owner_key, owner.get("name", owner_key))
        
        # Check if split point exists as a function (means already split)
        split_fn = fb.get(split_key)
        if split_fn:
            # Already split - this becomes the owner for next iteration
            print(f"INFO: {split_key} already exists (size {split_fn['size']}B), "
                  f"using as owner for next split")
            continue
        
        # Get bytecode for head and tail
        owner_bytes = owner.get("bytes", "")
        if not owner_bytes:
            print(f"ERROR: {owner_key} has no bytecode")
            continue
        
        # Calculate split position in bytes
        split_offset = split_at - owner_ea
        split_offset_bytes = split_offset * 2  # hex string, 2 chars per byte
        
        head_bytes = owner_bytes[:split_offset_bytes]
        tail_bytes = owner_bytes[split_offset_bytes:]
        
        head_size = len(head_bytes) // 2
        tail_size = len(tail_bytes) // 2
        
        # Compute SHA256 hashes
        sha256_head = compute_sha256(head_bytes)
        sha256_tail = compute_sha256(tail_bytes)
        
        split_entry = {
            "ea": owner_ea,
            "at": split_at,
            "end": owner_end,
            "name": owner_name,
            "far": owner.get("far", True),  # assume far for overlays
            "sha256_head": sha256_head,
            "sha256_tail": sha256_tail,
        }
        
        split_funcs.append(split_entry)
        
        print(f"{owner_name:30s} (0x{owner_ea:05X}, {owner['size']:3d}B)")
        print(f"  Split at 0x{split_at:05X} (+0x{split_offset:03X})")
        print(f"    Head: {head_size:3d}B  SHA256: {sha256_head[:16]}...")
        print(f"    Tail: {tail_size:3d}B  SHA256: {sha256_tail[:16]}...  ({tail_name})")
        print()
    
    # Save manifest
    manifest = {
        "finding": "183_phase1",
        "step": "S4: Level-0 batch 1 collision fixes (6 splits)",
        "split_funcs": split_funcs,
    }
    
    with open(OUT, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nWrote {OUT}")
    print(f"Total splits planned: {len(split_funcs)}")

if __name__ == "__main__":
    main()
