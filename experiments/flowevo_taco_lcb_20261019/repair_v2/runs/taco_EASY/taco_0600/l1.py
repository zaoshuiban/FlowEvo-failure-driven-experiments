import sys

n = int(sys.stdin.readline())

if n % 2 == 1:
    print(0)
else:
    m = n // 2
    print((m - 1) // 2)