import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
log = []
# resolve the dword far-call dispatch pointers at 220xx -> where do they jump?
targets = {
    0x220A4: "sub_256B2 target", 0x220A8: "sub_24D46 target",
    0x220D4: "sub_263F0 target", 0x220D8: "sub_24DDC target",
    0x220DC: "sub_24DE6 target", 0x220EC: "sub_25EF4/25F0D target",
    0x22100: "sub_25DEB target", 0x22120: "sub_25EEE target",
}
for ea, label in targets.items():
    raw = idc.get_bytes(ea, 4)
    if raw and len(raw) == 4:
        off = int.from_bytes(raw[:2], "little")
        segw = int.from_bytes(raw[2:], "little")
        # linear = segw*16 + off  (but real mode); try to resolve to IDA ea
        # the dword is seg:off -- far pointer.  off is offset within seg.
        log.append("%s @0x%X = %04X:%04X (seg=0x%X off=0x%X) raw=%s" % (
            label, ea, segw, off, segw, off, raw.hex()))
        # try: if segw looks like a CS, linear = segw<<4 + off
        lin = (segw << 4) + off
        f = ida_funcs.get_func(lin)
        if f:
            log.append("    -> linear 0x%X in fn %s (0x%X..0x%X)" % (
                lin, idc.get_func_name(f.start_ea), f.start_ea, f.end_ea))
        else:
            log.append("    -> linear 0x%X NOT a fn start (name=%s)" % (
                lin, idc.get_name(lin)))
    else:
        log.append("%s @0x%X: no bytes" % (label, ea))
# also the state vars the setters/getters use
log.append("")
log.append("=== state vars ===")
for ea, label in [(0x2223E, "sub_22841 writes"), (0x22220, "sub_22AFF/22964"),
                  (0x22222, "sub_22AFF"), (0x2224B, "sub_22AFF cmps ==1"),
                  (0x2322A, "sub_2322B writes al"), (0x22D26, "sub_231D3 reads"),
                  (0x22E27, "sub_22DFA writes ax"), (0x24BBA, "sub_24DDC reads al"),
                  (0x11CC8, "sub_16579 reads"), (0x10000, "sub_100AF reads"),
                  (0x2222C, "sub_222AA writes"), (0x2222E, "sub_222AA"), (0x22230, "sub_222AA")]:
    b = idc.get_bytes(ea, 2) or idc.get_bytes(ea, 1)
    log.append("  0x%X (%s): %s name=%s" % (ea, label, b.hex() if b else "?", idc.get_name(ea)))
with open(os.path.join(ROOT, "analysis/ida_falconcd/diag_dispatch.log"), "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)