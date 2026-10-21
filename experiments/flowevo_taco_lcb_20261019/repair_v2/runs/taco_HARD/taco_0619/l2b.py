import sys


def solve():
    input = sys.stdin.buffer.readline

    n, m = map(int, input().split())
    grid = []

    col_count = [0] * m
    col_first = [n] * m
    col_last = [-1] * m

    empty_rows = 0
    valid = True

    for i in range(n):
        s = input().strip()
        grid.append(s)

        first = s.find(b'#')
        if first == -1:
            empty_rows += 1
        else:
            last = s.rfind(b'#')
            if s.count(b'#') != last - first + 1:
                valid = False

        for j, ch in enumerate(s):
            if ch == 35:  # ord('#')
                col_count[j] += 1
                if col_first[j] == n:
                    col_first[j] = i
                col_last[j] = i

    empty_cols = 0

    for j in range(m):
        if col_count[j] == 0:
            empty_cols += 1
        else:
            if col_count[j] != col_last[j] - col_first[j] + 1:
                valid = False

    if (empty_rows > 0) != (empty_cols > 0):
        valid = False

    if not valid:
        print(-1)
        return

    visited = bytearray(n * m)
    components = 0

    for i in range(n):
        row = grid[i]
        base = i * m

        for j in range(m):
            start = base + j
            if row[j] == 35 and not visited[start]:
                components += 1
                visited[start] = 1
                stack = [start]

                while stack:
                    x = stack.pop()
                    r = x // m
                    c = x - r * m

                    if r > 0:
                        y = x - m
                        if not visited[y] and grid[r - 1][c] == 35:
                            visited[y] = 1
                            stack.append(y)

                    if r + 1 < n:
                        y = x + m
                        if not visited[y] and grid[r + 1][c] == 35:
                            visited[y] = 1
                            stack.append(y)

                    if c > 0:
                        y = x - 1
                        if not visited[y] and grid[r][c - 1] == 35:
                            visited[y] = 1
                            stack.append(y)

                    if c + 1 < m:
                        y = x + 1
                        if not visited[y] and grid[r][c + 1] == 35:
                            visited[y] = 1
                            stack.append(y)

    print(components)


if __name__ == "__main__":
    solve()