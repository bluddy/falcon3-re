import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

print(f"Total size of m113: {len(m113)}")

# Search for any sequence of 14 points (x, y, z) where v09 and v10 are DIFFERENT
# In REPORT.DAT:
# v09 is front, v10 is back. So they MUST have different longitudinal coordinates!
for p in range(0, len(m113) - 14 * 6, 2):
    # read 14 vertices
    verts = [struct.unpack_from('<3h', m113, p + i * 6) for i in range(14)]
    # Check if this could be the 14 vertices of M113
    # v09 and v10 should have different longitudinal coordinates!
    # v09 is front, v10 is back!
    # Let's check if the coordinates have reasonable ranges (-500 to 500)
    if all(all(-1000 < c < 1000 for c in pt) for pt in verts):
        # Check if v09 != v10 and v04 != v06
        if verts[9] != verts[10] and verts[4] != verts[6]:
            print(f"Candidate at 0x{p:04x}!")
            for idx, pt in enumerate(verts):
                print(f"  v{idx:02d}: {pt}")
            break
else:
    print("No candidate found where v09 != v10 and v04 != v06 in entire m113_obj!")
