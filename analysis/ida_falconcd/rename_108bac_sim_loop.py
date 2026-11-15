import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

# Rename main function to reflect it's the simulation loop
addr = 0x108BAC
old_name = idc.get_func_name(addr)
new_name = "r15_simulation_loop"
if idc.set_name(addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed {hex(addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(addr)}")

# Update comments to reflect simulation loop understanding
comments = {
    0x108BAC: "R15 SIMULATION LOOP - Main game physics/logic update. Flag cs:byte_107762 selects config mode",
    0x108BB2: "Branch: if flag==0 → Path A (37 calls), else → Path B (46 calls)",
    0x108BB4: "Jump to Path B at 0x108CDF",
    0x108BB7: "=== PATH A START: Standard simulation mode ===",
    0x108BCA: "Store fn_table_dispatch results: BX→0x3E, CX→0x3C, DX→0x3A",
    0x108BE4: "Copy 9 words (18 bytes) from DS:SI+0x2E to DS:DI+0x40",
    0x108BEC: "PHYSICS: Update entity position with world wrapping",
    0x108BF7: "PHYSICS: Clamp position to 40-unit boundary",
    0x108C0F: "ENTITY: Load state from offset 0x22 into buffer at 0x3A",
    0x108C1A: "TERRAIN: Update terrain frame (altitude, collision detection)",
    0x108C22: "VIEWPORT: Project viewport objects with visibility flags",
    0x108C2C: "FAR OBJECTS: Scan with timer check (LOD/culling)",
    0x108C31: "FAR OBJECTS: Scan with gate check (visibility)",
    0x108C36: "Initialize ES pointer slots",
    0x108C40: "Switch to segment 54AFh for viewport rendering",
    0x108C46: "VIEWPORT: Project table 32 with flags",
    0x108C4B: "VIEWPORT: Project table 64",
    0x108C50: "VIEWPORT: Project table 72 with flags",
    0x108C56: "AI: Process AI context batch (all entities)",
    0x108C5B: "ENTITY: Movement and projection step",
    0x108C60: "VIEWPORT: Scan viewobj_5982 table",
    0x108C65: "FAR OBJECTS: Sort by distance and step simulation",
    0x108C6F: "Switch DS and ES to segment 54AFh for HUD rendering",
    0x108C78: "HUD: Dispatch rendering phases (cockpit instruments)",
    0x108C7D: "ENTITY: Process table with gate 47a8d",
    0x108C84: "Call support function sub_108991",
    0x108C8F: "Read word_10788C (loop iteration count)",
    0x108C94: "Execute far callback 3: process 0x13F entities",
    0x108CA1: "Read word_10788C for callback 7 iteration count",
    0x108CA6: "Execute far callback 7: batch processing",
    0x108CAB: "TIMING: Compute frame tick rate (delta time)",
    0x108CB0: "Store tick rate → cs:word_107759 (frame delta)",
    0x108CB4: "MEMORY: EMS dual operation (page swap)",
    0x108CB9: "Call sub_2FBFD",
    0x108CBE: "Check cs:byte_10788B - early exit flag?",
    0x108CC6: "Early exit path: zero AX and return",
    0x108CCC: "TASKS: Run pending task queue",
    0x108CD1: "Call undoc_108E79 (cleanup?)",
    0x108CD4: "Zero AX before clip operation",
    0x108CD9: "CLIP: Apply pending atomic clip operations",
    0x108CDE: "Return from simulation loop",
    
    0x108CDF: "=== PATH B START: Alternate simulation mode (46 calls) ===",
    0x108CEA: "Path B uses fn_table_dispatch with same params",
    0x108D19: "Path B UNIQUE: Call 0xEFF (not in Path A)",
    0x108D26: "Path B UNIQUE: Call 0x111D (not in Path A)",
    0x108D31: "PHYSICS: Position wrapping (same as Path A)",
    0x108D3C: "PHYSICS: Position clamping (same as Path A)",
    0x108D54: "Path B UNIQUE: Call 0xD2D",
    0x108D59: "Path B UNIQUE: Call 0x2010",
    0x108D62: "Path B UNIQUE: Call 0xD70",
    0x108D67: "Path B UNIQUE: Call 0x7A8",
    0x108D71: "Path B UNIQUE: Call 0x2BC5",
    0x108D76: "FAR OBJECTS: Gate check (same as Path A)",
    0x108D7B: "FAR OBJECTS: Timer check (same as Path A)",
    0x108D85: "FAR OBJECTS: Clear (same as Path A)",
    0x108D90: "VIEWPORT: Project tables (same 3 calls as Path A)",
    0x108DA0: "AI: Context batch (same as Path A)",
    0x108DA5: "ENTITY: Movement step (same as Path A)",
    0x108DAA: "Path B UNIQUE: Call 0x2BCF",
    0x108DAF: "VIEWPORT: Scan viewobj (same as Path A)",
    0x108DB4: "Path B UNIQUE: Call 0x7AF",
    0x108DC2: "HUD: Rendering phases (same as Path A)",
    0x108DD6: "Path B UNIQUE: Call 0x211E",
    0x108DE1: "Path B UNIQUE: Call 0x1EFD",
    0x108DE4: "Path B UNIQUE: Call 0x2260",
    0x108DE7: "Path B UNIQUE: Call 0xF7E",
    0x108DEA: "Support function (same as Path A)",
    0x108DF8: "Far callback 3 (same as Path A)",
    0x108E0A: "Far callback 7 - iteration 1",
    0x108E1C: "Far callback 7 - iteration 2",
    0x108E2E: "Far callback 7 - iteration 3",
    0x108E40: "Far callback 3 again",
    0x108E45: "TIMING: Tick rate (same as Path A)",
    0x108E4E: "MEMORY: EMS operation (same as Path A)",
    0x108E60: "Check exit flag (same as Path A)",
    0x108E66: "TASKS: Pending tasks (same as Path A)",
    0x108E6B: "Cleanup call (same as Path A)",
    0x108E73: "CLIP: Apply operations (same as Path A)",
}

for addr, comment in comments.items():
    idc.set_cmt(addr, comment, 0)
    print(f"  Comment at {hex(addr)}")

print(f"\n✓ Added {len(comments)} inline comments")
print("Simulation loop renamed and fully documented")

# Rename the flag variable
flag_addr = 0x107762
if idc.set_name(flag_addr, "r15_sim_mode_flag", idaapi.SN_CHECK):
    print(f"✓ Renamed flag {hex(flag_addr)} → r15_sim_mode_flag")

idc.qexit(0)
