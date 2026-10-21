import sys

N, T, A = map(int, sys.stdin.readline().split())

remaining = N - T - A

if T > A + remaining or A > T + remaining:
    print("Yes")
else:
    print("No")