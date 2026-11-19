import struct
import glob
from pathlib import Path

THEATER_MAP = {
    'BOS': ('BOSNIA.MAP', 'ISLDAT.BOS', 'ALTPAL.BOS', 'MAPOBJ.BOS'),
    'HOK': ('JAPAN.MAP', 'ISLDAT.HOK', 'ALTPAL.HOK', 'MAPOBJ.HOK'),
    'IRQ': ('KUWAIT.MAP', 'ISLDAT.IRQ', 'ALTPAL.IRQ', 'MAPOBJ.IRQ'),
    'ISR': ('ISRAEL.MAP', 'ISLDAT.ISR', 'ALTPAL.ISR', 'MAPOBJ.ISR'),
    'KOR': ('KOREA.MAP', 'ISLDAT.KOR', 'ALTPAL.KOR', 'MAPOBJ.KOR'),
    'NEL': ('NELLIS.MAP', 'ISLDAT.NEL', 'ALTPAL.NEL', 'MAPOBJ.NEL'),
    'PAK': ('INDIA.MAP', 'ISLDAT.PAK', 'ALTPAL.PAK', 'MAPOBJ.PAK'),
    'PAN': ('PANAMA.MAP', 'ISLDAT.PAN', 'ALTPAL.PAN', 'MAPOBJ.PAN'),
}

def inspect_all():
    print(f"{'Code':4s} | {'MAP File':11s} | {'Dims':9s} | {'Tile Range':12s} | {'ISLDAT':10s} | {'Recs':4s} | {'Coord Box (X nm, Y nm)':32s} | {'MAPOBJ':8s}")
    print("-" * 115)

    for code, (map_f, isl_f, pal_f, obj_f) in sorted(THEATER_MAP.items()):
        # 1. MAP
        map_p = Path('game') / map_f
        w, h, min_t, max_t = 0, 0, 0, 0
        if map_p.exists():
            data = map_p.read_bytes()
            w, h = struct.unpack_from('<HH', data, 0)
            tiles = data[4:4+w*h]
            min_t, max_t = min(tiles), max(tiles)
            
        # 2. ISLDAT
        isl_p = Path('game') / isl_f
        n_recs = 0
        min_x, max_x, min_y, max_y = 0, 0, 0, 0
        attrs = set()
        if isl_p.exists():
            raw = isl_p.read_bytes()
            body = raw[9:]
            t1, t2 = struct.unpack_from('<HH', raw, 4)
            
            def u16(b, o): return struct.unpack_from('<H', b, o)[0]
            def table_extent(base, limit):
                best = 0
                for k in range(1, (limit - base) // 2 + 1):
                    if min(u16(body, base + 2 * j) for j in range(k)) == base + 2 * k:
                        best = k
                return [u16(body, base + 2 * j) for j in range(best)]
            
            recs = set()
            for ptr in table_extent(t1, t2) + table_extent(t2, len(body)):
                o = ptr
                while o + 2 <= len(body) and u16(body, o) != 0xFFFF:
                    recs.add(u16(body, o))
                    o += 2
            
            n_recs = len(recs)
            coords_x = []
            coords_y = []
            for r in recs:
                if r + 8 <= len(body):
                    x = struct.unpack_from('<i', body, r)[0] / 65536.0
                    y = struct.unpack_from('<i', body, r + 4)[0] / 65536.0
                    coords_x.append(x)
                    coords_y.append(y)
                    attr = u16(body, r + 0x20)
                    attrs.add(attr)
            if coords_x:
                min_x, max_x = min(coords_x), max(coords_x)
                min_y, max_y = min(coords_y), max(coords_y)

        # 3. MAPOBJ
        obj_p = Path('game') / obj_f
        obj_sz = obj_p.stat().st_size if obj_p.exists() else 0

        coord_str = f"[{min_x:5.1f}..{max_x:5.1f}, {min_y:5.1f}..{max_y:5.1f}]" if n_recs else "None"
        print(f"{code:4s} | {map_f:11s} | {w}x{h:<4d} | [{min_t:2d}..{max_t:2d}]     | {isl_f:10s} | {n_recs:4d} | {coord_str:32s} | {obj_sz:7d}B")

if __name__ == '__main__':
    inspect_all()
