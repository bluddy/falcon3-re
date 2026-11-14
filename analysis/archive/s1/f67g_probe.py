import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67g_probe.txt", "w")
out.write("del_func: %s\n" % ida_funcs.del_func(0x67F59))
ida_bytes.del_items(0x67F59, ida_bytes.DELIT_SIMPLE, 4)
out.write("set_name: %s\n" % ida_name.set_name(0x67F59, "", ida_name.SN_NOWARN))
out.write("create_insn 67F58: %s\n" % ida_ua.create_insn(0x67F58))
out.write("%s\n" % idc.generate_disasm_line(0x67F58, 0))
out.write("flags 67F58 %X 67F59 %X\n" % (ida_bytes.get_flags(0x67F58), ida_bytes.get_flags(0x67F59)))
out.close()
idc.qexit(0)
