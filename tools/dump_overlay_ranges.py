"""Dump full overlay linear ranges from IDB, then locate each record's bytes inside."""
import json
import ida_bytes
import ida_ida
import idaapi

OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\ida_overlay_dump.json"

# overlay ranges from registry/game_knowledge.yaml
RANGES = [
    (0x2CF60, 0x2EF16, "OVL_1CF6"),
    (0x303A5, 0x3A00B, "OVL_1E10"),
    (0x66A5D, 0x686F0, "OVL_569F"),
    (0x73271, 0x734DA, "OVL_5CD9"),
    (0x74742, 0x74C2C, "OVL_5DFF_a"),
    (0x74C2C, 0x7505F, "OVL_5E0B"),
    (0x7505F, 0x75074, "OVL_5DFF_b"),
    (0x75998, 0x75C58, "OVL_5E8F"),
    (0x76A70, 0x76C55, "OVL_5F6C"),
    (0x741A0, 0x74742, "OVL_606E"),
]

out = {}
for start, end, name in RANGES:
    data = ida_bytes.get_bytes(start, end - start)
    out[name] = {"start": start, "end": end, "bytes": data.hex() if data else None}
    print("%s 0x%X-0x%X got %s" % (name, start, end, len(data) if data else "FAIL"))

json.dump(out, open(OUT, "w"))
print("wrote", OUT)
idaapi.qexit(0)
