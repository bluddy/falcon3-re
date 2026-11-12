"""seg_base_probe.py — find seg020 base and compute op_dispatch linear targets."""
import idc, ida_funcs, ida_bytes, ida_segment, ida_ua, idaapi
import traceback
from pathlib import Path

LOG = Path("analysis/s4/seg_base.log")
log = []

try:
    # Find the segment that contains op_dispatch (0x2257B)
    OP_DISPATCH = 0x2257B
    s = ida_segment.getseg(OP_DISPATCH)
    if s:
        base = s.start_ea
        log.append("seg020 starts at: 0x%X" % base)
        log.append("seg020 ends at:   0x%X" % s.end_ea)
        log.append("seg020 size:      0x%X (%d)" % (s.end_ea - s.start_ea, s.end_ea - s.start_ea))
        log.append("")
        
        # Read the op_dispatch table (near offsets relative to this segment base)
        TABLE_EA = 0x22060
        TABLE_ENTRIES = 16
        log.append("op_dispatch table at 0x%X (CS base = 0x%X):" % (TABLE_EA, base))
        for i in range(TABLE_ENTRIES):
            near_off = ida_bytes.get_word(TABLE_EA + i*2)
            linear   = base + near_off
            # Check if there's a function here
            fn = ida_funcs.get_func(linear)
            fn_info = ""
            if fn:
                fn_info = "%s" % idc.get_func_name(fn.start_ea)
                if fn.start_ea == linear:
                    fn_info = "[FN_START] " + fn_info
                else:
                    fn_info = "[inside %s+0x%X]" % (fn_info, linear - fn.start_ea)
            log.append("  [%2d] near=0x%04X  linear=0x%X  %s" % (i, near_off, linear, fn_info))
            
            # Decode first 5 instructions at linear
            a = linear
            for _ in range(8):
                if a >= linear + 60: break
                n = ida_ua.create_insn(a)
                if n <= 0: n = 1
                d = idc.generate_disasm_line(a, 0)
                log.append("    %05X  %s" % (a, d))
                m = idc.print_insn_mnem(a)
                a += n
                if m in ('retf', 'retn', 'ret', 'iret', 'jmp', 'jmpf'):
                    break
        
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
