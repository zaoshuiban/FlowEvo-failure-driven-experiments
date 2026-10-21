import sys


def solve() -> None:
    input_data = sys.stdin.buffer
    n, m = map(int, input_data.readline().split())
    grid = [input_data.readline().strip() for _ in range(n)]

    # Check that black cells in every row form one contiguous segment.
    empty_rows = 0
    for row in grid:
        has_black = False
        closed = False
        for ch in row:
            if ch == 35:  # '#'
                if closed:
                    print(-1)
                    return
                has_black = True
            else:
                if has_black:
                    closed = True
        if not has_black:
            empty_rows += 1

    # Check that black cells in every column form one contiguous segment.
    empty_cols = 0
    for j in range(m):
        has_black = False
        closed = False
        for i in range(n):
            if grid[i][j] == 35:  # '#'
                if closed:
                    print(-1)
                    return
                has_black = True
            else:
                if has_black:
                    closed = True
        if not has_black:
            empty_cols += 1

    # Empty rows and empty columns must either both exist or both not exist.
    if (empty_rows > 0) != (empty_cols > 0):
        print(-1)
        return

    # Count connected components of black cells.
    flat = b"".join(grid)
    total = n * m
    visited = bytearray(total)
    components = 0

    for start in range(total):
        if flat[start] != 35 or visited[start]:
            continue

        components += 1
        visited[start] = 1
        stack = [start]

        while stack:
            cur = stack.pop()
            x = cur // m
            y = cur - x * m

            if x > 0:
                nxt = cur - m
                if flat[nxt] == 35 and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)

            if x + 1 < n:
                nxt = cur + m
                if flat[nxt] == 35 and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)

            if y > 0:
                nxt = cur - 1
                if flat[nxt] == 35 and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)

            if y + 1 < m:
                nxt = cur + 1
                if flat[nxt] == 35 and not visited[nxt]:
                    visited[nxt] = 1
                    stack.append(nxt)

    print(components)


if __name__ == "__main__":
    solve()