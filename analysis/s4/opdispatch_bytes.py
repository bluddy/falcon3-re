"""opdispatch_bytes.py — read raw bytes at op_dispatch targets and try to decode."""
import idc, ida_bytes, ida_ua, idaapi
import traceback
from pathlib import Path

LOG = Path("analysis/s4/opdispatch_bytes.log")

OP_TARGETS = [0x2F34, 0x2F66, 0x2FD9, 0x2FF6, 0x301F, 0x3028,
              0x3052, 0x307C, 0x30A0, 0x30D7, 0x30F4, 0x30FF,
              0x3108, 0x3158, 0x3113, 0x312C]

log = []

RETS = {0xC3, 0xCA, 0xCB, 0xC2, 0xCF}  # retn, retn imm, retf, retn, iret

try:
    for i, start_ea in enumerate(OP_TARGETS):
        # Find the end: scan for a RETN/RETF byte
        end_ea = start_ea
        for _ in range(200):
            b = ida_bytes.get_byte(end_ea)
            end_ea += 1
            if b in RETS:
                # For retf with imm (0xCA), skip the imm16 too
                if b in (0xC2, 0xCA):
                    end_ea += 2
                break
        
        raw = ["%02X" % ida_bytes.get_byte(start_ea+j) for j in range(end_ea-start_ea)]
        log.append("\n=== BX=%d  op 0x%X..0x%X  (%dB) ===" % (i, start_ea, end_ea-1, end_ea-start_ea))
        log.append("  bytes: %s" % " ".join(raw))
        
        # Force-decode the instructions
        lines = []
        a = start_ea
        while a < end_ea:
            # Force-clear and decode
            ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, 1)
            n = ida_ua.create_insn(a)
            if n <= 0: n = 1
            d = idc.generate_disasm_line(a, 0)
            lines.append("  %05X  %s" % (a, d))
            a += n
        log.extend(lines)
        
        # Put bytes back as undefined (we don't want to persist)
        # Just leave them decoded for now (this is a probe, DBFL_KILL will undo)

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
