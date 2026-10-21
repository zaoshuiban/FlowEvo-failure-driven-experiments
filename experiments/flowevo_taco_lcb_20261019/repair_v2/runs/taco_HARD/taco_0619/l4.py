import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    grid = [bytearray(data[2 + i]) for i in range(n)]

    valid = True
    empty_rows = 0

    for i in range(n):
        row = grid[i]
        first = -1
        last = -1
        count = 0

        for j, ch in enumerate(row):
            if ch == 35:  # '#'
                count += 1
                if first == -1:
                    first = j
                last = j

        if count == 0:
            empty_rows += 1
        elif count != last - first + 1:
            valid = False

    col_count = [0] * m
    col_first = [n] * m
    col_last = [-1] * m

    for i in range(n):
        row = grid[i]
        for j, ch in enumerate(row):
            if ch == 35:
                col_count[j] += 1
                if col_first[j] == n:
                    col_first[j] = i
                col_last[j] = i

    empty_cols = 0

    for j in range(m):
        if col_count[j] == 0:
            empty_cols += 1
        elif col_count[j] != col_last[j] - col_first[j] + 1:
            valid = False

    if (empty_rows > 0) != (empty_cols > 0):
        valid = False

    if not valid:
        sys.stdout.write("-1\n")
        return

    components = 0

    for i in range(n):
        row = grid[i]
        for j in range(m):
            if row[j] != 35:
                continue

            components += 1
            row[j] = 46  # '.'
            stack = [i * m + j]

            while stack:
                pos = stack.pop()
                x = pos // m
                y = pos - x * m

                if x > 0:
                    nxt = grid[x - 1]
                    if nxt[y] == 35:
                        nxt[y] = 46
                        stack.append((x - 1) * m + y)

                if x + 1 < n:
                    nxt = grid[x + 1]
                    if nxt[y] == 35:
                        nxt[y] = 46
                        stack.append((x + 1) * m + y)

                if y > 0:
                    nxt = grid[x]
                    if nxt[y - 1] == 35:
                        nxt[y - 1] = 46
                        stack.append(x * m + y - 1)

                if y + 1 < m:
                    nxt = grid[x]
                    if nxt[y + 1] == 35:
                        nxt[y + 1] = 46
                        stack.append(x * m + y + 1)

    sys.stdout.write(str(components) + "\n")


if __name__ == "__main__":
    main()