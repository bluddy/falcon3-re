from pathlib import Path
import struct

d = Path('game/FALCONCD.EXE').read_bytes()
tail = 0x1fb51
t = d[tail:]

base = 0x2c00 + 0x1AA3 * 16 + 0x0C1F
recs = []
for i in range(100):
    o = base + i * 18
    if o + 18 > len(d):
        break
    w = struct.unpack_from('<9H', d, o)
    if not (0x100 <= w[0] <= 0x9000):
        break
    recs.append(dict(id=w[7], seg=w[0], off=w[2], A=w[4], B=w[5], C=w[6]))

sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# Disassemble fixup stubs using capstone if available, otherwise pattern match
try:
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    HAS_CAPSTONE = True
except:
    HAS_CAPSTONE = False

def analyze_stub(gap_data, label):
    print(f"\n=== {label} ({len(gap_data)} bytes) ===")
    print(f"  Hex: {gap_data[:64].hex()}...")
    
    # Pattern analysis
    has_int21 = b'\xcd\x21' in gap_data
    has_mov_seg = any(b in gap_data for b in [0x8e, 0x8c])
    has_pop = any(b in gap_data for b in [0x07, 0x1f, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f])
    has_push = any(b in gap_data for b in [0x06, 0x0e, 0x16, 0x1e, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57])
    has_call = b'\xe8' in gap_data
    has_retf = b'\xcb' in gap_data
    has_ret = b'\xc3' in gap_data
    has_mov_imm = any(b in gap_data for b in [0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 
                                                 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf])
    
    print(f"  INT 21h: {has_int21} | Seg load: {has_mov_seg} | POP: {has_pop} | PUSH: {has_push} | CALL: {has_call} | RETF: {has_retf} | RET: {has_ret} | MOV imm: {has_mov_imm}")
    
    # Look for data tables in the stub (repeated patterns, word arrays)
    if len(gap_data) >= 4:
        words = struct.unpack(f'<{len(gap_data)//2}H', gap_data[:len(gap_data)-len(gap_data)%2])
        # Look for repeated values or sequences
        if len(words) > 4:
            unique = len(set(words))
            print(f"  Words: {len(words)} unique={unique} first={words[:8]}")

# Analyze key fixup stubs
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# Key stubs
key_stubs = [3, 5, 7, 8, 9, 29, 31, 31, 52, 71]  # ids with large fixup stubs

for r in sorted_recs:
    if r['id'] in key_stubs:
        next_r = None
        for nr in sorted_recs:
            if nr['off'] > r['off']:
                next_r = nr
                break
        if next_r:
            gap = next_r['off'] - (r['off'] + r['A'])
            if gap > 0:
                gap_data = t[r['off']+r['A']:next_r['off']]
                analyze_stub(gap_data, f"id={r['id']} seg={r['seg']:04x} gap={len(gap_data)}")

# Also analyze the large id71 stub (5347 bytes) - this is the big one for composite overlay
r71 = next(r for r in sorted_recs if r['id'] == 71)
next_r = None
for nr in sorted_recs:
    if nr['off'] > r71['off']:
        next_r = nr
        break
if next_r:
    gap = next_r['off'] - (r71['off'] + r71['A'])
    gap_data = t[r71['off']+r71['A']:next_r['off']]
    print(f"\n=== id71 fixup stub ({len(gap_data)} bytes) ===")
    # Look for data tables in the stub
    # Check for word arrays that could be fixup tables
    words = struct.unpack(f'<{len(gap_data)//2}H', gap_data[:len(gap_data)-len(gap_data)%2])
    # Look for repeated patterns
    from collections import Counter
    cnt = Counter(words)
    common = cnt.most_common(20)
    print(f"  Most common words: {common[:10]}")
    # Look for sequences
    for i in range(min(len(words)-3, 100)):
        if words[i] == words[i+1] or words[i]+1 == words[i+1]:
            pass  # sequences
    # Print first 100 words
    print(f"  First 100 words: {words[:100]}")

# Also check if fixup data is embedded in the stub as data after code
print("\n=== Checking for embedded data tables in large stubs ===")
for r in sorted_recs:
    next_r = None
    for nr in sorted_recs:
        if nr['off'] > r['off']:
            next_r = nr
            break
    if next_r:
        gap = next_r['off'] - (r['off'] + r['A'])
        if gap > 100:
            gap_data = t[r['off']+r['A']:next_r['off']]
            # Look for word arrays that could be fixup data
            # Check for sequences of words that could be offsets
            words = struct.unpack(f'<{len(gap_data)//2}H', gap_data[:len(gap_data)-len(gap_data)%2])
            # Count how many words are small (< 1000) - could be offsets
            small = sum(1 for w in words if 0 < w < 1000)
            if small > 10:
                print(f"id={r['id']:3d} stub_len={len(gap_data)} small_words={small}/{len(words)} ratio={small/len(words)*100:.1f}%")