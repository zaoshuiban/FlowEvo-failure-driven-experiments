import sys

s = sys.stdin.readline().strip()
t = s.rstrip('0')

print("YES" if t == t[::-1] else "NO")