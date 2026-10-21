import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    T = data[0]
    idx = 1
    answers = []

    for _ in range(T):
        X, Y, Z, A, B, C = data[idx:idx + 6]
        idx += 6

        x, y, z = sorted((X, Y, Z))

        total = x + y + z
        K = x + y - z

        candidates = set()

        for base in (0, x, K, K + 1):
            for d in range(-3, 4):
                t = base + d
                if 0 <= t <= x:
                    candidates.add(t)

        best = 10**30
        use_double = B < 2 * A

        for t in candidates:
            a = x - t
            b = y - t
            c = z - t

            remaining = total - 3 * t

            if use_double:
                doubles = remaining // 2
                pairs_possible = a + b
                if pairs_possible < doubles:
                    doubles = pairs_possible

                cost = C * t + B * doubles + A * (remaining - 2 * doubles)
            else:
                cost = C * t + A * remaining

            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()