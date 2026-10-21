import sys

A, B = map(int, sys.stdin.readline().split())
C = A - B

if C % 10 == 9:
    print(C - 1)
else:
    print(C + 1)