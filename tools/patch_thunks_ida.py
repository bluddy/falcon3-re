#!/usr/bin/env python3
"""Safely patch the 303 .RTLink thunks in IDA Pro and rebuild code/xrefs.

Run inside IDA: idat.exe -A -S"tools/patch_thunks_ida.py" FALCONCD.EXE.i64

Matches each thunk by (rec_id, orig_off) against thunk_states.json.
Converts runtime segs (normalized to load_base 0x01A2) to IDA segs (+0x0E5E).
Output goes to analysis/ida_falconcd/patch_thunks.log (IDA doesn't pipe stdout).
"""
import json
import os
import ida_auto
import ida_bytes
import ida_ua
import idc

THUNK_STATES_PATH = r"C:\Users\yotam\projects\falcon3\analysis\traces\thunk_states.json"
LOG_PATH = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\patch_thunks.log"
THUNK_COUNT = 303
THUNK_LEN = 10

# JSON segs are normalized to load_base 0x01A2; IDA loads MZ at 0x1000.
# IDA_SEG = JSON_SEG - 0x01A2 + 0x1000 = JSON_SEG + 0x0E5E
JSON_SEG_TO_IDA_SEG_DELTA = 0x0E5E

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

_log = open(LOG_PATH, "w")


def log(msg):
    _log.write(msg + "\n")
    _log.flush()


def find_thunk_table_ea():
    """Locate the 303-entry E8..EA thunk table in IDA."""
    candidates = [0x2BD9D, 0x2BFAB, 0x1EBAF]
    for ea in candidates:
        if ida_bytes.get_byte(ea) == 0xE8 and ida_bytes.get_byte(ea + 3) == 0xEA:
            log(f"[+] Found thunk table at IDA linear EA 0x{ea:X}")
            return ea
    log(f"[!] Could not find E8..EA thunk table at {[hex(x) for x in candidates]}")
    raise RuntimeError("thunk table not found")


def main():
    with open(THUNK_STATES_PATH, "r") as f:
        data = json.load(f)

    rec_targets = {}
    for rec in data["records"]:
        rid = rec["rec_id"]
        parsed = []
        for t in rec["resolved_targets"]:
            s_str, o_str = t.split(":")
            parsed.append((int(s_str, 16), int(o_str, 16)))
        rec_targets[rid] = parsed

    base_ea = find_thunk_table_ea()
    log(f"Thunk table: 0x{base_ea:X} .. 0x{base_ea + THUNK_COUNT * THUNK_LEN:X}")
    log(f"DRY_RUN={DRY_RUN}")
    log(f"Records in JSON: {len(rec_targets)}")

    matched = 0
    unmatched = 0
    patched = 0

    for idx in range(THUNK_COUNT):
        entry_ea = base_ea + idx * THUNK_LEN
        b0 = ida_bytes.get_byte(entry_ea)
        b3 = ida_bytes.get_byte(entry_ea + 3)
        orig_off = ida_bytes.get_word(entry_ea + 4)
        orig_seg = ida_bytes.get_word(entry_ea + 6)
        rec_id = ida_bytes.get_word(entry_ea + 8)

        if b0 != 0xE8 or b3 != 0xEA:
            log(
                f"  [!] Thunk #{idx:03d} @ 0x{entry_ea:X}: "
                f"unexpected bytes {b0:02X}..{b3:02X}, skipping"
            )
            unmatched += 1
            continue

        candidates = rec_targets.get(rec_id, [])
        matches = [(s, o) for (s, o) in candidates if o == orig_off]

        if len(matches) == 1:
            json_seg, target_off = matches[0]
            ida_seg = json_seg + JSON_SEG_TO_IDA_SEG_DELTA
            matched += 1
            if idx < 20 or not DRY_RUN:
                log(
                    f"  Thunk #{idx:03d} @ 0x{entry_ea:X} (rec {rec_id:02d}): "
                    f"orig={orig_seg:04X}:{orig_off:04X} -> "
                    f"JSON={json_seg:04X}:{target_off:04X} -> "
                    f"IDA={ida_seg:04X}:{target_off:04X}"
                )
            if not DRY_RUN:
                ida_bytes.patch_word(entry_ea + 4, target_off)
                ida_bytes.patch_word(entry_ea + 6, ida_seg)
                ida_bytes.patch_byte(entry_ea + 0, 0x90)
                ida_bytes.patch_byte(entry_ea + 1, 0x90)
                ida_bytes.patch_byte(entry_ea + 2, 0x90)
                ida_bytes.del_items(entry_ea, ida_bytes.DELIT_SIMPLE, THUNK_LEN)
                ida_ua.create_insn(entry_ea)
                ida_ua.create_insn(entry_ea + 3)
                patched += 1
        else:
            unmatched += 1
            log(
                f"  [!] Thunk #{idx:03d} @ 0x{entry_ea:X} (rec {rec_id:02d}): "
                f"orig={orig_seg:04X}:{orig_off:04X} had {len(matches)} "
                f"offset matches in {len(candidates)} candidates"
            )

    if not DRY_RUN:
        ida_auto.plan_and_wait(base_ea, base_ea + THUNK_COUNT * THUNK_LEN)
        log(f"\nSaved. {patched} thunks patched.")

    log(f"\nSummary (DRY_RUN={DRY_RUN}): "
        f"{matched}/{THUNK_COUNT} matched, {unmatched} unmatched/ambiguous.")


if __name__ == "__main__":
    try:
        main()
        # EXPLICIT save: headless idat only persists a dirty DB via its
        # implicit exit-save, which is unreliable and silently caused the
        # finding-39 regression. Never rely on it (finding 40 audit).
        import ida_loader
        ida_loader.save_database(
            r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64",
            0)
        log("saved")
    except Exception as e:
        log(f"[ERROR] {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        _log.close()
