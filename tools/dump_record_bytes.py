"""Dump IDA DB bytes for each RTLink fixup record at its runtime placement.

Placement (validated against segment ranges): linear = (0x1000 + seg)*16 + tail_off
Output: analysis/ida_falconcd/ida_record_bytes.json  {rec_id: hex}
"""
import json
import ida_bytes
import ida_ida
import idaapi

RT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\rtlink_records.json"
OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\ida_record_bytes.json"

base_para = ida_ida.inf_get_min_ea() >> 4
rt = json.load(open(RT))

out = {}
for key, r in rt.items():
    seg = r['seg']
    tail_off = r['off']
    a = r['A']
    linear = ((base_para + seg) << 4) + tail_off
    data = ida_bytes.get_bytes(linear, a)
    out[key] = {
        'seg': seg, 'tail_off': tail_off, 'A': a, 'linear': linear,
        'ida_bytes': data.hex() if data else None,
    }
    print('id=%s linear=0x%X A=%d got=%s' % (key, linear, a, 'ok' if data else 'FAIL'))

json.dump(out, open(OUT, 'w'), indent=1)
print('wrote', OUT)
idaapi.qexit(0)
