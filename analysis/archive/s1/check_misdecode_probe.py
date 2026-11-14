import os; os.environ["DBFL_KILL"]="1"
import ida_bytes, ida_funcs, idc, idautils, idaapi
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\check_misdecode.txt", "w")
# Check a few of the misdecode heads
cases = [0x2E91F, 0x2F05E, 0x2F293, 0x348ED, 0x3592B, 0x377F3]
for head in cases:
    insn_size = ida_bytes.get_item_size(head)
    is_code = ida_bytes.is_code(ida_bytes.get_flags(head))
    item_head = ida_bytes.get_item_head(head)
    out.write("head=0x%X: item_size=%d is_code=%s item_head=0x%X disasm='%s'\n" % (
        head, insn_size, is_code, item_head, idc.generate_disasm_line(item_head, 0)))
# Also check fn containing each
for head in cases:
    f = ida_funcs.get_func(head)
    if f:
        out.write("  fn=0x%X..0x%X (%s)\n" % (f.start_ea, f.end_ea, idc.get_func_name(f.start_ea)))
out.close()
idc.qexit(0)
