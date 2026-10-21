import sys
from collections import deque


def reachable(start_r, start_c, grid, n):
    visited = [[False] * n for _ in range(n)]
    cells = []
    q = deque([(start_r, start_c)])
    visited[start_r][start_c] = True

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while q:
        r, c = q.popleft()
        cells.append((r, c))

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < n and 0 <= nc < n:
                if not visited[nr][nc] and grid[nr][nc] == '0':
                    visited[nr][nc] = True
                    q.append((nr, nc))

    return cells, visited


def main():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)

    n = int(next(it))
    r1 = int(next(it)) - 1
    c1 = int(next(it)) - 1
    r2 = int(next(it)) - 1
    c2 = int(next(it)) - 1

    grid = [next(it) for _ in range(n)]

    component1, visited1 = reachable(r1, c1, grid, n)

    if visited1[r2][c2]:
        print(0)
        return

    component2, _ = reachable(r2, c2, grid, n)

    answer = float('inf')

    for r1, c1 in component1:
        for r2, c2 in component2:
            cost = (r1 - r2) ** 2 + (c1 - c2) ** 2
            answer = min(answer, cost)

    print(answer)


if __name__ == "__main__":
    main()