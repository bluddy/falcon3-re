import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_handlers_seg.txt"
with open(out_path, "w") as f:
    seg = idaapi.getseg(0x264ff)
    f.write(f"Segment of 0x264ff: start=0x{seg.start_ea:x}, end=0x{seg.end_ea:x}\n")
    # In instruction: cs:farobj_entity_type_handlers[bx]
    # In 16-bit x86, the displacement is relative to CS segment base!
    # Let's find the operand value
    insn = idaapi.insn_t()
    idaapi.decode_insn(insn, 0x264ff)
    disp = insn.Op1.addr
    f.write(f"Operand disp: 0x{disp:x}\n")
    # Base of segment
    cs_base = seg.start_ea
    target_ea = cs_base + disp
    f.write(f"Target EA: 0x{target_ea:x}\n")
    for i in range(16):
        ptr = idc.get_wide_word(target_ea + i * 2)
        target_func = cs_base + ptr
        name = idaapi.get_func_name(target_func)
        f.write(f"  Handler {i} (0x{i*2:02x}): disp=0x{ptr:04x} -> EA=0x{target_func:x} ({name})\n")

idc.qexit(0)
