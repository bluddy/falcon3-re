import ida_auto
import ida_name
import idc

ida_auto.auto_wait()

addr = 0x1820B0
new_name = "game_mode_r53_main_coordinator"

print(f"Renaming 0x{addr:X} to {new_name}")

if ida_name.set_name(addr, new_name, ida_name.SN_NOWARN):
    print(f"✅ SUCCESS: Renamed to {new_name}")
    idc.set_func_cmt(addr, "R53 game mode main coordinator: Script-driven mode integrating audio/SBI, UI rendering, map display, and input. Largest function (12,693B). Called via r53_opcode_decode_apply. Likely briefing/mission-planning mode.", 0)
    idc.save_database(idc.get_idb_path())
    print("✅ Database saved")
else:
    print(f"❌ FAILED to rename")

idc.qexit(0)
