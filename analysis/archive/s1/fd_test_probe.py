import os; os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idc, idautils, idaapi, hashlib

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fd_test.txt"
out = open(OUT, "w")

h, t, fn_ea = 0x3592B, 0x3592C, 0x356A7

# Before fix
out.write("=== BEFORE ===\n")
out.write("item_size(h): %d\n" % ida_bytes.get_item_size(h))
out.write("is_code(h): %s\n" % ida_bytes.is_code(ida_bytes.get_flags(h)))
out.write("is_code(t): %s\n" % ida_bytes.is_code(ida_bytes.get_flags(t)))
out.write("item_head(t): 0x%X\n" % ida_bytes.get_item_head(t))
fn = ida_funcs.get_func(fn_ea)
out.write("fn: 0x%X..0x%X\n" % (fn.start_ea, fn.end_ea))
out.write("disasm at h: %s\n" % idc.generate_disasm_line(h, 0))
out.write("byte at h: %02X\n" % (ida_bytes.get_byte(h) & 0xFF))
out.write("byte at t: %02X\n" % (ida_bytes.get_byte(t) & 0xFF))

insn_size = ida_bytes.get_item_size(h)
clear_len = max(insn_size, 1) + 7
out.write("insn_size: %d, clear_len: %d\n" % (insn_size, clear_len))

# Apply fix
ida_bytes.del_items(h, ida_bytes.DELIT_SIMPLE, clear_len)
out.write("\n=== AFTER del_items ===\n")
out.write("item_size(h): %d is_code(h): %s\n" % (ida_bytes.get_item_size(h), ida_bytes.is_code(ida_bytes.get_flags(h))))
out.write("item_size(t): %d is_code(t): %s item_head(t): 0x%X\n" % (
    ida_bytes.get_item_size(t), ida_bytes.is_code(ida_bytes.get_flags(t)), ida_bytes.get_item_head(t)))

# Try create_insn on t
ida_bytes.del_items(t, ida_bytes.DELIT_SIMPLE, 1)
n = ida_ua.create_insn(t)
out.write("create_insn(t): n=%d\n" % n)
if n > 0:
    out.write("disasm_t: %s\n" % idc.generate_disasm_line(t, 0))
    out.write("item_head(t): 0x%X, is_code(t): %s\n" % (
        ida_bytes.get_item_head(t), ida_bytes.is_code(ida_bytes.get_flags(t))))
out.close()
idc.qexit(0)
