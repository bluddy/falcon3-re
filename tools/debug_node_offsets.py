#!/usr/bin/env python3
import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def parse_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    t1 = []
    off = t1_base
    while off + 2 <= len(body):
        v = struct.unpack_from('<H', body, off)[0]
        off += 2
        if v == 0xFFFF: break
        t1.append(v)
    t2 = []
    off = t2_base
    while off + 2 <= len(body):
        v = struct.unpack_from('<H', body, off)[0]
        off += 2
        if v == 0xFFFF: break
        t2.append(v)
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF: break
            recs.add(v)
    recs_list = []
    for r in sorted(recs):
        if r + 0x36 > len(body): continue
        attr = struct.unpack_from('<H', body, r + 0x20)[0]
        if attr not in (0x14, 0x32, 0x64, 0xC8): continue
        pc = struct.unpack_from('<H', body, r + 0x2E)[0]
        pts_off = r + 0x38
        sub_off = pts_off + pc * 6
        min_node = 0xFFFF
        for _ in range(50):
            if sub_off + 4 > len(body): break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF: break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            if nodes:
                mn = min(nodes)
                if mn < 0x10000:
                    pass
                if mn < 0xFFFF:
                    pass
                # track min
            if sub_off >= len(body) or sub_off > r + 800: break
        # just print record offset and attr
        attr = struct.unpack_from('<H', body, r + 0x20)[0]
        sub_off = r + 0x38 + struct.unpack_from('<H', body, r + 0x2E)[0] * 6
        min_node = 0xFFFF
        for _ in range(50):
            if sub_off + 4 > len(body): break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF: break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            if nodes:
                mn = min(nodes)
                if mn < 0xFFFF: pass
        # just print first record for debugging
        break

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body_len, _, t1_base, t2_base, swap = struct.unpack('<HHHHB', data[:9])
body = data[9:]
t1 = []
off = t1_base
while off + 2 <= len(body):
    v = struct.unpack_from('<H', body, off)[0]
    off += 2
    if v == 0xFFFF: break
    t1.append(v)
t2 = []
off = t2_base
while off + 2 <= len(body):
    v = struct.unpack_from('<H', body, off)[0]
    off += 2
    if v == 0xFFFF: break
    t2.append(v)
recs = set()
for idx in t1 + t2:
    off = idx
    while off + 2 <= len(body):
        v = struct.unpack_from('<H', body, off)[0]
        off += 2
        if v == 0xFFFF: break
        recs.add(v)

for r in sorted(recs):
    if r + 0x36 > len(body): continue
    attr = struct.unpack_from('<H', body, r + 0x20)[0]
    if attr not in (0x14, 0x32, 0x64, 0xC8): continue
    pc = struct.unpack_from('<H', body, r + 0x2E)[0]
    pts_off = r + 0x38
    sub_off = pts_off + pc * 6
    min_node = 0xFFFF
    for _ in range(50):
        if sub_off + 4 > len(body): break
        flags, opcode = struct.unpack_from('<HH', body, sub_off)
        sub_off += 4
        nodes = []
        if flags & 0x1000:
            while sub_off + 2 <= len(body):
                v = struct.unpack_from('<H', body, sub_off)[0]
                sub_off += 2
                if v == 0xFFFF: break
                nodes.append(v)
        else:
            if sub_off + 2 <= len(body):
                nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                sub_off += 2
        if nodes:
            mn = min(nodes)
            if mn < min_node:
                min_node = mn
    if min_node != 0xFFFF:
        attr_name = {0x14: 'coast', 0x32: 'river', 0x64: 'lake', 0xC8: 'border'}.get(attr, f'unk{attr:02X}')
        print(f'0x{r:04X} attr=0x{attr:02X} ({attr_name}) min_node=0x{min_node:04X}')