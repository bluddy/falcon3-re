"""check_si_bytes.py — manually check bytes at known [si+NN] accesses."""
import idc, ida_bytes, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "check_si_bytes.log"

log = []

try:
    # From entity_attr_dump.log, we know these access [si+NN]:
    # 0x443C7: mov [si+14h], bx
    # 0x443CC: mov [si+1Eh], ax
    # 0x443CF: mov [si+20h], ax
    
    test_eas = [
        (0x443C7, "[si+14h]"),
        (0x443CC, "[si+1Eh]"),
        (0x443CF, "[si+20h]"),
        (0x4435C, "[si+13h]"),
    ]
    
    for ea, desc in test_eas:
        log.append("=== 0x%X: %s ===" % (ea, desc))
        log.append("Disasm: %s" % idc.generate_disasm_line(ea, 0))
        
        # Read 6 bytes
        bytes_str = " ".join("%02X" % ida_bytes.get_byte(ea + i) for i in range(6))
        log.append("Bytes:  %s" % bytes_str)
        
        # Decode
        b0 = ida_bytes.get_byte(ea)
        b1 = ida_bytes.get_byte(ea + 1)
        b2 = ida_bytes.get_byte(ea + 2)
        
        log.append("  b0=0x%02X, b1=0x%02X (ModRM=0x%02X, masked=0x%02X), b2=0x%02X (disp)" % (
            b0, b1, b1, b1 & 0xC7, b2
        ))
        log.append("  ModRM: mod=%d, reg=%d, rm=%d" % (
            (b1 >> 6) & 0x3, (b1 >> 3) & 0x7, b1 & 0x7
        ))
        log.append("")
    
    LOG.write_text("\n".join(log), encoding='utf-8')

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
