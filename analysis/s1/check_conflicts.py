"""Check which auto-queue entries conflict with existing functions."""
import ida_funcs, idc
from pathlib import Path

AUTOQ = [
    (0x3FB20, 0x3FB22), (0x434B2, 0x434BB), (0x43BAC, 0x43BCA), (0x4DA3D, 0x4DA46),
    (0x4E5B4, 0x4E5C5), (0x4E5C5, 0x4E5CC), (0x4E5CC, 0x4E601), (0x4E601, 0x4E602),
    (0x4E602, 0x4E645), (0x4E645, 0x4E64C), (0x4E64C, 0x4E653), (0x4E653, 0x4E6E7),
    (0x4E6E7, 0x4E6F4), (0x4E6F4, 0x4E705), (0x4E705, 0x4E793), (0x4E793, 0x4E803),
    (0x6E31D, 0x6E321), (0x107410, 0x1074E2), (0x1074E2, 0x1074EE), (0x1074EE, 0x1074FA),
    (0x10A68D, 0x10A814), (0x10A814, 0x10B355), (0x112451, 0x112BE8),
    (0x131D5F, 0x132012), (0x1326CF, 0x13276D), (0x13276D, 0x13280B),
    (0x1390C1, 0x139169), (0x139559, 0x1395FE), (0x13AB16, 0x13AB62),
    (0x13DBD8, 0x13DC09), (0x15DB74, 0x15DB7F), (0x15DCA3, 0x15DCA8), (0x17C610, 0x17C640),
]

LOG = Path("analysis/s1/check_conflicts.log")
log = []
conflicts = []
ok = []

for ea, end in AUTOQ:
    # Check if ea is already a function head
    f = ida_funcs.get_func(ea)
    if f and f.start_ea == ea:
        log.append("ALREADY_FN: 0x%X..0x%X (fn 0x%X..0x%X)" % (ea, end, f.start_ea, f.end_ea))
        conflicts.append((ea, end))
    elif any(ida_funcs.get_func(a) for a in range(ea, end)):
        # Owned by some other function
        owner = ida_funcs.get_func(ea)
        log.append("OWNED: 0x%X..0x%X (owner 0x%X)" % (ea, end, owner.start_ea if owner else -1))
        conflicts.append((ea, end))
    else:
        ok.append((ea, end))
        log.append("OK: 0x%X..0x%X" % (ea, end))

log.append("")
log.append("conflicts: %d, ok: %d" % (len(conflicts), len(ok)))
LOG.write_text("\n".join(log))
import idaapi; idaapi.qexit(0)
