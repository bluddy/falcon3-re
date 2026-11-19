# Test triangulation of [23, 24, 22, 21]
v23 = (-15, -45)
v24 = ( 70, -30)
v22 = ( 10, -120)
v21 = ( 70, -120)

def tri_area(p0, p1, p2):
    return 0.5 * abs((p1[0]-p0[0])*(p2[1]-p0[1]) - (p1[1]-p0[1])*(p2[0]-p0[0]))

print("Points:")
print("v23:", v23)
print("v24:", v24)
print("v22:", v22)
print("v21:", v21)

# Option A: Fan [0,1,2] + [0,2,3]
a1 = tri_area(v23, v24, v22)
a2 = tri_area(v23, v22, v21)
print(f"Fan areas: t1={a1}, t2={a2}, sum={a1+a2}")

# Option B: Strip [0,1,2] + [1,2,3]
b1 = tri_area(v23, v24, v22)
b2 = tri_area(v24, v22, v21)
print(f"Strip areas: t1={b1}, t2={b2}, sum={b1+b2}")

# Option C: Perimeter [23, 24, 21, 22]
c1 = tri_area(v23, v24, v21)
c2 = tri_area(v23, v21, v22)
print(f"Perimeter areas: t1={c1}, t2={c2}, sum={c1+c2}")
