import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    grid = data[2:2 + n]

    stride = m + 2
    black = bytearray((n + 2) * stride)

    col_first = [n] * m
    col_last = [-1] * m
    col_count = [0] * m

    empty_rows = 0
    valid = True

    for i in range(n):
        row = grid[i]

        first = row.find(b'#')
        if first == -1:
            empty_rows += 1
        else:
            last = row.rfind(b'#')
            if row.count(b'#') != last - first + 1:
                valid = False

        base = (i + 1) * stride + 1

        for j, ch in enumerate(row):
            if ch == 35:  # ord('#')
                black[base + j] = 1
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
        sys.stdout.write("-1\n")
        return

    components = 0

    for i in range(1, n + 1):
        base = i * stride

        for j in range(1, m + 1):
            start = base + j

            if not black[start]:
                continue

            components += 1
            black[start] = 0
            stack = [start]

            while stack:
                x = stack.pop()

                y = x - 1
                if black[y]:
                    black[y] = 0
                    stack.append(y)

                y = x + 1
                if black[y]:
                    black[y] = 0
                    stack.append(y)

                y = x - stride
                if black[y]:
                    black[y] = 0
                    stack.append(y)

                y = x + stride
                if black[y]:
                    black[y] = 0
                    stack.append(y)

    sys.stdout.write(str(components) + "\n")


if __name__ == "__main__":
    main()