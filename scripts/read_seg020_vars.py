with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

import struct

# loc_28D14 in dump is 0x1A14E.
# off_code in seg020 is 0x9654.
seg_base = 0x1A14E - 0x9654
print(f'seg020 base in dump: 0x{seg_base:X}')

# Let's inspect around offset 0x0052 in seg020:
var_off = seg_base + 0x0052
print(f'word_1F712 address in dump: 0x{var_off:X}')

for delta in range(-4, 8, 2):
    p = var_off + delta
    w12, w14, w16, w18 = struct.unpack_from('<4H', dump, p)
    print(f'At delta {delta:+2d} (0x{p:06X}): 1F712=0x{w12:04X}, 1F714=0x{w14:04X}, 1F716=0x{w16:04X}, 1F718=0x{w18:04X}')
