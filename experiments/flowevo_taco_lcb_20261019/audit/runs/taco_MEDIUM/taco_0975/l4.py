import sys
from collections import deque


def main() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    r1 = int(data[1]) - 1
    c1 = int(data[2]) - 1
    r2 = int(data[3]) - 1
    c2 = int(data[4]) - 1
    grid = data[5:5 + n]

    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def bfs(sr: int, sc: int):
        visited = [[False] * n for _ in range(n)]
        cells = []
        q = deque([(sr, sc)])
        visited[sr][sc] = True

        while q:
            r, c = q.popleft()
            cells.append((r, c))

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < n
                    and 0 <= nc < n
                    and not visited[nr][nc]
                    and grid[nr][nc] == '0'
                ):
                    visited[nr][nc] = True
                    q.append((nr, nc))

        return cells, visited

    component1, visited1 = bfs(r1, c1)

    if visited1[r2][c2]:
        print(0)
        return

    component2, _ = bfs(r2, c2)

    answer = 10**18
    for x1, y1 in component1:
        for x2, y2 in component2:
            cost = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
            if cost < answer:
                answer = cost

    print(answer)


if __name__ == "__main__":
    main()