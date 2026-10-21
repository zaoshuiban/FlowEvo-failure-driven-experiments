import sys

S = sys.stdin.readline().strip()
print(S[S.rfind('.') + 1:])