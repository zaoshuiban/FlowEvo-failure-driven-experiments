import sys
from collections import deque


def main():
    input = sys.stdin.readline

    n = int(input())
    r1, c1 = map(int, input().split())
    r2, c2 = map(int, input().split())

    r1 -= 1
    c1 -= 1
    r2 -= 1
    c2 -= 1

    grid = [input().strip() for _ in range(n)]

    def get_component(sr, sc):
        visited = [[False] * n for _ in range(n)]
        queue = deque([(sr, sc)])
        visited[sr][sc] = True
        cells = []

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while queue:
            r, c = queue.popleft()
            cells.append((r, c))

            for dr, dc in directions:
                nr, nc = r + dr, c + dc

                if (
                    0 <= nr < n
                    and 0 <= nc < n
                    and not visited[nr][nc]
                    and grid[nr][nc] == "0"
                ):
                    visited[nr][nc] = True
                    queue.append((nr, nc))

        return visited, cells

    visited_start, start_component = get_component(r1, c1)

    if visited_start[r2][c2]:
        print(0)
        return

    _, target_component = get_component(r2, c2)

    answer = 10**9

    for r1, c1 in start_component:
        for r2, c2 in target_component:
            cost = (r1 - r2) ** 2 + (c1 - c2) ** 2
            if cost < answer:
                answer = cost

    print(answer)


if __name__ == "__main__":
    main()