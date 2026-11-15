import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

# Rename main function
addr = 0x108BAC
old_name = idc.get_func_name(addr)
new_name = "r15_frame_processor"
if idc.set_name(addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed {hex(addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(addr)}")

# Add inline comments documenting the structure
comments = {
    0x108BAC: "Check initialization flag - two nearly identical code paths",
    0x108BB7: "flag_clear + initialization sequence",
    0x108BCA: "Store return values from fn_table_dispatch",
    0x108BE4: "Copy 9 words (18 bytes) from offset 0x2E to 0x40",
    0x108BEC: "Update entity position with wrapping",
    0x108BF7: "Clamp position to 40-unit boundary",
    0x108C0F: "Load entity state from offset 0x22 into buffer at 0x3A",
    0x108C1A: "Update terrain frame (altitude/collision)",
    0x108C22: "Project viewport objects with flags",
    0x108C2C: "Scan far objects with timer check",
    0x108C31: "Scan far objects with gate check",
    0x108C3B: "Unknown subsystem call",
    0x108C46: "Project 3 viewport object tables (32, 64, 72 entries)",
    0x108C56: "Process AI context batch",
    0x108C5B: "Entity movement and projection step",
    0x108C65: "Sort and step far objects",
    0x108C78: "Dispatch HUD rendering phases",
    0x108C7D: "Process entity table with gate",
    0x108C84: "Call sub_108991",
    0x108C8F: "Read word_10788C for loop count",
    0x108C94: "Execute callback 3 (far_cb_3) with range 0-0x13F",
    0x108CA6: "Execute callback 7 (far_cb_7) with count from word_10788C",
    0x108CAB: "Compute tick rate",
    0x108CB0: "Store tick rate in word_107759",
    0x108CB4: "EMS dual operation (page swap?)",
    0x108CBE: "Check byte_10788B flag",
    0x108CCC: "Run pending tasks",
    0x108CD1: "Call undoc_108E79",
    0x108CD9: "Apply pending atomic clip operations",
    0x108CDE: "Return from frame processor",
    0x108CDF: "Alternate entry: flag_clear + same sequence",
}

for addr, comment in comments.items():
    idc.set_cmt(addr, comment, 0)
    print(f"  Comment at {hex(addr)}")

print(f"\n✓ Added {len(comments)} inline comments")
print("Function renamed and documented")

idc.qexit(0)
