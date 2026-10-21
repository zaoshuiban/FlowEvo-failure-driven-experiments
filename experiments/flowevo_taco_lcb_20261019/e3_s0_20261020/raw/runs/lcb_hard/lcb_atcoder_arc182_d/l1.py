import sys


def canonical(seq, m):
    n = len(seq)
    h = [0] * n
    h[0] = seq[0]
    for i in range(1, n):
        d = (seq[i] - seq[i - 1]) % m
        h[i] = h[i - 1] + d
    return h


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    a = [next(it) for _ in range(n)]
    b = [next(it) for _ in range(n)]

    if m == 2:
        print(0 if a == b else -1)
        return

    ha = canonical(a, m)
    hb = canonical(b, m)

    c = [ha[i] - hb[i] for i in range(n)]
    c.sort()

    candidates = set()
    for idx in (n // 2, (n - 1) // 2):
        base = c[idx] // m
        for d in range(-5, 6):
            candidates.add(base + d)

    ans = None
    for q in candidates:
        shift = q * m
        cost = 0
        for x in c:
            cost += abs(x - shift)
        if ans is None or cost < ans:
            ans = cost

    print(ans)


if __name__ == "__main__":
    solve()