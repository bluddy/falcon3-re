import idaapi
import idautils
import idc

# Check both addresses
addr1 = 0x128518
addr2 = 0x128598

print("=" * 70)
print("ADDRESS VERIFICATION")
print("=" * 70)

for addr in [addr1, addr2]:
    func = idaapi.get_func(addr)
    if func:
        name = idc.get_func_name(addr)
        size = func.end_ea - func.start_ea
        callers = len(list(idautils.CodeRefsTo(addr, 1)))
        print(f"\n0x{addr:X}:")
        print(f"  Name: {name}")
        print(f"  Size: {size} bytes")
        print(f"  Callers: {callers}")
        print(f"  Start: 0x{func.start_ea:X}")
        print(f"  End: 0x{func.end_ea:X}")
    else:
        print(f"\n0x{addr:X}: NOT A FUNCTION")

idc.qexit(0)
