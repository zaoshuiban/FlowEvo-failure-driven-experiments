import sys
from collections import deque

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    cells = ''.join(data[1:])

    grid = [list(cells[i * n:(i + 1) * n]) for i in range(n)]

    start = end = None
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 'S':
                start = (i, j)
            elif grid[i][j] == 'E':
                end = (i, j)

    if start is None or end is None:
        return

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    visited = [[False] * n for _ in range(n)]

    sr, sc = start
    er, ec = end

    queue = deque([(sr, sc, 0)])
    visited[sr][sc] = True

    while queue:
        r, c, dist = queue.popleft()

        if (r, c) == (er, ec):
            print(dist)
            return

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < n and 0 <= nc < n:
                if not visited[nr][nc] and grid[nr][nc] != 'T':
                    visited[nr][nc] = True
                    queue.append((nr, nc, dist + 1))

    print(-1)

if __name__ == "__main__":
    main()