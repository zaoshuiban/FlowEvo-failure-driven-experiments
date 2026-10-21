import sys
from collections import deque


def main() -> None:
    input = sys.stdin.buffer.readline

    n, m, k = map(int, input().split())
    grid = [input().strip() for _ in range(n)]

    x1, y1, x2, y2 = map(int, input().split())
    x1 -= 1
    y1 -= 1
    x2 -= 1
    y2 -= 1

    if x1 == x2 and y1 == y2:
        print(0)
        return

    start = x1 * m + y1
    target = x2 * m + y2

    dist = [-1] * (n * m)
    dist[start] = 0

    q = deque([start])
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    while q:
        pos = q.popleft()
        x = pos // m
        y = pos - x * m
        next_dist = dist[pos] + 1

        for dx, dy in directions:
            nx = x + dx
            ny = y + dy

            for _ in range(k):
                if nx < 0 or nx >= n or ny < 0 or ny >= m:
                    break

                if grid[nx][ny] == 35:  # ord('#')
                    break

                npos = nx * m + ny
                cur_dist = dist[npos]

                if cur_dist == -1:
                    dist[npos] = next_dist

                    if npos == target:
                        print(next_dist)
                        return

                    q.append(npos)
                else:
                    if cur_dist < next_dist:
                        break

                nx += dx
                ny += dy

    print(-1)


if __name__ == "__main__":
    main()