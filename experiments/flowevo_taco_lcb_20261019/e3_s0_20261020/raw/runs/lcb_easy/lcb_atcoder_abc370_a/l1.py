import sys

L, R = map(int, sys.stdin.readline().split())

if L == 1 and R == 0:
    print("Yes")
elif L == 0 and R == 1:
    print("No")
else:
    print("Invalid")