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
    func_bytes = {}
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        size = f.end_ea - f.start_ea
        name = ida_name.get_ea_name(ea) or ("sub_%X" % ea)
        # dedupe names (IDA name should be unique, but be safe)
        key = name
        n = 1
        while key in func_bytes:
            n += 1
            key = "%s_%d" % (name, n)
        try:
            data = ida_bytes.get_bytes(ea, size)
        except Exception:
            data = None
        func_bytes[key] = {
            'ea': ea,
            'size': size,
            'bytes': data.hex() if data else None,
            'is_far': bool(f.flags & ida_funcs.FUNC_FAR),
            'overlay': ea >= 0x2CF60,
        }

    with open('analysis/ida_falconcd/function_bytes.json', 'w') as fh:
        json.dump(func_bytes, fh, indent=2)

    nov = sum(1 for v in func_bytes.values() if v['overlay'])
    print("Extracted bytes for %d functions (%d overlay)" % (len(func_bytes), nov))
    idaapi.qexit(0)


if __name__ == '__main__':
    main()
