import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        parent = list(range(n + 1))
        size = [1] * (n + 1)

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        off_diagonal = 0
        extra_moves = 0

        for _ in range(m):
            x = next(it)
            y = next(it)

            if x == y:
                continue

            off_diagonal += 1

            rx = find(x)
            ry = find(y)

            if rx == ry:
                extra_moves += 1
            else:
                if size[rx] < size[ry]:
                    rx, ry = ry, rx
                parent[ry] = rx
                size[rx] += size[ry]

        answers.append(str(off_diagonal + extra_moves))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()