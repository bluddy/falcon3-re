"""Experiment (copy only): does an SR_user DS range survive re-decode / reanalysis
of the instruction that opened an auto range there?  Does it produce drefs?"""
import idaapi, ida_segregs, ida_ua, ida_auto, ida_segment, idautils, idc, ida_loader
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\exp_user.txt"
DS = idaapi.str2reg("ds")
out = []
rr = ida_segregs.sreg_range_t()


def rng(ea):
    ida_segregs.get_sreg_range(rr, ea, DS)
    return "%X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val, rr.tag)


POP = 0x43EFC         # pop ds (unmatched) in sub_43EE3
FS = 0x43EFF          # sub_43EFF: mov [si+0Ah],ax etc.
out.append("before pop+1 %s | fs %s" % (rng(POP + 1), rng(FS)))
sel = ida_segment.setup_selector(0x7A32)
out.append("sel %X" % sel)
out.append("split user @FS -> %s %s" % (ida_segregs.split_sreg_range(FS, DS, sel, ida_segregs.SR_user), rng(FS)))
ida_auto.auto_wait()
out.append("after auto_wait %s" % rng(FS))
# re-create the insn that precedes and the ones in the function
for h in idautils.FuncItems(FS):
    ida_ua.create_insn(h)
ida_auto.auto_wait()
out.append("after recreate %s" % rng(FS))
# auto split over user
out.append("auto split BAD over user -> %s %s" % (
    ida_segregs.split_sreg_range(FS, DS, idaapi.BADSEL, ida_segregs.SR_auto), rng(FS)))
ida_segregs.split_sreg_range(FS, DS, sel, ida_segregs.SR_user)
out.append("reset user %s" % rng(FS))
# reanalyze whole function
ida_auto.plan_range(FS, idc.get_func_attr(FS, idc.FUNCATTR_END))
ida_auto.auto_wait()
out.append("after plan_range %s" % rng(FS))
# drefs from a mem operand under DS=7A32: find first o_mem insn in a 7A32 known area
n = 0
for h in idautils.FuncItems(0x2E100):
    pass
# check a dref example: mov word_..., in sub_43EFF none; use set on a function with o_mem
tgt = None
for fs in idautils.Functions(0x10000, 0x2CF60):
    for h in idautils.FuncItems(fs):
        insn = ida_ua.insn_t()
        ida_ua.decode_insn(insn, h)
        if insn.ops[0].type == ida_ua.o_mem and "cs:" not in idc.print_operand(h, 0) and "es:" not in idc.print_operand(h, 0) \
                and ida_segregs.get_sreg(h, DS) in (idaapi.BADSEL, 0xFFFF):
            tgt = (fs, h)
            break
    if tgt:
        break
fs, h = tgt
out.append("dref test fn %X insn %X '%s' xrefs %s" % (fs, h, idc.generate_disasm_line(h, 0),
                                                    [hex(x.to) for x in idautils.XrefsFrom(h, 0) if not x.iscode]))
ida_segregs.split_sreg_range(fs, DS, sel, ida_segregs.SR_user)
ida_auto.auto_wait()
out.append(" after split+auto_wait: ds %s '%s' xrefs %s" % (rng(h), idc.generate_disasm_line(h, 0),
                                                         [hex(x.to) for x in idautils.XrefsFrom(h, 0) if not x.iscode]))
ida_ua.create_insn(h)
out.append(" after create_insn: '%s' xrefs %s" % (idc.generate_disasm_line(h, 0),
                                                 [hex(x.to) for x in idautils.XrefsFrom(h, 0) if not x.iscode]))
open(OUT, "w").write("\n".join(out))
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
