import sys

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

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def collect_component(sr, sc):
        seen = [[False] * n for _ in range(n)]
        stack = [(sr, sc)]
        seen[sr][sc] = True
        cells = []

        while stack:
            r, c = stack.pop()
            cells.append((r, c))

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n:
                    if not seen[nr][nc] and grid[nr][nc] == '0':
                        seen[nr][nc] = True
                        stack.append((nr, nc))

        return seen, cells

    seen1, component1 = collect_component(r1, c1)

    if seen1[r2][c2]:
        print(0)
        return

    _, component2 = collect_component(r2, c2)

    answer = 10**9

    for r1, c1 in component1:
        for r2, c2 in component2:
            cost = (r1 - r2) ** 2 + (c1 - c2) ** 2
            if cost < answer:
                answer = cost

    print(answer)


if __name__ == "__main__":
    main()