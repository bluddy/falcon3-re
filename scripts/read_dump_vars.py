with open('analysis/ida_falconcd/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

# Let's verify the exact offset map:
# In IDA, 0x28D14 is loc_28D14.
# In EXE, pos_in_exe = 0x1ADFE.
# In DUMP, pos_in_dump = 0x1A14E.
# Let's check 0x26B2E (object_3d_project_and_draw):
# ida_offset = 0x26B2E
# In EXE, offset is 0x26B2E - (0x28D14 - 0x1ADFE) = 0x26B2E - 0xDF16 = 0x18C18.
# Let's verify bytes at 0x18C18 in EXE:
exe_bytes = exe[0x18C18 : 0x18C28]
print('Bytes at 0x18C18 in EXE:', exe_bytes.hex(' '))
# And in DUMP: 0x18C18 - 0xCB0 = 0x17F68:
dump_bytes = dump[0x17F68 : 0x17F78]
print('Bytes at 0x17F68 in DUMP:', dump_bytes.hex(' '))

# Let's check where CS variables are:
# word_1F712 in IDA:
# ida_addr = 0x1F712
# in EXE: 0x1F712 - 0xDF16 = 0x117FC
# in DUMP: 0x117FC - 0xCB0 = 0x10B4C
dump_var_phys = 0x10B4C
import struct
w_1F712, w_1F714, w_1F716, w_1F718 = struct.unpack_from('<4H', dump, dump_var_phys)
print(f'In DUMP at 0x{dump_var_phys:X}:')
print(f'  word_1F712 (model segment) = 0x{w_1F712:04X}')
print(f'  word_1F714                 = 0x{w_1F714:04X}')
print(f'  word_1F716 (model offset)  = 0x{w_1F716:04X}')
print(f'  word_1F718                 = 0x{w_1F718:04X}')
