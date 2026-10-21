import sys

S = sys.stdin.readline().strip()

if S[0].isupper() and all(c.islower() for c in S[1:]):
    print("Yes")
else:
    print("No")