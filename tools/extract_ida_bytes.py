#!/usr/bin/env python3
"""
Extract function bytes from IDA database (with fixups applied).
Enumerates ALL live functions (resident + rebuilt overlays), not the stale survey.
Run via: idat.exe -A -S"extract_ida_bytes.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json
import idautils
import ida_funcs
import ida_bytes
import ida_name
import idaapi


def main():
    # Stable keys + preserved renames: previous extract's keys/name-fields win over
    # current IDB display names (push-ida / GUI renames change display names).
    ea_to_ida = {}
    prev_names = {}
    try:
        fb_prev = json.load(open('analysis/ida_falconcd/function_bytes.json'))
        for k, v in fb_prev.items():
            ea_to_ida.setdefault(v.get('ea'), k)
            prev_names[k] = v.get('name')
    except Exception:
        pass

    func_bytes = {}
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        size = f.end_ea - f.start_ea
        name = ida_name.get_ea_name(ea) or ("sub_%X" % ea)
        # stable key: previous key for this ea, else current display name
        key = ea_to_ida.get(ea) or name
        # dedupe names (IDA name should be unique, but be safe)
        k2 = key
        n = 1
        while k2 in func_bytes:
            n += 1
            k2 = "%s_%d" % (key, n)
        try:
            data = ida_bytes.get_bytes(ea, size)
        except Exception:
            data = None
        func_bytes[k2] = {
            'ea': ea,
            'size': size,
            'bytes': data.hex() if data else None,
            'is_far': bool(f.flags & ida_funcs.FUNC_FAR),
            'overlay': ea >= 0x2CF60,
            'name': prev_names.get(k2),
        }

    with open('analysis/ida_falconcd/function_bytes.json', 'w') as fh:
        json.dump(func_bytes, fh, indent=2)

    nov = sum(1 for v in func_bytes.values() if v['overlay'])
    print("Extracted bytes for %d functions (%d overlay)" % (len(func_bytes), nov))
    idaapi.qexit(0)


if __name__ == '__main__':
    main()
