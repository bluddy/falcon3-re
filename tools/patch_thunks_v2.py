#!/usr/bin/env python3
"""Patch the FALCONCD.EXE thunk table with live runtime targets."""
import json
import struct
from pathlib import Path

EXE_PATH = Path("game/FALCONCD.EXE")
STATIC_ENTRIES = Path("analysis/ida_falconcd/overlay_entries.json")
THUNK_STATES = Path("analysis/traces/thunk_states.json")
THUNK_TABLE_OFF = 0x1EBAF
THUNK_LEN = 10


def parse_seg_off(s: str):
    try:
        seg_str, off_str = s.split(":")
        return (int(seg_str, 16), int(off_str, 16))
    except Exception:
        return None


def main() -> int:
    if not EXE_PATH.exists():
        print(f"EXE not found: {EXE_PATH}")
        return 1

    # Load static entries (for reference)
    static = json.loads(Path("analysis/ida_falconcd/overlay_entries.json").read_text())

    # Load thunk states (live targets)
    thunk_states = json.loads(Path("analysis/traces/thunk_states.json").read_text())

    # rec_id -> (seg, off) from resolved_targets
    live_targets = {}
    for rec in thunk_states["records"]:
        if rec["resolved_targets"]:
            seg, off = parse_seg_off(rec["resolved_targets"][0])
            if seg is not None:
                live_targets[rec["rec_id"]] = (seg, off)

    # Load EXE
    data = bytearray(EXE_PATH.read_bytes())

    # Scan thunk table to build rec_id -> list of entry indices
    # Thunk table at 0x1EBAF, 10 bytes per entry
    # Each entry: E8 disp16 (3) + EA off seg (5) + rec_id word (2)
    rec_to_indices = {}
    for idx in range(500):
        off = THUNK_TABLE_OFF + idx * 10
        if off + 10 > len(data):
            break
        rec_id = struct.unpack_from("<H", data, THUNK_TABLE_OFF + idx * 10 + 8)[0]
        if rec_id > 0:
            if rec_id not in rec_to_indices:
                rec_to_indices[rec_id] = []
            rec_to_indices[rec_id].append(idx)

    print(f"Found {len(rec_to_indices)} distinct rec_ids in thunk table")
    for rec_id, idxs in sorted(rec_to_indices.items()):
        print(f"  rec {rec_id}: {len(idxs)} entries at indices {idxs[:5]}{'...' if len(idxs)>5 else ''}")

    # Patch each rec_id that has a live target
    data = bytearray(EXE_PATH.read_bytes())
    patched = 0
    skipped = 0

    for rec_id, (seg, off) in sorted(live_targets.items()):
        if rec_id not in rec_to_indices:
            print(f"Rec {rec_id}: not found in thunk table, skipping")
            continue

        indices = rec_to_indices[rec_id]
        for idx in indices:
            entry_off = THUNK_TABLE_OFF + idx * 10
            # Verify rec_id matches
            existing_rec = struct.unpack_from("<H", data, THUNK_TABLE_OFF + idx * 10 + 8)[0]
            if existing_rec != rec_id:
                print(f"  WARNING: rec_id mismatch at idx {idx} (expected {rec_id}, got {existing_rec})")
                continue

            # Patch the ljmp target (EA off seg) at offset +3
            # EA off_low off_high seg_low seg_high
            patch_off = THUNK_TABLE_OFF + idx * 10 + 3
            data[patch_off] = 0xEA
            data[patch_off + 1] = off & 0xFF
            data[patch_off + 1 + 1] = (off >> 8) & 0xFF
            data[patch_off + 3] = seg & 0xFF
            data[patch_off + 4] = (seg >> 8) & 0xFF

            print(f"Patched rec {rec_id} idx {idx} @ 0x{THUNK_TABLE_OFF + idx * 10:X} -> {seg:04X}:{off:04X}")
            patched += 1

    # Write back
    EXE_PATH.write_bytes(data)
    print(f"\nPatched {patched} thunk entries in {EXE_PATH}")
    return 0


if __name__ == "__main__":
    import struct
    import sys
    sys.exit(main())