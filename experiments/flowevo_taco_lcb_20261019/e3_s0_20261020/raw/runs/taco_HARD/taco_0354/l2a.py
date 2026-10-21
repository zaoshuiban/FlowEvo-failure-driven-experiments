import sys


def solve() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)

    answers = []
    NEG_INF = -10**30

    for _ in range(t):
        n = next(data)
        q = next(data)

        a = [next(data) for _ in range(n)]

        m = n - 1
        size = 1
        while size < m:
            size <<= 1

        seg = [NEG_INF] * (2 * size)

        for i in range(m):
            seg[size + i] = a[i] - a[i + 1]

        for p in range(size - 1, 0, -1):
            seg[p] = max(seg[p << 1], seg[p << 1 | 1])

        def update(pos: int, value: int) -> None:
            p = size + pos
            seg[p] = value
            p >>= 1

            while p:
                seg[p] = max(seg[p << 1], seg[p << 1 | 1])
                p >>= 1

        for _ in range(q):
            idx = next(data) - 1
            x = next(data)

            a[idx] = x

            if idx > 0:
                update(idx - 1, a[idx - 1] - a[idx])

            if idx < n - 1:
                update(idx, a[idx] - a[idx + 1])

            max_drop = seg[1]
            answers.append(str(max_drop if max_drop > 0 else 0))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()