import sys


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

    lakes = []

    for i in range(n):
        for j in range(m):
            if grid[i][j] == '.' and not visited[i][j]:
                stack = [(i, j)]
                visited[i][j] = True
                cells = []
                touches_border = False

                while stack:
                    x, y = stack.pop()
                    cells.append((x, y))

                    if x == 0 or x == n - 1 or y == 0 or y == m - 1:
                        touches_border = True

                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < n
                            and 0 <= ny < m
                            and grid[nx][ny] == '.'
                            and not visited[nx][ny]
                        ):
                            visited[nx][ny] = True
                            stack.append((nx, ny))

                if not touches_border:
                    lakes.append(cells)

    lakes.sort(key=len)

    answer = 0
    lakes_to_remove = len(lakes) - k

    for cells in lakes[:lakes_to_remove]:
        answer += len(cells)
        for x, y in cells:
            grid[x][y] = '*'

    result = [str(answer)]
    result.extend(''.join(row) for row in grid)

    sys.stdout.write('\n'.join(result) + '\n')


if __name__ == "__main__":
    main()