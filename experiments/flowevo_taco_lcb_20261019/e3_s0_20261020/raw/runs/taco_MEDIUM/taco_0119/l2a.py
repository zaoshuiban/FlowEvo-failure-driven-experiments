import sys

n, m = map(int, sys.stdin.readline().split())

a = min(n, m)
print(a + 1)

for x in range(a + 1):
    y = a - x
    print(x, y)