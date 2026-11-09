import idaapi, ida_loader, ida_name
ida_name.set_name(0x10002, "KILLTEST_RENAMED", 0)
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
