import struct
from collections import Counter, defaultdict
from pathlib import Path

# Load ISLDAT.ISR
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from render_all_theater_maps import parse_isldat

features = parse_isldat(Path('game/ISLDAT.ISR'))
print(f"Features in ISR: {len(features)}")

for i, f in enumerate(features):
    rec = f['rec']
    attr = f['attr']
    tx = f['tx']
    ty = f['ty']
    polys = f['polylines']
    poly_pts = [len(p['world_pts']) for p in polys]
    closed = [p['closed'] for p in polys]
    
    # Calculate polyline world coordinate span
    all_p = [pt for p in polys for pt in p['world_pts']]
    if all_p:
        xs = [p[0] for p in all_p]
        ys = [p[1] for p in all_p]
        span_str = f"X=[{min(xs):5.1f}..{max(xs):5.1f}], Y=[{min(ys):5.1f}..{max(ys):5.1f}]"
    else:
        span_str = "no outline edges"
        
    print(f"#{i:2d} Rec 0x{rec:04X}: attr=0x{attr:02X}, Centroid=({tx:6.2f}, {ty:6.2f}), Polys={len(polys)} (pts={poly_pts}, closed={closed}), {span_str}")
