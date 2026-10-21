import sys
from collections import deque

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    cells = []
    for token in data[1:]:
        cells.extend(token)

    size = n * n
    start = end = -1
    for i in range(size):
        if cells[i] == 'S':
            start = i
        elif cells[i] == 'E':
            end = i

    dist = [-1] * size
    dist[start] = 0

    q = deque([start])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while q:
        cur = q.popleft()

        if cur == end:
            break

        r, c = divmod(cur, n)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < n and 0 <= nc < n:
                nxt = nr * n + nc

                if dist[nxt] == -1 and cells[nxt] != 'T':
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)

    print(dist[end])

if __name__ == "__main__":
    solve()