import sys
from collections import deque

def solve():
    input = sys.stdin.readline

    n, m, k = map(int, input().split())
    grid = [list(input().strip()) for _ in range(n)]

    visited = [[False] * m for _ in range(n)]
    lakes = []

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for i in range(n):
        for j in range(m):
            if grid[i][j] == '.' and not visited[i][j]:
                queue = deque([(i, j)])
                visited[i][j] = True

                cells = []
                touches_border = False

                while queue:
                    x, y = queue.popleft()
                    cells.append((x, y))

                    if x == 0 or x == n - 1 or y == 0 or y == m - 1:
                        touches_border = True

                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy

                        if 0 <= nx < n and 0 <= ny < m:
                            if grid[nx][ny] == '.' and not visited[nx][ny]:
                                visited[nx][ny] = True
                                queue.append((nx, ny))

                if not touches_border:
                    lakes.append((len(cells), cells))

    lakes.sort(key=lambda item: item[0])

    to_remove = len(lakes) - k
    answer = 0

    for i in range(to_remove):
        size, cells = lakes[i]
        answer += size

        for x, y in cells:
            grid[x][y] = '*'

    print(answer)

    for row in grid:
        print(''.join(row))


if __name__ == "__main__":
    solve()