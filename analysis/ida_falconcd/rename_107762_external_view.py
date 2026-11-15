import idaapi
import idc
import ida_auto

ida_auto.auto_wait()

# Rename the flag to external_view_flag
flag_addr = 0x107762
old_name = idc.get_name(flag_addr)
new_name = "r15_external_view_flag"

if idc.set_name(flag_addr, new_name, idaapi.SN_CHECK):
    print(f"✓ Renamed flag {hex(flag_addr)}: {old_name} → {new_name}")
else:
    print(f"✗ Failed to rename {hex(flag_addr)}")

# Update the comment on the simulation loop
sim_loop_addr = 0x108BAC
idc.set_cmt(sim_loop_addr, "R15 SIMULATION LOOP - Main game physics/logic update. Flag cs:r15_external_view_flag selects: 0=cockpit view (37 calls), 1=external view (46 calls)", 0)
print(f"✓ Updated comment at {hex(sim_loop_addr)}")

# Update the branch comment
idc.set_cmt(0x108BB2, "Branch: if external_view_flag==0 → Path A (cockpit), else → Path B (external view)", 0)
print(f"✓ Updated branch comment")

print("\n✓ Renamed to r15_external_view_flag - indicates external camera/view mode vs cockpit")

idc.qexit(0)
