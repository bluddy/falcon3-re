"""Minimal OMF .LIB parser: module names, publics, LEDATA code blocks."""
from pathlib import Path


def _records(buf, start):
    """Yield OMF records; Microsoft .LIB pads modules to 16-byte boundaries."""
    pos = start
    n = len(buf)
    while pos + 3 <= n:
        rtype = buf[pos]
        rlen = buf[pos + 1] | (buf[pos + 2] << 8)
        if rlen >= 1 and pos + 3 + rlen <= n and rtype in (
                0x80, 0x82, 0x88, 0x8A, 0x8B, 0x8C, 0x8E, 0x90, 0x91, 0x92,
                0x94, 0x96, 0x98, 0x99, 0x9A, 0x9C, 0x9E, 0xA0, 0xA1, 0xA2,
                0xA3, 0xB0, 0xB4, 0xB6, 0xC2, 0xF0, 0xF2):
            yield rtype, buf[pos + 3:pos + 3 + rlen - 1]
            pos += 3 + rlen
            continue
        # padding between modules: skip to the next 16-byte boundary
        if rtype == 0:
            pos = (max(pos, 1) + 15) & ~15
            while pos < n and buf[pos] == 0:
                pos += 16
            continue
        return


def _name(s, pos):
    ln = s[pos]
    return s[pos + 1:pos + 1 + ln].decode("latin1", "replace"), pos + 1 + ln


def parse_lib(path):
    buf = Path(path).read_bytes()
    start = None
    for o in (0, 32, 33):
        try:
            it = _records(buf, o)
            rtype, payload = next(it)
            if rtype in (0x80, 0x82, 0x88, 0xF0, 0x6F) or rtype < 0xF0:
                start = o
                break
        except StopIteration:
            continue
    if start is None:
        start = 33

    mods = []
    cur = None
    for rtype, payload in _records(buf, start):
        if rtype in (0x80, 0x82):  # THEADR / LHEADR
            nm, _ = _name(payload, 0) if payload else ("", 0)
            cur = {"name": nm, "segs": [], "pubs": [], "strings": []}
            mods.append(cur)
        elif cur is None:
            continue
        elif rtype == 0xA0:  # LEDATA
            segidx = payload[0]
            off = payload[1] | (payload[2] << 8)
            cur["segs"].append({"idx": segidx, "off": off,
                                "data": bytearray(payload[3:])})
        elif rtype == 0xA1:  # LIDATA (iterated) - skip
            continue
        elif rtype == 0x90 or rtype == 0x91:  # PUBDEF
            pos = 2
            if pos < len(payload):
                segidx = payload[pos]
                pos += 1
                if segidx == 0:
                    pos += 2
            while pos < len(payload):
                if pos >= len(payload):
                    break
                ln = payload[pos]
                if ln == 0 or pos + 1 + ln + 3 > len(payload):
                    break
                nm, pos = _name(payload, pos)
                off = payload[pos] | (payload[pos + 1] << 8)
                pos += 2
                if pos < len(payload) and payload[pos] & 0x80:
                    pos += 2          # two-byte type index
                else:
                    pos += 1
                cur["pubs"].append((nm, off))
        elif rtype == 0x88 or rtype == 0x8C or rtype == 0xA1:  # COMENT
            if payload and payload[0] == 0xA1:  # translator/impdef etc.
                pass
            if len(payload) > 6 and payload[1:4] == b"MS ":
                cur["strings"].append(payload[4:].decode("latin1", "replace"))
    return mods


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        mods = parse_lib(p)
        print(f"== {p}: {len(mods)} modules")
        for m in mods[:10]:
            print(f"   {m['name']} segs={len(m['segs'])} pub={m['pubs'][:6]}")
