import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, idc
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142c.txt", "w")
# raw hex + linear decode without modifying the db
LO, HI = 0x6E69E, 0x6E8F0
out.write("HEX\n")
for a in range(LO, HI, 16):
    out.write("%X %s\n" % (a, ida_bytes.get_bytes(a, min(16, HI - a)).hex(" ")))
out.close(); idc.qexit(0)
