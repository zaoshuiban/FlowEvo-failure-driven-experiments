import sys


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False
    for b in data:
        if 48 <= b <= 57:
            num = num * 10 + (b - 48)
            inside = True
        elif inside:
            yield num
            num = 0
            inside = False
    if inside:
        yield num


def main():
    it = int_generator()

    n = next(it)
    m = next(it)
    k = next(it)

    grid = []
    for _ in range(n):
        row = bytearray(m)
        for j in range(m):
            row[j] = next(it)
        grid.append(row)

    sentinel = n + 1

    # parent[c][r] = first still-horizontal cell at or below row r in column c
    parent = []
    for c in range(m):
        p = [sentinel] * (n + 2)
        nxt = sentinel
        for r in range(n, 0, -1):
            if grid[r - 1][c] != 2:
                nxt = r
                p[r] = r
            else:
                p[r] = nxt
        parent.append(p)

    answers = []

    for _ in range(k):
        c = next(it) - 1
        r = 1

        while True:
            p = parent[c]

            # Find first active cell at or below row r in this column
            x = r
            while p[x] != x:
                p[x] = p[p[x]]
                x = p[x]
            rr = x

            if rr == sentinel:
                answers.append(str(c + 1))
                break

            direction = grid[rr - 1][c]

            # This cell is visited and becomes direction 2
            x = rr + 1
            while p[x] != x:
                p[x] = p[p[x]]
                x = p[x]
            p[rr] = x

            r = rr

            if direction == 1:
                c += 1
            else:  # direction == 3
                c -= 1

    sys.stdout.write(" ".join(answers))


if __name__ == "__main__":
    main()