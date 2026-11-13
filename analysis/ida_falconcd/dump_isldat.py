"""Quick dump of isldat_state_load function"""
import idc
import idaapi

idaapi.auto_wait()

addr = 0x12FC4
end = idc.get_func_attr(addr, idc.FUNCATTR_END)

print("=== ISLDAT_STATE_LOAD @ 0x12FC4 ===")
ea = addr
while ea < end:
    print(f"{hex(ea)}: {idc.GetDisasm(ea)}")
    ea = idc.next_head(ea)

print("\n=== WORLDMAP_STATE_APPLY @ 0x130D5 ===")
addr2 = 0x130D5
end2 = idc.get_func_attr(addr2, idc.FUNCATTR_END)
ea = addr2
while ea < end2:
    print(f"{hex(ea)}: {idc.GetDisasm(ea)}")
    ea = idc.next_head(ea)
