import idc, idaapi
idc.set_name(0x3470D, "range_key_event_dispatch", idc.SN_NOCHECK)
print("renamed 0x3470D ->", idc.get_name(0x3470D))
idaapi.qexit(0)
