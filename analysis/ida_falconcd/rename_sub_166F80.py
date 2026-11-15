import ida_auto
import ida_name
import idc

ida_auto.auto_wait()

addr = 0x166F80
new_name = "r38_loadout_menu_dispatcher"

print(f"Renaming 0x{addr:X} to {new_name}")

if ida_name.set_name(addr, new_name, ida_name.SN_NOWARN):
    print(f"✅ SUCCESS: Renamed to {new_name}")
    idc.set_func_cmt(addr, "R38 loadout menu state machine dispatcher: Jump-table dispatcher (18+ cases) coordinating weapons/loadout configuration UI. 147 callers, 2,943B. Transition from mega-coordinators to specialized subsystem handlers.", 0)
    idc.save_database(idc.get_idb_path())
    print("✅ Database saved")
else:
    print(f"❌ FAILED to rename")

idc.qexit(0)
