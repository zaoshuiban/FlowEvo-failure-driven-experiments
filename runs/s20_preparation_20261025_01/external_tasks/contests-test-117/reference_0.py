from collections import deque
import sys

input = sys.stdin.readline

def get_ways(idx):
    ways = []
    if (idx[1] + 1 < m) and (rows[idx[0]][idx[1] + 1] == '.'):
        ways.append((idx[0], idx[1] + 1))
    if (idx[1] > 0) and (rows[idx[0]][idx[1] - 1] == '.'):
        ways.append((idx[0], idx[1] - 1))
    if (idx[0] + 1 < n) and (rows[idx[0] + 1][idx[1]] == '.'):
        ways.append((idx[0] + 1, idx[1]))
    if (idx[0] > 0) and (rows[idx[0] - 1][idx[1]] == '.'):
        ways.append((idx[0] - 1, idx[1]))
    return ways

n = int(input())
for i in range(n):
    n, m = list(map(int, input().split()))
    rows = []
    l_idx = None
    for j in range(n):
        row = list(input())
        rows.append(row)
        if (l_idx is None) and ('L' in row):
            l_idx = (j, row.index('L'))
    stek = deque()
    for way in get_ways(l_idx):
        stek.append(way)
    while len(stek) > 0:
        idx = stek.pop()
        ways = get_ways(idx)
        if len(ways) == 0:
            rows[idx[0]][idx[1]] = '+'
        elif len(ways) == 1:
            rows[idx[0]][idx[1]] = '+'
            stek.append(ways[0])
    for i in range(len(rows)):
        rows[i] = ''.join(rows[i])
    sys.stdout.write("\n".join(rows))