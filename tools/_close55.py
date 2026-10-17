"""Finding 55 closing numbers.

(1) Thunk traversal: export_callrefs only walks heads INSIDE functions, so a
    thunk slot that is not a registered function never yields its JMP FAR ref.
    Count: slots with a ref emitted from slot+3 (the JMP FAR), out of 303.
(2) Record 5 payload boundary: what sits between the fixup-table end and the
    data window the delta analysis points at (+5440)?

Usage: venv\\Scripts\\python tools\\_close55.py
"""
import json
import struct
from bisect import bisect_right
from collections import Counter

d = open("game/FALCONCD.EXE", "rb").read()
cls = json.load(open("analysis/ida_falconcd/classification.json"))
refs = json.load(open("analysis/ida_falconcd/callgraph_refs.json"))["refs"]
place = {p["idx"]: p for p in json.load(open("analysis/ida_falconcd/overlay_placement.json"))}

starts = sorted(v["ea"] for v in cls.values())
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())


def res(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2]
    return None


REAL = 0x1E99D
IDA_BASE = 0x2BD9D
n = 0
while d[REAL + n * 10] == 0xE8 and d[REAL + n * 10 + 3] == 0xEA:
    n += 1
slots = [IDA_BASE + i * 10 for i in range(n)]

srcset = {r[0] for r in refs}
traversed = [s for s in slots if (s + 3) in srcset]
reg = [s for s in slots if res(s)]
reg_trav = [s for s in reg if (s + 3) in srcset]
print("(1) RTLink thunk table: %d slots (IDA 0x%X..0x%X)" % (len(slots), IDA_BASE, IDA_BASE + n * 10))
print("    slots registered as functions            : %d" % len(reg))
print("    slots whose JMP FAR (slot+3) produced a ref: %d   <-- export_callrefs traversal"
      % len(traversed))
# proper target check
tgt_ok = 0
tgt_bad = []
for s in traversed:
    i = (s - IDA_BASE) // 10
    off, seg, _w = struct.unpack_from("<HHH", d, REAL + i * 10 + 4)
    t = ((seg + 0x1000) << 4) + off
    if res(t):
        tgt_ok += 1
    else:
        tgt_bad.append((s, t))
print("      ... of those, target registered      : %d ; NOT registered: %d" % (tgt_ok, len(tgt_bad)))
print("    slots NEVER traversed                   : %d" % (len(slots) - len(traversed)))

# how many refs point INTO the table (calls to thunks) and of those resolve?
into = [r for r in refs if IDA_BASE <= r[1] <= IDA_BASE + n * 10]
print("    refs INTO the thunk table: %d ; resolving to a fn: %d ; NOT: %d"
      % (len(into), sum(1 for r in into if res(r[1])), sum(1 for r in into if not res(r[1]))))

print("")
p = place[5]
_w0, _w1, w2, _w3, w4, w5, _w6, _w7, _w8 = struct.unpack_from("<9H", d, 0x1E24F + 5 * 18)
tpos = w2 << 4
tend = tpos + w5 * 4
print("(2) record 5: fixup table 0x%X..0x%X (w5=%d) ; data window 0x%X ; ida_ea=0x%X"
      % (tpos, tend, w5, p["data_file"], p["ida_ea"]))
print("    gap table-end -> data_file : %d bytes" % (p["data_file"] - tend))
print("    data_file + 5440 (delta-implied payload base) = 0x%X" % (p["data_file"] + 5440))
print("    bytes at table-end+0x00:", d[tend:tend + 32].hex())
print("    bytes at data_file+0x00:", d[p["data_file"]:p["data_file"] + 32].hex())
print("    bytes at data_file+0x1F0:", d[p["data_file"] + 0x1F0:p["data_file"] + 0x1F0 + 8].hex(),
      " <- IDB sub_2E2F0 head (should be 57561e...)")
fb = json.load(open("analysis/ida_falconcd/function_bytes.json"))
print("    IDB  sub_2E2F0 head     :", fb["sub_2E2F0"]["bytes"][:16])
# is there a second arena-valid table starting at tend?
arena = set(range(_w0, _w0 + w4)) | {0x1D0D, 0x1D31}
k = 0
while tend + (k + 1) * 4 <= len(d):
    _o, s = struct.unpack_from("<HH", d, tend + k * 4)
    if s not in arena:
        break
    k += 1
print("    arena-valid run starting at table-end: %d entries" % k)
