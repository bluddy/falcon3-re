import idc
import idaapi

idaapi.auto_wait()

ea = idc.get_name_ea_simple("word_1F712")
print(f"word_1F712 ea: 0x{ea:X}, seg: 0x{idc.get_segm_start(ea):X}")
seg_name = idc.get_segm_name(ea)
print(f"seg_name: {seg_name}")

ea_code = 0x28D14
print(f"loc_28D14 ea: 0x{ea_code:X}, seg: 0x{idc.get_segm_start(ea_code):X}")
seg_name_code = idc.get_segm_name(ea_code)
print(f"seg_name_code: {seg_name_code}")

# Let's check distance within segment
off_var = ea - idc.get_segm_start(ea)
off_code = ea_code - idc.get_segm_start(ea_code)
print(f"off_var: 0x{off_var:X}, off_code: 0x{off_code:X}")

with open(r'analysis/viewer/seg_info.txt', 'w') as f:
    f.write(f"var: 0x{ea:X} in {seg_name} (off 0x{off_var:X})\ncode: 0x{ea_code:X} in {seg_name_code} (off 0x{off_code:X})\n")

idc.qexit(0)
