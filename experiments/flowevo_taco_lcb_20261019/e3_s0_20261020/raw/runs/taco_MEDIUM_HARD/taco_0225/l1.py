import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        parent = list(range(n + 1))
        rank = [0] * (n + 1)

        def find(v: int) -> int:
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        off_diagonal = 0
        cycles = 0

        for _ in range(m):
            x = next(it)
            y = next(it)

            if x == y:
                continue

            off_diagonal += 1

            rx = find(x)
            ry = find(y)

            if rx == ry:
                cycles += 1
            else:
                if rank[rx] < rank[ry]:
                    rx, ry = ry, rx
                parent[ry] = rx
                if rank[rx] == rank[ry]:
                    rank[rx] += 1

        answers.append(str(off_diagonal + cycles))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()