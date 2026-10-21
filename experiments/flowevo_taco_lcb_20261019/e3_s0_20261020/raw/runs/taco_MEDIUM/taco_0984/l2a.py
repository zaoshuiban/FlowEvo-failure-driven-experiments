import sys

s = sys.stdin.readline().strip()

v = 0  # next column for vertical tiles (rows 1-2)
h = 0  # 0 -> column 1, 1 -> column 3 for horizontal tiles (row 3)

ans = []

for ch in s:
    if ch == '0':
        ans.append(f"1 {v + 1}")
        v = (v + 1) % 4
    else:
        col = 1 if h == 0 else 3
        ans.append(f"3 {col}")
        h ^= 1

print("\n".join(ans))