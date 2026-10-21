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
                q = deque([(i, j)])
                visited[i][j] = True

                cells = []
                touches_border = False

                while q:
                    x, y = q.popleft()
                    cells.append((x, y))

                    if x == 0 or x == n - 1 or y == 0 or y == m - 1:
                        touches_border = True

                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy

                        if 0 <= nx < n and 0 <= ny < m:
                            if not visited[nx][ny] and grid[nx][ny] == '.':
                                visited[nx][ny] = True
                                q.append((nx, ny))

                if not touches_border:
                    lakes.append(cells)

    lakes.sort(key=len)

    remove_count = len(lakes) - k
    answer = 0

    for idx in range(remove_count):
        for x, y in lakes[idx]:
            grid[x][y] = '*'
        answer += len(lakes[idx])

    print(answer)
    for row in grid:
        print(''.join(row))


if __name__ == "__main__":
    solve()