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
    fixups = {}        # seg_index -> set of offsets needing relocation
    pos = 0
    last_lname = None
    last_ledata = None  # (seg, offset) of most recent LEDATA (FIXUPP attaches to it)
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
        elif rtype == 0xA0:                    # LEDATA (TASM/BCC dialect)
            seg = payload[0]
            off = struct.unpack_from("<H", payload, 1)[0]
            contents.setdefault(seg, {})[off] = payload[3:]
            last_ledata = (seg, off)
        elif rtype in (0x9C, 0x8A):            # FIXUPP (BCC native / TASM)
            # locat (2B, bit7 of first set) -> record offset in last LEDATA,
            # then fixdata (1B, bit7 clear) + target/index (1B, no disp case)
            if last_ledata is None:
                continue
            base_seg, base_off = last_ledata
            i = 0
            while i + 1 < len(payload):
                if payload[i] & 0x80:
                    locat = (payload[i] << 8) | payload[i + 1]
                    rec_off = locat & 0x3FF
                    fixups.setdefault(base_seg, set()).add(base_off + rec_off)
                    i += 2
                    # consume fixdata + index bytes (bit7-clear run), cap generously
                    j = i
                    while j < len(payload) and not (payload[j] & 0x80):
                        j += 1
                    # Borland simple case: fixdata(1) + index(1)
                    i = min(j, i + 2) if j > i else i + 1
                else:
                    i += 1
        # 0x80 THEADR, 0x88 COMENT, 0x8C EXTDEF, 0x8a end etc ignored
    return segs, pubs, contents, fixups


def extract_ex(obj_path: str, routine: str):
    """Returns (bytes, fixup_offsets_within_routine) — see extract()."""
    data = Path(obj_path).read_bytes()
    segs, pubs, contents, fixups = parse_obj(data)
    key = "_" + routine
    if key not in pubs:
        matches = [k for k in pubs if k.lower() == key.lower()]
        if not matches:
            raise SystemExit("pub %s not found; have: %s" % (key, list(pubs)[:10]))
        key = matches[0]
    seg, off = pubs[key]
    ends = [o for n, (s, o) in pubs.items() if s == seg and o > off]
    end = min(ends) if ends else segs[seg - 1][1]
    blob = bytearray()
    chunks = contents.get(seg, {})
    fx = fixups.get(seg, set())

    def at(a):
        for start, b in chunks.items():
            if start <= a < start + len(b):
                return b[a - start]
        return 0

    for a in range(off, end):
        blob.append(at(a))
    # fixup positions relative to routine; if locat points at an E8 opcode,
    # the relocated field is the disp16 that follows (locat+1..+2)
    rel = set()
    for fp in fx:
        if off <= fp < end:
            k = fp - off
            if k < len(blob) and blob[k] == 0xE8:
                rel.update((k + 1, k + 2))     # near call disp16
            elif k < len(blob) and blob[k] == 0x9A:
                rel.update(range(k + 1, k + 5))   # far call off16:seg16 (link-resolved)
            else:
                rel.update((k, k + 1))
    # placeholder scans: link-time unresolved operands embedded as zeros
    for i in range(len(blob) - 4):
        if blob[i] == 0x9A and blob[i + 1:i + 5] == b"\x00\x00\x00\x00":
            rel.update(range(i + 1, i + 5))
        if blob[i] == 0xE8 and blob[i + 1:i + 3] == b"\x00\x00":
            rel.update((i + 1, i + 2))
    return bytes(blob), sorted(rel)


def extract(obj_path: str, routine: str) -> bytes:
    return extract_ex(obj_path, routine)[0]


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
