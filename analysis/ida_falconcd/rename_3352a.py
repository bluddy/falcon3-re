import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

# Rename function
addr = 0x3352A
old_name = idc.get_func_name(addr)
new_name = "aircraft_state_dispatcher"

if idc.set_name(addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed {hex(addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(addr)}")

# Add inline comments
comments = {
    0x3352A: "AIRCRAFT STATE DISPATCHER - 49 self-calls (state machine)",
    0x3352F: "Load word from CS table offset +0xC, +0xE",
    0x33541: 'Set string pointer to "EJECT" for display',
    0x3354B: "Recompute mode extents",
    0x3355D: "HUD track strip pipeline",
    0x33562: "Return point 1",
    0x33563: "Check matrix constants copy gate",
    0x3356A: "Check byte_54F6D state flags",
    0x3356D: "Test bit 2 (mask 0x04)",
    0x33571: "Test bits 0-1 (mask 0x03)",
    0x33575: "Test bit 3 (mask 0x08)",
    0x335D6: "Get AI far pointer table",
    0x335E6: "Return point 2",
    0x335E7: "State machine: check byte_54F6D bits 0-1",
    0x335EE: "Load and increment word_54D3D counter",
    0x335F2: "Mask to 0-3 range",
    0x335F5: "Check if counter == 3",
    0x33605: "Set state byte at 1F733h",
    0x3362F: "Apply state table 71C1",
    0x33635: "View block 4287 angles update",
    0x33639: "Hardware config scan",
    0x33641: "Store to R37 farptr with gate",
    0x33646: "Terrain VM buffer decay",
    0x3364B: "Copy hardware config",
    0x33650: "Return point 3",
    0x33651: "Check word_54D2B against 0xE",
    0x33658: "Zero DGROUP state 5",
}

for ea, comment in comments.items():
    idc.set_cmt(ea, comment, 0)
    print(f"  Comment at {hex(ea)}")

print(f"\n✓ Added {len(comments)} inline comments")
print("Function renamed to aircraft_state_dispatcher")
print("Note: Has EJECT string reference - likely handles ejection sequence")

idc.qexit(0)
