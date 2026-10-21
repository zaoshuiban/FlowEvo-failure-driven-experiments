import sys

s = sys.stdin.readline().strip()

color_at_mod = [None] * 4

for i, ch in enumerate(s):
    if ch != '!':
        color_at_mod[i % 4] = ch

answer = {'R': 0, 'B': 0, 'Y': 0, 'G': 0}

for i, ch in enumerate(s):
    if ch == '!':
        answer[color_at_mod[i % 4]] += 1

print(answer['R'], answer['B'], answer['Y'], answer['G'])