import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    k = int(data[2])

    grid = [list(data[i + 3].decode()) for i in range(n)]

    visited = [[False] * m for _ in range(n)]
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    # Mark all water connected to the border as ocean.
    q = deque()
    for i in range(n):
        for j in range(m):
            if (
                (i == 0 or i == n - 1 or j == 0 or j == m - 1)
                and grid[i][j] == '.'
                and not visited[i][j]
            ):
                visited[i][j] = True
                q.append((i, j))

    while q:
        x, y = q.popleft()
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < n
                and 0 <= ny < m
                and not visited[nx][ny]
                and grid[nx][ny] == '.'
            ):
                visited[nx][ny] = True
                q.append((nx, ny))

    # Every remaining unvisited water component is a lake.
    lakes = []

    for i in range(n):
        for j in range(m):
            if grid[i][j] == '.' and not visited[i][j]:
                q = deque([(i, j)])
                visited[i][j] = True
                cells = []

                while q:
                    x, y = q.popleft()
                    cells.append((x, y))

                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < n
                            and 0 <= ny < m
                            and not visited[nx][ny]
                            and grid[nx][ny] == '.'
                        ):
                            visited[nx][ny] = True
                            q.append((nx, ny))

                lakes.append(cells)

    # Remove the smallest lakes until exactly k lakes remain.
    lakes.sort(key=len)
    answer = 0

    for idx in range(len(lakes) - k):
        answer += len(lakes[idx])
        for x, y in lakes[idx]:
            grid[x][y] = '*'

    result = [str(answer)]
    result.extend(''.join(row) for row in grid)
    sys.stdout.write('\n'.join(result) + '\n')


if __name__ == "__main__":
    main()