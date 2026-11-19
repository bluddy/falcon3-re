# Test Face 38 [46, 40, 64, 70]
# v46: (250, -20) (Falcon X, Y)
# v40: (155, 0)
# v64: (140, 0)
# v70: (-115, -15)

def tri_area(p0, p1, p2):
    return 0.5 * abs((p1[0]-p0[0])*(p2[1]-p0[1]) - (p1[1]-p0[1])*(p2[0]-p0[0]))

v46 = (250, -20)
v40 = (155, 0)
v64 = (140, 0)
v70 = (-115, -15)

# Fan [0,1,2] + [0,2,3]
a1 = tri_area(v46, v40, v64)
a2 = tri_area(v46, v64, v70)
print(f"Face 38 Fan: t1={a1}, t2={a2}, sum={a1+a2}")

# Strip [0,1,2] + [1,3,2]
b1 = tri_area(v46, v40, v64)
b2 = tri_area(v40, v70, v64)
print(f"Face 38 Strip: t1={b1}, t2={b2}, sum={b1+b2}")
