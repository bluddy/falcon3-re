import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

addr = 0x112451
old_name = idc.get_func_name(addr)
new_name = "file_processor_large_buffer"

if idc.set_name(addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed {hex(addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(addr)}")

# Add key comments
comments = {
    0x112451: "FILE PROCESSOR - 58 self-calls, HUGE stack frame (0x632 = 1586 bytes!)",
    0x112457: "Get state word from 2222Ah",
    0x112464: "Push args from BP (arg_2, arg_0)",
    0x112470: "op_dispatch_far_entry with operation 6 (FILE OPEN)",
    0x11247E: "Call loc_27667 with file handle",
    0x112490: "op_dispatch_far_entry with operation 0xA (FILE READ) - 2 bytes to [BP+var_10]",
    0x1124A4: "op_dispatch_far_entry with operation 0xA (FILE READ) - 2 bytes to [BP+var_12]",
}

for ea, comment in comments.items():
    idc.set_cmt(ea, comment, 0)

print(f"✓ Added {len(comments)} comments")
print("Note: Large stack buffer suggests complex file parsing/processing")

idc.qexit(0)
