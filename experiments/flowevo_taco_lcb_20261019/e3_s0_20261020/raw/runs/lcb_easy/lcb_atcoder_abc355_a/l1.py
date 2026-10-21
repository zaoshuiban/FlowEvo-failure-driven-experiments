import sys

A, B = map(int, sys.stdin.readline().split())

candidates = [i for i in range(1, 4) if i != A and i != B]

if len(candidates) == 1:
    print(candidates[0])
else:
    print(-1)