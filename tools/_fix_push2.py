import ida_name, ida_loader, idaapi, idc
IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
log = []
tests = [(0x112F6, "segment_change_debounce_cx"),
         (0x14152, "segment_bitfield_decode")]
ok_all = True
for ea, nm in tests:
    ok = ida_name.set_name(ea, nm, 0)
    now = ida_name.get_ea_name(ea)
    stuck = now == nm
    ok_all = ok_all and stuck
    log.append("0x%X %-30s -> %-5s now=%r %s" % (ea, nm, ok, now,
               "STUCK" if stuck else "REVERTED"))
if ok_all:
    log.append("BOTH STUCK -- will persist via naming.py push-ida after ledger update")
open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fix_push2.log", "w").write("\n".join(log))
idaapi.qexit(0)   # probe only, no save (ledger not yet updated)