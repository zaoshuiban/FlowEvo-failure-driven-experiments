import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        a = [next(it) for _ in range(n)]

        diff = [0] * (2 * k + 3)
        pairs = n // 2

        for i in range(pairs):
            p = a[i]
            q = a[n - 1 - i]

            s = p + q
            low = min(p, q) + 1
            high = max(p, q) + k

            # At most one replacement is needed for sums in [low, high]
            diff[low] -= 1
            diff[high + 1] += 1

            # No replacement is needed when the sum is already s
            diff[s] -= 1
            diff[s + 1] += 1

        current = 0
        best = n

        for x in range(2, 2 * k + 1):
            current += diff[x]
            cost = n + current
            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()