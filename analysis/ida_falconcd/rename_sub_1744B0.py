import ida_auto
import ida_name
import idc

ida_auto.auto_wait()

addr = 0x1744B0
new_name = "game_mode_r48_main_coordinator"

print(f"Renaming 0x{addr:X} to {new_name}")

if ida_name.set_name(addr, new_name, ida_name.SN_NOWARN):
    print(f"✅ SUCCESS: Renamed to {new_name}")
    idc.set_func_cmt(addr, "R48 game mode main coordinator: UI/menu dispatcher with 360 callers. Integrates rendering, input, state management, and resource loading for this game mode. 9061 bytes, 110 callees.", 0)
    idc.save_database(idc.get_idb_path())
    print("✅ Database saved")
else:
    print(f"❌ FAILED to rename")

idc.qexit(0)
