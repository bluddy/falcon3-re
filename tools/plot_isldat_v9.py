#!/usr/bin/env python3
"""Full ISLDAT geometry pipeline simulation with grid-walk order."""
import sys, struct, glob, os, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}
ATTR_NAMES = {0x14: 'coastline', 0x32: 'river', 0x64: 'lake', 0xC8: 'border'}
ATTR_COLORS = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def build_line_table(pts):
    """Build line table entries for all segments in a closed polygon"""
    entries = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        
        x0_f = x0 << 16
        y0_f = y0 << 16
        x1_f = x1 << 16
        y1_f = y1 << 16
        
        dx = x1_f - x0_f
        dy = y1_f - y0_f
        
        if dx == 0:
            q = 0x7FFF if dy >= 0 else -0x8000
        else:
            q = clamp_slope((dy << 16) // dx)
        
        neg2q = -2 * q
        if neg2q > 0x7FFF: neg2q = 0x7FFF
        if neg2q < -0x8000: neg2q = -0x8000
        
        dx_i = x1 - x0
        dy_i = y1 - y0
        flags = 0
        if dx_i < 0: flags |= 4
        if dy_i < 0: flags |= 2
        if abs(dy_i) > abs(dx_i): flags |= 1
        if dx_i == 0: flags |= 8
        if dy_i == 0: flags |= 0x10
        
        entries.append((x0, y0, x1, y1, q, -2*q, flags, 0))
    return entries

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def build_line_table(pts):
    """Build line table entries for all segments in a closed polygon"""
    entries = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        
        x0_f = x0 << 16
        y0_f = y0 << 16
        x1_f = x1 << 16
        y1_f = y1 << 16
        
        dx = x1_f - x0_f
        dy = y1_f - y0_f
        
        if dx == 0:
            q = 0x7FFF if dy >= 0 else -0x8000
        else:
            q = clamp_slope((dy << 16) // dx)
        
        neg2q = -2 * q
        if neg2q > 0x7FFF: neg2q = 0x7FFF
        if neg2q < -0x8000: neg2q = -0x8000
        
        dx_i = x1 - x0
        dy_i = y1 - y0
        flags = 0
        if dx_i < 0: flags |= 4
        if dy_i < 0: flags |= 2
        if abs(dy_i) > abs(dx_i): flags |= 1
        if dx_i == 0: flags |= 8
        if dy_i == 0: flags |= 0x10
        
        entries.append((x0, y0, x1, y1, q, -2*q, flags, 0))
    return entries

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def grid_walk_sort_key(record, view_x, view_y, word_11C16, word_11C18, word_11C1A, word_11CC4, word_11CC6):
    """Compute sort key for grid-walk order based on view position."""
    r_off, attr, pts, subs = record
    if not pts:
        return (0xFFFFFFFF, 0)
    # Use centroid of record's points as its position
    cx = sum(p[0] for p in pts) // len(pts)
    cy = sum(p[1] for p in pts) // len(pts)
    # Compute quadrant relative to view position
    dx = cx - view_x
    dy = cy - view_y
    # Use the same quadrant formula as the game
    pos = (dx + dy) & 0xFFFF  # approximate
    q = compute_quadrant(pos)
    # Grid index within quadrant
    gx = cx & 0x1F  # 5 bits
    gy = cy & 0x1F
    return (q, gy, gx)

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def build_line_table(pts):
    """Build line table entries for all segments in a closed polygon"""
    entries = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        
        x0_f = x0 << 16
        y0_f = y0 << 16
        x1_f = x1 << 16
        y1_f = y1 << 16
        
        dx = x1_f - x0_f
        dy = y1_f - y0_f
        
        if dx == 0:
            q = 0x7FFF if dy >= 0 else -0x8000
        else:
            q = clamp_slope((dy << 16) // dx)
        
        neg2q = -2 * q
        if neg2q > 0x7FFF: neg2q = 0x7FFF
        if neg2q < -0x8000: neg2q = -0x8000
        
        dx_i = x1 - x0
        dy_i = y1 - y0
        flags = 0
        if dx_i < 0: flags |= 4
        if dy_i < 0: flags |= 2
        if abs(dy_i) > abs(dx_i): flags |= 1
        if dx_i == 0: flags |= 8
        if dy_i == 0: flags |= 0x10
        
        entries.append((x0, y0, x1, y1, q, -2*q, flags, 0))
    return entries

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def build_line_table(pts):
    """Build line table entries for all segments in a closed polygon"""
    entries = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        
        x0_f = x0 << 16
        y0_f = y0 << 16
        x1_f = x1 << 16
        y1_f = y1 << 16
        
        dx = x1_f - x0_f
        dy = y1_f - y0_f
        
        if dx == 0:
            q = 0x7FFF if dy >= 0 else -0x8000
        else:
            q = clamp_slope((dy << 16) // dx)
        
        neg2q = -2 * q
        if neg2q > 0x7FFF: neg2q = 0x7FFF
        if neg2q < -0x8000: neg2q = -0x8000
        
        dx_i = x1 - x0
        dy_i = y1 - y0
        flags = 0
        if dx_i < 0: flags |= 4
        if dy_i < 0: flags |= 2
        if abs(dy_i) > abs(dx_i): flags |= 1
        if dx_i == 0: flags |= 8
        if dy_i == 0: flags |= 0x10
        
        entries.append((x0, y0, x1, y1, q, -2*q, flags, 0))
    return entries

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def compute_quadrant(pos):
    """q = ((pos + 0x800) & 0x3FFF) rol 4 & 3"""
    v = (pos + 0x800) & 0x3FFF
    v = ((v << 4) | (v >> 12)) & 0xFFFF  # ROL 4
    return v & 3

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def build_line_table(pts):
    """Build line table entries for all segments in a closed polygon"""
    entries = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        
        x0_f = x0 << 16
        y0_f = y0 << 16
        x1_f = x1 << 16
        y1_f = y1 << 16
        
        dx = x1_f - x0_f
        dy = y1_f - y0_f
        
        if dx == 0:
            q = 0x7FFF if dy >= 0 else -0x8000
        else:
            q = clamp_slope((dy << 16) // dx)
        
        neg2q = -2 * q
        if neg2q > 0x7FFF: neg2q = 0x7FFF
        if neg2q < -0x8000: neg2q = -0x8000
        
        dx_i = x1 - x0
        dy_i = y1 - y0
        flags = 0
        if dx_i < 0: flags |= 4
        if dy_i < 0: flags |= 2
        if abs(dy_i) > abs(dx_i): flags |= 1
        if dx_i == 0: flags |= 8
        if dy_i == 0: flags |= 0x10
        
        entries.append((x0, y0, x1, y1, q, -2*q, flags, 0))
    return entries

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        sub_off = pts_off
        subs = []
        for _ in range(50):
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def generate_svg(records, theater_name, output_dir='analysis/isldat_svgs_v9'):
    os.makedirs(output_dir, exist_ok=True)
    
    # Build GLOBAL line table in record order (simulating processing order)
    all_line_entries = []  # each: (x0, y0, x1, y1, q, -2*q, flags, 0)
    
    # First pass: build global line table in record order
    for r_off, attr, pts, subs in records:
        entries = build_line_table(pts)
        all_line_entries.extend(entries)
    
    # Second pass: resolve sub-record node chains against GLOBAL line table
    all_polys = []
    for r_off, attr, pts, subs in records:
        for flags, opcode, nodes in subs:
            if not nodes:
                continue
            poly = []
            for node_off in nodes:
                idx = node_off // 0x10  # convert byte offset to entry index
                if 0 <= idx < len(all_line_entries):
                    x0, y0, x1, y1, _, _, _, _ = all_line_entries[idx]
                    if not poly:
                        poly.append((x0, y0))
                    poly.append((x1, y1))
            if len(poly) >= 3:
                all_polys.append((attr, poly))
    
    all_pts = []
    for _, _, pts, _ in records:
        all_pts.extend(pts)
    if not all_pts:
        return
    
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    
    CANVAS = 4000
    MARGIN = 100
    w = maxx - minx
    h = maxy - miny
    scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
    
    def tx(x): return MARGIN + (x - minx) * scale
    def ty(y): return CANVAS - (MARGIN + (y - miny) * scale)
    
    os.makedirs(output_dir, exist_ok=True)
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT Full Pipeline</text>']
    
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        for attr_p, poly in all_polys:
            if attr_p != attr:
                continue
            if len(poly) < 3:
                continue
            path = f'M {tx(poly[0][0])} {ty(poly[0][1])}'
            for px, py in poly[1:]:
                path += f' L {tx(px)} {ty(py)}'
            path += ' Z'
            svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7"/>')
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_proper.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_proper.svg')

if __name__ == '__main__':
    import glob, os
    os.makedirs('analysis/isldat_svgs_v9', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            print(f'{name}: {len(recs)} valid records')
            generate_svg(recs, f'ISLDAT_{name}', 'analysis/isldat_svgs_v9')