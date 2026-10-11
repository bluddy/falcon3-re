"""Extract a routine's bytes from a Borland/Intel 16-bit .OBJ.

Finds PUBDEF entry for the routine (underscore-prefixed), collects LEDATA
content for its segment, returns bytes from pub offset to next pub/seg end.

Usage: obj_extract.py <file.obj> <routine_name>
"""
import json
import struct
import sys
from pathlib import Path


def parse_obj(data: bytes):
    segs = []          # list of (name, length) in index order (1-based)
    pubs = {}          # name -> (seg_index, offset)
    contents = {}      # seg_index -> {offset: bytes}
    pos = 0
    last_lname = None
    while pos + 3 <= len(data):
        rtype = data[pos]
        rlen = struct.unpack_from("<H", data, pos + 1)[0]
        if rlen < 1 or pos + 3 + rlen > len(data):
            break
        payload = data[pos + 3:pos + 3 + rlen - 1]   # strip checksum
        pos += 3 + rlen
        if rtype == 0x98:                      # SEGDEF (TASM dialect)
            # attr(1), length(2), ...
            length = struct.unpack_from("<H", payload, 1)[0]
            segs.append((last_lname or "?", length))
            last_lname = None
        elif rtype == 0x96:                    # LNAMES
            if payload:
                n = payload[0]
                if 0 < n <= len(payload) - 1:
                    last_lname = payload[1:1 + n].decode("ascii", "ignore")
        elif rtype == 0x90:                    # PUBDEF (TASM dialect)
            # group(1) seg(1) then entries: len name offset(2) type(1)
            i = 2
            seg = payload[1]
            while i < len(payload):
                nlen = payload[i]; i += 1
                if nlen == 0 or i + nlen + 3 > len(payload):
                    break
                name = payload[i:i + nlen].decode("ascii", "ignore"); i += nlen
                off = struct.unpack_from("<H", payload, i)[0]; i += 2
                i += 1                        # type index
                pubs[name] = (seg, off)
        elif rtype == 0xA0:                    # LEDATA (TASM dialect)
            seg = payload[0]
            off = struct.unpack_from("<H", payload, 1)[0]
            contents.setdefault(seg, {})[off] = payload[3:]
        # 0x80 THEADR, 0x88 COMENT, 0x8a, 0xa1 etc ignored
    return segs, pubs, contents


def extract(obj_path: str, routine: str) -> bytes:
    data = Path(obj_path).read_bytes()
    segs, pubs, contents = parse_obj(data)
    key = "_" + routine
    if key not in pubs:
        # case-insensitive fallback
        matches = [k for k in pubs if k.lower() == key.lower()]
        if not matches:
            raise SystemExit("pub %s not found; have: %s" % (key, list(pubs)[:10]))
        key = matches[0]
    seg, off = pubs[key]
    # end = next pub in same seg, else seg length
    ends = [o for n, (s, o) in pubs.items() if s == seg and o > off]
    end = min(ends) if ends else segs[seg - 1][1]
    size = end - off
    blob = bytearray()
    chunks = contents.get(seg, {})
    for a in range(off, end):
        for start, b in chunks.items():
            if start <= a < start + len(b):
                blob.append(b[a - start])
                break
        else:
            blob.append(0)
    return bytes(blob)


if __name__ == "__main__":
    obj, routine = sys.argv[1], sys.argv[2]
    got = extract(obj, routine)
    fb_path = Path(r"analysis/ida_falconcd/function_bytes.json")
    want = bytes.fromhex(json.load(open(fb_path))[routine]["bytes"])
    print("got  (%d): %s" % (len(got), got.hex()))
    print("want (%d): %s" % (len(want), want.hex()))
    n = min(len(got), len(want))
    if got[:n] == want[:n] and len(got) == len(want):
        print("MATCH!")
        sys.exit(0)
    for i in range(n):
        if got[i] != want[i]:
            print("first diff @%d: got %02x want %02x" % (i, got[i], want[i]))
            print("got ctx :", got[max(0, i - 4):i + 8].hex())
            print("want ctx:", want[max(0, i - 4):i + 8].hex())
            break
    else:
        print("prefix ok but lengths differ (%d vs %d)" % (len(got), len(want)))
    sys.exit(1)
