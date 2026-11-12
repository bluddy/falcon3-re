"""opdispatch_probe.py — raw disassembly of op_dispatch table targets."""
import idc, ida_funcs, ida_bytes, idautils, idaapi
import traceback
from pathlib import Path

LOG = Path("analysis/s4/opdispatch.log")

OP_TARGETS = [0x2F34, 0x2F66, 0x2FD9, 0x2FF6, 0x301F, 0x3028,
              0x3052, 0x307C, 0x30A0, 0x30D7, 0x30F4, 0x30FF,
              0x3108, 0x3158, 0x3113, 0x312C]

log = []

try:
    for i, ea in enumerate(OP_TARGETS):
        fn = ida_funcs.get_func(ea)
        fn_info = "fn_start=0x%X (%s)" % (fn.start_ea, idc.get_func_name(fn.start_ea)) if fn else "no_fn"
        head = ida_bytes.get_item_head(ea)
        log.append("\n=== BX=%d  op 0x%X  [%s]  head=0x%X ===" % (i, ea, fn_info, head))
        # Dump 25 instructions from ea
        a = ea
        for _ in range(25):
            if a > ea + 200: break
            isz = ida_bytes.get_item_size(a)
            d = idc.generate_disasm_line(a, 0)
            m = idc.print_insn_mnem(a)
            log.append("  %05X  %s" % (a, d))
            if m in ('retf', 'retn', 'ret', 'iret', 'jmp', 'jmpf'):
                break
            a += max(isz, 1)

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
