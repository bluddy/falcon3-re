"""Fix functions whose bodies autoanalysis shrank after registration (finding 37).

Run 1 of add_trace_functions.py registered 18 fns with explicit ranges, but
idaapi.auto_wait() re-decided bodies and shrank most to 1-5B (and grew
0x22AFF past its iret). This script:
  1. disables autoanalysis (so IDA stops second-guessing),
  2. del_func + del_items over the known-good range,
  3. force-decodes every instruction (DELIT_SIMPLE + create_insn loop),
  4. add_func with the explicit range and set_func_end,
  5. saves WITHOUT auto_wait().

Ranges come from the terminator-disassembly pass in add_trace_functions.py.

Usage: cmd /c "tools\\run_idat.bat tools\\fix_trace_functions.py"
"""
import json
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fixfunc.log"

# (ea, end_ea) known-good ranges from terminator disassembly (finding 37)
FUNCS = [
    (0x22AFF, 0x22B27),   # 40B  iret  174,766 calls
    (0x1656F, 0x16579),   # 10B  retf    4,902 calls
    (0x260F4, 0x26250),   # 348B retf    2,587 calls
    (0x24DCA, 0x24DDC),   # 18B  retf    1,105 calls
    (0x25602, 0x25608),   # 6B   retf      498 calls
    (0x208E7, 0x20A7A),   # 403B retf      498 calls
    (0x142CC, 0x142DA),   # 14B  retf      498 calls
    (0x202DB, 0x202F8),   # 29B  retf      449 calls
    (0x25A56, 0x25A70),   # 26B  retf      307 calls
    (0x2E20A, 0x2E227),   # 29B  retf       58 calls
    (0x2100F, 0x21127),   # 280B retf       18 calls
    (0x18062, 0x1806A),   # 8B   retf        7 calls
    (0x24F80, 0x24F9D),   # 29B  retf        6 calls
    (0x25522, 0x25540),   # 30B  retf        3 calls
    (0x13E83, 0x13E93),   # 16B  retf        2 calls
    (0x6E558, 0x6E581),   # 41B  retf        1 call (autoanalysis grew to 132B)
]

log = []
try:
    # stop IDA re-deciding bodies under us
    ida_auto.enable_auto(False)
    log.append("autoanalysis disabled")

    for ea, end in FUNCS:
        # wipe whatever is there
        prev = ida_funcs.get_func(ea)
        if prev and prev.start_ea == ea:
            ida_funcs.del_func(ea)
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, end - ea)

        # force-decode the whole range instruction by instruction
        pos = ea
        decoded = 0
        bad = None
        while pos < end:
            if not ida_ua.create_insn(pos):
                bad = pos
                break
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                bad = pos
                break
            pos += sz
            decoded += 1

        if bad is not None or pos != end:
            log.append("0x%X..0x%X DECODE MISMATCH bad=%s pos=0x%X -> abort fn"
                       % (ea, end, hex(bad) if bad else None, pos))
            continue

        ok = ida_funcs.add_func(ea, end)
        ida_name.set_name(ea, "sub_%X" % ea, ida_name.SN_CHECK)
        # force the end explicitly
        if ok:
            ida_funcs.set_func_end(ea, end)
        f = ida_funcs.get_func(ea)
        got = ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"
        log.append("0x%X..0x%X %dB insns=%d add_func=%s -> %s"
                   % (ea, end, end - ea, decoded, ok, got))

    # save WITHOUT auto_wait to avoid re-analysis
    ida_loader.save_database(IDB, 0)
    log.append("saved (no auto_wait); total fns=%d" % ida_funcs.get_func_qty())
    ida_auto.enable_auto(True)
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
