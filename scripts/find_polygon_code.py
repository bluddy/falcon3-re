import struct
with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

header = exe[:0x40]
fields = struct.unpack('<14H', header[:28])
cparhdr = fields[4]
cs = fields[11]
ip = fields[10]
print(f"MZ header: cparhdr={cparhdr} (header size = {cparhdr*16:#x}), cs:ip={cs:#x}:{ip:#x}")
