#!/usr/bin/env python3
"""Patch the static thunk table in IDA with live runtime targets from thunk_states.json.

Run this inside IDA Pro (File -> Script File...).

Reads:
- analysis/traces/thunk_states.json (resolved targets per rec_id)
- Uses the static overlay_entries.json mapping (already in IDA as comments/names)

Patches:
- The thunk table at 0x1EBAF (file offset) / corresponding IDA address
- Each 10-byte entry: E8 disp16 (3) + EA off seg (5) + word rec_id (2)
- Patches the EA off seg (bytes 3-7) with the live target segment:offset
"""
import json
import ida_bytes
import ida_name
import ida_segment
import idc

THUNK_TABLE_EA = 0x1EBAF  # IDA linear address of thunk table start
THUNK_LEN = 10
EXPECTED_RECORDS = 66


def main():
    # Load thunk states
    thunk_states_path = r"C:\Users\yotam\projects\falcon3\analysis\traces\thunk_states.json"
    with open(thunk_states_path, 'r') as f:
        thunk_states = json.load(f)

    # Build rec_id -> live target mapping (seg, off)
    live_targets = {}
    for rec in thunk_states["records"]:
        if rec["resolved_targets"]:
            t = rec["resolved_targets"][0]
            seg_str, off_str = t.split(":")
            seg = int(seg_str, 16)
            off = int(off_str, 16)
            live_targets[rec["rec_id"]] = (seg, off)

    print(f"Loaded {len(live_targets)} live targets from thunk_states.json")

    # Scan thunk table in IDA to map rec_id -> list of entry EAs
    rec_to_eas = {}
    ea = THUNK_TABLE_EA
    for idx in range(500):  # enough for 303 entries
        entry_ea = THUNK_TABLE_EA + idx * 10
        if ea >= idc.get_segm_end(idc.get_segm_start(ea)):
            break
        rec_id = ida_bytes.get_word(ea + 8)
        if rec_id > 0:
            rec_to_eas.setdefault(rec_id, []).append(ea)

    print(f"Found {len(rec_to_eas)} distinct rec_ids in IDA thunk table")

    # Patch each entry
    patched = 0
    skipped = 0
    for rec_id, eas in sorted(rec_to_eas.items()):
        if rec_id not in live_targets:
            print(f"  Rec {rec_id}: no live target, skipping")
            continue

        seg, off = live_targets[rec_id]
        for ea in eas:
            # Verify rec_id matches
            existing_rec = ida_bytes.get_word(ea + 8)
            if existing_rec != rec_id:
                print(f"  WARNING: rec_id mismatch at 0x{ea:X} (expected {rec_id}, got {existing_rec})")
                continue

            # Patch the ljmp target (EA off seg) at ea+3
            # EA opcode at ea+3, then off (2 bytes), seg (2 bytes)
            patch_ea = ea + 3
            if idc.get_byte(patch_ea) != 0xEA:
                print(f"  WARNING: expected EA opcode at 0x{patch_ea:X}, got {ida_bytes.get_byte(patch_ea):02X}")
                continue

            # Patch off (2 bytes) + seg (2 bytes)
            ida_bytes.patch_byte(patch_ea + 1, off & 0xFF)
            ida_bytes.patch_byte(patch_ea + 2, (off >> 8) & 0xFF)
            ida_bytes.patch_byte(patch_ea + 3, rec_id & 0xFF)  # Wait, seg is the target segment
            # Actually the ljmp target is seg:off where seg is the TARGET segment
            # The live target gives us (seg, off)
            ida_bytes.patch_byte(patch_ea + 1, live_targets[rec_id][1] & 0xFF)
            ida_bytes.patch_byte(patch_ea + 2, (live_targets[rec_id][1] >> 8) & 0xFF)
            ida_bytes.patch_byte(patch_ea + 3, live_targets[rec_id][0] & 0xFF)
            ida_bytes.patch_byte(patch_ea + 4, (live_targets[rec_id][0] >> 8) & 0xFF)

            # Verify
            new_seg = ida_bytes.get_word(patch_ea + 3)
            new_off = ida_bytes.get_word(patch_ea + 1)
            if new_seg == seg and new_off == off:
                print(f"  Patched rec {rec_id} @ 0x{ea:X} -> {seg:04X}:{off:04X}")
            else:
                print(f"  WARNING: verify failed for rec {rec_id} @ 0x{ea:X}")

    print("Done. Remember to save the IDB!")


if __name__ == "__main__":
    import json
    main()