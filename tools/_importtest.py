import traceback
try:
    import idautils, ida_name, ida_funcs, ida_bytes, ida_nalt, ida_ua, idaapi
    open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\importtest.log","w").write("imports ok")
except Exception:
    open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\importtest.log","w").write(traceback.format_exc())
idaapi.qexit(0)
