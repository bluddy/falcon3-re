import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

grid_b = body[0x000:0x400]
grid_a = body[0x400:0x500]

print(f"t1 = 0x{t1:04X} ({t1}), t2 = 0x{t2:04X} ({t2}), len(body) = {len(body)}")
print(f"Grid B values: min={min(grid_b)}, max={max(grid_b)}, unique={len(set(grid_b))}")
print(f"Grid A values: min={min(grid_a)}, max={max(grid_a)}, unique={len(set(grid_a))}")

# Let's trace EVERY non-zero index in Grid B and Grid A directly using Falcon's formula!
# In Falcon:
# For Grid B: ptr = u16(t1 + grid_byte * 2)
# For Grid A: ptr = u16(t2 + grid_byte * 2)

def u16(o): return struct.unpack_from('<H', body, o)[0]

b_records = set()
for b in set(grid_b):
    if b == 0: continue
    off = t1 + b * 2
    if off + 2 <= len(body):
        list_ptr = u16(off)
        # Walk list
        p = list_ptr
        while p + 2 <= len(body):
            rec = u16(p)
            p += 2
            if rec == 0xFFFF: break
            b_records.add(rec)

a_records = set()
for a in set(grid_a):
    if a == 0: continue
    off = t2 + a * 2
    if off + 2 <= len(body):
        list_ptr = u16(off)
        p = list_ptr
        while p + 2 <= len(body):
            rec = u16(p)
            p += 2
            if rec == 0xFFFF: break
            a_records.add(rec)

print(f"Direct Falcon index - Grid B records: {len(b_records)}")
print(f"Direct Falcon index - Grid A records: {len(a_records)}")
all_records = b_records | a_records
print(f"Total direct records: {len(all_records)}")

# Now let's scan the ENTIRE body for ANY record header pattern:
# An ISLDAT record has:
# +0x20: attr (0x14, 0x32, 0x64, 0xC8)
# +0x24: const 0x000B
# +0x26: 0xFFFF
# +0x28: 0x0000
# +0x2C: 0x0004
all_scanned_records = set()
for offset in range(0, len(body) - 0x38, 2):
    attr = u16(offset + 0x20)
    c24 = u16(offset + 0x24)
    c26 = u16(offset + 0x26)
    c28 = u16(offset + 0x28)
    c2c = u16(offset + 0x2C)
    if attr in [0x14, 0x32, 0x64, 0xC8] and c24 == 0x000B and c26 == 0xFFFF and c28 == 0x0000 and c2c == 0x0004:
        all_scanned_records.add(offset)

print(f"Binary scanned records matching struct signature in ENTIRE body: {len(all_scanned_records)}")
missing = all_scanned_records - all_records
print(f"Records in file NOT reached by Grid A or B: {len(missing)}")
if missing:
    print(f"Missing records: {[hex(m) for m in sorted(missing)]}")
