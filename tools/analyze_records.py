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

# Let's look at the actual record data + gap for a few key records
def dump_record_and_gap(r, next_r=None):
    off, A, B, C, seg, id = r['off'], r['A'], r['B'], r['C'], r['seg'], r['id']
    print(f"\n=== Record id={id} seg={seg:04x} off={off:05x} A={A} B={B} C={C:04x} ===")
    # First 32 bytes of record
    rec_data = t[off:off+min(A, 64)]
    print(f"  Record head: {rec_data[:32].hex()}")
    # Gap after record
    if next_r:
        gap_start = off + A
        gap_end = next_r['off']
        gap_size = gap_end - gap_start
        if gap_size > 0:
            gap = t[gap_start:gap_end]
            print(f"  Gap ({gap_size} bytes): {gap[:64].hex()}")
            # Disassemble if it looks like code
            try:
                import capstone
                md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
                for insn in md.disasm(bytes(t[off+A:off+A+min(gap_size, 32)]), 0):
                    print(f"    {insn.address:04x}: {insn.mnemonic} {insn.op_str}")
            except:
                pass

# Sort by offset
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])
for i in range(len(sorted_recs)):
    dump_record_and_gap(sorted_recs[i], sorted_recs[i+1] if i+1 < len(sorted_recs) else None)
    if i > 10:
        break