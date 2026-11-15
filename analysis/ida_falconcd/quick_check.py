import ida_auto
import idc

ida_auto.auto_wait()

# Quick check of key functions
addrs = [0x12FC43, 0x130A2F, 0x130C80, 0x128518]
for addr in addrs:
    print(f"0x{addr:06X}: {idc.get_func_name(addr)}")

idc.qexit(0)
