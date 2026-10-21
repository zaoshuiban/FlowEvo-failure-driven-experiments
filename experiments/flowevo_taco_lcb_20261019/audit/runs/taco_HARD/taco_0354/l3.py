import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []
    NEG = -10**30

    for _ in range(t):
        n = next(it)
        q = next(it)
        a = [next(it) for _ in range(n)]

        m = n - 1  # Number of adjacent differences

        size = 1
        while size < m:
            size <<= 1

        tree = [NEG] * (size << 1)

        for i in range(m):
            tree[size + i] = a[i] - a[i + 1]

        for i in range(size - 1, 0, -1):
            left = tree[i << 1]
            right = tree[i << 1 | 1]
            tree[i] = left if left > right else right

        for _ in range(q):
            idx = next(it) - 1
            x = next(it)

            if a[idx] != x:
                a[idx] = x

                # Update difference at idx - 1
                if idx > 0:
                    pos = idx - 1
                    val = a[pos] - a[pos + 1]

                    p = size + pos
                    tree[p] = val
                    p >>= 1

                    while p:
                        left = tree[p << 1]
                        right = tree[p << 1 | 1]
                        tree[p] = left if left > right else right
                        p >>= 1

                # Update difference at idx
                if idx < m:
                    pos = idx
                    val = a[pos] - a[pos + 1]

                    p = size + pos
                    tree[p] = val
                    p >>= 1

                    while p:
                        left = tree[p << 1]
                        right = tree[p << 1 | 1]
                        tree[p] = left if left > right else right
                        p >>= 1

            best = tree[1] if m > 0 else 0
            if best < 0:
                best = 0

            answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()