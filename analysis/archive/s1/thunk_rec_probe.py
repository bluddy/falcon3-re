"""Read-only (DBFL_KILL): raw 10-byte thunk slots for the far-tail owners (rec_id at +8).
Output: analysis/s1/thunk_rec_probe.json"""
import json
import idaapi, idc
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\thunk_rec_probe.json"
EAS = [0x2BDC5, 0x2BDED, 0x2BE0B, 0x2BE6F, 0x2C013, 0x2C03B, 0x2C167, 0x2C199, 0x2C24D, 0x2C289]
open(OUT, "w").write(json.dumps({"%X" % e: idc.get_bytes(e, 10).hex() for e in EAS}, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
