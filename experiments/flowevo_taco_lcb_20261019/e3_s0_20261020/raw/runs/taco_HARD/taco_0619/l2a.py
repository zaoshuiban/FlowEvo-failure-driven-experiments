import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    grid = data[2:2 + n]

    first_col = [-1] * m
    last_col = [-1] * m
    count_col = [0] * m

    empty_rows = 0

    for i, row in enumerate(grid):
        first = row.find(b'#')

        if first == -1:
            empty_rows += 1
        else:
            last = row.rfind(b'#')
            if row.count(b'#', first, last + 1) != last - first + 1:
                print(-1)
                return

        for j, cell in enumerate(row):
            if cell == 35:  # ord('#')
                if first_col[j] == -1:
                    first_col[j] = i
                last_col[j] = i
                count_col[j] += 1

    empty_cols = 0

    for j in range(m):
        if first_col[j] == -1:
            empty_cols += 1
        else:
            if count_col[j] != last_col[j] - first_col[j] + 1:
                print(-1)
                return

    if (empty_rows > 0) != (empty_cols > 0):
        print(-1)
        return

    if sum(count_col) == 0:
        print(0)
        return

    visited = [bytearray(m) for _ in range(n)]
    answer = 0

    for i in range(n):
        for j in range(m):
            if grid[i][j] == 35 and not visited[i][j]:
                answer += 1
                visited[i][j] = 1
                stack = [i * m + j]

                while stack:
                    v = stack.pop()
                    x = v // m
                    y = v - x * m

                    if x > 0 and grid[x - 1][y] == 35 and not visited[x - 1][y]:
                        visited[x - 1][y] = 1
                        stack.append((x - 1) * m + y)

                    if x + 1 < n and grid[x + 1][y] == 35 and not visited[x + 1][y]:
                        visited[x + 1][y] = 1
                        stack.append((x + 1) * m + y)

                    if y > 0 and grid[x][y - 1] == 35 and not visited[x][y - 1]:
                        visited[x][y - 1] = 1
                        stack.append(x * m + y - 1)

                    if y + 1 < m and grid[x][y + 1] == 35 and not visited[x][y + 1]:
                        visited[x][y + 1] = 1
                        stack.append(x * m + y + 1)

    print(answer)


if __name__ == "__main__":
    main()