import sys

data = list(map(int, sys.stdin.buffer.read().split()))

n = data[0]
ax, ay = data[1], data[2]
bx, by = data[3], data[4]
cx, cy = data[5], data[6]

if (bx < ax) == (cx < ax) and (by < ay) == (cy < ay):
    print("YES")
else:
    print("NO")