import sys

values = list(map(int, sys.stdin.read().split()))
a, b, c, d, e, f = values[:6]
g, h, i, j, k, l = values[6:12]

overlap_x = max(a, g) < min(d, j)
overlap_y = max(b, h) < min(e, k)
overlap_z = max(c, i) < min(f, l)

print("Yes" if overlap_x and overlap_y and overlap_z else "No")