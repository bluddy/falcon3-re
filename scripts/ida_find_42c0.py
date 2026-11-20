import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_42c0_refs.txt"
with open(out_path, "w") as f:
    f.write("=== Refs to 0x42C0 ===\n")
    # Search for immediate value 0x42C0 in instructions
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        ea = seg.start_ea
        while ea < seg.end_ea:
            insn = idaapi.insn_t()
            if idaapi.decode_insn(insn, ea):
                for op in insn.ops:
                    if op.type == idaapi.o_imm and op.value == 0x42c0:
                        f.write(f"  0x{ea:x} in {idaapi.get_func_name(ea)}: {idc.generate_disasm_line(ea, 0)}\n")
            ea = idc.next_head(ea, seg.end_ea)

idc.qexit(0)
