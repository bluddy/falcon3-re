import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

# Rename function
addr = 0x32D22
old_name = idc.get_func_name(addr)
new_name = "mission_state_initializer"

if idc.set_name(addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed {hex(addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(addr)}")

# Add inline comments
comments = {
    0x32D22: "MISSION STATE INITIALIZER - 31 self-calls (state machine)",
    0x32D23: "Zero state byte at 22246h",
    0x32D28: "Reset key input state",
    0x32D2C: "Dispatch entity build - returns AL with status",
    0x32D31: "Check if AL == 1",
    0x32D35: "Check if AL == 3",
    0x32D39: "Set byte at DS:45Eh to 1",
    0x32D41: "Test farptr field 2F with OR",
    0x32D4C: "Set state byte at BX+2F to 0",
    0x32D53: "Set state byte at 1084Ch to 1",
    0x32D58: "Kick terrain VM sweep (1st)",
    0x32D5D: "Refresh EMS operation stream table",
    0x32D62: "Kick terrain VM sweep (2nd)",
    0x32D67: "Clear CS buffer at 5762h",
    0x32D6E: "Set state byte at 1084Ch to 0",
    0x32D7C: "Set state byte at 22246h to FFh",
    0x32D81: "Load ISLDAT state (island data)",
    0x32D8B: "Branch: entity build returned != 1 && != 3",
}

for ea, comment in comments.items():
    idc.set_cmt(ea, comment, 0)
    print(f"  Comment at {hex(ea)}")

print(f"\n✓ Added {len(comments)} inline comments")
print("Function renamed to mission_state_initializer")
print("Note: Handles entity building, terrain VM, EMS, ISLDAT loading")

idc.qexit(0)
