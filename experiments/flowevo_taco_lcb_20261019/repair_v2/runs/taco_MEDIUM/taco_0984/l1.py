import sys

s = sys.stdin.readline().strip()

vertical_pos = 0
horizontal_pos = 0

ans = []

for ch in s:
    if ch == '0':
        col = vertical_pos + 1
        ans.append(f"1 {col}")
        vertical_pos = (vertical_pos + 1) % 4
    else:
        col = 1 if horizontal_pos == 0 else 3
        ans.append(f"3 {col}")
        horizontal_pos = (horizontal_pos + 1) % 2

sys.stdout.write("\n".join(ans))